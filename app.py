#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, session, request, send_from_directory, send_file
from flask_socketio import SocketIO, emit
import requests
import uuid
import math
import copy
import json
import importlib

# import numpy as np
# from scipy.spatial import Delaunay
# from shapely.geometry import Polygon, MultiPolygon, Point

from model import esdl_sup as esdl
import esdl_config


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

color_method = 'buildingyear'
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

BUILDING_COLORS_TYPE = {
    "RESIDENTIAL": '#800000', # dark red
    "GATHERING":   '#ffff00', # yellow
    "PRISON":      '#c0c0ff', # light blue / purple
    "HEALTHCARE":  '#ff0000', # light red
    "INDUSTRY":    '#000000', # black
    "OFFICE":      '#0000ff', # blue
    "EDUCATION":   '#ff00ff', # purple
    "SPORTS":      '#ff8000', # orange
    "SHOPPING":    '#00ff00', # light green
    "HOTEL":       '#00ffff', # cyan
    "GREENHOUSE":  '#008000', # dark green
    "UTILITY":     '#330000', # brown
    "OTHER":       '#888888'  # gray
}

AREA_LINECOLOR = 'blue'
AREA_FILLCOLOR = 'red'

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


def get_boundary_from_service(scope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    try:
        url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(scope)] + '/' + id
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


def get_subboundaries_from_service(scope, subscope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param subscope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    try:
        url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(subscope)]\
              + '/' + scope + '/' + id
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
    firstlat = points[0].get_lat()
    firstlon = points[0].get_lon()
    for point in points:
        lat = point.get_lat()
        lon = point.get_lon()
        ar.append([lon, lat])
    ar.append([firstlon, firstlat])     # close the polygon: TODO: check if necessary??
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


def create_boundary_from_geometry(geometry):
    if isinstance(geometry, esdl.Polygon):
        exterior = geometry.get_exterior()
        interiors = geometry.get_interior()

        ar = []
        ar.append(_parse_esdl_subpolygon(exterior))
        for interior in interiors:
            ar.append(_parse_esdl_subpolygon(interior))

        geom = {
            'type': 'Polygon',     # TODO: was POLYGON
            'coordinates': ar
        }
        # print(geom)

    if isinstance(geometry, esdl.MultiPolygon):
        polygons = geometry.get_polygon()
        mp = []
        for polygon in polygons:
            exterior = polygon.get_exterior()
            interiors = polygon.get_interior()

            ar = []
            ar.append(_parse_esdl_subpolygon(exterior))
            for interior in interiors:
                ar.append(_parse_esdl_subpolygon(interior))

            mp.append(ar)

        geom = {
            'type': 'MultiPolygon',
            'coordinates': mp
        }
        # print(geom)

    return geom


def _convert_coordinates_into_subpolygon(coord_list):
    # print(coord_list)
    # [[x1,y1], [x2,y2], ...]

    subpolygon = esdl.SubPolygon()
    for coord_pairs in coord_list:
        point = esdl.Point()
        point.set_lat(coord_pairs[0])
        point.set_lon(coord_pairs[1])
        subpolygon.add_point(point)

    return subpolygon


def _convert_pcoordinates_into_polygon(coord_list):
    polygon = esdl.Polygon()

    coord_exterior = coord_list[0]
    exterior = _convert_coordinates_into_subpolygon(coord_exterior)
    polygon.set_exterior(exterior)

    if len(coord_list) > 1:
        coord_list.pop(0)  # remove exterior polygon
        for coord_interior in coord_list:  # iterate over remaining interiors
            interior = _convert_coordinates_into_subpolygon(coord_interior)
            polygon.add_interior(interior)

    return polygon


def _convert_mpcoordinates_into_multipolygon(coord_list):
    mp = esdl.MultiPolygon()
    for coord_polygon in coord_list:
        polygon = _convert_pcoordinates_into_polygon(coord_polygon)
        mp.add_polygon(polygon)

    return mp


def create_geometry_from_geom(geom):
    """
    :param geom: geometry information
    :return: esdl.MultiPolygon or esdl.Polygon
    """
    # paramter geom has following structure:
    # 'geom': {
    #    "type":"MultiPolygon",
    #    "bbox":[...],
    #    "coordinates":[[[[6.583651,53.209594], [6.58477,...,53.208816],[6.583651,53.209594]]]]
    # }

    type = geom['type']
    coordinates = geom['coordinates']

    if type == 'MultiPolygon':
        return _convert_mpcoordinates_into_multipolygon(coordinates)
    if type == 'Polygon':
        return _convert_pcoordinates_into_polygon(coordinates)

    return None


def _determine_color(asset, color_method):
    building_color = '#808080'

    if isinstance(asset, esdl.Building):
        if color_method == 'buildingyear':
            building_year = asset.get_buildingYear()
            if building_year:
                building_color = None
                i = 0
                while not building_color:
                    if BUILDING_COLORS_BUILDINGYEAR[i]['from'] <= building_year < BUILDING_COLORS_BUILDINGYEAR[i]['to']:
                        building_color = BUILDING_COLORS_BUILDINGYEAR[i]['color']
                    i += 1
        elif color_method == 'floor area':
            floorarea = asset.get_floorArea()
            if floorarea:
                building_color = None
                i = 0
                while not floorarea:
                    if BUILDING_COLORS_AREA[i]['from'] <= floorarea < BUILDING_COLORS_AREA[i]['to']:
                        building_color = BUILDING_COLORS_AREA[i]['color']
                    i += 1
        elif color_method == 'type':
            bassets = asset.get_asset()
            for basset in bassets:
                if isinstance(basset, esdl.BuildingUnit):
                    type = basset.get_type()
                    if type:
                        building_color = BUILDING_COLORS_TYPE[type]

    return building_color


def _find_more_area_boundaries(this_area):
    area_id = this_area.get_id()
    area_scope = this_area.get_scope()
    area_geometry = this_area.get_geometry()

    if area_geometry:
        if isinstance(area_geometry, esdl.Polygon):
            boundary = create_boundary_from_geometry(area_geometry)
            emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
        if isinstance(area_geometry, esdl.MultiPolygon):
            boundary = create_boundary_from_geometry(area_geometry)
            emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

        # check to see if ESDL file contains asset locations; if not generate locations
        # TODO: following call does nothing now
        # TODO: Check if this can be called recursively
        update_asset_geometries2(this_area, boundary)
    else:
        # simple hack to check if ID is not a UUID and area_scope is defined --> then query GEIS for boundary
        if area_id and area_scope:
            if len(area_id) < 20:
                boundary = get_boundary_from_service(area_scope, area_id)
                if boundary:
                    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

    assets = this_area.get_asset()
    for asset in assets:
        if isinstance(asset, esdl.AbstractBuilding):
            name = asset.get_name()
            if not name:
                name = ''
            asset_geometry = asset.get_geometry()
            if asset_geometry:
                if isinstance(asset_geometry, esdl.Polygon):
                    building_color = _determine_color(asset, session["color_method"])
                    boundary = create_boundary_from_contour(asset_geometry)

                    emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': building_color, 'name': name})

    areas = this_area.get_area()
    for area in areas:
        _find_more_area_boundaries(area)


# TODO: This seems not to be required. No seperate treatment for top level area?
def find_boundaries_in_ESDL(top_area):
    _find_more_area_boundaries(top_area)


# ---------------------------------------------------------------------------------------------------------------------
#  Application definition, configuration and setup of simple file server
# ---------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode, path='/socket.io')


# TEMPORARY SOLUTION TO DISABLE BROWSER CACHING DURING TESTING
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/')
def index():
    print('in def index()')
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
    print('in def download_esdl()'+ path)
    return send_from_directory('', path)


@app.route('/images/<path:path>')
def send_image(path):
    print('in def send_image()'+ path)
    return send_from_directory('images', path)


@app.route('/plugins/<path:path>')
def send_plugin(path):
    print('in def send_plugin()'+ path)
    return send_from_directory('plugins', path)


@app.route('/icons/<path:path>')
def send_icon(path):
    print('in def send_icon()'+ path)
    return send_from_directory('icons', path)


# FOR TESTING
@app.route('/html/<path:path>')
def send_html(path):
    print('in def send_html()'+ path)
    return send_from_directory('html', path)


# ---------------------------------------------------------------------------------------------------------------------
#  parse the ESDL config file
# ---------------------------------------------------------------------------------------------------------------------
def parse_esdl_config():
    esdlc = esdl_config.esdl_config
    print('Configuration found:')
    print(esdlc)


# ---------------------------------------------------------------------------------------------------------------------
#  Send alert to client UI
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


def find_potential(area, pot_id):
    for pot in area.get_potential():
        if pot.get_id() == pot_id:
            return pot

    for subarea in area.get_area():
        pot = find_potential(subarea, pot_id)
        if pot:
            return pot

    return None


def _find_asset_in_building_and_container(building, asset_id):
    for ass in building.get_asset():
        if ass.get_id() == asset_id:
            return ass, building
        if isinstance(ass, esdl.AbstractBuilding):
            asset, build = _find_asset_in_building_and_container(ass, asset_id)
            if asset:
                return asset, build
    return None


def find_asset_and_container(area, asset_id):
    for ass in area.get_asset():
        if ass.get_id() == asset_id:
            return ass, area
        if isinstance(ass, esdl.AbstractBuilding):
            asset, ar = _find_asset_in_building_and_container(ass, asset_id)
            if asset:
                return asset, ar

    for subarea in area.get_area():
        asset, ar = find_asset_and_container(subarea, asset_id)
        if asset:
            return asset, ar

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
    asset_dict = session['asset_dict']
    for p_remove in ports:
        p_id = p_remove.get_id()
        connected_to = p_remove.get_connectedTo()
        if connected_to:
            connected_to_list = connected_to.split(' ')
            for conns in connected_to_list:
                # conns now contains the id's of the port this port is referring to
                ass_info = mapping[conns]
                # asset = find_asset(area, ass_info['asset_id'])    # find_asset doesn't look for asset in top level area
                asset = asset_dict[ass_info['asset_id']]
                asset_ports = asset.get_port()
                for p_remove_ref in asset_ports:
                    conn_to = p_remove_ref.get_connectedTo()
                    conn_tos = conn_to.split(' ')
                    if p_id in conn_tos:
                        conn_tos.remove(p_id)
                    conn_to = ' '.join(conn_tos)
                    p_remove_ref.set_connectedTo(conn_to)


def _remove_object_from_building(area, building, object_id):
    for ass in building.get_asset():
        if ass.get_id() == object_id:
            ports = ass.get_port()
            _remove_port_references(area, ports)
            building.asset.remove(ass)
            print('Asset with id ' + object_id+ ' removed from building with id: ', + building.get_id())


def _recursively_remove_object_from_area(area, object_id):
    for ass in area.get_asset():
        if ass.get_id() == object_id:
            ports = ass.get_port()
            _remove_port_references(area, ports)
            area.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from area with id: ' + area.get_id())
        if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
            _remove_object_from_building(area, ass, object_id)
    for pot in area.get_potential():
        if pot.get_id() == object_id:
            area.potential.remove(pot)
            print('Potential with id ' + object_id + ' removed from area with id: ' + area.get_id())
    for sub_area in area.get_area():
        _recursively_remove_object_from_area(sub_area, object_id)


def remove_object_from_energysystem(es, object_id):
    # find area with area_id
    instance = es.get_instance()[0]
    area = instance.get_area()
    _recursively_remove_object_from_area(area, object_id)


def get_asset_capability_type(asset):
    if isinstance(asset, esdl.Producer): return 'producer'
    if isinstance(asset, esdl.Consumer): return 'consumer'
    if isinstance(asset, esdl.Storage): return 'storage'
    if isinstance(asset, esdl.Transport): return 'transport'
    if isinstance(asset, esdl.Conversion): return 'conversion'
    return 'none'


def get_carrier_list(es):
    carrier_list = []
    esi = es.get_energySystemInformation()
    if esi:
        ecs = esi.get_carriers()
        if ecs:
            ec = ecs.get_carrier()

            if ec:
                for carrier in ec:
                    carrier_info = {
                        'type': type(carrier).__name__,
                        'id': carrier.get_id(),
                        'name': carrier.get_name(),
                    }
                    if isinstance(carrier, esdl.Commodity):
                        if isinstance(carrier, esdl.ElectricityCommodity):
                            carrier_info['voltage'] = carrier.get_voltage()
                        if isinstance(carrier, esdl.GasCommodity):
                            carrier_info['pressure'] = carrier.get_pressure()
                        if isinstance(carrier, esdl.HeatCommodity):
                            carrier_info['supplyTemperature'] = carrier.get_supplyTemperature()
                            carrier_info['returnTemperature'] = carrier.get_returnTemperature()

                    if isinstance(carrier, esdl.EnergyCarrier):
                        carrier_info['energyContent'] = carrier.get_energyContent()
                        carrier_info['emission'] = carrier.get_emission()
                        carrier_info['energyCarrierType'] = carrier.get_energyCarrierType()
                        carrier_info['stateOfMatter'] = carrier.get_stateOfMatter()

                    # carrier_list.append({carrier.get_id(): carrier_info})
                    carrier_list.append(carrier_info)

    return carrier_list


def _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets):
    mapping = session['port_to_asset_mapping']
    asset_dict = session['asset_dict']

    asset = asset_dict[asset_id]
    processed_assets.append(asset_id)
    for p in asset.get_port():
        p.set_carrier(carrier_id)
        conn_to = p.get_connectedTo()
        if conn_to:
            conn_to_list = conn_to.split(' ')
            for conn_port_id in conn_to_list:
                conn_asset_id = mapping[conn_port_id]['asset_id']
                conn_asset = asset_dict[conn_asset_id]
                if isinstance(conn_asset, esdl.Transport) and not isinstance(conn_asset, esdl.HeatExchange)\
                        and not isinstance(conn_asset, esdl.Transformer):
                    if not conn_asset_id in processed_assets:
                        _set_carrier_for_connected_transport_assets(conn_asset_id, carrier_id, processed_assets)
                else:
                    for conn_asset_port in conn_asset.get_port():
                        if conn_asset_port.get_id() == conn_port_id:
                            conn_asset_port.set_carrier(carrier_id)


def set_carrier_for_connected_transport_assets(asset_id, carrier_id):
    processed_assets = []       # List of asset_id's that are processed
    _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets)
    # print(processed_assets)


# ---------------------------------------------------------------------------------------------------------------------
#  Initialize
#  TODO: find out what should be here :-)
# ---------------------------------------------------------------------------------------------------------------------
def initialize():
    session['port_to_asset_mapping'] = {}


# ---------------------------------------------------------------------------------------------------------------------
#  Builds up a dictionary from asset_id to asset
# ---------------------------------------------------------------------------------------------------------------------
def _create_building_asset_dict(asset_dict, building):
    for basset in building.get_asset():
        asset_dict[basset.get_id()] = basset


def _create_area_asset_dict(asset_dict, area):
    for ar in area.get_area():
        _create_area_asset_dict(asset_dict, ar)
    for asset in area.get_asset():
        asset_dict[asset.get_id()] = asset
        if isinstance(asset, esdl.AbstractBuilding):
            _create_building_asset_dict(asset_dict, asset)


def create_asset_dict(area):
    asset_dict = {}
    _create_area_asset_dict(asset_dict, area)

    return asset_dict


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
            else:
                for p in ports:
                    mapping[p.get_id()] = {'asset_id': basset.get_id(), 'coord': ()}


def create_port_to_asset_mapping(area, mapping):
    # process subareas
    for ar in area.get_area():
        create_port_to_asset_mapping(ar, mapping)

    # process assets in area
    for asset in area.get_asset():
        if isinstance(asset, esdl.AggregatedBuilding):
            create_building_port_to_asset_mapping(asset, mapping)
        else:
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
                                p_id = str(uuid.uuid4())
                                p.set_id(p_id)
                            mapping[p_id] = {'asset_id': asset.get_id(), 'coord': coord}
                    if isinstance(geom, esdl.Line):
                        points = geom.get_point()
                        if ports:
                            first = (points[0].get_lat(), points[0].get_lon())
                            last = (points[len(points) - 1].get_lat(), points[len(points) - 1].get_lon())
                            mapping[ports[0].get_id()] = {'asset_id': asset.get_id(), 'coord': first, 'pos': 'first'}
                            mapping[ports[1].get_id()] = {'asset_id': asset.get_id(), 'coord': last, 'pos': 'last'}
                else:
                    for p in ports:
                        mapping[p.get_id()] = {'asset_id': asset.get_id(), 'coord': ()}


# ---------------------------------------------------------------------------------------------------------------------
#  Build up initial information about energysystem to send to browser
# ---------------------------------------------------------------------------------------------------------------------
def generate_point_in_area(boundary):
    return


def update_building_asset_geometries(building, avail_locations):
    for basset in building.get_asset():
        if isinstance(basset, esdl.EnergyAsset):
            geom = basset.get_geometry()
            if not geom:
                location = avail_locations.pop(0)
                geom = esdl.Point()
                geom.set_lon(location[1])
                geom.set_lat(location[0])
                basset.set_geometry(geom)


def update_area_asset_geometries(area, avail_locations):
    # process subareas
    for ar in area.get_area():
        update_area_asset_geometries(ar, avail_locations)

    # process assets in area
    for asset in area.get_asset():
        if isinstance(asset, esdl.AggregatedBuilding):
            update_building_asset_geometries(asset, avail_locations)
        if isinstance(asset, esdl.EnergyAsset):
            geom = asset.get_geometry()
            if not geom:
                location = avail_locations.pop(0)
                geom = esdl.Point()
                geom.set_lon(location[1])
                geom.set_lat(location[0])
                asset.set_geometry(geom)


def count_building_assets_and_potentials(building):
    num = len(building.get_asset())

    for basset in building.get_asset():
        if isinstance(basset, esdl.AbstractBuilding):
            num += count_building_assets_and_potentials(basset)

    return num


def count_assets_and_potentials(area):
    num = len(area.get_asset())
    num += len(area.get_potential())

    for ar_asset in area.get_asset():
        if isinstance(ar_asset, esdl.AbstractBuilding):
            num += count_building_assets_and_potentials(ar_asset)

    for ar in area.get_area():
        num += count_assets_and_potentials(ar)

    return num


def calculate_triangle_center(triangle):
    sumx = triangle[0][0] + triangle[1][0] + triangle[2][0]
    sumy = triangle[0][1] + triangle[1][1] + triangle[2][1]

    center_coord = [sumx / 3, sumy / 3]
    return center_coord


def update_asset_geometries(area, boundary):
    # coords = boundary['coordinates']
    # type = boundary['type']
    #
    # num_assets = count_assets_and_potentials(area)
    #
    # if type == 'Polygon':
    #     exterior_polygon_coords = coords[0]
    # elif type == 'MultiPolygon':
    #     # search for largest polygon in multipolygon
    #     maxlen = 0
    #     maxpolygon = []
    #     for polygon in coords:
    #         exterior = polygon[0]
    #         if len(exterior) > maxlen:
    #             maxlen = len(exterior)
    #             maxpolygon = exterior
    #     exterior_polygon_coords = maxpolygon[0]
    #
    # print(exterior_polygon_coords)
    #
    # points = np.array(exterior_polygon_coords)
    # tri = Delaunay(points)
    # triangles = points[tri.simplices]
    #
    # num_triangles = len(triangles)
    #
    # if num_assets <= num_triangles:
    #     triangle_step = num_triangles / num_assets + 2      # TODO: check 2?
    #     asset_coords = []
    #     for i in range(1, num_assets):      # TODO: check number
    #         asset_coords.append(calculate_triangle_center(triangles[round(triangle_step + triangle_step * i)]))
    #
    #     # TODO: iterate over all assets and assign coordinates
    #     print(asset_coords)
    #
    # else:
    #     print('ERROR: Number of assets larger than number of triangles')
    #
    pass


def update_asset_geometries2(area, boundary):
    # coords = boundary['coordinates']
    # type = boundary['type']
    #
    # num_assets = count_assets_and_potentials(area)
    #
    # if type == 'Polygon':
    #     exterior_polygon_coords = coords[0]
    # elif type == 'MultiPolygon':
    #     # search for largest polygon in multipolygon
    #     for polygon in coords:
    #         exterior_polygon_coords = polygon[0]
    #         # TODO: what's next? :-)
    #
    # polygon = Polygon(exterior_polygon_coords)
    # print(polygon.area)
    # bbox_coords = polygon.bounds
    # bl_x = bbox_coords[0]
    # bl_y = bbox_coords[1]
    # tr_x = bbox_coords[2]
    # tr_y = bbox_coords[3]
    # bbox_polygon = Polygon([[bl_x,bl_y],[tr_x, bl_y],[tr_x, tr_y],[bl_x, tr_y]])
    # print(bbox_polygon.area)
    # area_perc = polygon.area / bbox_polygon.area
    #
    # width = tr_x - bl_x
    # height = tr_y - bl_y
    #
    # req_num_points_in_area = num_assets * 1.5       # safety margin
    # num_points_in_bbox = req_num_points_in_area / area_perc
    #
    # # width/dx * height/dy = num_points_in_bbox
    # # 1 / dx * dy = num_points_in_bbox / (width * height)
    # # dx * dy = area / num_points_in_bbox
    # dxy = math.sqrt(bbox_polygon.area / num_points_in_bbox)
    #
    # available_locations = []
    #
    # xcntr = 1
    # while (bl_x + xcntr * dxy < tr_x):
    #     ycntr = 1
    #     while (bl_y + ycntr * dxy < tr_y):
    #         point = Point(bl_x + xcntr * dxy, bl_y + ycntr * dxy)
    #         if point.within(polygon):
    #             available_locations.append([bl_y + ycntr * dxy, bl_x + xcntr * dxy])
    #         ycntr += 1
    #     xcntr += 1
    #
    # update_area_asset_geometries(area, available_locations)
    pass


def generate_profile_info(profile):
    profile_class = type(profile).__name__
    print(profile_class)
    profile_type = profile.get_profileType()
    profile_name = profile.get_name()
    if profile_class == 'SingleValue':
        value = profile.get_value()
        profile_info = {'class': 'SingleValue', 'value': value, 'type': profile_type}
    if profile_class == 'InfluxDBProfile':
        multiplier = profile.get_multiplier()
        measurement = profile.get_measurement()
        profile_name = 'UNKNOWN'
        for p in esdl_config.esdl_config['influxdb_profile_data']:
            if p['measurement'] == measurement:
                profile_name = p['profile_uiname']
        profile_info = {'class': 'InfluxDBProfile', 'multiplier': multiplier, 'type': profile_type, 'uiname': profile_name}
    if profile_class == 'DateTimeProfile':
        profile_info = {'class': 'DateTimeProfile', 'type': profile_type}

    return profile_info


def process_building(asset_list, area_bld_list, conn_list, port_asset_mapping, building, level):
    area_bld_list.append(['Building', building.get_id(), building.get_name(), level])

    for basset in building.get_asset():
        port_list = []
        ports = basset.get_port()
        for p in ports:
            conn_to = p.get_connectedTo()
            port_list.append({'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': conn_to})

        geom = basset.get_geometry()
        coord = ()
        if geom:
            if isinstance(geom, esdl.Point):
                lat = geom.get_lat()
                lon = geom.get_lon()
                coord = (lat, lon)

                capability_type = get_asset_capability_type(basset)
                asset_list.append(['point', 'asset', basset.get_name(), basset.get_id(), type(basset).__name__, lat, lon, port_list, capability_type])

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
            process_building(asset_list, area_bld_list, conn_list, port_asset_mapping, basset, level+1)


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
            port_list = []
            ports = asset.get_port()
            for p in ports:
                p_asset = port_asset_mapping[p.get_id()]
                p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
                conn_to = p.get_connectedTo()
                profile = p.get_profile()
                profile_info = {}
                if profile:
                    profile_info = generate_profile_info(profile)
                port_list.append({'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': conn_to, 'profile': profile_info})
                if conn_to:
                    conn_to_list = conn_to.split(' ')   # connectedTo attribute is list of port ID's separated by a space
                    for pc in conn_to_list:
                        pc_asset = port_asset_mapping[pc]
                        pc_asset_coord = pc_asset['coord']

                        conn_list.append({'from-port-id': p.get_id(), 'from-asset-id': p_asset['asset_id'], 'from-asset-coord': p_asset_coord,
                                          'to-port-id': pc, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})

            geom = asset.get_geometry()
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.get_lat()
                    lon = geom.get_lon()

                    capability_type = get_asset_capability_type(asset)
                    asset_list.append(['point', 'asset', asset.get_name(), asset.get_id(), type(asset).__name__, lat, lon, port_list, capability_type])
                if isinstance(geom, esdl.Line):
                    coords = []
                    for point in geom.get_point():
                        coords.append([point.get_lat(), point.get_lon()])
                    asset_list.append(['line', 'asset', asset.get_name(), asset.get_id(), type(asset).__name__, coords, port_list])

    for potential in area.get_potential():
        geom = potential.get_geometry()
        if geom:
            if isinstance(geom, esdl.Point):
                lat = geom.get_lat()
                lon = geom.get_lon()

                asset_list.append(
                    ['point', 'potential', potential.get_name(), potential.get_id(), type(potential).__name__, lat, lon])
            # if isinstance(geom, esdl.Polygon):
            #     coords = []
            #     for point in geom.get_point():
            #         coords.append([point.get_lat(), point.get_lon()])
            #     asset_list.append(['line', asset.get_name(), asset.get_id(), type(asset).__name__, coords, port_list])


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

    emit('clear_connections')
    emit('add_connections', conn_list)

    session['conn_list'] = conn_list

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

    emit('clear_connections')
    emit('add_connections', conn_list)

    session['conn_list'] = conn_list

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
    asset1_geom = asset1.get_geometry()
    ports2 = asset2.get_port()
    num_ports2 = len(ports2)
    asset2_geom = asset2.get_geometry()

    if not isinstance(asset1_geom, esdl.Point) or not isinstance(asset2_geom, esdl.Point):
        send_alert('UNSUPPORTED - asset geometry is not a Point')
        return

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
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
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
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
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
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
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
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
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
    if 'dataSource' in asset_attrs:
        asset_attrs.pop('dataSource', None)

    attrs_sorted = sorted(asset_attrs.items(), key=lambda kv: kv[0])
    return attrs_sorted


def get_potential_attributes(potential):
    potential_attrs = copy.deepcopy(vars(potential))
    # method_list = [func for func in dir(potential) if callable(getattr(potential, func)) and func.startswith("set_")]

    # TODO: check which attributes must be filtered (cannot be easily edited)
    if 'geometry' in potential_attrs:
        potential_attrs.pop('geometry', None)
    if 'dataSource' in potential_attrs:
        potential_attrs.pop('dataSource', None)
    if 'quantityAndUnit' in potential_attrs:
        potential_attrs.pop('quantityAndUnit', None)

    attrs_sorted = sorted(potential_attrs.items(), key=lambda kv: kv[0])
    return attrs_sorted


# ---------------------------------------------------------------------------------------------------------------------
#  Split a conductor into two pieces
# ---------------------------------------------------------------------------------------------------------------------
def distance_point_to_line(p, p1, p2):
    x = p1['x']
    y = p1['y']
    dx = p2['x'] - x
    dy = p2['y'] - y
    dot = dx * dx + dy * dy
    
    if dot > 0:
        t = ((p['x'] - x) * dx + (p['y'] - y) * dy) / dot
    
        if t > 1:
            x = p2['x']
            y = p2['y']
        else:
            if t > 0:
                x += dx * t
                y += dy * t
                
    dx = p['x'] - x
    dy = p['y'] - y
    
    return dx * dx + dy * dy


def split_conductor(conductor, location, mode, conductor_container):
    mapping = session['port_to_asset_mapping']
    conn_list = session['conn_list']
    asset_dict = session['asset_dict']

    geometry = conductor.get_geometry()
    conductor_type = type(conductor).__name__
    conductor_id = conductor.get_id()
    middle_point = esdl.Point()
    middle_point.set_lat(location['lat'])
    middle_point.set_lon(location['lng'])

    if isinstance(geometry, esdl.Line):
        #create two seperate line segments
        line1 = esdl.Line()
        line2 = esdl.Line()

        #find piece of line where user clicked
        points = geometry.get_point()
        begin_point = points[0]
        line1.add_point(begin_point)

        points.pop(0)
        min_dist = 1e99
        segm_ctr = 0
        for point in points:
            p1 = {'x': begin_point.get_lat(), 'y': begin_point.get_lon()}
            p2 = {'x': point.get_lat(), 'y': point.get_lon()}
            p =  {'x': location['lat'], 'y': location['lng']}
            dist = distance_point_to_line(p, p1, p2)
            if dist < min_dist:
                min_dist = dist
                min_dist_segm = segm_ctr
            begin_point = point
            segm_ctr += 1

        # copy appropriate points in original conductor to either line1 or line2
        points = geometry.get_point()
        segm_ctr = 0
        for point in points:
            if segm_ctr == min_dist_segm:
                line1.add_point(copy.deepcopy(middle_point))
                line2.add_point(copy.deepcopy(middle_point))
            if segm_ctr < min_dist_segm:
                line1.add_point(point)
            else:
                line2.add_point(point)
            segm_ctr += 1
        end_point = point

        #find old ports and connections
        ports = conductor.get_port()
        if len(ports) != 2:
            send_alert('UNSUPPORTED: Conductor doesn\'t have two ports!')
            return
        port1 = ports[0]        # reuse old conductor's ports; TODO: check what happens after deleting conductor
        port2 = ports[1]

        # create two conductors of same type as conductor that is splitted
        module = importlib.import_module('model.esdl_sup')
        class_ = getattr(module, conductor_type)
        new_cond1 = class_()
        new_cond2 = class_()

        new_cond1_id = str(uuid.uuid4())
        new_cond2_id = str(uuid.uuid4())
        new_port1_id = str(uuid.uuid4())
        new_port2_id = str(uuid.uuid4())

        new_cond1.set_id(new_cond1_id)
        new_cond2.set_id(new_cond2_id)

        if type(port1).__name__ == "InPort":
            new_port2 = esdl.OutPort()
        else:
            new_port2 = esdl.InPort()
        new_port2.set_id(new_port2_id)
        if mode == 'connect':
            new_port2.set_connectedTo(new_port1_id)
        new_cond1.add_port_with_type(port1)
        new_cond1.add_port_with_type(new_port2)

        if type(port2).__name__ == "InPort":
            new_port1 = esdl.OutPort()
        else:
            new_port1 = esdl.InPort()
        new_port1.set_id(new_port1_id)
        if mode == 'connect':
            new_port1.set_connectedTo(new_port2_id)
        new_cond2.add_port_with_type(new_port1)
        new_cond2.add_port_with_type(port2)

        new_cond1.set_geometry_with_type(line1)
        new_cond2.set_geometry_with_type(line2)

        # remove conductor from container (area or building) and add new two conductors
        assets = conductor_container.get_asset()
        assets.remove(conductor)
        conductor_container.add_asset_with_type(new_cond1)
        conductor_container.add_asset_with_type(new_cond2)
        asset_dict[new_cond1_id] = new_cond1
        asset_dict[new_cond2_id] = new_cond2

        # update port asset mappings for conductors
        mapping[port1.get_id()] = {'asset_id': new_cond1_id, 'coord': (begin_point.get_lat(), begin_point.get_lon()), 'pos': 'first'}
        mapping[new_port2.get_id()] = {'asset_id': new_cond1_id, 'coord': (middle_point.get_lat(), middle_point.get_lon()), 'pos': 'last'}
        mapping[new_port1.get_id()] = {'asset_id': new_cond2_id, 'coord': (middle_point.get_lat(), middle_point.get_lon()), 'pos': 'first'}
        mapping[port2.get_id()] = {'asset_id': new_cond2_id, 'coord': (end_point.get_lat(), end_point.get_lon()), 'pos': 'last'}

        # create list of ESDL assets to be added to UI
        esdl_assets_to_be_added = []
        coords = []
        for point in line1.get_point():
            coords.append([point.get_lat(), point.get_lon()])
        esdl_assets_to_be_added.append(['line', 'asset', new_cond1.get_name(), new_cond1.get_id(), type(new_cond1).__name__, coords])
        coords = []
        for point in line2.get_point():
            coords.append([point.get_lat(), point.get_lon()])
        esdl_assets_to_be_added.append(['line', 'asset', new_cond2.get_name(), new_cond2.get_id(), type(new_cond2).__name__, coords])

        # update asset id's of conductor with new_cond1 and new_cond2 in conn_list
        for c in conn_list:
            if c['from-asset-id'] == conductor_id and c['from-port-id'] == port1.get_id():
                c['from-asset-id'] = new_cond1_id
            if c['from-asset-id'] == conductor_id and c['from-port-id'] == port2.get_id():
                c['from-asset-id'] = new_cond2_id
            if c['to-asset-id'] == conductor_id and c['to-port-id'] == port1.get_id():
                c['to-asset-id'] = new_cond1_id
            if c['to-asset-id'] == conductor_id and c['to-port-id'] == port2.get_id():
                c['to-asset-id'] = new_cond2_id

        # create list of connections to be added to UI
        if mode == 'connect':
            conn_list.append({'from-port-id': new_port2_id, 'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.get_lat(), middle_point.get_lon()),
                          'to-port-id': new_port1_id, 'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.get_lat(), middle_point.get_lon())})

        if mode == 'add_joint':
            joint = esdl.Joint()
            joint_id = str(uuid.uuid4())
            joint.set_id(joint_id)
            inp = esdl.InPort()
            joint_inp_id = str(uuid.uuid4())
            inp.set_id(joint_inp_id)
            outp = esdl.OutPort()
            joint_outp_id = str(uuid.uuid4())
            outp.set_id(joint_outp_id)

            if type(new_port2).__name__ == "OutPort":
                inp.set_connectedTo(new_port2_id)
                new_port2.set_connectedTo(joint_inp_id)
                new_port2_conn_to_id = joint_inp_id
            else:
                outp.set_connectedTo(new_port2_id)
                new_port2.set_connectedTo(joint_outp_id)
                new_port2_conn_to_id = joint_outp_id

            if type(new_port1).__name__ == "InPort":
                outp.set_connectedTo(new_port1_id)
                new_port1.set_connectedTo(joint_outp_id)
                new_port1_conn_to_id = joint_outp_id
            else:
                inp.set_connectedTo(new_port1_id)
                new_port1.set_connectedTo(joint_inp_id)
                new_port1_conn_to_id = joint_inp_id

            joint.add_port_with_type(inp)
            joint.add_port_with_type(outp)
            joint.set_geometry_with_type(middle_point)
            conductor_container.add_asset_with_type(joint)
            asset_dict[joint_id] = joint

            # Change port asset mappings
            mapping[joint_inp_id] = {'asset_id': joint_id, 'coord': (middle_point.get_lat(), middle_point.get_lon())}
            mapping[joint_outp_id] = {'asset_id': joint_id, 'coord': (middle_point.get_lat(), middle_point.get_lon())}

            esdl_assets_to_be_added.append(['point', 'asset', joint.get_name(), joint_id, type(joint).__name__, middle_point.get_lat(), middle_point.get_lon(), 'transport'])

            conn_list.append({'from-port-id': new_port2_id, 'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.get_lat(), middle_point.get_lon()),
                          'to-port-id': new_port2_conn_to_id, 'to-asset-id': joint_id, 'to-asset-coord': (middle_point.get_lat(), middle_point.get_lon())})
            conn_list.append({'from-port-id': new_port1_conn_to_id, 'from-asset-id': joint_id, 'from-asset-coord': (middle_point.get_lat(), middle_point.get_lon()),
                          'to-port-id': new_port1_id, 'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.get_lat(), middle_point.get_lon())})

        # now send new objects to UI
        emit('add_esdl_objects', {'list': esdl_assets_to_be_added, 'zoom': False})
        emit('clear_connections')
        emit('add_connections', conn_list)

        session['port_to_asset_mapping'] = mapping
        session['conn_list'] = conn_list
        session['asset_dict'] = asset_dict
    else:
        send_alert('UNSUPPORTED: Conductor is not of type esdl.Line!')


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('command', namespace='/esdl')
def process_command(message):
    print ('received: ' + message['cmd'])
    print (message)
    es_edit = session['es_edit']
    mapping = session['port_to_asset_mapping']
    asset_dict = session['asset_dict']
    # print (session['es_edit'].get_instance()[0].get_area().get_name())

    if message['cmd'] == 'add_asset':
        area_bld_id = message['area_bld_id']
        asset_id = message['asset_id']
        assettype = message['asset']

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an OutPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['GenericProducer', 'GeothermalSource', 'PVParc', 'WindTurbine']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            outp = esdl.OutPort()
            port_id = str(str(uuid.uuid4()))
            outp.set_id(port_id)
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['Battery', 'ElectricityDemand', 'GenericConsumer', 'HeatingDemand', 'UTES']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            port_id = str(str(uuid.uuid4()))
            inp.set_id(port_id)
            asset.add_port_with_type(inp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort and an OutPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['ElectricityNetwork', 'Electrolyzer', 'GasHeater', 'GasNetwork', 'GenericConversion', 'HeatNetwork',
                         'HeatPump', 'Joint', 'Transformer', 'PowerPlant']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

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
        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort and two OutPorts
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['CHP', 'FuelCell']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            port_id = str(uuid.uuid4())
            inp.set_id(port_id)
            asset.add_port_with_type(inp)
            outp = esdl.OutPort()
            port_id = str(uuid.uuid4())
            outp.set_id(port_id)
            asset.add_port_with_type(outp)
            outp = esdl.OutPort()
            port_id = str(uuid.uuid4())
            outp.set_id(port_id)
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a polyline geometry and an InPort and an OutPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['ElectricityCable', 'Pipe']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            inp_id = str(uuid.uuid4())
            inp.set_id(inp_id)
            outp = esdl.OutPort()
            outp_id = str(uuid.uuid4())
            outp.set_id(outp_id)
            asset.add_port_with_type(inp)
            asset.add_port_with_type(outp)

            polyline_data = message['polyline']
            # print(polyline_data)
            # print(type(polyline_data))
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

        # TODO: check / solve cable as Point issue?
        if assettype not in ['ElectricityCable', 'Pipe']:
            port_list = []
            asset_to_be_added_list = []
            ports = asset.get_port()
            for p in ports:
                port_list.append(
                    {'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': p.get_connectedTo()})
            capability_type = get_asset_capability_type(asset)
            asset_to_be_added_list.append(['point', 'asset', asset.get_name(), asset.get_id(), type(asset).__name__, message['lat'], message['lng'], port_list, capability_type])
            emit('add_esdl_objects', {'list': asset_to_be_added_list, 'zoom': False})

        asset_dict[asset_id] = asset

    if message['cmd'] == 'remove_object':        # TODO: remove form asset_dict
        # removes asset or potential from EnergySystem
        obj_id = message['id']
        if obj_id:
            remove_object_from_energysystem(es_edit, obj_id)
        else:
            send_alert('Asset or potential without an id cannot be removed')

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

    if message['cmd'] == 'get_object_info':
        object_id = message['id']
        asspot = message['asspot']
        area = es_edit.get_instance()[0].get_area()

        if asspot == 'asset':
            asset = find_asset(area, object_id)
            print('Get info for asset ' + asset.get_id())
            attrs_sorted = get_asset_attributes(asset)
            name = asset.get_name()
        else:
            pot = find_potential(area, object_id)
            print('Get info for potential ' + pot.get_id())
            attrs_sorted = get_potential_attributes(pot)
            name = pot.get_name()

        if name is None: name = ''
        emit('asset_info', {'id': object_id, 'name': name, 'attrs': attrs_sorted})

    if message['cmd'] == 'get_conductor_info':
        asset_id = message['id']
        latlng = message['latlng']
        area = es_edit.get_instance()[0].get_area()
        asset = find_asset(area, asset_id)
        print('Get info for conductor ' + asset.get_id())
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
            if prev_lat != coord['lat'] or prev_lng != coord['lng']:
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
            area_selected.set_geometry(polygon)
        else:
            bld_selected = find_asset(area, area_bld_id)
            if bld_selected:
                bld_selected.set_geometry_with_type(polygon)
            else:
                send_alert('SERIOUS ERROR: set_area_bld_polygon - connot find area or building')

    if message['cmd'] == 'split_conductor':
        cond_id = message['id']
        mode = message['mode']      # connect, add_joint, no_connect
        location_to_split = message['location']

        area = es_edit.get_instance()[0].get_area()
        conductor, container = find_asset_and_container(area, cond_id)

        split_conductor(conductor, location_to_split, mode, container)

    if message['cmd'] == 'get_port_profile_info':
        port_id = message['port_id']

        asset_id = mapping[port_id]['asset_id'] # {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}
        if asset_id:
            asset = find_asset(es_edit.get_instance()[0].get_area(), asset_id)
            ports = asset.get_port()
            for p in ports:
                if p.get_id() == port_id:
                    profile = p.get_profile()
                    if profile:
                        profile_info = generate_profile_info(profile)
                        emit('port_profile_info', profile_info)
                    else:
                        emit('port_profile_info', {'class': 'SingleValue', 'value': 1, 'type': 'ENERGY_IN_TJ'})

    if message['cmd'] == 'add_profile_to_port':
        port_id = message['port_id']
        multiplier_or_value = message['multiplier']
        profile_class = message['profile_class']
        profile_type = message['profile_type']

        # print(port_id)
        # print(multiplier_or_value)
        # print(profile_class)

        module = importlib.import_module('model.esdl_sup')

        # TODO: Am I nuts? Why use getattr here?
        if profile_class == 'SingleValue':
            esdl_profile_class = getattr(module, 'SingleValue')
            esdl_profile = esdl_profile_class()
            esdl_profile.set_value(float(multiplier_or_value))
            esdl_profile.set_profileType(profile_type)
        elif profile_class == 'DateTimeProfile':
            esdl_profile_class = getattr(module, 'DateTimeProfile')
            esdl_profile = esdl_profile_class()
            # TODO: Determine how to deal with DateTimeProfiles in the UI
        else:
            # Assume all other options are InfluxDBProfiles
            profiles = esdl_config.esdl_config['influxdb_profile_data']
            for p in profiles:
                if p['profile_uiname'] == profile_class:
                    esdl_profile_class = getattr(module, 'InfluxDBProfile')
                    esdl_profile = esdl_profile_class()
                    esdl_profile.set_multiplier(float(multiplier_or_value))
                    esdl_profile.set_profileType(profile_type)

                    esdl_profile.set_measurement(p['measurement'])
                    esdl_profile.set_field(p['field'])

                    esdl_profile.set_host(esdl_config.esdl_config['profile_database']['host'])
                    esdl_profile.set_port(int(esdl_config.esdl_config['profile_database']['port']))
                    esdl_profile.set_database(esdl_config.esdl_config['profile_database']['database'])
                    esdl_profile.set_filters(esdl_config.esdl_config['profile_database']['filters'])


        esdl_profile.set_id(str(uuid.uuid4()))

        asset_id = mapping[port_id]['asset_id'] # {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}
        if asset_id:
            asset = find_asset(es_edit.get_instance()[0].get_area(), asset_id)
            ports = asset.get_port()
            for p in ports:
                if p.get_id() == port_id:
                    p.set_profile(esdl_profile)

    if message['cmd'] == 'set_carrier':
        asset_id = message['asset_id']
        carrier_id = message['carrier_id']
        area = es_edit.get_instance()[0].get_area()

        if asset_id:
            asset = find_asset(area, asset_id)
            num_ports = len(asset.get_port())
            if isinstance(asset, esdl.Transport) or num_ports == 1:
                set_carrier_for_connected_transport_assets(asset_id, carrier_id)
            else:
                send_alert("Error: Can only start setting carriers from transport assets or assets with only one port")

    if message['cmd'] == 'set_building_color_method':
        session["color_method"] = message['method']
        print(session["color_method"])

    session['es_edit'] = es_edit
    session['asset_dict'] = asset_dict


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
        carrier_list = []
        asset_dict = {}
        mapping = {}

        create_port_to_asset_mapping(area, mapping)
        session['port_to_asset_mapping'] = mapping
        process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)

        emit('clear_ui')
        emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
        emit('area_bld_list', area_bld_list)
        emit('add_connections', conn_list)
        emit('carrier_list', carrier_list)

        # create_ESDL_store_item(es_id, es_edit, title, description, email)
        emit('es_title', title)

        session['es_title'] = title
        session['es_edit'] = es_edit
        session['es_id'] = es_id
        session['es_descr'] = description
        session['es_email'] = email
        session['es_start'] = 'new'
        session['conn_list'] = conn_list
        session['carrier_list'] = carrier_list
        session['asset_dict'] = asset_dict

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
        carrier_list = []
        mapping = {}

        instance = es_edit.get_instance()
        area = instance[0].get_area()
        asset_dict = create_asset_dict(area)

        create_port_to_asset_mapping(area, mapping)
        session['port_to_asset_mapping'] = mapping
        process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)

        emit('clear_ui')
        emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
        emit('area_bld_list', area_bld_list)
        emit('add_connections', conn_list)
        emit('es_title', es_title)
        emit('carrier_list', carrier_list)

        session['es_id'] = es_id
        session['es_edit'] = es_edit
        session['es_title'] = es_title
        session['es_start'] = 'load_store'
        session['conn_list'] = conn_list
        session['carrier_list'] = carrier_list
        session['asset_dict'] = asset_dict

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
#  Load ESDL file
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
    mapping = {}
    carrier_list = get_carrier_list(es_edit)

    instance = es_edit.get_instance()
    area = instance[0].get_area()
    area_id = area.get_id()
    area_scope = area.get_scope()
    asset_dict = create_asset_dict(area)

    emit('clear_ui')
    find_boundaries_in_ESDL(area)

    create_port_to_asset_mapping(area, mapping)
    session['port_to_asset_mapping'] = mapping
    process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)

    emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
    emit('area_bld_list', area_bld_list)
    emit('add_connections', conn_list)
    emit('es_title', es_title)
    emit('carrier_list', carrier_list)

    session['es_id'] = es_id
    session['es_edit'] = es_edit
    session['es_title'] = es_title
    session['es_start'] = 'load_file'
    session['conn_list'] = conn_list
    session['carrier_list'] = carrier_list
    session['asset_dict'] = asset_dict

# ---------------------------------------------------------------------------------------------------------------------
#  Update ESDL coordinates on movement of assets in browser
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('update-coord', namespace='/esdl')
def update_coordinates(message):
    print ('received: ' + str(message['id']) + ':' + str(message['lat']) + ',' + str(message['lng']) + ' - ' + str(message['asspot']))

    es_edit = session['es_edit']
    instance = es_edit.get_instance()
    area = instance[0].get_area()
    obj_id = message['id']

    if message['asspot'] == 'asset':
        asset = find_asset(area, obj_id)

        if asset:
            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

        # Update locations of connections on moving assets
        update_asset_connection_locations(obj_id, message['lat'], message['lng'])
    else:
        potential = find_potential(area, obj_id)
        if potential:
            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            potential.set_geometry_with_type(point)

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
    print('get_boundary_info:')
    print(info)
    identifier = info["identifier"]
    scope = info["scope"]
    subscope = info["subscope"]
    initialize_ES = info["initialize_ES"]
    add_boundary_to_ESDL = info["add_boundary_to_ESDL"]

    # TODO: Check if valid scopes were given

    es_edit = session['es_edit']
    instance = es_edit.get_instance()
    area = instance[0].get_area()

    if initialize_ES:
        # change ID, name and scope of ES
        area.set_id(identifier)
        area.set_scope(str.upper(scope))
        if add_boundary_to_ESDL:
            # returns boundary: { type: '', boundary: [[[[ ... ]]]] } (multipolygon in RD)
            boundary = get_boundary_from_service(str.upper(scope), identifier)
            geometry = create_geometry_from_geom(boundary)
            area.set_geometry(geometry)

            # boundary = get_boundary_from_service(area_scope, area_id)
            # if boundary:
            #    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})

    boundaries = get_subboundaries_from_service(scope, subscope, identifier)
    # result (boundaries) is an ARRAY of:
    # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
    # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

    for boundary in boundaries:
        geom = None
        try:
            geom = json.loads(boundary["geom"])
        except:
            print('exception: probably unable to parse JSON from GEIS boundary service')

        if geom:
            # print('boundary["geom"]: ')
            # print(boundary["geom"])
            # print(boundary)

            if initialize_ES:
                sub_area = esdl.Area()
                sub_area.set_id(boundary["code"])
                sub_area.set_scope(str.upper(subscope))

                if add_boundary_to_ESDL:
                    geometry = create_geometry_from_geom(geom)
                    sub_area.set_geometry(geometry)

                area.add_area(sub_area)

            # print({'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': json.loads(geom)})
            # boundary = create_boundary_from_contour(area_contour)
            # emit('area_boundary', {'crs': 'WGS84', 'boundary': boundary})

            emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': geom, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

    print('Ready prcessing boundary information')


# ---------------------------------------------------------------------------------------------------------------------
#  Connect from browser
#   - initialize energysystem information
#   - send info to browser
# ---------------------------------------------------------------------------------------------------------------------
def initialize_app():
    emit('log', {'data': 'Connected', 'count': 0})
    print('Client connected: ', request.sid)

    # TODO: Seems not to work: refresh in browser creates new session?
    if 'es_edit' in session:
        print ('Energysystem in memory - reloading client data')
        es_edit = session['es_edit']
        es_title = session['es_title']
        es_id = session['es_id']
        area = es_edit.instance[0].area
    else:
        print ('No energysystem in memory - generating empty energysystem')
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

    asset_list = []
    area_bld_list = []
    conn_list = []
    mapping = {}
    carrier_list = []
    asset_dict = {}

    create_port_to_asset_mapping(area, mapping)
    session['port_to_asset_mapping'] = mapping
    process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)

    emit('clear_ui')
    emit('es_title', es_title)
    emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
    emit('area_bld_list', area_bld_list)
    emit('add_connections', conn_list)
    emit('carrier_list', carrier_list)

    session['es_title'] = es_title
    session['es_edit'] = es_edit
    session['es_id'] = es_id
    session['conn_list'] = conn_list
    session['carrier_list'] = carrier_list
    session['asset_dict'] = asset_dict
    session['color_method'] = 'buildingyear'

@socketio.on('connect', namespace='/esdl')
def on_connect():
    print("Websocket connection established")
    emit('log', {'data': 'Connected', 'count': 0})
    emit('profile_info', esdl_config.esdl_config['influxdb_profile_data'])
    # emit('carrier_list', [{'NaturalGas': {'type': 'EnergyCarrier', 'id': 'NaturalGas', 'name': 'NaturalGas', 'energyContent': 38370000.0, 'emission': 1.788225, 'energyCarrierType': 'FOSSIL', 'stateOfMatter': 'GASEOUS'}}, {'Hydrogen': {'type': 'EnergyCarrier', 'id': 'Hydrogen', 'name': 'Hydrogen', 'energyContent': 120000000.0, 'emission': 0.0, 'energyCarrierType': 'RENEWABLE', 'stateOfMatter': 'GASEOUS'}}, {'HEATCOMM': {'type': 'HeatCommodity', 'id': 'HEATCOMM', 'name': 'HeatCommodity', 'supplyTemperature': 0.0, 'returnTemperature': None}}, {'ELECCOMM': {'type': 'ElectricityCommodity', 'id': 'ELECCOMM', 'name': 'ElectricityCommodity', 'voltage': None}}, {'Biomass': {'type': 'EnergyCarrier', 'id': 'Biomass', 'name': 'Biomass', 'energyContent': 15100000.0, 'emission': 1.65496, 'energyCarrierType': 'RENEWABLE', 'stateOfMatter': 'SOLID'}}])

    initialize_app()


# ---------------------------------------------------------------------------------------------------------------------
#  Disconnect
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect', namespace='/esdl')
def on_disconnect():
    print('Client disconnected: ', request.sid)


# ---------------------------------------------------------------------------------------------------------------------
#  Start application
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    parse_esdl_config()
    print("starting App")
    socketio.run(app, debug=False, host='0.0.0.0', port=8111)

