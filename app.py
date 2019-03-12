#!/usr/bin/env python
from flask import Flask, render_template, session, request, send_from_directory, send_file
from flask_socketio import SocketIO, emit
import requests
import uuid
import math
import copy
import json
from model import esdl_sup as esdl

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

BUILDING_COLORS_BUILDINGYEAR = [
    {'from':    0, 'to': 1900, 'color': '#800000'},     # dark red
    {'from': 1900, 'to': 1940, 'color': '#ff0000'},     # red
    {'from': 1940, 'to': 1970, 'color': '#ff8080'},     # light red
    {'from': 1970, 'to': 1990, 'color': '#ff8000'},     # orange
    {'from': 1990, 'to': 2010, 'color': '#00ff00'},     # light green
    {'from': 2010, 'to': 2999, 'color': '#008000'}      # dark green
]

BUILDING_COLORS_AREA = [
    {'from':    0, 'to':    50, 'color': '#c0c0ff'},    # light blue / purple
    {'from':   50, 'to':   100, 'color': '#8080ff'},    #
    {'from':  100, 'to':   150, 'color': '#4040ff'},    #
    {'from':  150, 'to':   200, 'color': '#0000ff'},    # blue
    {'from':  200, 'to':   500, 'color': '#0000c0'},    #
    {'from':  500, 'to':  1000, 'color': '#000080'},    #
    {'from': 1000, 'to': 99999, 'color': '#000040'}     # dark blue
]

# ---------------------------------------------------------------------------------------------------------------------
#  File I/O and ESDL Store API calls
# ---------------------------------------------------------------------------------------------------------------------
xml_namespace = ('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\nxmlns:esdl="http://www.tno.nl/esdl"\nxsi:schemaLocation="http://www.tno.nl/esdl ../esdl/model/esdl.ecore"\n')
GEIS_CLOUD_IP = '10.30.2.1'
ESDL_STORE_PORT = '3003'
store_url = 'http://' + GEIS_CLOUD_IP + ':' + ESDL_STORE_PORT + '/store/'


def write_energysystem_to_file(filename, es):
    f = open(filename, 'w+', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='esdl:', name_='esdl:EnergySystem', namespacedef_=xml_namespace, pretty_print=True)
    f.close()


def create_ESDL_store_item(id, es, title, description, email):
    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
                   pretty_print=True)
    f.close()

    with open('/tmp/temp.xmi', 'r') as esdl_file:
        esdlstr = esdl_file.read()

    payload = {'id': id, 'title': title, 'description': description, 'email':email, 'esdl': esdlstr}
    requests.post(store_url, data=payload)


def load_ESDL_EnergySystem(id):
    url = store_url + 'esdl/' + id + '?format=xml'
    r = requests.get(url)
    esdlstr = r.text
    # emit('esdltxt', esdlstr)
    esdlstr = esdlstr.encode()

    return esdl.parseString(esdlstr)


def store_ESDL_EnergySystem(id, es):
    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
                   pretty_print=True)
    f.close()

    with open('/tmp/temp.xmi', 'r') as esdl_file:
        esdlstr = esdl_file.read()

    payload = {'id': id, 'esdl': esdlstr}
    requests.put(store_url + id, data=payload)


def send_ESDL_as_file(es, name):
    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
                   pretty_print=True)
    f.close()

    # send_file('/tmp/temp.xmi', name)


# ---------------------------------------------------------------------------------------------------------------------
#  GEIS Boundary service access
# ---------------------------------------------------------------------------------------------------------------------
BOUNDARY_SERVICE_PORT = '4000'
boundary_service_mapping = {
    'ZIPCODE': 'zipcodes',
    'NEIGHBOURHOOD': 'neighbourhoods',
    'DISTRICT': 'districts',
    'MUNICIPALITY': 'municipalities',
    'ENERGYREGION': 'energyregions',
    'PROVINCE': 'provinces',
    'COUNTRY': 'countries'
}


def get_boundary_from_service(type, id):
    """
    :param type: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    try:
        url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(type)] + '/' + id
        r = requests.get(url)
        reply = json.loads(r.text)

        print(reply)
        geom = reply['geom']

        # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
        # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
        # 'tCode': 'GM0003', 'tName': 'Appingedam'}

        return geom
    except:
        return None


def get_subboundaries_from_service(type, subtype, id):
    """
    :param type: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    try:
        url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(subtype)]\
              + '/' + type + '/' + id
        r = requests.get(url)
        reply = json.loads(r.text)
        print(reply)

        # ARRAY OF:
        # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
        # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

        return reply
    except:
        return None


def _parse_esdl_subpolygon(subpol):
    ar = []
    points = subpol.get_point()
    for point in points:
        lat = point.get_lat()
        lon = point.get_lon()
        ar.append([lon, lat])
    return ar


def create_boundary_from_contour(contour):
    exterior = contour.get_exterior()
    interiors = contour.get_interior()

    ar = []
    ar.append(_parse_esdl_subpolygon(exterior))
    for interior in interiors:
        ar.append(_parse_esdl_subpolygon(interior))

    geom = {
        'type': 'Polygon',
        'coordinates': ar
    }
    # print(geom)

    return geom


def _determine_color(asset):
    building_color = '#808080'

    if isinstance(asset, esdl.Building):
        building_year = asset.get_buildingYear()
        if building_year:
            building_color = None
            i = 0
            while not building_color:
                if BUILDING_COLORS_BUILDINGYEAR[i]['from'] <= building_year < BUILDING_COLORS_BUILDINGYEAR[i]['to']:
                    building_color = BUILDING_COLORS_BUILDINGYEAR[i]['color']
                i += 1

    return building_color


"""
        floorarea = asset.get_floorArea()
        if floorarea:
            building_color = None
            i = 0
            while not floorarea:
                if BUILDING_COLORS_AREA[i]['from'] <= floorarea < BUILDING_COLORS_AREA[i]['to']:
                    building_color = BUILDING_COLORS_AREA[i]['color']
                i += 1
"""


def _find_more_area_boundaries(this_area):

    area_contour = this_area.get_contour()
    if area_contour:
        boundary = create_boundary_from_contour(area_contour)
        emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary})

    assets = this_area.get_asset()
    for asset in assets:
        if isinstance(asset, esdl.AbstractBuilding):
            asset_geometry = asset.get_geometry()
            if asset_geometry:
                if isinstance(asset_geometry, esdl.Polygon):
                    building_color =_determine_color(asset)
                    boundary = create_boundary_from_contour(asset_geometry)

                    emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': building_color})

    areas = this_area.get_area()
    for area in areas:
        _find_more_area_boundaries(area)


def find_more_boundaries_in_ESDL(top_area):
    _find_more_area_boundaries(top_area)


# ---------------------------------------------------------------------------------------------------------------------
#  Application definition, configuration and setup of simple file server
# ---------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


# @app.route('/<path:path>')
# def download_esdl(path):
#    session_info = session
#    es_edit = session_info['es_edit']
#    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
#    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
#    es_edit.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
#                   pretty_print=True)
#    f.seek(0)

#    f = open('/tmp/temp.xmi', 'r')
#   return send_file(f, attachment_filename='file.esdl',
#                     as_attachment=True)

@app.route('/<path:path>')
def download_esdl(path):
    return send_from_directory('', path)

@app.route('/images/<path:path>')
def send_image(path):
    return send_from_directory('images', path)


@app.route('/plugins/<path:path>')
def send_plugin(path):
    return send_from_directory('plugins', path)


# FOR TESTING
@app.route('/html/<path:path>')
def send_html(path):
    return send_from_directory('html', path)


# ---------------------------------------------------------------------------------------------------------------------
#  Functions to find assets in, remove assets from and add assets to areas and buildings
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    print(message)
    emit('alert', message)


# ---------------------------------------------------------------------------------------------------------------------
#  Functions to find assets in, remove assets from and add assets to areas and buildings
# ---------------------------------------------------------------------------------------------------------------------
def find_area(area, area_id):
    if area.get_id() == area_id: return area
    for a in area.get_area():
        ar = find_area(a, area_id)
        if ar:
            return ar
    return None


def _find_asset_in_building(building, asset_id):
    for ass in building.get_asset():
        if ass.get_id() == asset_id:
            return ass
        if isinstance(ass, esdl.AbstractBuilding):
            asset = _find_asset_in_building(ass, asset_id)
            if asset:
                return asset
    return None


def find_asset(area, asset_id):
    for ass in area.get_asset():
        if ass.get_id() == asset_id:
            return ass
        if isinstance(ass, esdl.AbstractBuilding):
            asset = _find_asset_in_building(ass, asset_id)
            if asset:
                return asset

    for subarea in area.get_area():
        asset = find_asset(subarea, asset_id)
        if asset:
            return asset

    return None


def add_asset_to_area(es, asset, area_id):
    # find area with area_id
    instance = es.get_instance()[0]
    area = instance.get_area()
    ar = find_area(area, area_id)

    if ar:
        ar.add_asset_with_type(asset)
        return 1
    else:
        return 0


def add_asset_to_building(es, asset, building_id):
    # find area with area_id
    instance = es.get_instance()[0]
    area = instance.get_area()
    ar = find_asset(area, building_id)

    if ar:
        ar.add_asset_with_type(asset)
        return 1
    else:
        return 0


def _remove_port_references(area, ports):
    mapping = session['port_to_asset_mapping']
    for p_remove in ports:
        p_id = p_remove.get_id()
        connected_to = p_remove.get_connectedTo()
        if connected_to:
            connected_to_list = connected_to.split(' ')
            for conns in connected_to_list:
                # conns now contains the id's of the port this port is referring to
                ass_info = mapping[conns]
                asset = find_asset(area, ass_info['asset_id'])
                asset_ports = asset.get_port()
                for p_remove_ref in asset_ports:
                    conn_to = p_remove_ref.get_connectedTo()
                    conn_to = conn_to.replace(p_id, '')
                    conn_to = conn_to.replace(' ', '')
                    conn_to = conn_to.strip()
                    p_remove_ref.set_connectedTo(conn_to)


def _remove_asset_from_building(area, building, asset_id):
    for ass in building.get_asset():
        if ass.get_id() == asset_id:
            ports = ass.get_port()
            _remove_port_references(area, ports)
            building.asset.remove(ass)
            print('Asset with id ' + asset_id+ ' removed from building with id: ', + building.get_id())


def _recursively_remove_asset_from_area(area, asset_id):
    for ass in area.get_asset():
        if ass.get_id() == asset_id:
            ports = ass.get_port()
            _remove_port_references(area, ports)
            area.asset.remove(ass)
            print('Asset with id ' + asset_id + ' removed from area with id: ' + area.get_id())
        if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
            _remove_asset_from_building(area, ass, asset_id)
    for sub_area in area.get_area():
        _recursively_remove_asset_from_area(sub_area, asset_id)


def remove_asset_from_energysystem(es, asset_id):
    # find area with area_id
    instance = es.get_instance()[0]
    area = instance.get_area()
    _recursively_remove_asset_from_area(area, asset_id)


# ---------------------------------------------------------------------------------------------------------------------
#  Initialize
# ---------------------------------------------------------------------------------------------------------------------
def initialize():
    session['port_to_asset_mapping'] = {}


# ---------------------------------------------------------------------------------------------------------------------
#  Builds up a mapping from ports to assets
# ---------------------------------------------------------------------------------------------------------------------
def create_building_port_to_asset_mapping(building, mapping):
    for basset in building.get_asset():
        if isinstance(basset, esdl.AbstractBuilding):
            create_building_port_to_asset_mapping(basset, mapping)
        else:
            geom = basset.get_geometry()
            ports = basset.get_port()
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.get_lat()
                    lon = geom.get_lon()
                    coord = (lat, lon)
                    for p in ports:
                        mapping[p.get_id()] = {'asset_id': basset.get_id(), 'coord': coord}
                if isinstance(geom, esdl.Line):
                    points = geom.get_point()
                    if ports:
                        first = (points[0].get_lat(), points[0].get_lon())
                        last = (points[len(points)-1].get_lat(), points[len(points)-1].get_lon())
                        mapping[ports[0].get_id()] = {'asset_id': basset.get_id(), 'coord': first}
                        mapping[ports[1].get_id()] = {'asset_id': basset.get_id(), 'coord': last}


def create_port_to_asset_mapping(area, mapping):
    # process subareas
    for ar in area.get_area():
        create_port_to_asset_mapping(ar, mapping)

    # process assets in area
    for asset in area.get_asset():
        if isinstance(asset, esdl.AggregatedBuilding):
            create_building_port_to_asset_mapping(asset, mapping)
        else:
            # asset can be of type Potential too ???
            if isinstance(asset, esdl.EnergyAsset):
                geom = asset.get_geometry()
                ports = asset.get_port()
                if geom:
                    if isinstance(geom, esdl.Point):
                        lat = geom.get_lat()
                        lon = geom.get_lon()
                        coord = (lat, lon)
                        for p in ports:
                            p_id = p.get_id()
                            # hack for ESDL files generated by geis_dsl project:
                            #   if ESDL file contains ports without id's, create new id's
                            # Hmmm, doesn't work because assets have no geometry
                            if p_id is None:
                                p_id = uuid.uuid4()
                                p.set_id(p_id)
                            mapping[p_id] = {'asset_id': asset.get_id(), 'coord': coord}
                    if isinstance(geom, esdl.Line):
                        points = geom.get_point()
                        if ports:
                            first = (points[0].get_lat(), points[0].get_lon())
                            last = (points[len(points) - 1].get_lat(), points[len(points) - 1].get_lon())
                            mapping[ports[0].get_id()] = {'asset_id': asset.get_id(), 'coord': first, 'pos': 'first'}
                            mapping[ports[1].get_id()] = {'asset_id': asset.get_id(), 'coord': last, 'pos': 'last'}


# ---------------------------------------------------------------------------------------------------------------------
#  Build up initial information about energysystem to send to browser
# ---------------------------------------------------------------------------------------------------------------------
def process_building(asset_list, area_bld_list, conn_list, port_asset_mapping, building, level):
    area_bld_list.append(['Building', building.get_id(), building.get_name(), level])

    for basset in building.get_asset():
        geom = basset.get_geometry()
        coord = ()
        if geom:
            if isinstance(geom, esdl.Point):
                lat = geom.get_lat()
                lon = geom.get_lon()
                coord = (lat, lon)

                asset_list.append(['point', basset.get_name(), basset.get_id(), type(basset).__name__, lat, lon])

        ports = basset.get_port()
        for p in ports:
            conn_to = p.get_connectedTo()
            if conn_to:
                conn_to_list = conn_to.split(' ')
                for pc in conn_to_list:
                    pc_asset = port_asset_mapping[pc]
                    pc_asset_coord = pc_asset['coord']
                    conn_list.append({'from-port-id': p.get_id(), 'from-asset-id': basset.get_id(), 'from-asset-coord': coord,
                        'to-port-id': pc, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})

        if isinstance(basset, esdl.AbstractBuilding):
            process_building(asset_list, area_bld_list, port_asset_mapping, basset, level+1)


def process_area(asset_list, area_bld_list, conn_list, port_asset_mapping, area, level):
    area_bld_list.append(['Area', area.get_id(), area.get_name(), level])

    # process subareas
    for ar in area.get_area():
        process_area(asset_list, area_bld_list, conn_list, port_asset_mapping, ar, level+1)

    # process assets in area
    for asset in area.get_asset():
        if isinstance(asset, esdl.AggregatedBuilding):
            process_building(asset_list, area_bld_list, conn_list, port_asset_mapping, asset, level+1)
        if isinstance(asset, esdl.EnergyAsset):
            geom = asset.get_geometry()
            coord =()
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.get_lat()
                    lon = geom.get_lon()

                    asset_list.append(['point', asset.get_name(), asset.get_id(), type(asset).__name__, lat, lon])
                if isinstance(geom, esdl.Line):
                    coords = []
                    for point in geom.get_point():
                        coords.append([point.get_lat(), point.get_lon()])
                    asset_list.append(['line', asset.get_name(), asset.get_id(), type(asset).__name__, coords])

            ports = asset.get_port()
            for p in ports:
                p_asset = port_asset_mapping[p.get_id()]
                p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
                conn_to = p.get_connectedTo()
                if conn_to:
                    conn_to_list = conn_to.split(' ')   # connectedTo attribute is list of port ID's separated by a space
                    for pc in conn_to_list:
                        pc_asset = port_asset_mapping[pc]
                        pc_asset_coord = pc_asset['coord']

                        conn_list.append({'from-port-id': p.get_id(), 'from-asset-id': p_asset['asset_id'], 'from-asset-coord': p_asset_coord,
                                          'to-port-id': pc, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})


# TODO: Not used now, should we keep the conn_list updated?
def add_connection_to_list(conn_list, from_port_id, from_asset_id, from_asset_coord, to_port_id, to_asset_id, to_asset_coord):
    conn_list.append(
        {'from-port-id': from_port_id, 'from-asset-id': from_asset_id, 'from-asset-coord': from_asset_coord,
         'to-port-id': to_port_id, 'to-asset-id': to_asset_id, 'to-asset-coord': to_asset_coord})


def update_asset_connection_locations(ass_id, lat, lon):
    conn_list = session['conn_list']
    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            c['from-asset-coord'] = (lat, lon)
        if c['to-asset-id'] == ass_id:
            c['to-asset-coord'] = (lat, lon)
    emit('conn_list', conn_list)


def update_transport_connection_locations(ass_id, asset, coords):
    conn_list = session['conn_list']
    mapping = session['port_to_asset_mapping']

    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            port_id = c['from-port-id']
            port_ass_map = mapping[port_id]
            if port_ass_map['pos'] == 'first':
                c['from-asset-coord'] = coords[0]
            else:
                c['from-asset-coord'] = coords[len(coords)-1]
        if c['to-asset-id'] == ass_id:
            port_id = c['to-port-id']
            port_ass_map = mapping[port_id]
            if port_ass_map['pos'] == 'first':
                c['to-asset-coord'] = coords[0]
            else:
                c['to-asset-coord'] = coords[len(coords)-1]

    emit('conn_list', conn_list)


# mapping[ports[1].get_id()] = {'asset_id': asset.get_id(), 'coord': last, 'pos': 'last'}


# ---------------------------------------------------------------------------------------------------------------------
#  Calculate distance between two points (for cable and pipe lengths)
# ---------------------------------------------------------------------------------------------------------------------
def distance(origin, destination):
    """
    source: https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


# ---------------------------------------------------------------------------------------------------------------------
#  Create connections between assets
# ---------------------------------------------------------------------------------------------------------------------
def connect_ports(port1, port2):
    port1conn = port1.get_connectedTo()
    port2conn = port2.get_connectedTo()

    if port1conn:
        port1.set_connectedTo(port1conn + ' ' + port2.get_id())
    else:
        port1.set_connectedTo(port2.get_id())
    if port2conn:
        port2.set_connectedTo(port2conn + ' ' + port1.get_id())
    else:
        port2.set_connectedTo(port1.get_id())


def connect_asset_with_conductor(asset, conductor):
    asset_geom = asset.get_geometry()
    cond_geom = conductor.get_geometry()

    if isinstance(cond_geom, esdl.Line):
        points = cond_geom.get_point()
        first_point = points[0]
        last_point = points[len(points) - 1]
    else:
        send_alert('UNSUPPORTED - conductor geometry is not a Line')
        return

    if not isinstance(asset_geom, esdl.Point):
        send_alert('UNSUPPORTED - asset geometry is not a Point')
        return

    if (distance((asset_geom.get_lat(), asset_geom.get_lon()), (first_point.get_lat(), first_point.get_lon())) <
            distance((asset_geom.get_lat(), asset_geom.get_lon()), (last_point.get_lat(), last_point.get_lon()))):
        # connect asset with first_point of conductor

        cond_port = conductor.get_port()[0]
        for p in asset.get_port():
            if not type(p).__name__ == type(cond_port).__name__:
                print('connect asset with first_point')
                connect_ports(p, cond_port)
                emit('add_new_conn', [[asset_geom.get_lat(),asset_geom.get_lon()],[first_point.get_lat(),first_point.get_lon()]])
                return
    else:
        # connect asset with last_point of conductor

        cond_port = conductor.get_port()[1]
        for p in asset.get_port():
            if not type(p).__name__ == type(cond_port).__name__:
                print('connect asset with last_point')
                connect_ports(p, cond_port)
                emit('add_new_conn',
                     [[asset_geom.get_lat(), asset_geom.get_lon()], [last_point.get_lat(), last_point.get_lon()]])
                return


def connect_asset_with_asset(asset1, asset2):
    ports1 = asset1.get_port()
    num_ports1 = len(ports1)
    ports2 = asset2.get_port()
    num_ports2 = len(ports2)

    if num_ports1 == 1:
        found = None
        if isinstance(ports1[0], esdl.OutPort):
            # find inport on other asset

            for p in ports2:
                if isinstance(p, esdl.InPort):
                    # connect p and ports1[0]
                    print('connect p and ports1[0]')
                    connect_ports(p, ports1[0])
                    emit('add_new_conn',
                         [[asset1.get_lat(), asset1.get_lon()], [asset2.get_lat(), asset2.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No InPort found on asset2')
                return
        else:
            # find inport on other asset
            for p in ports2:
                if isinstance(p, esdl.OutPort):
                    # connect p and ports1[0]
                    print('connect p and ports1[0]')
                    connect_ports(p, ports1[0])
                    emit('add_new_conn',
                         [[asset1.get_lat(), asset1.get_lon()], [asset2.get_lat(), asset2.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No OutPort found on asset2')
                return
    elif num_ports2 == 1:
        found = None
        if isinstance(ports2[0], esdl.OutPort):
            # find inport on other asset

            for p in ports1:
                if isinstance(p, esdl.InPort):
                    # connect p and ports2[0]
                    print('connect p and ports2[0]')
                    connect_ports(p, ports2[0])
                    emit('add_new_conn',
                         [[asset1.get_lat(), asset1.get_lon()], [asset2.get_lat(), asset2.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No InPort found on asset1')
                return
        else:
            # find inport on other asset
            for p in ports1:
                if isinstance(p, esdl.OutPort):
                    # connect p and ports2[0]
                    print('connect p and ports2[0]')
                    connect_ports(p, ports2[0])
                    emit('add_new_conn',
                         [[asset1.get_lat(), asset1.get_lon()], [asset2.get_lat(), asset2.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No OutPort found in asset1')
                return
    else:
        send_alert('UNSUPPORTED - Cannot determine what ports to connect')


def connect_conductor_with_conductor(conductor1, conductor2):
    c1points = conductor1.get_geometry().get_point()
    c1p0 = c1points[0]
    c1p1 = c1points[len(c1points) - 1]
    c2points = conductor2.get_geometry().get_point()
    c2p0 = c2points[0]
    c2p1 = c2points[len(c2points) - 1]

    dp = []
    dp.append(distance((c1p0.get_lat(),c1p0.get_lon()),(c2p0.get_lat(),c2p0.get_lon())))
    dp.append(distance((c1p0.get_lat(),c1p0.get_lon()),(c2p1.get_lat(),c2p1.get_lon())))
    dp.append(distance((c1p1.get_lat(),c1p1.get_lon()),(c2p0.get_lat(),c2p0.get_lon())))
    dp.append(distance((c1p1.get_lat(),c1p1.get_lon()),(c2p1.get_lat(),c2p1.get_lon())))

    smallest = 0
    for i in range(1,3):
        if dp[i] < dp[smallest]:
            smallest = i

    if smallest == 0:
        conn1 = conductor1.get_port()[0]
        conn2 = conductor2.get_port()[0]
        conn_pnt1 = c1p0
        conn_pnt2 = c2p0
    elif smallest == 1:
        conn1 = conductor1.get_port()[0]
        conn2 = conductor2.get_port()[1]
        conn_pnt1 = c1p0
        conn_pnt2 = c2p1
    elif smallest == 2:
        conn1 = conductor1.get_port()[1]
        conn2 = conductor2.get_port()[0]
        conn_pnt1 = c1p1
        conn_pnt2 = c2p0
    elif smallest == 3:
        conn1 = conductor1.get_port()[1]
        conn2 = conductor2.get_port()[1]
        conn_pnt1 = c1p1
        conn_pnt2 = c2p1

    if not type(conn1).__name__ == type(conn2).__name__:
        connect_ports(conn1, conn2)
        emit('add_new_conn',
             [[conn_pnt1.get_lat(), conn_pnt1.get_lon()], [conn_pnt2.get_lat(), conn_pnt2.get_lon()]])
    else:
        send_alert('UNSUPPORTED - Cannot connect two ports of same type')


def get_asset_attributes(asset):
    asset_attrs = copy.deepcopy(vars(asset))
    # method_list = [func for func in dir(asset) if callable(getattr(asset, func)) and func.startswith("set_")]

    # TODO: check which attributes must be filtered (cannot be easily edited)
    if 'geometry' in asset_attrs:
        asset_attrs.pop('geometry', None)
    if 'port' in asset_attrs:
        asset_attrs.pop('port', None)
    if 'costInformation' in asset_attrs:
        asset_attrs.pop('costInformation', None)

    attrs_sorted = sorted(asset_attrs.items(), key=lambda kv: kv[0])
    return attrs_sorted
# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('command', namespace='/esdl')
def process_command(message):
    print ('received: ' + message['cmd'])
    es_edit = session['es_edit']
    mapping = session['port_to_asset_mapping']
    # print (session['es_edit'].get_instance()[0].get_area().get_name())

    if message['cmd'] == 'add_asset':
        area_bld_id = message['area_bld_id']
        asset_id = message['asset_id']
        assettype = message['asset']
        if assettype == 'WindTurbine' or assettype == 'PVParc' or assettype == 'GeothermalSource':
            if assettype == 'WindTurbine': asset = esdl.WindTurbine()
            if assettype == 'PVParc': asset = esdl.PVParc()
            if assettype == 'GeothermalSource': asset = esdl.GeothermalSource()

            outp = esdl.OutPort()
            port_id = str(uuid.uuid4())
            outp.set_id(port_id)
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        if assettype == 'ElectricityDemand' or assettype == 'HeatingDemand':
            if assettype == 'ElectricityDemand': asset = esdl.ElectricityDemand()
            if assettype == 'HeatingDemand': asset = esdl.HeatingDemand()

            inp = esdl.InPort()
            port_id = str(uuid.uuid4())
            inp.set_id(port_id)
            asset.add_port_with_type(inp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        if assettype == 'Joint':
            asset = esdl.Joint()

            inp = esdl.InPort()
            port_id = str(uuid.uuid4())
            inp.set_id(port_id)
            asset.add_port_with_type(inp)
            outp = esdl.OutPort()
            port_id = str(uuid.uuid4())
            outp.set_id(port_id)
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}

        if assettype == 'ElectricityCable' or assettype == 'Pipe':
            if assettype == 'ElectricityCable': asset = esdl.ElectricityCable()
            if assettype == 'Pipe': asset = esdl.Pipe()

            inp = esdl.InPort()
            inp_id = str(uuid.uuid4())
            inp.set_id(inp_id)
            outp = esdl.OutPort()
            outp_id = str(uuid.uuid4())
            outp.set_id(outp_id)
            asset.add_port_with_type(inp)
            asset.add_port_with_type(outp)

            polyline_data = message['polyline']
            print(polyline_data)
            print(type(polyline_data))
            polyline_length = float(message['length'])
            asset.set_length(polyline_length)

            line = esdl.Line()
            i = 0
            prev_lat = 0
            prev_lng = 0
            while i < len(polyline_data):
                coord = polyline_data[i]

                if i == 0:
                    first = (coord['lat'], coord['lng'])
                if i == len(polyline_data)-1:
                    last = (coord['lat'], coord['lng'])

                # Don't understand why, but sometimes coordinates come in twice
                if prev_lat != coord['lat'] and prev_lng != coord['lng']:
                    point = esdl.Point()
                    point.set_lon(coord['lng'])
                    point.set_lat(coord['lat'])
                    line.add_point(point)
                    prev_lat = coord['lat']
                    prev_lng = coord['lng']
                i += 1

            asset.set_geometry_with_type(line)

            mapping[inp_id] = {'asset_id': asset_id, 'coord': first, 'pos': 'first'}
            mapping[outp_id] = {'asset_id': asset_id, 'coord': last, 'pos': 'last'}

        asset.set_id(asset_id)

        if not add_asset_to_area(es_edit, asset, area_bld_id):
            add_asset_to_building(es_edit, asset, area_bld_id)

    if message['cmd'] == 'remove_asset':
        asset_id = message['id']
        if asset_id:
            remove_asset_from_energysystem(es_edit, asset_id)
        else:
            send_alert('Asset without an id cannot be removed')

    if message['cmd'] == 'get_asset_ports':
        asset_id = message['id']
        port_list = []
        if asset_id:
            asset = find_asset(es_edit.get_instance()[0].get_area(), asset_id)
            ports = asset.get_port()
            for p in ports:
                port_list.append({id: p.get_id(), type: type(p).__name__})
            emit('portlist', port_list)

    if message['cmd'] == 'connect_assets':
        asset_id1 = message['id1']
        asset_id2 = message['id2']
        area = es_edit.get_instance()[0].get_area()

        asset1 = find_asset(area, asset_id1)
        asset2 = find_asset(area, asset_id2)
        print('Connecting asset ' + asset1.get_id() + ' and asset ' + asset2.get_id())

        geom1 = asset1.get_geometry()
        geom2 = asset2.get_geometry()

        if isinstance(asset1, esdl.AbstractConductor) or isinstance(asset2, esdl.AbstractConductor):

            if isinstance(asset1, esdl.AbstractConductor):
                if isinstance(geom1, esdl.Line):
                    points = geom1.get_point()
                    first_point1 = points[0]
                    last_point1 = points[len(points)-1]
                    first = 'line'
                if isinstance(geom1, esdl.Point): # in case of a Joint
                    point1=geom1
                    first='point'
            else:
                if isinstance(geom1, esdl.Point):
                    point1 = geom1
                    first = 'point'

            if isinstance(asset2, esdl.AbstractConductor):
                if isinstance(geom2, esdl.Line):
                    points = geom2.get_point()
                    first_point2 = points[0]
                    last_point2 = points[len(points)-1]
                    second = 'line'
                if isinstance(geom2, esdl.Point): # in case of a Joint
                    point2=geom2
                    second='point'
            else:
                if isinstance(geom2, esdl.Point):
                    point2 = geom2
                    second = 'point'
        else:
            point1 = geom1
            first = 'point'
            point2 = geom2
            second = 'point'

        if first == 'point' and second == 'point':
            connect_asset_with_asset(asset1, asset2)
        if first == 'point' and second == 'line':
            connect_asset_with_conductor(asset1, asset2)
        if first == 'line' and second == 'point':
            connect_asset_with_conductor(asset2, asset1)
        if first == 'line' and second == 'line':
            connect_conductor_with_conductor(asset1, asset2)

    if message['cmd'] == 'get_asset_info':
        asset_id = message['id']
        area = es_edit.get_instance()[0].get_area()

        asset = find_asset(area, asset_id)
        print('Get info for asset ' + asset.get_id())
        attrs_sorted = get_asset_attributes(asset)
        name = asset.get_name()
        if name is None: name = ''
        emit('asset_info', {'id': asset_id, 'name': name, 'attrs': attrs_sorted})

    if message['cmd'] == 'get_conductor_info':
        asset_id = message['id']
        latlng = message['latlng']
        area = es_edit.get_instance()[0].get_area()
        asset = find_asset(area, asset_id)
        print('Get info for asset ' + asset.get_id())
        attrs_sorted = get_asset_attributes(asset)
        name = asset.get_name()
        if name is None: name = ''
        emit('conductor_info', {'id': asset_id, 'name': name, 'latlng': latlng, 'attrs': attrs_sorted})

    if message['cmd'] == 'set_asset_param':
        asset_id = message['id']
        param_name = message['param_name']
        param_value = message['param_value']

        area = es_edit.get_instance()[0].get_area()

        asset = find_asset(area, asset_id)
        print('Set param '+ param_name +' for asset ' + asset_id + ' to value '+ param_value)

        # TODO: Find nice way to set al parameters based on their names
        # TODO: Take care of int, float, string (and ENUM?)
        if param_name in ['name', 'description']:
            getattr(asset, 'set_' + param_name)(param_value)
        if param_name in ['power']:
            getattr(asset, 'set_'+param_name)(float(param_value))

    if message['cmd'] == 'set_area_bld_polygon':
        area_bld_id = message['area_bld_id']
        polygon_data = message['polygon']

        polygon = esdl.Polygon()
        exterior = esdl.SubPolygon()
        polygon.set_exterior(exterior)

        i = 0
        prev_lat = 0
        prev_lng = 0
        while i < len(polygon_data[0]):
            coord = polygon_data[0][i]

            if i == 0:
                first = (coord['lat'], coord['lng'])
            if i == len(polygon_data) - 1:
                last = (coord['lat'], coord['lng'])

            # Don't understand why, but sometimes coordinates come in twice
            if prev_lat != coord['lat'] and prev_lng != coord['lng']:
                point = esdl.Point()
                point.set_lon(coord['lng'])
                point.set_lat(coord['lat'])
                exterior.add_point(point)
                prev_lat = coord['lat']
                prev_lng = coord['lng']
            i += 1

        area = es_edit.get_instance()[0].get_area()
        area_selected = find_area(area, area_bld_id)
        if area_selected:
            area_selected.set_contour(polygon)
        else:
            bld_selected = find_asset(area, area_bld_id)
            if bld_selected:
                bld_selected.set_geometry_with_type(polygon)
            else:
                send_alert('SERIOUS ERROR: set_area_bld_polygon - connot find area or building')

    session['es_edit'] = es_edit


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('file_command', namespace='/esdl')
def process_file_command(message):
    print ('received: ' + message['cmd'])

    if message['cmd'] == 'new_esdl':
        title = message['title']
        description = message['description']
        email = message['email']
        top_area_name = message['top_area_name']
        if top_area_name == '': top_area_name = 'Test area'

        es_edit = esdl.EnergySystem()
        es_id = str(uuid.uuid4())
        es_edit.set_id(es_id)
        es_edit.set_name(title)
        es_edit.set_description(description)

        instance = esdl.Instance()
        instance.set_id(str(uuid.uuid4()))
        es_edit.add_instance(instance)

        area = esdl.Area()
        area.set_id(str(uuid.uuid4()))
        area.set_name(top_area_name)
        instance.set_area(area)

        asset_list = []
        area_bld_list = []
        conn_list = []

        mapping = {}
        create_port_to_asset_mapping(area, mapping)
        session['port_to_asset_mapping'] = mapping
        process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)
        session['conn_list'] = conn_list

        emit('loadesdl', asset_list)
        emit('area_bld_list', area_bld_list)
        emit('conn_list', conn_list)

        # create_ESDL_store_item(es_id, es_edit, title, description, email)
        emit('es_title', title)

        session['es_title'] = title
        session['es_edit'] = es_edit
        session['es_id'] = es_id
        session['es_descr'] = description
        session['es_email'] = email
        session['es_start'] = 'new'

    if message['cmd'] == 'get_list_from_store':
        result = requests.get(store_url)
        data = result.json()
        store_list = []
        for es in data:
            store_list.append({'id': es['id'], 'title': es['title']})

        emit('store_list', store_list)

    if message['cmd'] == 'load_esdl_from_store':
        es_id = message['id']
        es_edit = load_ESDL_EnergySystem(es_id)
        es_title = es_edit.get_name()       # TODO: check if this is right title, can also be the name in the store
        if es_title is None:
            es_title = 'No name'

        asset_list = []
        area_bld_list = []
        conn_list = []

        instance = es_edit.get_instance()
        area = instance[0].get_area()

        mapping = {}
        create_port_to_asset_mapping(area, mapping)
        session['port_to_asset_mapping'] = mapping
        process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)
        session['conn_list'] = conn_list

        emit('loadesdl', asset_list)
        emit('area_bld_list', area_bld_list)
        emit('conn_list', conn_list)
        emit('es_title', es_title)

        session['es_id'] = es_id
        session['es_edit'] = es_edit
        session['es_title'] = es_title
        session['es_start'] = 'load_store'

    if message['cmd'] == 'store_esdl':
        es_edit = session['es_edit']
        es_id = session['es_id']
        store_ESDL_EnergySystem(es_id, es_edit)

    if message['cmd'] == 'save_esdl':
        es_edit = session['es_edit']
        es_id = session['es_id']
        write_energysystem_to_file('EnergySystem.esdl', es_edit)
        emit('and_now_press_download_file')

    if message['cmd'] == 'download_esdl':
        es_edit = session['es_edit']
        name = session['es_title'].replace(' ', '_')

        send_ESDL_as_file(es_edit, name)


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('load_esdl_file', namespace='/esdl')
def load_esdl_file(message):
    print ('received load_esdl_file command')
    if message.startswith('<?xml'):
        # remove the <?xml encoding='' stuff, as the parseString doesn't like encoding in there
        message = message.split('\n', 1)[1]
    es_edit = esdl.parseString(message, True)

    es_title = es_edit.get_name()  # TODO: check if this is right title, can also be the name in the store
    if es_title is None:
        es_title = 'No name'
    es_id = es_edit.get_id()
    if es_id is None:
        es_id = str(uuid.uuid4())
        es_edit.set_id(es_id)

    asset_list = []
    area_bld_list = []
    conn_list = []

    instance = es_edit.get_instance()
    area = instance[0].get_area()
    area_id = area.get_id()
    area_scope = area.get_scope()
    if len(area_id) < 20 and area_scope:
        boundary = get_boundary_from_service(area_scope, area_id)
        if boundary:
            emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})
    area_contour = area.get_contour()
    if area_contour:
        boundary = create_boundary_from_contour(area_contour)
        emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'WGS84', 'boundary': boundary})

    find_more_boundaries_in_ESDL(area)

    mapping = {}
    create_port_to_asset_mapping(area, mapping)
    session['port_to_asset_mapping'] = mapping
    process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)
    session['conn_list'] = conn_list

    emit('loadesdl', asset_list)
    emit('area_bld_list', area_bld_list)
    emit('conn_list', conn_list)
    emit('es_title', es_title)

    session['es_id'] = es_id
    session['es_edit'] = es_edit
    session['es_title'] = es_title
    session['es_start'] = 'load_file'

# ---------------------------------------------------------------------------------------------------------------------
#  Update ESDL coordinates on movement of assets in browser
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('update-coord', namespace='/esdl')
def update_coordinates(message):
    print ('received: ' + str(message['id']) + ':' + str(message['lat']) + ',' + str(message['lng']))
    ass_id = message['id']

    es_edit = session['es_edit']
    instance = es_edit.get_instance()
    area = instance[0].get_area()
    asset = find_asset(area, ass_id)

    if asset:
        point = esdl.Point()
        point.set_lon(message['lng'])
        point.set_lat(message['lat'])
        asset.set_geometry_with_type(point)

    # Update locations of connections on moving assets
    update_asset_connection_locations(ass_id, message['lat'], message['lng'])

    session['es_edit'] = es_edit

@socketio.on('update-line-coord', namespace='/esdl')
def update_line_coordinates(message):
    print ('received: ' + str(message['id']) + ':' + str(message['polyline']))
    ass_id = message['id']

    es_edit = session['es_edit']
    instance = es_edit.get_instance()
    area = instance[0].get_area()
    asset = find_asset(area, ass_id)

    if asset:
        polyline_data = message['polyline']
        # print(polyline_data)
        # print(type(polyline_data))
        polyline_length = float(message['length'])
        asset.set_length(polyline_length)

        line = esdl.Line()
        for i in range(0, len(polyline_data)):
            coord = polyline_data[i]

            point = esdl.Point()
            point.set_lon(coord['lng'])
            point.set_lat(coord['lat'])
            line.add_point(point)

        asset.set_geometry_with_type(line)

        update_transport_connection_locations(ass_id, asset, polyline_data)

    session['es_edit'] = es_edit

# ---------------------------------------------------------------------------------------------------------------------
#  Get boundary information
#
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('get_boundary_info', namespace='/esdl')
def get_boundary_info(info):
    print(info)
    identifier = info["identifier"]
    scope = info["scope"]
    subscope = info["subscope"]

    boundaries = get_subboundaries_from_service(scope, subscope, identifier)
    # boundaries is an ARRAY of:
    # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
    # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

    for boundary in boundaries:
        # print(boundary)

        geom = boundary["geom"]
        print('boundary["geom"]: ')
        print(boundary["geom"])
        print({'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': json.loads(geom)})

        # boundary = create_boundary_from_contour(area_contour)
        # emit('area_boundary', {'crs': 'WGS84', 'boundary': boundary})

        emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': json.loads(geom)})

    print('ready')


# ---------------------------------------------------------------------------------------------------------------------
#  Connect from browser
#   - initialize energysystem information
#   - send info to browser
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('connect', namespace='/esdl')
def on_connect():
    emit('log', {'data': 'Connected', 'count': 0})
    print('Connected')

    asset_list = []
    area_bld_list = []
    conn_list = []

    # ES_ID = "5df98542-430a-44b0-933c-e1c663a48c70"   # Ameland met coordinaten
    # es_id = "86179000-de3a-4173-a4d5-9a2dda2fe7c7"  # Ameland met coords en ids
    # es_edit = load_ESDL_EnergySystem(es_id)
    # es_title = 'Ameland'

    es_title = 'Test EnergySystem'
    es_id = str(uuid.uuid4())
    es_edit = esdl.EnergySystem()
    es_edit.set_id(es_id)
    instance = esdl.Instance()
    instance.set_id(str(uuid.uuid4()))
    es_edit.add_instance(instance)
    area = esdl.Area()
    area.set_id(str(uuid.uuid4()))
    instance.set_area(area)

    # instance = es_edit.get_instance()
    # area = instance[0].get_area()
    mapping = {}
    create_port_to_asset_mapping(area, mapping)
    session['port_to_asset_mapping'] = mapping
    process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)
    session['conn_list'] = conn_list

    emit('es_title', es_title)
    emit('loadesdl', asset_list)
    emit('area_bld_list', area_bld_list)
    emit('conn_list', conn_list)

    session['es_title'] = es_title
    session['es_edit'] = es_edit
    session['es_id'] = es_id


# ---------------------------------------------------------------------------------------------------------------------
#  Disconnect
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect', namespace='/esdl')
def on_disconnect():
    print('Client disconnected', request.sid)


# ---------------------------------------------------------------------------------------------------------------------
#  Start application
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True)
