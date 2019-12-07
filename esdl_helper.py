from esdl import esdl
import esdl_config
from esdl.processing import ESDLGeometry, ESDLAsset, ESDLQuantityAndUnits


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
            multiplier = profile.multiplier
            measurement = profile.measurement
            field = profile.field
            # profile_name = 'UNKNOWN'
            for p in esdl_config.esdl_config['influxdb_profile_data']:
                if p['measurement'] == measurement and p['field'] == field:
                    profile_name = p['profile_uiname']
            profile_info_list.append({'id': profile_id, 'class': 'InfluxDBProfile', 'multiplier': multiplier, 'type': profile_type, 'uiname': profile_name})
        if profile_class == 'DateTimeProfile':
            profile_info_list.append({'id': profile_id, 'class': 'DateTimeProfile', 'type': profile_type, 'uiname': profile_name})

    return profile_info_list


def create_port_asset_mapping(asset, mapping):
    geom = asset.geometry
    ports = asset.port
    if geom:
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon
            coord = (lat, lon)
            for p in ports:
                p_id = p.id
                # hack for ESDL files generated by geis_dsl project:
                #   if ESDL file contains ports without id's, create new id's
                # Hmmm, doesn't work because assets have no geometry
                if p_id is None:
                    p_id = str(uuid.uuid4())
                    p.id = p_id
                mapping[p_id] = {'asset_id': asset.id, 'coord': coord}
        if isinstance(geom, esdl.Line):
            points = geom.point
            if ports:
                first = (points[0].lat, points[0].lon)
                last = (points[len(points) - 1].lat, points[len(points) - 1].lon)
                mapping[ports[0].id] = {'asset_id': asset.id, 'coord': first, 'pos': 'first'}
                mapping[ports[1].id] = {'asset_id': asset.id, 'coord': last, 'pos': 'last'}
        if isinstance(geom, esdl.Polygon):
            center = ESDLGeometry.calculate_polygon_center(geom)
            for p in ports:
                mapping[p.id] = {'asset_id': asset.id, 'coord': center}
    else:
        for p in ports:
            mapping[p.id] = {'asset_id': asset.id, 'coord': ()}


def energy_asset_to_ui(asset, port_asset_mapping):
    port_list = []
    conn_list = []

    ports = asset.port
    for p in ports:
        p_asset = port_asset_mapping[p.id]
        p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
        conn_to = [cp.id for cp in p.connectedTo]
        profile = p.profile
        profile_info_list = []
        if profile:
            profile_info_list = generate_profile_info(profile)
        port_list.append \
            ({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to, 'profile': profile_info_list})
        if conn_to:
            # conn_to_list = conn_to.split(' ')   # connectedTo attribute is list of port ID's separated by a space
            for id in conn_to:
                pc_asset = port_asset_mapping[id]
                pc_asset_coord = pc_asset['coord']

                conn_list.append \
                    ({'from-port-id': p.id, 'from-asset-id': p_asset['asset_id'], 'from-asset-coord': p_asset_coord,
                                  'to-port-id': id, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})

    geom = asset.geometry
    if geom:
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon

            capability_type = ESDLAsset.get_asset_capability_type(asset)
            return ['point', 'asset', asset.name, asset.id, type(asset).__name__, [lat, lon], port_list, capability_type], conn_list
        elif isinstance(geom, esdl.Line):
            coords = []
            for point in geom.point:
                coords.append([point.lat, point.lon])
            return ['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list], conn_list
        elif isinstance(geom, esdl.Polygon):
            if isinstance(asset, esdl.WindParc) or isinstance(asset, esdl.PVParc) or isinstance(asset, esdl.WindPark) \
                    or isinstance(asset, esdl.PVPark):
                coords = ESDLGeometry.parse_esdl_subpolygon(geom.exterior, False)   # [lon, lat]
                coords = ESDLGeometry.exchange_coordinates(coords)                  # --> [lat, lon]
                capability_type = ESDLAsset.get_asset_capability_type(asset)
                # print(coords)
                return ['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list, capability_type], conn_list
        else:
            return [], []