""" Extension for Heat Networks
    Contains functions to duplicate a single pipe network into a double pipe network.

"""

from esdl.esdl_handler import EnergySystemHandler
from esdl import Pipe, Line, Point, EnergyAsset, AbstractConductor
from esdl.processing import ESDLAsset
from uuid import uuid4
from flask import Flask, session
from flask_socketio import SocketIO

DEFAULT_SHIFT_LAT = 0.000080
DEFAULT_SHIFT_LON = 0.000080


class HeatNetwork:
    def __init__(self, app: Flask, socket: SocketIO):
        self.app = app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering HeatNetwork extension')

        @self.socketio.on('duplicate', namespace='/esdl')
        def socketio_duplicate(message):
            #with self.app.test_request_context('/editor'):
            with self.app.app_context():
                import app as mapeditor
                esh = mapeditor.get_handler()
                print('Duplicate message: %s' % message)
                duplicate = duplicate_energy_asset(esh, message['asset_id'])
                self.add_asset_and_emit(esh, duplicate, message['area_bld_id'])

    def add_asset_and_emit(self, esh: EnergySystemHandler, asset: EnergyAsset, area_bld_id: str):
        asset_to_be_added_list = list()

        # add port mappings to session
        mapping = session['mapping']
        port_list = list()

        for i in range(0..len(asset.port)):
            port = asset.port[i]
            if i == 0:
                mapping[port.id] = {'asset_id': asset.id,
                                    'coord': (asset.geometry.points[i].lat, asset.geometry.points[i].lon),
                                    'pos': 'first'}
            elif i == len(asset.port) - 1:
                mapping[port.id] = {'asset_id': asset.id,
                                    'coord': (asset.geometry.points[i].lat, asset.geometry.points[i].lon),
                                    'pos': 'last'}
            connTo_ids = list(o.id for o in port.connectedTo)
            port_list.append(
                {'name': port.name, 'id': port.id, 'type': type(port).__name__, 'conn_to': connTo_ids})
            if isinstance(asset, AbstractConductor):
                # assume a Line geometry here
                coords = [(p.lat, p.lon) for p in asset.geometry.points]
                asset_to_be_added_list.append(
                    ['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list])

            else:
                capability_type = ESDLAsset.get_asset_capability_type(asset)
                asset_to_be_added_list.append(
                    ['point', 'asset', asset.name, asset.id, type(asset).__name__, asset.geometry.lat,
                     asset.geometry.lon, port_list,
                     capability_type])

        if not ESDLAsset.add_asset_to_area(esh.get_energy_system(), asset, area_bld_id):
            ESDLAsset.add_asset_to_building(esh.get_energy_system(), asset, area_bld_id)

        self.socketio.emit('add_esdl_objects', {'list': asset_to_be_added_list, 'zoom': False})


######
def _shift_point(point: Point):
        point.lat = point.lat - DEFAULT_SHIFT_LAT
        point.lon = point.lon - DEFAULT_SHIFT_LON


def duplicate_energy_asset(esh: EnergySystemHandler, energy_asset_id: str):
    original_asset = esh.get_by_id(energy_asset_id)

    duplicate_asset = original_asset.clone()
    duplicate_asset.id = str(uuid4())
    name = original_asset.name + '_ret'
    if original_asset.name.endswith('_ret'):
        name = original_asset.name + '_sup'
    if not isinstance(duplicate_asset, Pipe): # do different naming for other pipes
        name = original_asset + '_' + duplicate_asset.id[:4]
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
        esh.add_asset(newport) # add to UUID registry

    esh.add_asset(duplicate_asset) # add to UUID registry

    return duplicate_asset
