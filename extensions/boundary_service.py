#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
from enum import Enum

from flask import Flask
from flask_socketio import SocketIO, emit

import time
import requests
import json
import uuid
import re
import os

from esdl import esdl
from esdl.processing import ESDLGeometry
from esdl.undo_wrapper import undo_record_changes
from extensions.session_manager import get_project_manager, get_session, set_session, get_session_for_esid, \
    set_session_for_esid
from extensions.settings_storage import SettingsStorage

from src.shape import Shape
import src.settings as settings
import src.log as log
from utils.utils import str2float

logger = log.get_logger(__name__)

BOUNDARY_SERVICE_SYSTEM_CONFIG = 'BOUNDARY_SERVICE_SYSTEM_CONFIG'
BOUNDARY_SERVICE_USER_CONFIG = 'BOUNDARY_SERVICE_USER_CONFIG'

boundary_service = None


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


# ---------------------------------------------------------------------------------------------------------------------
#  GEIS Boundary service access
# ---------------------------------------------------------------------------------------------------------------------
boundary_service_mapping = {
    'ZIPCODE': 'zipcodes',
    'NEIGHBOURHOOD': 'neighbourhoods',
    'DISTRICT': 'districts',
    'MUNICIPALITY': 'municipalities',
    'REGION': 'regions',
    'PROVINCE': 'provinces',
    'COUNTRY': 'countries'
}

#create a cache for the boundary service
boundary_cache = dict()
DEFAULT_BOUNDARIES_YEAR = 2019


class ServiceAreaDataType(Enum):
    """Type of service area data, either VIVET DSO data or CapaciteitsKaart data"""

    VIVET_DSO_data = "VIVET_DSO_data"
    Capaciteitskaart_data = "Capaciteitskaart_data"


def is_valid_boundary_id(id):
    return re.match('PV[0-9]{2,2}|ES[0-9]{2,2}|GM[0-9]{4,4}|WK[0-9]{6,6}|BU[0-9]{8,8}|[0-9]{2,2}', id.upper())


# ---------------------------------------------------------------------------------------------------------------------
#  Get boundary information
# ---------------------------------------------------------------------------------------------------------------------
class BoundaryService:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.plugin_settings = self.get_settings()
        self.register()

        if settings.boundaries_config["host"] is None or settings.boundaries_config["host"] == "":
            logger.warn("Warning: Boundary service is not configured.")

        global boundary_service
        if boundary_service:
            logger.error("ERROR: Only one BoundaryService object can be instantiated")
        else:
            boundary_service = self

    @staticmethod
    def get_instance():
        global boundary_service
        return boundary_service

    # Do we want system_settings here, e.g. for the service endpoint configuration?
    def get_settings(self):
        boundary_service_plugin_settings = dict()
        if self.settings_storage.has_system(BOUNDARY_SERVICE_SYSTEM_CONFIG):
            boundary_service_plugin_settings = self.settings_storage.get_system(BOUNDARY_SERVICE_SYSTEM_CONFIG)
        else:
            boundary_service_plugin_settings = {
                'parameter': 'value'
            }
            self.settings_storage.set_system(BOUNDARY_SERVICE_SYSTEM_CONFIG, boundary_service_plugin_settings)
        return boundary_service_plugin_settings

    def register(self):
        logger.info('Registering BoundaryService extension')

        @self.flask_app.route('/boundaries_names/<scope_type>')
        def get_boundaries_names(scope_type):
            with self.flask_app.app_context():
                print("getting boundaries names information")

                user = get_session('user-email')
                user_settings = self.get_user_settings(user)
                boundaries_year = str(user_settings['boundaries_year'])

                try:
                    url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                          settings.boundaries_config["path_names"] + '/YEAR/' + boundaries_year + '/' + scope_type
                    print(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        reply = json.loads(r.text)
                        return {"boundaries_names": reply}

                except Exception as e:
                    print('ERROR in accessing Boundaries service: ' + str(e))
                    return 'ERROR in accessing Boundaries service: ' + str(e), 404

        @self.flask_app.route('/boundaries_names/<select_scope_type>/<select_scope_id>/<scope_type>')
        def get_subboundaries_names(select_scope_type, select_scope_id, scope_type):
            with self.flask_app.app_context():
                print("getting boundaries names information")

                user = get_session('user-email')
                user_settings = self.get_user_settings(user)
                boundaries_year = str(user_settings['boundaries_year'])

                try:
                    url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                          settings.boundaries_config["path_names"] + '/YEAR/' + boundaries_year + '/' \
                          + select_scope_type + '/' + select_scope_id + '/' + scope_type
                    print(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        reply = json.loads(r.text)
                        return {"boundaries_names": reply}

                except Exception as e:
                    print('ERROR in accessing Boundaries service: ' + str(e))
                    return 'ERROR in accessing Boundaries service: ' + str(e), 404

        @self.socketio.on('get_boundary_service_settings', namespace='/esdl')
        def get_boundary_service_settings():
            user = get_session('user-email')
            user_settings = self.get_user_settings(user)
            return user_settings

        @self.socketio.on('set_boundary_service_setting', namespace='/esdl')
        def get_boundary_service_settings(setting):
            user = get_session('user-email')
            self.set_user_setting(user, setting['name'], setting['value'])

        @self.socketio.on('get_boundary_info', namespace='/esdl')
        @undo_record_changes(label="Add boundary information")
        def get_boundary_info(info):
            print('get_boundary_info:')
            print(info)

            user = get_session('user-email')
            user_settings = self.get_user_settings(user)
            boundaries_year = user_settings['boundaries_year']

            active_es_id = get_session('active_es_id')
            shape_dictionary = get_session_for_esid(active_es_id, 'shape_dictionary')
            if not shape_dictionary:
                shape_dictionary = {}

            identifier = info["identifier"]
            toparea_name = info["toparea_name"]
            scope = info["scope"]
            subscope_enabled = info["subscope_enabled"]
            subscope = info["subscope"]
            select_subareas = info["select_subareas"]
            selected_subareas = info["selected_subareas"]
            initialize_ES = info["initialize_ES"]
            add_boundary_to_ESDL = info["add_boundary_to_ESDL"]
            add_service_area_info = info["add_service_area_info"]
            add_service_area_ck_info = info["add_service_area_ck_info"]
            add_station_info = info["add_station_info"]
            add_service_area_tennet_info = info["add_service_area_tennet_info"]
            if add_service_area_tennet_info == "0":
                add_service_area_tennet_info = None
            use_capacity_data_for = info["use_capacity_data_for"]

            if not is_valid_boundary_id(identifier):
                send_alert("Not a valid identifier. Try identifiers like PV27 (Noord-Holland) or GM0060 (Ameland)")
                return False

            active_es_id = get_session('active_es_id')
            pm = get_project_manager()
            active_variant = pm.active_variant
            es_edit = pm.get_active_energy_system()
            instance = es_edit.instance
            area = instance[0].area

            area_list = []
            boundary = None
            if subscope_enabled:
                self.__preload_subboundaries_in_cache(boundaries_year, esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                               esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                               str.upper(identifier))
            else:
                boundary = self.get_boundary_from_service(boundaries_year, esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
                if boundary:
                    geom = boundary['geom']
                    shape = Shape.parse_geojson_geometry(boundary['geom'])
                    if shape:
                        shape_dictionary[identifier] = shape

                    for i in range(0, len(geom['coordinates'])):
                        if len(geom['coordinates']) > 1:
                            area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                        else:
                            area_id_number = ""
                        area_list.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": geom['coordinates'][i]
                            },
                            "properties": {
                                "id": area.id + area_id_number,
                                "name": area.name,
                                "KPIs": []
                            }
                        })

            if initialize_ES:
                # change ID, name and scope of ES
                if select_subareas:
                    area.id = "part of " + identifier
                else:
                    area.id = identifier

                # Area ID has changed, re-add to dictionairy
                pm.add_object_to_dict(active_es_id, area)

                area.scope = esdl.AreaScopeEnum.from_string(str.upper(scope))
                area.name = toparea_name
                es_edit.name = toparea_name
                active_variant.name = toparea_name
                if add_boundary_to_ESDL:
                    # returns boundary: { type: '', boundary: [[[[ ... ]]]] } (multipolygon in RD)
                    if not boundary:    # check if already requested
                        boundary = self.get_boundary_from_service(boundaries_year, esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
                    if boundary:
                        geometry = ESDLGeometry.create_geometry_from_geom(boundary['geom'])
                        area.geometry = geometry

                        shape = Shape.parse_geojson_geometry(boundary['geom'])
                        if shape:
                            shape_dictionary[identifier] = shape

                    # boundary = get_boundary_from_service(area_scope, area_id)
                    # if boundary:
                    #    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})

            if subscope_enabled:
                boundaries = self.__get_subboundaries_from_service(boundaries_year, esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                                            esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                                            str.upper(identifier))
                # result (boundaries) is an ARRAY of:
                # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
                # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

                if not boundaries:
                    send_alert('Error processing boundary information or no boundary information returned')

                if initialize_ES:
                    # If "Add supply area DSO" is checked, also put the other areas in a logical group
                    if add_service_area_info or add_service_area_ck_info:
                        cbs_area_logical_group = esdl.Area(id=str(uuid.uuid4()), name="CBS gebieden",
                                                           logicalGroup=True)
                        area.area.append(cbs_area_logical_group)
                        pm.add_object_to_dict(active_es_id, cbs_area_logical_group)
                        area_to_add = cbs_area_logical_group
                    else:
                        area_to_add = area

                for boundary in boundaries:
                    geom = None
                    try:
                        # geom = json.loads(boundary["geom"])
                        geom = boundary["geom"]

                        shape = Shape.parse_geojson_geometry(boundary['geom'])
                        if shape:
                            shape_dictionary[boundary['code']] = shape
                    except Exception as e:
                        logger.exception('Error parsing JSON from GEIS boundary service: '+ str(e))

                    if geom:
                        skip_subarea = False
                        if select_subareas and selected_subareas and boundary["code"] not in selected_subareas:
                            skip_subarea = True

                        if not skip_subarea:
                            sub_area_id = boundary["code"]
                            sub_area_name = boundary["name"]

                            if initialize_ES:
                                sub_area = esdl.Area()
                                sub_area.id = sub_area_id
                                sub_area.name = sub_area_name
                                sub_area.scope = esdl.AreaScopeEnum.from_string(str.upper(subscope))

                                if add_boundary_to_ESDL:
                                    geometry = ESDLGeometry.create_geometry_from_geom(geom)
                                    sub_area.geometry = geometry

                                area_to_add.area.append(sub_area)
                                pm.add_object_to_dict(active_es_id, sub_area)

                            for i in range(0, len(geom['coordinates'])):
                                if len(geom['coordinates']) > 1:
                                    area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                                else:
                                    area_id_number = ""
                                area_list.append({
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": geom['coordinates'][i]
                                    },
                                    "properties": {
                                        "id": sub_area_id + area_id_number,
                                        "name": sub_area_name,
                                        "KPIs": []
                                    }
                                })

            if add_station_info:
                stations = self.get_station_from_service(
                    boundaries_year,
                    use_capacity_data_for,
                    esdl.AreaScopeEnum.from_string(str.upper(scope)),
                    str.upper(identifier)
                )
                if stations:
                    logger.info("BoundaryService: stations", stations=stations)
                    stations_dict = {}

                    for st in stations:
                        stations_dict[st["station"]] = st

                    if not (add_service_area_info or add_service_area_ck_info):
                        # If stations were requested but not the supply areas, add the stations to the main area
                        for st in stations:
                            transformer = self.create_esdl_station(st)
                            area.asset.append(transformer)
                            pm.add_object_to_dict(active_es_id, transformer, recursive=True)
                            # pm.add_object_to_dict(active_es_id, transformer.port[0])
                            # pm.add_object_to_dict(active_es_id, transformer.port[1])

            if add_service_area_info or add_service_area_ck_info:
                dso_data_source = ServiceAreaDataType.VIVET_DSO_data if add_station_info else ServiceAreaDataType.Capaciteitskaart_data
                service_area_info = self.get_service_area_from_service(
                    boundaries_year,
                    esdl.AreaScopeEnum.from_string(str.upper(scope)),
                    str.upper(identifier),
                    dso_data_source,
                    add_service_area_tennet_info
                )

                if service_area_info:
                    service_area_logical_group = esdl.Area(id=str(uuid.uuid4()), name="Verzorgingsgebieden", logicalGroup=True)
                    area.area.append(service_area_logical_group)
                    pm.add_object_to_dict(active_es_id, service_area_logical_group)

                    tso_service_areas, dso_service_areas, stations = self.preprocess_service_area_information(service_area_info)

                    tso_service_area_dict = dict()
                    for tsa in tso_service_areas:
                        service_area = esdl.Area(
                            id=tsa["id"],
                            name=tsa["naam"],
                            scope=esdl.AreaScopeEnum.from_string("SERVICE_AREA"),
                            geometry=ESDLGeometry.create_geometry_from_geom(tsa["geom"])
                        )
                        tso_service_area_dict[tsa["id"]] = service_area
                        service_area_logical_group.area.append(service_area)
                        pm.add_object_to_dict(active_es_id, service_area)

                        area_list.extend(self.create_area_json_info(tsa["geom"], service_area.id, service_area.name))

                    for dsa in dso_service_areas:
                        service_area = esdl.Area(
                            id=dsa["id"] if "id" in dsa else str(uuid.uuid4()),
                            name=dsa["naam"] if "name" in dsa else dsa["station"] if "station" in dsa else "",
                            scope=esdl.AreaScopeEnum.from_string("SERVICE_AREA"),
                            geometry=ESDLGeometry.create_geometry_from_geom(dsa["geom"])
                        )
                        if "parent" in dsa:
                            if dsa["parent"] in tso_service_area_dict:
                                tso_service_area = tso_service_area_dict[dsa["parent"]]
                                tso_service_area.area.append(service_area)
                            else:
                                logger.error(f"Service area {service_area.name} refers to a parent that does not exist. Ignor service area for now.")
                        else:
                            service_area_logical_group.area.append(service_area)

                        pm.add_object_to_dict(active_es_id, service_area)

                        # For capaciteitskaart data, there are no stations yet, so we add relevant capacity information as Area KPIs
                        if "aanwezige_transportcapaciteit_afname" in dsa and "aanwezige_transportcapaciteit_invoeding" in dsa:
                            KPIs = esdl.KPIs(id=str(uuid.uuid4()))
                            ata_KPI = esdl.DoubleKPI(id=str(uuid.uuid4()), name="aanwezige_transportcapaciteit_afname", value=str2float(dsa["aanwezige_transportcapaciteit_afname"]))
                            ata_KPI.quantityAndUnit = esdl.QuantityAndUnitType(
                                description="Power in MW",
                                physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                unit=esdl.UnitEnum.WATT,
                                multiplier=esdl.MultiplierEnum.MEGA
                            )
                            ati_KPI = esdl.DoubleKPI(id=str(uuid.uuid4()), name="aanwezige_transportcapaciteit_invoeding", value=str2float(dsa["aanwezige_transportcapaciteit_invoeding"]))
                            ati_KPI.quantityAndUnit = esdl.QuantityAndUnitType(
                                description="Power in MW",
                                physicalQuantity=esdl.PhysicalQuantityEnum.POWER,
                                unit=esdl.UnitEnum.WATT,
                                multiplier=esdl.MultiplierEnum.MEGA
                            )
                            KPIs.kpi.extend([ata_KPI, ati_KPI])
                            service_area.KPIs = KPIs

                        if add_station_info:
                            # This code is only relevant for VIVET data
                            # if both supply areas and stations have been requested, add station to the belonging
                            # service_area.
                            if dsa["station"] in stations_dict:
                                station = stations_dict[dsa["station"]]

                                transformer = self.create_esdl_station(station)
                                service_area.asset.append(transformer)
                                pm.add_object_to_dict(active_es_id, transformer, recursive=True)
                            else:
                                logger.error(f"Station {dsa['station']} is not present in stations_dict. Change query!")

                        area_list.extend(self.create_area_json_info(dsa["geom"], service_area.id, service_area.name))

                    for s in stations:
                        # This code is only relevant for Tennet pocket data (VIVET stations are handled differently)
                        if "area_id" in s:
                            if s["area_id"] in tso_service_area_dict:
                                tso_service_area = tso_service_area_dict[s["area_id"]]
                                transformer = esdl.Transformer(id=str(s["id"]), name=str(s["naam"]))
                                shapely_shp = Shape.transform_crs(Shape.parse_geojson_geometry(s["geom"]).shape, "EPSG:28992")
                                transformer.geometry = Shape.create(shapely_shp).get_esdl()
                                transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                                transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))

                                tso_service_area.asset.append(transformer)
                            else:
                                logger.error(
                                    f"Station {s['naam']} refers to a area that does not exist. Ignor station for now.")

            set_session_for_esid(active_es_id, 'shape_dictionary', shape_dictionary)
            # By returning True the frontend requests a full refresh of the ESDL. So the geojson doesn't need to be
            # sent right here.
            # emit('geojson', {"layer": "area_layer", "geojson": area_list})
            return True

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, BOUNDARY_SERVICE_USER_CONFIG):
            return self.settings_storage.get_user(user, BOUNDARY_SERVICE_USER_CONFIG)
        else:
            user_settings = {
                'boundaries_year': DEFAULT_BOUNDARIES_YEAR
            }
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, BOUNDARY_SERVICE_USER_CONFIG, settings)

    def get_user_setting(self, user, name):
        user_settings = self.get_user_settings(user)
        if name in user_settings:
            return user_settings[name]
        else:
            return None

    def set_user_setting(self, user, name, value):
        user_settings = self.get_user_settings(user)
        user_settings[name] = value
        self.set_user_settings(user, user_settings)

    def create_esdl_station(self, station_info):
        transformer = esdl.Transformer(id=str(uuid.uuid4()), name=station_info["station"])

        # For now, only use the "demand" capacity
        transformer.capacity = 1e6 * station_info["capaciteit_afname_mva"]
        shp = Shape.parse_geojson_geometry(station_info["geom"])
        transformer.geometry = shp.get_esdl()
        transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))

        # Add capacity afname and invoeding as constraints
        rc = esdl.RangedConstraint(id=str(uuid.uuid4()), name="capaciteit_afname_mva", attributeReference="power", range=
                                   esdl.Range(maxValue=float(station_info["capaciteit_afname_mva"]),
                                                    profileQuantityAndUnit=esdl.QuantityAndUnitType(
                                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                                        multiplier=esdl.MultiplierEnum.MEGA,
                                                        unit=esdl.UnitEnum.WATT)))
        transformer.constraint.append(rc)
        rc = esdl.RangedConstraint(id=str(uuid.uuid4()), name="totale_capaciteit_invoeding_mva", attributeReference="power",
                                   range=esdl.Range(maxValue=float(station_info["totale_capaciteit_invoeding_mva"]),
                                                    profileQuantityAndUnit=esdl.QuantityAndUnitType(
                                                        physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                                                        multiplier=esdl.MultiplierEnum.MEGA,
                                                        unit=esdl.UnitEnum.WATT)))
        transformer.constraint.append(rc)

        return transformer

    def get_boundary_from_service(self, year, scope, id):
        """
        :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
        :param id: the identifier of the 'scope'
        :return: the geomertry of the indicated 'scope'
        """
        if is_valid_boundary_id(id):
            time.sleep(0.01) # yield a little concurrency when running this in a thread

            if str(year)+id in boundary_cache:
                # print('Retrieve boundary from cache', str(year)+id)
                # res_boundary = copy.deepcopy(boundary_cache[id])   # this doesn't solve messing up cache
                # return res_boundary
                return boundary_cache[str(year)+id]

            try:
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                      settings.boundaries_config["path_boundaries"] + '/YEAR/' + str(year) + '/' + boundary_service_mapping[scope.name] + '/' + id
                # print('Retrieve from boundary service', id)
                r = requests.get(url, timeout=settings.boundaries_config["timeout"])
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    # geom = reply['geom']
                    # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
                    # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
                    # 'tCode': 'GM0003', 'tName': 'Appingedam'}
                    boundary_cache[str(year)+id] = reply
                    return reply
                else:
                    logger.warning("WARNING: Empty response for Boundary service for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                logger.exception('ERROR in accessing Boundary service for {} with id {}: {}'.format(scope.name, id, e))
                return None
        else:
            return None

    def get_service_area_from_service(self, year, scope, scope_id, dso_data_source, tennet_data_year=None):
        """
         :param year: year for which the data must be obtained
         :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
         :param id: the identifier of the 'scope'
         :param dso_data_source: the type of service area data to use, can be 'SA' (for VIVET) or 'CK' (for CapaciteitsKaart)
         :param tennet_data_year: specifies whether to include TenneT pocket data for a specific year (2025, 2035 or 2045).
         Can only be combined with Capaciteitskaart data.
         :return: list of supply areas in the indicated 'scope'
         """
        if tennet_data_year is not None:
            if int(tennet_data_year) not in [2025, 2035, 2045]:
                logger.error("TenneT data is only available for the years 2025, 2035 and 2045")
                return None

        if is_valid_boundary_id(scope_id):
            time.sleep(0.01)  # yield a little concurrency when running this in a thread

            cache_key = "SA_" + str(dso_data_source) + "_" + scope_id
            if tennet_data_year:
                cache_key += '_TenneT_' + str(tennet_data_year)

            logger.info(f"Checking for SA_{scope_id} in boundary cache...")
            if cache_key in boundary_cache:
                # print('Retrieve boundary from cache', str(year)+id)
                # res_boundary = copy.deepcopy(boundary_cache[id])   # this doesn't solve messing up cache
                # return res_boundary
                logger.info(f"{cache_key} in boundary cache, returning from cache")
                return boundary_cache[cache_key]
            else:
                logger.info("Not found, using boundary service to find information")

            try:
                if dso_data_source == ServiceAreaDataType.VIVET_DSO_data:
                    endpoint = 'service_area'
                else:
                    endpoint = 'service_area_ck'
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                      settings.boundaries_config["path_service_areas"] + '/' + endpoint + '/' + str(year) + '/' + \
                      boundary_service_mapping[scope.name] + '/' + scope_id
                if tennet_data_year:
                    url += '/' + str(tennet_data_year)

                # print('Retrieve from boundary service', id)
                r = requests.get(url)
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    boundary_cache[cache_key] = reply
                    return reply
                else:
                    logger.warning("WARNING: Empty response for Boundary service supply area info for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                logger.exception('ERROR in accessing Boundary service supply area info for {} with id {}: {}'.format(scope.name, id, e))
                return None
        else:
            return None

    def get_station_from_service(self, year, delta_year, scope, scope_id):
        """
         :param year: year for which the data must be obtained
         :param delta_year: delta of the year for which the data must be obtained (can be 0 (current), 3, 5, or 10)
         :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
         :param id: the identifier of the 'scope'
         :return: list of stations in the indicated 'scope'
         """
        if is_valid_boundary_id(scope_id):
            time.sleep(0.01)  # yield a little concurrency when running this in a thread

            try:
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                      settings.boundaries_config["path_service_areas"] + '/station/' + str(year) + '/' + \
                      str(delta_year) + '/' + boundary_service_mapping[scope.name] + '/' + scope_id
                r = requests.get(url)
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    return reply
                else:
                    logger.warning("WARNING: Empty response for Boundary service station info for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                logger.exception('ERROR in accessing Boundary service station info for {} with id {}: {}'.format(scope.name, id, e))
                return None
        else:
            return None

    def __get_subboundaries_from_service(self, year, scope, subscope, id):
        """
        :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
        :param subscope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
        :param id: the identifier of the 'scope'
        :return: the geomertry of the indicated 'scope'
        """

        if is_valid_boundary_id(id):
            try:
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] \
                      + settings.boundaries_config["path_boundaries"] + '/YEAR/' + str(year) + '/' \
                      + boundary_service_mapping[subscope.name] + '/' \
                      + boundary_service_mapping[scope.name] + '/' + id
                r = requests.get(url)
                reply = json.loads(r.text)
                # print(reply)

                # ARRAY OF:
                # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
                # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

                return reply
            except Exception as e:
                logger.exception('ERROR in accessing Boundary service for {} with id {}, subscope {}: {}'.format(scope.name, id, subscope.name, str(e)))
                return {}
        else:
            return {}

    def __preload_subboundaries_in_cache(self, year, top_area_scope, sub_area_scope, top_area_id):
        sub_boundaries = self.__get_subboundaries_from_service(year, top_area_scope, sub_area_scope, top_area_id)

        for sub_boundary in sub_boundaries:
            code = sub_boundary['code']
            geom = sub_boundary['geom']
            if code and geom:
                boundary_cache[str(year)+code] = sub_boundary

    def preload_area_subboundaries_in_cache(self, top_area):
        user = get_session('user-email')
        user_settings = self.get_user_settings(user)
        boundaries_year = user_settings['boundaries_year']

        top_area_scope = top_area.scope
        # fix bug in that the top area does not have an id
        if top_area.id is None:
            top_area.id = str(uuid.uuid4())
        top_area_id = top_area.id

        sub_areas = top_area.area
        if sub_areas:
            first_sub_area = sub_areas[0]
            sub_area_scope = first_sub_area.scope

            if top_area_scope and top_area_scope is not esdl.AreaScopeEnum.UNDEFINED and \
                sub_area_scope and sub_area_scope is not esdl.AreaScopeEnum.UNDEFINED and \
                is_valid_boundary_id(top_area_id):
                self.__preload_subboundaries_in_cache(boundaries_year, top_area_scope, sub_area_scope, top_area_id)

    def preprocess_service_area_information(self, service_area_info):
        tso_service_areas = list()
        dso_service_areas = list()
        stations = list()

        tso_service_areas_must_be_present = False
        for sai in service_area_info:
            if "type" in sai and sai["type"] == "Station":
                stations.append(sai)
            if "type" in sai and sai["type"] == "Area" and "parent" in sai:
                # if an area contains the parent attribute, then both TSO and DSO information must be present
                tso_service_areas_must_be_present = True
                dso_service_areas.append(sai)

        for sai in service_area_info:
            if tso_service_areas_must_be_present:
                if "type" in sai and sai["type"] == "Area":
                    if "parent" not in sai:
                        tso_service_areas.append(sai)
            else:
                # This applies for the VIVET DSO service area data
                if "type" in sai and sai["type"] == "Area":
                    dso_service_areas.append(sai)

        if len(tso_service_areas) + len(dso_service_areas) + len(stations) != len(service_area_info):
            logger.error("We've lost information, check the code and the data!")

        return tso_service_areas, dso_service_areas, stations

    def create_area_json_info(self, geom, id, name):
        result_list = list()
        for i in range(0, len(geom['coordinates'])):
            if len(geom['coordinates']) > 1:
                area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
            else:
                area_id_number = ""

            result_list.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": geom['coordinates'][i]
                },
                "properties": {
                    "id": id + area_id_number,
                    "name": name,
                    "type": "SERVICE_AREA",
                    "KPIs": []
                }
            })
        return result_list
