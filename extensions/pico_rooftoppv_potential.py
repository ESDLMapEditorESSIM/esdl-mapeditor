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
from extensions.session_manager import get_handler, get_session
from extensions.boundary_service import is_valid_boundary_id
from esdl import esdl
from esdl.processing import ESDLAsset
from src.process_es_area_bld import calc_building_assets_location, recalculate_area_bld_list, get_area_id_from_mapeditor_id
import uuid
import requests
import src.log as log

logger = log.get_logger(__name__)


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


PICO_ID_TO_URL_MAPPING = {
    "BU": "buurt",
    "GM": "gemeenten",
    "PV": "provincies",
    "RES": "resgebieden"
}

PICO_ROOF_ORIENTATIONS = {
    0: "Flat",
    90: "East",
    180: "South",
    270: "West",
    360: "North"
}

PICO_API_URL = "https://pico.geodan.nl/pico/api/v1/"


class PICORooftopPVPotential:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket

        self.register()

    def register(self):
        logger.info("Registering PICORooftopPVPotential extension")

        @self.socketio.on('use_part_of_potential', namespace='/esdl')
        def use_part_of_potential(pot_id, percentage, all_potentials):
            """
            Use part of a SolarPotential to install a PVInstallation

            :param pot_id: id of the SolarPotential
            :param percentage: percentage (0-100) of the SolarPotential that should be installed as a PVInstallation
            :param all_potentials: boolean specifying if this action should be applied to all SolarPotentials in the
            energy system
            :return: None
            """
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                asset_list = []
                add_to_building = False

                pot = esh.get_by_id(active_es_id, pot_id)
                if pot.solarPotentialType != esdl.PVInstallationTypeEnum.ROOFTOP_PV:
                    send_alert('SolarPotential is not of type ROOFTOP_PV')
                else:
                    self.convert_potential(esh, active_es_id, pot, add_to_building, percentage, asset_list)
                    emit('add_esdl_objects',
                         {'es_id': active_es_id, 'add_to_building': add_to_building, 'asset_pot_list': asset_list,
                          'zoom': False})

                    if all_potentials:
                        es = esh.get_energy_system(active_es_id)
                        area = es.instance[0].area

                        for obj in area.eAllContents():
                            if isinstance(obj, esdl.SolarPotential):
                                if obj.solarPotentialType == esdl.PVInstallationTypeEnum.ROOFTOP_PV and obj.id != pot_id:
                                    # not the selected one
                                    asset_list = []
                                    add_to_building = False

                                    pvi = self.convert_potential(esh, active_es_id, obj, add_to_building, percentage, asset_list)
                                    if add_to_building:
                                        # if the PVInstalliation is in the same building as the selected potential
                                        if pot.eContainer() == pvi.eContainer():
                                            emit('add_esdl_objects', {'es_id': active_es_id,
                                                                      'add_to_building': True,
                                                                      'asset_pot_list': asset_list,
                                                                      'zoom': False})
                                        # for potentials/assets that are in another building, we don't need to do anything here
                                    else:
                                        # for all potentials outside a building
                                        emit('add_esdl_objects', {'es_id': active_es_id,
                                                                  'add_to_building': False,
                                                                  'asset_pot_list': asset_list,
                                                                  'zoom': False})

        @self.socketio.on('use_part_of_potential_area', namespace='/esdl')
        def use_part_of_potential_area(area_id, percentage, all_areas):
            """
            Use part of all SolarPotentials in an Area to install a PVInstallation

            :param area_id: id of the Area where the SolarPotentials are part of
            :param percentage: percentage (0-100) of the SolarPotential that should be installed as a PVInstallation
            :param all_areas: boolean specifying if this action should be applied to all Areas in the energy system
            :return: None
            """
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                asset_list = []
                if all_areas:
                    es = esh.get_energy_system(active_es_id)
                    area = es.instance[0].area
                else:
                    area_id = get_area_id_from_mapeditor_id(area_id)
                    area = esh.get_by_id(active_es_id, area_id)
                if area:
                    for obj in area.eAllContents():
                        if isinstance(obj, esdl.SolarPotential):
                            if obj.solarPotentialType == esdl.PVInstallationTypeEnum.ROOFTOP_PV:
                                asset_info = []
                                add_to_building_list = [False]  # Put into list, to pass by reference
                                self.convert_potential(esh, active_es_id, obj, add_to_building_list, percentage, asset_info)
                                if not add_to_building_list[0]:
                                    asset_list = asset_list + asset_info

                    # for all potentials outside a building
                    if asset_list:
                        emit('add_esdl_objects', {'es_id': active_es_id,
                                                  'add_to_building': False,
                                                  'asset_pot_list': asset_list,
                                                  'zoom': False})
                else:
                    send_alert("Serious error, area not found")

        @self.socketio.on('query_solar_potentials', namespace='/esdl')
        def query_solar_potentials(area_id, all_areas):
            """
            Query SolarPotentials information for a specific Area or all areas in the energysystem

            :param area_id: id of the Area where the SolarPotentials should be queried for
            :param all_areas: boolean specifying if this action should be applied to all Areas in the energy system
            :return: None
            """
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                shape_dictionary = get_session('shape_dictionary')
                if not shape_dictionary:
                    shape_dictionary = {}

                es = esh.get_energy_system(active_es_id)
                if all_areas:
                    area = es.instance[0].area
                else:
                    area_id = get_area_id_from_mapeditor_id(area_id)
                    area = esh.get_by_id(active_es_id, area_id)

                if area:
                    building_list = []
                    found_a_building = False
                    # Assume one level deep
                    for subarea in area.area:
                        subarea_id = subarea.id.split()[0]
                        if is_valid_boundary_id(subarea_id):
                            building = self.query_pico_rooftoppv_api(subarea)
                            if building:
                                calc_building_assets_location(building)
                                if subarea_id in shape_dictionary:
                                    shape = shape_dictionary[subarea_id]
                                    center = shape.shape.centroid
                                    building.geometry = esdl.Point(lat=center.y, lon=center.x)
                                found_a_building = True
                                subarea.asset.append(building)
                                esh.add_object_to_dict(active_es_id, building, True)
                                building_list.append(self.get_building_info_for_emit_list(building))
                            else:
                                logger.warning('No correct information returned for area with ID {}'.format(subarea_id))

                    if not found_a_building:
                        # if sublevel areas did not produce any results, try the toplevel area
                        area_id = area.id.split()[0]
                        if is_valid_boundary_id(area_id):
                            building = self.query_pico_rooftoppv_api(area)
                            if building:
                                calc_building_assets_location(building)

                                if area_id in shape_dictionary:
                                    shape = shape_dictionary[area_id]
                                    center = shape.shape.centroid
                                    building.geometry = esdl.Point(lat=center.y, lon=center.x)
                                area.asset.append(building)
                                esh.add_object_to_dict(active_es_id, building, True)
                                building_list.append(self.get_building_info_for_emit_list(building))

                    if building_list:
                        # emit the list of buildings to the frontend to draw them on the map
                        emit('add_building_objects', {'es_id': active_es_id, 'building_list': building_list, 'zoom': False})

                        # Recalculate the list of areas and buildings and emit to frontend
                        area = es.instance[0].area
                        area_bld_list = recalculate_area_bld_list(area)
                        emit('area_bld_list', {'es_id': es.id, 'area_bld_list': area_bld_list})
                    else:
                        send_alert("For these areas no information about solar potential was found")
                else:
                    send_alert("Serious error, area not found")

                return True

    @staticmethod
    def query_pico_rooftoppv_api(area):
        esh = get_handler()

        asset_copy = None
        for code in PICO_ID_TO_URL_MAPPING:
            if area.id[0: len(code)] == code:
                url = PICO_API_URL + PICO_ID_TO_URL_MAPPING[code] + "/" + area.id.upper() + "/zonopdak?geometrie=false"
                headers = {
                    "Accept": "application/esdl+xml",
                    "User-Agent": "ESDL Mapeditor/0.1",
                }

                try:
                    r = requests.get(url, headers=headers)

                    if r.status_code == 200:
                        # print(r.text)
                        pzod_es, parse_info = esh.load_external_string(r.text, "pico_zon_op_dak")

                        asset = pzod_es.instance[0].area.asset[0]
                        if asset:
                            if isinstance(asset, esdl.AggregatedBuilding):
                                asset_copy = asset.deepcopy()
                    else:
                        logger.warning("PICO API requests returned error {} for area ID {}".format(r.status_code, area.id))
                except Exception as e:
                   logger.warning("Error accessing PICO API: " + str(e))

        return asset_copy

    @staticmethod
    def get_building_info_for_emit_list(building):
        return ['point', building.name, building.id, type(building).__name__,
                        [building.geometry.lat, building.geometry.lon], True, {}]

    @staticmethod
    def convert_potential(esh, active_es_id, pot, add_to_building, percentage, asset_list):
        pot_container = pot.eContainer()

        # Determine orientation from potential information
        orientation_name = ""
        if pot.orientation in PICO_ROOF_ORIENTATIONS:
            orientation_name = " (" + PICO_ROOF_ORIENTATIONS[pot.orientation] + ")"

        # Create a PVInstallation instance and attach a profile with the percentage of the potential that
        # will be 'installed'
        pv_installation = esdl.PVInstallation(id=str(uuid.uuid4()),name="PV Installation" + orientation_name)
        pv_outport = esdl.OutPort(id=str(uuid.uuid4()), name="Out")
        pv_profile = esdl.SingleValue(id=str(uuid.uuid4()), name="PV production", value=pot.value * percentage / 100)
        # Assume kWh for now, Geodan should communicate this in the ESDL in the end
        pv_profile.profileQuantityAndUnit = esdl.QuantityAndUnitType(
            physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
            unit=esdl.UnitEnum.WATTHOUR,
            multiplier=esdl.MultiplierEnum.KILO)
        pv_outport.profile.append(pv_profile)
        pv_installation.port.append(pv_outport)

        # Generate a location on the map for the PV Installation
        if isinstance(pot_container, esdl.AbstractBuilding):
            # Place the Asset in the top left corner of the BuildingEditor
            pv_geometry = esdl.Point(lon=10.0, lat=490.0, CRS="Simple")
            pv_installation.geometry = pv_geometry
            add_to_building[0] = True
        else:
            pot_geometry = pot.geometry
            if isinstance(pot_geometry, esdl.Point):
                # Place the Asset with a small offset from the SolarPotential marker
                pv_geometry = esdl.Point(lon=pot_geometry.lon + 0.001, lat=pot_geometry.lat - 0.001)
                pv_installation.geometry = pv_geometry
            else:
                logger.warning('Using potentials with geometry other than esdl.Point not supported yet')

        # Add the PVInstallation to the same container as the SolarPotential (Area or Building)
        pot_container.asset.append(pv_installation)
        esh.add_object_to_dict(active_es_id, pv_installation, recursive=True)
        if isinstance(pot_container, esdl.AbstractBuilding):
            calc_building_assets_location(pot_container, True)

        # Adapt the potential (substract the installed value)
        pot.value = pot.value * (100-percentage) / 100

        port_list = [{'name': pv_outport.name, 'id': pv_outport.id, 'type': type(pv_outport).__name__, 'conn_to': []}]
        capability_type = ESDLAsset.get_asset_capability_type(pv_installation)
        asset_list.append(['point', 'asset', pv_installation.name, pv_installation.id,
                           type(pv_installation).__name__, 'e', [pv_geometry.lat, pv_geometry.lon], port_list,
                                       capability_type])
        return pv_installation