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
from typing import List

from esdl import esdl
from esdl.processing import ESDLGeometry


def identical_connection(conn, check_list: List[dict]):
    """ define if a connection is identical to the one we want to delete """
    for item in check_list:
        if conn['from-port-id'] == item['from-port-id'] and conn['to-port-id'] == item['to-port-id']:
            return True
    return False


def remove_connection_from_conn_list(from_port: esdl.Port, to_port: esdl.Port, conn_list: List[dict]):
    check_list = list()
    check_list.append({'from-port-id': from_port.id, 'to-port-id': to_port.id})
    check_list.append({'from-port-id': to_port.id, 'to-port-id': from_port.id})  # sometimes they are reversed
    conn_list[:] = [conn for conn in conn_list if not identical_connection(conn, check_list)]


def create_connection(from_port: esdl.Port, to_port: esdl.Port) -> dict:
    """
    Creates a dict that is required for a connection to be sent (though the conn_list) to the front-end
    Parameters
    ----------
    from_port
    to_port

    Returns a Dict used in conn_list
    -------

    """
    from_energy_asset = from_port.energyasset
    from_port_index = from_energy_asset.port.index(from_port)
    from_coords = get_port_coordinates(from_port.energyasset, from_port_index)
    to_port_index = to_port.energyasset.port.index(to_port)
    to_coords = get_port_coordinates(to_port.energyasset, to_port_index)

    return {'from-port-id': from_port.id,
            'from-port-carrier': from_port.carrier.id if from_port.carrier else None,
            'from-asset-id': from_energy_asset.id,
            'from-asset-coord': from_coords,
            'to-port-id': to_port.id,
            'to-port-carrier': to_port.carrier.id if to_port.carrier else None,
            'to-asset-id': to_port.energyasset.id,
            'to-asset-coord': to_coords
            }


def get_port_coordinates(asset, index):
    from_coords = ()
    if asset.containingAsset or asset.containingBuilding:
        # handle assets in buildings or compound assets
        asset = asset.containingAsset or asset.containingBuilding
    if isinstance(asset.geometry, esdl.Line):
        if index == 0:  # first port == first coordinate
            point: esdl.Point = asset.geometry.point[0]
            from_coords = (point.lat, point.lon)
        elif index == len(asset.port) - 1:
            point: esdl.Point = asset.geometry.point[-1]
            from_coords = (point.lat, point.lon)
    elif isinstance(asset.geometry, esdl.Point):
        from_coords = (asset.geometry.lat, asset.geometry.lon)
    if isinstance(asset.geometry, esdl.Polygon):
        from_coords = ESDLGeometry.calculate_polygon_center(asset.geometry)
    return from_coords
