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
from builtins import isinstance

import esdl
from esdl.esdl_handler import EnergySystemHandler
from esdl import Pipe, Line, Point, EnergyAsset, AbstractConductor, Port, InPort, OutPort, Polygon
from esdl.processing import ESDLAsset
from uuid import uuid4
from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, get_session_for_esid
import src.log as log
from src.esdl_helper import asset_state_to_ui, get_tooltip_asset_attrs, add_spatial_attributes
from esdl.processing import ESDLGeometry

logger = log.get_logger(__name__)


DEFAULT_SHIFT_LAT = 0.000050
DEFAULT_SHIFT_LON = 0.000050


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

            add_to_building = False
            if not ESDLAsset.add_object_to_area(esh.get_energy_system(es_id), asset, area_bld_id):
                ESDLAsset.add_object_to_building(esh.get_energy_system(es_id), asset, area_bld_id)
                add_to_building = True

            emit('add_esdl_objects', {'es_id': es_id, 'add_to_building': add_to_building, 'asset_pot_list': asset_to_be_added_list, 'zoom': False}, namespace='/esdl')

    def reverse_conductor(self, active_es_id: str, conductor: AbstractConductor):
        if isinstance(conductor.geometry, Line):
            line: Line = conductor.geometry
            Point.__repr__ = lambda x: 'Point lat={}, lon={}, elev={}'.format(x.lat, x.lon, x.elevation)
            rev_point = list(reversed(line.point))
            line.point.clear()
            line.point.extend(rev_point)

            # todo: swap port connections, but that is only possible if the connectedTo assets
            # have besides an InPort also an OutPort
            # not that easy...
            # inPort, outPort = None
            # for p in conductor.port:
            #     if isinstance(p, InPort):
            #         inPort: InPort = p
            #     if isinstance(p, OutPort):
            #         outPort: OutPort = p
            # for other in inPort.connectedTo:
            for p in conductor.port:
                if isinstance(p, esdl.InPort):
                    inPort: esdl.InPort = p
                elif isinstance(p, esdl.OutPort):
                    outPort: esdl.OutPort = p

            # remove current existing connections from gui first
            self.remove_connections_from_connlist(conductor, active_es_id)

            newConnections = list() # of tuples
            # update connections mapping such that it is connected correctly when reversed
            for connectedInToOut in inPort.connectedTo:
                # remove connection
                inPort.connectedTo.remove(connectedInToOut)
                connectedAsset = connectedInToOut.energyasset
                inPortTo = self.findFirstPortOfType(connectedAsset, esdl.InPort)
                if inPortTo is None:
                    continue # can't flip this port
                else:
                    # add connections to list, so it wont intefere with algorithm
                    newConnections.append((outPort, inPortTo))

            for connectedOutToIn in outPort.connectedTo:
                outPort.connectedTo.remove(connectedOutToIn)
                connectedAsset = connectedOutToIn.energyasset
                outPortTo = self.findFirstPortOfType(connectedAsset, esdl.OutPort)
                if outPortTo is None:
                    continue  # can't flip this port
                else:
                    newConnections.append((inPort, outPortTo))

            # now add the actual connections
            for c in newConnections:
                c[0].connectedTo.append(c[1])

            # create new connection list
            connections = self.update_conn_list(conductor, active_es_id)
            # send update_esdl_object message (to be invented) to refresh gui
            emit('delete_esdl_object', {'asset_id': conductor.id})
            port_list = self.calculate_port_list(conductor)
            asset_description = self.create_asset_description_message(conductor, port_list)
            add_esdl_object_message = {'es_id': active_es_id, 'asset_pot_list': [asset_description], 'zoom': False}
            print(add_esdl_object_message)
            emit('add_esdl_objects', add_esdl_object_message, namespace='/esdl')
            emit("add_connections", {"es_id": active_es_id, "conn_list": connections})


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
            tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'line')
            add_spatial_attributes(asset, tooltip_asset_attrs)
            return ['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, tooltip_asset_attrs, state,
                    port_list]
        else:
            capability_type = ESDLAsset.get_asset_capability_type(asset)
            tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'marker')
            extra_attributes = dict()
            extra_attributes['assetType'] = asset.assetType
            add_spatial_attributes(asset, tooltip_asset_attrs)
            return ['point', 'asset', asset.name, asset.id, type(asset).__name__,
                    [asset.geometry.lat,asset.geometry.lon], tooltip_asset_attrs, state, port_list, capability_type,
                    extra_attributes]

    def remove_connections_from_connlist(self, asset: EnergyAsset, active_es_id: str):
        check_list = list()
        for port in asset.port:
            from_id = port.id
            to_ports = port.connectedTo
            for to_port in to_ports:
                to_id = to_port.id
                check_list.append({'from-port-id': from_id, 'to-port-id': to_id})
                check_list.append({'from-port-id': to_id, 'to-port-id': from_id}) # sometimes they are reversed
                emit('remove_single_connection', {'from-port-id': from_id, 'to-port-id': to_id, 'es_id': active_es_id})

        # update conn_list
        conn_list = get_session_for_esid(active_es_id, 'conn_list')
        l = len(conn_list)

        def identical(conn):  # define if a connection is identical to the one we want to delete
            for item in check_list:
                if conn['from-port-id'] == item['from-port-id'] and \
                        conn['to-port-id'] == item['to-port-id']:
                    print("Connection to remove found ", conn)
                    return True
            return False
        conn_list[:] = [conn for conn in conn_list if not identical(conn)]
        print("removed {} connections".format(l - len(conn_list)))

    def update_conn_list(self, asset: EnergyAsset, active_es_id: str):
        conn_list = get_session_for_esid(active_es_id, 'conn_list')
        connections = list()
        for index, port in enumerate(asset.port):
            from_coords = self.get_port_coordinates(asset, index)
            for target_port in port.connectedTo:
                target_port_index = target_port.energyasset.port.index(target_port)
                to_coords = self.get_port_coordinates(target_port.energyasset, target_port_index)
                connections.append(
                    {'from-port-id': port.id,
                     'from-port-carrier': port.carrier.id if port.carrier else None,
                     'from-asset-id': asset.id,
                     'from-asset-coord': from_coords,
                     'to-port-id': target_port.id,
                     'to-port-carrier': target_port.carrier.id if target_port.carrier else None,
                     'to-asset-id': target_port.energyasset.id,
                     'to-asset-coord': to_coords
                     })
        conn_list.extend(connections)
        #print(connections)
        return connections # only return the newly added connections


    def get_port_coordinates(self, asset, index):
        from_coords = ()
        if isinstance(asset.geometry, Line):
            if index == 0:  # first port == first coordinate
                point: Point = asset.geometry.point[0]
                from_coords = (point.lat, point.lon)
            elif index == len(asset.port) - 1:
                point: Point = asset.geometry.point[-1]
                from_coords = (point.lat, point.lon)
        elif isinstance(asset.geometry, Point):
            from_coords = (asset.geometry.lat, asset.geometry.lon)
        if isinstance(asset.geometry, Polygon):
            from_coords = ESDLGeometry.calculate_polygon_center(asset.geometry)
        return from_coords

    ######
    def findFirstPortOfType(self, connectedAsset: esdl.EnergyAsset, portType):
        for p in connectedAsset.port:
            if isinstance(p, portType):
                return p


def _shift_point(point: Point):
        point.lat = point.lat - DEFAULT_SHIFT_LAT
        point.lon = point.lon - DEFAULT_SHIFT_LON


def duplicate_energy_asset(esh: EnergySystemHandler, es_id, energy_asset_id: str):
    original_asset = esh.get_by_id(es_id, energy_asset_id)

    duplicate_asset = original_asset.deepcopy()
    # reset all id's
    for c in duplicate_asset.eContents:
        if c.eClass.findEStructuralFeature('id'):
            if c.eGet('id'):
                c.eSet('id', str(uuid4()))
    duplicate_asset.id = str(uuid4())
    name = original_asset.name + '_ret'
    if original_asset.name.endswith('_ret'):
        name = original_asset.name[:-4] + '_sup'
    if original_asset.name.endswith('_sup'):
        name = original_asset.name[:-4] + '_ret'
    if not isinstance(duplicate_asset, Pipe): # do different naming for other conductors then pipes
        name = '{}_{}'.format(original_asset.name, 'copy')
    duplicate_asset.name = name

    geometry = duplicate_asset.geometry
    if isinstance(geometry, Line):
        line: Line = geometry  # geometry.clone()
        rev_point = list(reversed(line.point))  # reverse coordinates
        line.point.clear()
        line.point.extend(rev_point)
        for p in line.point:
            _shift_point(p)

    if isinstance(geometry, Point):
        _shift_point(geometry)

    # disconnect the ports as also the connectedTo has been duplicated, we need to remove this reference
    for port in duplicate_asset.port:
        # port.connectedTo.clear()  # pyEcore bug: clear() does not work as expected.
        connected_to_copy = list(port.connectedTo)
        for p in connected_to_copy:
            p.delete()

    esh.add_object_to_dict(es_id, duplicate_asset, recursive=True)  # add to UUID registry
    return duplicate_asset
