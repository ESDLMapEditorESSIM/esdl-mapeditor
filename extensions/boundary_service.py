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
from extensions.session_manager import get_handler, get_session, set_session
from extensions.settings_storage import SettingsStorage

from src.shape import Shape
import src.settings as settings
import src.log as log

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
        def get_boundary_info(info):
            print('get_boundary_info:')
            print(info)

            user = get_session('user-email')
            user_settings = self.get_user_settings(user)
            boundaries_year = user_settings['boundaries_year']

            shape_dictionary = get_session('shape_dictionary')
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
            add_station_info = info["add_station_info"]

            if not is_valid_boundary_id(identifier):
                send_alert("Not a valid identifier. Try identifiers like PV27 (Noord-Holland) or GM0060 (Ameland)")
                return

            active_es_id = get_session('active_es_id')
            esh = get_handler()
            es_edit = esh.get_energy_system(es_id=active_es_id)
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
                esh.add_object_to_dict(active_es_id, area)

                area.scope = esdl.AreaScopeEnum.from_string(str.upper(scope))
                area.name = toparea_name
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
                    if add_service_area_info:
                        cbs_area_logical_group = esdl.Area(id=str(uuid.uuid4()), name="CBS gebieden",
                                                           logicalGroup=True)
                        area.area.append(cbs_area_logical_group)
                        esh.add_object_to_dict(active_es_id, cbs_area_logical_group)
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
                        print('Error parsing JSON from GEIS boundary service: '+ str(e))

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
                                esh.add_object_to_dict(active_es_id, sub_area)

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
                    esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
                if stations:
                    stations_dict = {}

                    for st in stations:
                        stations_dict[st["station"]] = st

                    if not add_service_area_info:
                        # If stations were requested but not the supply areas, add the stations to the main area
                        for st in stations:
                            transformer = esdl.Transformer(id=str(uuid.uuid4()), name=st["station"])
                            shp = Shape.parse_geojson_geometry(st["geom"])
                            transformer.geometry = shp.get_esdl()
                            transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                            transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))

                            area.asset.append(transformer)
                            esh.add_object_to_dict(active_es_id, transformer, recursive=True)
                            # esh.add_object_to_dict(active_es_id, transformer.port[0])
                            # esh.add_object_to_dict(active_es_id, transformer.port[1])


            if add_service_area_info:
                service_areas = self.get_service_area_from_service(
                    esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))

                if service_areas:
                    service_area_logical_group = esdl.Area(id=str(uuid.uuid4()), name="Verzorgingsgebieden", logicalGroup=True)
                    area.area.append(service_area_logical_group)
                    esh.add_object_to_dict(active_es_id, service_area_logical_group)

                    for sar in service_areas:
                        service_area = esdl.Area()
                        service_area.id = str(uuid.uuid4())
                        service_area.name = sar["station"]
                        service_area.scope = esdl.AreaScopeEnum.from_string("SERVICE_AREA")

                        geometry = ESDLGeometry.create_geometry_from_geom(sar["geom"])
                        service_area.geometry = geometry

                        service_area_logical_group.area.append(service_area)
                        esh.add_object_to_dict(active_es_id, service_area)

                        if add_station_info:
                            # if both supply areas and stations have been requested, add station to the belonging
                            # service_area.
                            if sar["station"] in stations_dict:
                                station = stations_dict[sar["station"]]

                                transformer = esdl.Transformer(id=str(uuid.uuid4()), name=station["station"])
                                shp = Shape.parse_geojson_geometry(station["geom"])
                                transformer.geometry = shp.get_esdl()
                                transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                                transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))

                                service_area.asset.append(transformer)
                                esh.add_object_to_dict(active_es_id, transformer, recursive=True)
                            else:
                                logger.error(f"Station {sar['station']} is not present in stations_dict. Change query!")

                        geom = sar["geom"]
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
                                    "id": sar["station"] + area_id_number,
                                    "name": sar["station"],
                                    "type": "SERVICE_AREA",
                                    "KPIs": []
                                }
                            })

            set_session('shape_dictionary', shape_dictionary)
            emit('geojson', {"layer": "area_layer", "geojson": area_list})
            print('Ready processing boundary information')

            # Process area information in ESDL again and send to frontend, as logical groups could be present now, and
            # that requires recreation of the layer control dialog
            # TODO: Fix circular import
            # find_boundaries_in_ESDL(area)

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
                r = requests.get(url)
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    # geom = reply['geom']
                    # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
                    # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
                    # 'tCode': 'GM0003', 'tName': 'Appingedam'}
                    boundary_cache[str(year)+id] = reply
                    return reply
                else:
                    print("WARNING: Empty response for Boundary service for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                print('ERROR in accessing Boundary service for {} with id {}: {}'.format(scope.name, id, e))
                return None
        else:
            return None

    def get_service_area_from_service(self, scope, scope_id):
        """
         :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
         :param id: the identifier of the 'scope'
         :return: list of supply areas in the indicated 'scope'
         """
        if is_valid_boundary_id(scope_id):
            time.sleep(0.01)  # yield a little concurrency when running this in a thread

            if "SA_" + scope_id in boundary_cache:
                # print('Retrieve boundary from cache', str(year)+id)
                # res_boundary = copy.deepcopy(boundary_cache[id])   # this doesn't solve messing up cache
                # return res_boundary
                return boundary_cache["SA_" + scope_id]

            try:
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                      settings.boundaries_config["path_service_areas"] + '/service_area/' + \
                      boundary_service_mapping[scope.name] + '/' + scope_id
                # print('Retrieve from boundary service', id)
                r = requests.get(url)
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    boundary_cache["SA_" + scope_id] = reply
                    return reply
                else:
                    print("WARNING: Empty response for Boundary service supply area info for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                print('ERROR in accessing Boundary service supply area info for {} with id {}: {}'.format(scope.name, id, e))
                return None
        else:
            return None

    def get_station_from_service(self, scope, scope_id):
        """
         :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
         :param id: the identifier of the 'scope'
         :return: list of stations in the indicated 'scope'
         """
        if is_valid_boundary_id(scope_id):
            time.sleep(0.01)  # yield a little concurrency when running this in a thread

            try:
                url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                      settings.boundaries_config["path_service_areas"] + '/station/' + \
                      boundary_service_mapping[scope.name] + '/' + scope_id
                r = requests.get(url)
                if len(r.text) > 0:
                    reply = json.loads(r.text)
                    return reply
                else:
                    print("WARNING: Empty response for Boundary service station info for {} with id {}".format(scope.name, id))
                    return None

            except Exception as e:
                print('ERROR in accessing Boundary service station info for {} with id {}: {}'.format(scope.name, id, e))
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
                print('ERROR in accessing Boundary service for {} with id {}, subscope {}: {}'.format(scope.name, id, subscope.name, str(e)))
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