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

import re

from flask_socketio import emit
from pyecore.ecore import EEnum

from esdl import esdl
from esdl.processing import ESDLGeometry, ESDLAsset, ESDLQuantityAndUnits
from extensions.session_manager import get_handler, get_session, get_session_for_esid
from extensions.profiles import Profiles


def generate_profile_info(profile_list):
    profile_info_list = []
    for profile in profile_list:
        profile_class = type(profile).__name__
        qau = profile.profileQuantityAndUnit
        if isinstance(qau, esdl.QuantityAndUnitReference):
            qau = qau.reference
        if qau:
            profile_type = ESDLQuantityAndUnits.qau_to_string(qau)
        else:
            profile_type = profile.profileType.name
        profile_name = profile.name
        profile_id = profile.id
        if profile_class == 'SingleValue':
            value = profile.value
            profile_info_list.append({'id': profile_id, 'class': 'SingleValue', 'value': value, 'type': profile_type, 'uiname': profile_name})
        if profile_class == 'InfluxDBProfile':
            database = profile.database
            multiplier = profile.multiplier
            measurement = profile.measurement
            field = profile.field

            profiles = Profiles.get_instance().get_profiles()['profiles']
            for pkey in profiles:
                p = profiles[pkey]
                if p['database'] == database and p['measurement'] == measurement and p['field'] == field:
                    profile_name = p['profile_uiname']
            if profile_name == None:
                profile_name = field
            profile_info_list.append({'id': profile_id, 'class': 'InfluxDBProfile', 'multiplier': multiplier, 'type': profile_type, 'uiname': profile_name})
        if profile_class == 'DateTimeProfile':
            profile_info_list.append({'id': profile_id, 'class': 'DateTimeProfile', 'type': profile_type, 'uiname': profile_name})

    return profile_info_list


def get_port_profile_info(asset):
    ports = asset.port

    port_profile_list = []
    for p in ports:
        prof = p.profile
        profile_info_list = []
        if prof:
            profile_info_list = generate_profile_info(prof)

        port_profile_list.append({'port_id': p.id, 'port_name': p.name, 'profiles': profile_info_list})

    return port_profile_list


# ---------------------------------------------------------------------------------------------------------------------
#  Get connections information for an asset
# ---------------------------------------------------------------------------------------------------------------------
def get_connected_to_info(asset):
    result = []
    ports = asset.port
    for p in ports:
        ptype = type(p).__name__

        if p.carrier:
            pcarr = p.carrier.name
        else:
            pcarr = None

        ct_list = []
        conn_to = p.connectedTo
        if conn_to:
            for conn_port in conn_to:
                conn_asset = conn_port.energyasset #small a instead of Asset
                ct_list.append({'opid': p.id, 'pid': conn_port.id, 'aid': conn_asset.id, 'atype': type(conn_asset).__name__, 'aname': conn_asset.name})

        result.append({'pid': p.id, 'ptype': ptype, 'pname': p.name, 'pcarr': pcarr, 'ct_list': ct_list})
    #logger.debug(result)
    return result


def get_asset_geom_info(asset):
    geom = asset.geometry
    if geom:
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon
            return (lat, lon)
        if isinstance(geom, esdl.Line):
            points = geom.point
            first = (points[0].lat, points[0].lon)
            last = (points[len(points) - 1].lat, points[len(points) - 1].lon)
            return [first, last]
        if isinstance(geom, esdl.Polygon):
            center = ESDLGeometry.calculate_polygon_center(geom)
            return center
    return ()


def get_asset_from_port_id(esh, es_id, pid):
    port = esh.get_by_id(es_id, pid)
    return port.eContainer()


def get_asset_and_coord_from_port_id(esh, es_id, pid):
    port = esh.get_by_id(es_id, pid)
    asset = port.eContainer()
    if asset.geometry:
        coord = get_asset_geom_info(asset)
        if isinstance(asset.geometry, esdl.Line):
            # Take care of returning first coordinate for first port and last coordinate for second port
            if asset.port[0].id == pid:
                return {'asset': asset, 'coord': coord[0]}
            if asset.port[1].id == pid:
                return {'asset': asset, 'coord': coord[1]}
        else:
            return {'asset': asset, 'coord': coord}

    return {'asset': asset, 'coord': ()}


def asset_state_to_ui(asset):
    if asset.state == esdl.AssetStateEnum.ENABLED:
        return 'e'
    elif asset.state == esdl.AssetStateEnum.OPTIONAL:
        return 'o'
    else:
        return 'd'


def get_tooltip_asset_attrs(asset, shape):
    user_settings = get_session('user_settings')

    attrs_dict = dict()
    if user_settings:
        if 'ui_settings' in user_settings:
            if 'tooltips' in user_settings['ui_settings']:
                tooltip_settings = user_settings['ui_settings']['tooltips']
                if (shape == 'marker' or shape == 'polygon') and 'marker_tooltip_format' in tooltip_settings:
                    tooltip_format = tooltip_settings['marker_tooltip_format']
                elif shape == 'line' and 'line_tooltip_format' in tooltip_settings:
                    tooltip_format = tooltip_settings['line_tooltip_format']

                attr_names_list = re.findall('\{(.*?)\}', tooltip_format)
                for attr_names in attr_names_list:
                    for attr_name in attr_names.split('/'):
                        if attr_name not in ['name', 'id']:
                            attr = asset.eClass.findEStructuralFeature(attr_name)
                            if attr and asset.eIsSet(attr_name):
                                value = asset.eGet(attr_name)
                                if isinstance(attr.eType, EEnum):
                                    attrs_dict[attr_name] = value.name
                                else:
                                    attrs_dict[attr_name] = value

    return attrs_dict


def add_spatial_attributes(asset, attrs):
    user_settings = get_session('user_settings')

    if user_settings:
        if 'ui_settings' in user_settings:
            if 'spatial_buffers' in user_settings['ui_settings']:
                spatial_buffer_settings = user_settings['ui_settings']['spatial_buffers']
                if 'visible_on_startup' in spatial_buffer_settings and spatial_buffer_settings['visible_on_startup']:
                    if asset.bufferDistance:
                        attrs['dist'] = dict()
                        for bd in asset.bufferDistance:
                            attrs['dist'][bd.type.name] = bd.distance

    # To be able to show a circle for assets that have a Point geometry and surfaceArea attribute
    if asset.eIsSet('surfaceArea'):
        attrs['surfaceArea'] = asset.surfaceArea


def energy_asset_to_ui(esh, es_id, asset): # , port_asset_mapping):
    port_list = []
    conn_list = []

    ports = asset.port
    for p in ports:
        # p_asset = port_asset_mapping[p.id]
        p_asset = get_asset_and_coord_from_port_id(esh, es_id, p.id)
        p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
        conn_to = [cp.id for cp in p.connectedTo]
        profile = p.profile
        profile_info_list = []
        carrier_id = p.carrier.id if p.carrier else None
        if profile:
            profile_info_list = generate_profile_info(profile)
        port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to,
                          'profile': profile_info_list, 'carrier': carrier_id})
        if conn_to:
            # conn_to_list = conn_to.split(' ')   # connectedTo attribute is list of port ID's separated by a space
            for id in conn_to:
                # pc_asset = port_asset_mapping[id]
                pc_asset = get_asset_and_coord_from_port_id(esh, es_id, id)
                pc_asset_coord = pc_asset['coord']

                conn_list.append(
                    {'from-port-id': p.id,
                     'from-asset-id': p_asset['asset'].id,
                     'from-port-carrier': p.carrier.id if p.carrier else None,
                     'from-asset-coord': p_asset_coord,
                     'to-port-id': id,
                     'to-port-carrier': pc_asset['asset'].carrier.id if pc_asset['asset'].carrier else None,
                     'to-asset-id': pc_asset['asset'].id,
                     'to-asset-coord': pc_asset_coord
                     })

    state = asset_state_to_ui(asset)
    geom = asset.geometry
    extra_attributes = dict()
    extra_attributes['assetType'] = asset.assetType
    if geom:
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon

            capability_type = ESDLAsset.get_asset_capability_type(asset)
            tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'marker')
            add_spatial_attributes(asset, tooltip_asset_attrs)
            return ['point', 'asset', asset.name, asset.id, type(asset).__name__, [lat, lon], tooltip_asset_attrs,
                    state, port_list, capability_type, extra_attributes], conn_list
        elif isinstance(geom, esdl.Line):
            coords = []
            for point in geom.point:
                coords.append([point.lat, point.lon])
            tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'line')
            add_spatial_attributes(asset, tooltip_asset_attrs)
            return ['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, tooltip_asset_attrs, state,
                    port_list], conn_list
        elif isinstance(geom, esdl.Polygon):
            if isinstance(asset, esdl.WindPark) or isinstance(asset, esdl.PVPark):
                coords = ESDLGeometry.parse_esdl_subpolygon(geom.exterior, False)   # [lon, lat]
                coords = ESDLGeometry.exchange_coordinates(coords)                  # --> [lat, lon]
                capability_type = ESDLAsset.get_asset_capability_type(asset)
                # print(coords)
                tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'polygon')
                add_spatial_attributes(asset, tooltip_asset_attrs)
                return ['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords, tooltip_asset_attrs,
                        state, port_list, capability_type], extra_attributes, conn_list
        else:
            return [], []


def update_carrier_conn_list():
    esh = get_handler()
    active_es_id = get_session('active_es_id')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')

    for c in conn_list:
        from_port = esh.get_by_id(active_es_id, c['from-port-id'])
        if from_port.carrier:
            c['from-port-carrier'] = from_port.carrier.id
        to_port = esh.get_by_id(active_es_id, c['from-port-id'])
        if to_port.carrier:
            c['to-port-carrier'] = to_port.carrier.id

    emit('clear_connections')  # clear current active layer connections
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})
