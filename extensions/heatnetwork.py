""" Extension for Heat Networks
    Contains functions to duplicate a single pipe network into a double pipe network.

"""

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

from esdl.esdl_handler import EnergySystemHandler
from esdl import Pipe, Line, Point, EnergyAsset, AbstractConductor, AssetStateEnum
from esdl.processing import ESDLAsset
from uuid import uuid4
from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session
import src.log as log
from src.esdl_helper import asset_state_to_ui

logger = log.get_logger(__name__)


DEFAULT_SHIFT_LAT = 0.000020
DEFAULT_SHIFT_LON = 0.000020


class HeatNetwork:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering HeatNetwork extension')

        @self.socketio.on('duplicate', namespace='/esdl')
        def socketio_duplicate(message):
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                print('Duplicate EnergyAsset: %s' % message)
                duplicate = duplicate_energy_asset(esh, active_es_id, message['asset_id'])
                self.add_asset_and_emit(esh, active_es_id, duplicate, message['area_bld_id'])

        @self.socketio.on('reverse_conductor', namespace='/esdl')
        def reverse_conductor(message):
            # reverses the points in the line, so the in and outport are swapped
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            print('Reverse conductor: %s' % message)
            asset_id = message['asset_id']
            conductor = esh.get_by_id(es_id=active_es_id, object_id=asset_id)
            self.reverse_conductor(active_es_id, conductor)
            resource = esh.get_resource(active_es_id)

    def add_asset_and_emit(self, esh: EnergySystemHandler, es_id: str, asset: EnergyAsset, area_bld_id: str):
        with self.flask_app.app_context():
            asset_to_be_added_list = list()
            port_list = self.calculate_port_list(asset)
            message = self.create_asset_description_message(asset, port_list)
            asset_to_be_added_list.append(message)

            if not ESDLAsset.add_object_to_area(esh.get_energy_system(es_id), asset, area_bld_id):
                ESDLAsset.add_object_to_building(esh.get_energy_system(es_id), asset, area_bld_id)

            emit('add_esdl_objects', {'es_id': es_id, 'asset_pot_list': asset_to_be_added_list, 'zoom': False}, namespace='/esdl')

    def reverse_conductor(self, active_es_id: str, conductor: AbstractConductor):
        if isinstance(conductor.geometry, Line):
            line: Line = conductor.geometry
            Point.__repr__ = lambda x: 'Point lat={}, lon={}, elev={}'.format(x.lat, x.lon, x.elevation)
            print('input', line.point)
            print('fragment', line.point[0].eURIFragment())
            rev_point = list(reversed(line.point))
            line.point.clear()
            line.point.extend(rev_point)
            print('output', line.point)
            print('fragment', line.point[0].eURIFragment())


            # send update_esdl_object message (to be invented) to refresh gui
            emit('delete_esdl_object', {'asset_id': conductor.id})
            port_list = self.calculate_port_list(conductor)
            asset_description = self.create_asset_description_message(conductor, port_list)
            add_esdl_object_message = {'es_id': active_es_id, 'asset_pot_list': [asset_description], 'zoom': False}
            print(add_esdl_object_message)
            emit('add_esdl_objects', add_esdl_object_message,namespace='/esdl')

    @staticmethod
    def calculate_port_list(asset: EnergyAsset):
        port_list = list()
        for i in range(len(asset.port)):
            port = asset.port[i]
            coord = ()
            if i == 0:
                if isinstance(asset.geometry, Point):
                    coord = (asset.geometry.lat, asset.geometry.lon)
                elif isinstance(asset.geometry, Line):
                    coord = (asset.geometry.point[0].lat, asset.geometry.point[0].lon)
            elif i == len(asset.port) - 1:
                if isinstance(asset.geometry, Point):
                    coord = (asset.geometry.lat, asset.geometry.lon)
                elif isinstance(asset.geometry, Line):
                    coord = (asset.geometry.point[-1].lat, asset.geometry.point[-1].lon)
            connTo_ids = list(o.id for o in port.connectedTo)
            carrier_id = port.carrier.id if port.carrier else None
            port_list.append(
                {'name': port.name, 'id': port.id, 'type': type(port).__name__, 'conn_to': connTo_ids, 'carrier': carrier_id})

        return port_list

    @staticmethod
    def create_asset_description_message(asset: EnergyAsset, port_list):
        state = asset_state_to_ui(asset)
        if isinstance(asset, AbstractConductor):
            # assume a Line geometry here
            coords = [(p.lat, p.lon) for p in asset.geometry.point]
            return ['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, state, port_list]
        else:
            capability_type = ESDLAsset.get_asset_capability_type(asset)
            return ['point', 'asset', asset.name, asset.id, type(asset).__name__, [asset.geometry.lat,
                 asset.geometry.lon], state, port_list, capability_type]


######
def _shift_point(point: Point):
        point.lat = point.lat - DEFAULT_SHIFT_LAT
        point.lon = point.lon - DEFAULT_SHIFT_LON


def duplicate_energy_asset(esh: EnergySystemHandler, es_id, energy_asset_id: str):
    original_asset = esh.get_by_id(es_id, energy_asset_id)

    duplicate_asset = original_asset.clone()
    duplicate_asset.id = str(uuid4())
    name = original_asset.name + '_ret'
    if original_asset.name.endswith('_ret'):
        name = original_asset.name[:-4] + '_sup'
    if original_asset.name.endswith('_sup'):
        name = original_asset.name[:-4] + '_ret'
    if not isinstance(duplicate_asset, Pipe): # do different naming for other pipes
        name = '{}_{}'.format(original_asset.name, 'copy')
    duplicate_asset.name = name

    geometry = original_asset.geometry
    if isinstance(geometry, Line):
        line = geometry.clone()
        for p in geometry.point:
            point_clone = p.clone()
            _shift_point(point_clone)
            line.point.insert(0, point_clone) # reverse the list
        duplicate_asset.geometry = line

    if isinstance(geometry, Point):
        point_clone = geometry.clone()
        _shift_point(point_clone)
        duplicate_asset.geometry = point_clone

    for port in original_asset.port:
        newport = port.clone()
        newport.id = str(uuid4())
        duplicate_asset.port.append(newport)
        esh.add_object_to_dict(es_id, newport) # add to UUID registry

    esh.add_object_to_dict(es_id, duplicate_asset) # add to UUID registry

    return duplicate_asset
