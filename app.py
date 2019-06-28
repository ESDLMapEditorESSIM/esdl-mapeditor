#!/usr/bin/env python
import os

if os.environ.get('GEIS'):
    import gevent.monkey
    gevent.monkey.patch_all()

from flask import Flask, render_template, session, request, send_from_directory, jsonify, abort
from flask_socketio import SocketIO, emit
from flask_session import Session
import requests
import urllib
import time
#from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import math
import copy
import json
import importlib
from datetime import datetime
import random
from RDWGSConverter import RDWGSConverter

from es_generic import *
from essim_validation import validate_ESSIM
from essim_config import essim_config
from essim_kpis import ESSIM_KPIs
from wms_layers import WMSLayers

# import numpy as np
# from scipy.spatial import Delaunay
# from shapely.geometry import Polygon, MultiPolygon, Point

from model import esdl_sup as esdl
import esdl_config
import settings

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

wms_layers = WMSLayers()

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
GEIS_CLOUD_HOSTNAME = 'geis.hesi.energy'
GEIS_CLOUD_IP = '10.30.2.1'
ESDL_STORE_PORT = '3003'
# store_url = 'http://' + GEIS_CLOUD_IP + ':' + ESDL_STORE_PORT + '/store/'
store_url = 'http://' + GEIS_CLOUD_HOSTNAME + '/store/'


def write_energysystem_to_file(filename, es):
    f = open(filename, 'w+', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='esdl:', name_='esdl:EnergySystem', namespacedef_=xml_namespace, pretty_print=True)
    f.close()


def create_ESDL_store_item(id, es, title, description, email):
    try:
        f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
        # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
                       pretty_print=True)
        f.close()

        with open('/tmp/temp.xmi', 'r') as esdl_file:
            esdlstr = esdl_file.read()
    except:
        send_alert('Error accessing temporary file system')
        return

    try:
        payload = {'id': id, 'title': title, 'description': description, 'email':email, 'esdl': esdlstr}
        requests.post(store_url, data=payload)
    except:
        send_alert('Error accessing ESDL store')


def load_ESDL_EnergySystem(id):
    url = store_url + 'esdl/' + id + '?format=xml'

    try:
        r = requests.get(url)
    except:
        send_alert('Error accessing ESDL store')
        return None

    esdlstr = r.text
    if esdlstr.startswith('<?xml'):
        # remove the <?xml encoding='' stuff, as the parseString doesn't like encoding in there
        esdlstr = esdlstr.split('\n', 1)[1]

    esdlstr = esdlstr.encode()
    try:
        es_load = esdl.parseString(esdlstr)
        return es_load
    except:
        send_alert('Error interpreting ESDL file from store')
        return None


def store_ESDL_EnergySystem(id, es):
    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
    # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
                   pretty_print=True)
    f.close()

    with open('/tmp/temp.xmi', 'r') as esdl_file:
        esdlstr = esdl_file.read()

    payload = {'id': id, 'esdl': esdlstr}
    try:
        requests.put(store_url + id, data=payload)
    except:
        send_alert('Error saving ESDL file to store')


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
        # url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(scope)] + '/' + id
        url = 'http://' + GEIS_CLOUD_HOSTNAME + '/boundaries/' + boundary_service_mapping[str.upper(scope)] + '/' + id
        r = requests.get(url)
        reply = json.loads(r.text)

        print(reply)
        geom = reply['geom']

        # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
        # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
        # 'tCode': 'GM0003', 'tName': 'Appingedam'}

        return geom
    except:
        print('ERROR: GEIS boundary service not reachable!')
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
        return {}


# ---------------------------------------------------------------------------------------------------------------------
#  ESSIM interfacing
# ---------------------------------------------------------------------------------------------------------------------
def start_ESSIM():
    es = session['es_edit']
    es_id = session['es_id']
    es_simid = None
    # session['es_simid'] = es_simid

    f = open('/tmp/temp.xmi', 'w', encoding='UTF-8')
    es.export(f, 0, namespaceprefix_='', name_='esdl:EnergySystem', namespacedef_=xml_namespace,
              pretty_print=True)
    f.close()

    with open('/tmp/temp.xmi', 'r') as esdl_file:
        esdlstr = esdl_file.read()

    ESSIM_config = esdl_config.esdl_config['ESSIM']

    url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path']
    # print('ESSIM url: ', url)

    payload = {
        'user': ESSIM_config['user'],
        'scenarioID': es_id,
        'simulationDescription': '',
        'startDate': ESSIM_config['start_datetime'],
        'endDate': ESSIM_config['end_datetime'],
        'influxURL': ESSIM_config['influxURL'],
        'grafanaURL': ESSIM_config['grafanaURL'],
        'esdlContents': urllib.parse.quote(esdlstr)
    }

    headers = {
        'Content-Type': "application/json",
        'Accept': "application/json",
        'User-Agent': "ESDL Mapeditor/0.1"
        # 'Cache-Control': "no-cache",
        # 'Host': ESSIM_config['ESSIM_host'],
        # 'accept-encoding': "gzip, deflate",
        # 'Connection': "keep-alive",
        # 'cache-control': "no-cache"
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        #print(r)
        #print(r.content)
        if r.status_code == 201:
            result = json.loads(r.text)
            #print(result)
            id = result['id']
            session['es_simid'] = id
            print(id)
            # emit('', {})
        else:
            send_alert('Error starting ESSIM simulation - response '+ str(r.status_code) + ' with reason: ' + str(r.reason))
            print(r)
            print(r.content)
            # emit('', {})
            return 0
    except Exception as e:
        print('Exception: ')
        print(e)
        send_alert('Error accessing ESSIM API at starting')
        return 0

    return 1


# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
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
        if color_method == 'building year':
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
        elif color_method == 'building type':
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

    print('Finding area boundaries for', area_scope, area_id)
    boundary = None

    if area_geometry:
        print('Geometry specified in the ESDL')
        if isinstance(area_geometry, esdl.Polygon):
            boundary = create_boundary_from_geometry(area_geometry)
            print('emiting Polygon WGS84')
            emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})
        if isinstance(area_geometry, esdl.MultiPolygon):
            boundary = create_boundary_from_geometry(area_geometry)
            print('emiting MultiPolygon WGS84')
            emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

        # check to see if ESDL file contains asset locations; if not generate locations
        # TODO: following call does nothing now
        # TODO: Check if this can be called recursively
        update_asset_geometries2(this_area, boundary)
    else:
        # simple hack to check if ID is not a UUID and area_scope is defined --> then query GEIS for boundary
        if area_id and area_scope:
            if len(area_id) < 20:
                print('Finding boundary from GEIS service')
                boundary = get_boundary_from_service(area_scope, area_id)
                if boundary:
                    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

    if boundary:
        update_asset_geometries3(this_area, boundary)

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

                    emit('area_boundary', {'info-type': 'P-WGS84', 'crs': 'WGS84', 'boundary': boundary,
                                           'color': building_color, 'name': name, 'boundary_type': 'building'})
        else: # No AbstractBuilding
            asset_geometry = asset.get_geometry()
            name = asset.get_name()
            if asset_geometry:
                if isinstance(asset_geometry, esdl.WKT):
                        emit('area_boundary', {'info-type': 'WKT', 'boundary': asset_geometry.get_value(),
                                               'color': 'grey', 'name': name, 'boundary_type': 'asset'})

    potentials = this_area.get_potential()
    for potential in potentials:
        potential_geometry = potential.get_geometry()
        potential_name = potential.get_name()
        if potential_geometry:
            if isinstance(potential_geometry, esdl.WKT):
                emit('pot_boundary', {'info-type': 'WKT', 'boundary': potential_geometry.get_value(), 'color': 'grey',
                                      'name': potential_name, 'boundary_type': 'potential'})

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
app.config['SECRET_KEY'] = b'\xc3g\x19\xbf\x8e\xa0\xe7\xc8\x9a/\xae%\x04g\xbe\x9f\xaex\xb5\x8c\x81f\xaf`' #os.urandom(24)   #'secret!'
app.config['SESSION_COOKIE_NAME'] = 'ESDL-WebEditor-session'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24 # 1 day in seconds
socketio = SocketIO(app, async_mode=async_mode, manage_session=False, path='/socket.io')
# fix sessions with socket.io. see: https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
Session(app)
# socketio = SocketIO(app, async_mode=async_mode)


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
    # print('in index()')
    return render_template('index.html', async_mode=socketio.async_mode, dir_settings=settings.dir_settings)


@app.route('/<path:path>')
def serve_static(path):
    # print('in serve_static(): '+ path)
    return send_from_directory('static', path)


@app.route('/simulation_progress')
def get_simulation_progress():
    if 'es_simid' in session:
        es_simid = session['es_simid']
        ESSIM_config = esdl_config.esdl_config['ESSIM']
        url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/' + es_simid

        try:
            r = requests.get(url + '/status')
            if r.status_code == 200:
                result = r.text
                print(result)
                # emit('update_simulation_progress', {'percentage': result, 'url': ''})
                if float(result) >= 1:
                    r = requests.get(url)
                    if r.status_code == 200:
                        del session['es_simid']         # simulation ready
                        result = json.loads(r.text)
                        # print(result)
                        dashboardURL = result['dashboardURL']
                        print(dashboardURL)
                        session['simulationRun'] = es_simid
                        # emit('update_simulation_progress', {'percentage': '1', 'url': dashboardURL})
                        return (jsonify({'percentage': '1', 'url': dashboardURL, 'simulationRun': es_simid})), 200
                    else:
                        send_alert('Error in getting the ESSIM dashboard URL')
                        abort(500, 'Error in getting the ESSIM dashboard URL')
                else:
                    return (jsonify({'percentage': result, 'url': '', 'simulationRun': es_simid})), 200
            else:
                print('code: ', r.status_code)
                send_alert('Error in getting the ESSIM progress status')
                abort(500, 'Error in getting the ESSIM progress status')
        except Exception as e:
            print('Exception: ')
            print(e)
            send_alert('Error accessing ESSIM API')
            abort(500, 'Error accessing ESSIM API')
    else:
        abort(500, 'Simulation not running')


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


def _remove_port_references(port):
    mapping = session['port_to_asset_mapping']
    asset_dict = session['asset_dict']

    p_id = port.get_id()
    connected_to = port.get_connectedTo()
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


def _remove_object_from_building(building, object_id):
    for ass in building.get_asset():
        if ass.get_id() == object_id:
            for p in ass.get_port():
                _remove_port_references(p)
            building.asset.remove(ass)
            print('Asset with id ' + object_id+ ' removed from building with id: ', + building.get_id())


def _recursively_remove_object_from_area(area, object_id):
    for ass in area.get_asset():
        if ass.get_id() == object_id:
            for p in ass.get_port():
                _remove_port_references(p)
            area.asset.remove(ass)
            print('Asset with id ' + object_id + ' removed from area with id: ' + area.get_id())
        if isinstance(ass, esdl.AggregatedBuilding) or isinstance(ass, esdl.Building):
            _remove_object_from_building(ass, object_id)
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
    if isinstance(asset, esdl.Producer): return 'Producer'
    if isinstance(asset, esdl.Consumer): return 'Consumer'
    if isinstance(asset, esdl.Storage): return 'Storage'
    if isinstance(asset, esdl.Transport): return 'Transport'
    if isinstance(asset, esdl.Conversion): return 'Conversion'
    return 'none'


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


def calc_center(coords):
    min_x = float('inf')
    min_y = float('inf')
    max_x = 0
    max_y = 0

    for c in coords:
        if c[0] < min_x: min_x = c[0]
        if c[1] < min_y: min_y = c[1]
        if c[0] > max_x: max_x = c[0]
        if c[1] > max_y: max_y = c[1]

    return [(min_x + max_x) / 2, (min_y + max_y) / 2]


def update_asset_geometries3(area, boundary):
    coords = boundary['coordinates']
    type = boundary['type']
    print(coords)
    print(type)

    if type == 'Polygon':
        outer_polygon = coords[0]       # Take exterior polygon
    elif type == 'MultiPolygon':
        outer_polygon = coords[0][0]    # Assume first polygon is most relevant and then take exterior polygon
    else:
        send_alert('Non supported polygon')

    center = calc_center(outer_polygon)
    print(center)

    for asset in area.get_asset():
        if isinstance(asset, esdl.AbstractBuilding):
            for asset2 in asset.get_asset():
                geom = asset2.get_geometry()

                if not geom:
                    geom = esdl.Point()
                    x = center[0] + (-0.5 + random.random()) * 1000
                    y = center[1] + (-0.5 + random.random()) * 1000
                    if x > 180 or y > 180:  # Assume RD
                        rdwgs = RDWGSConverter()
                        wgs = rdwgs.fromRdToWgs([x, y])
                        geom.set_lat(wgs[0])
                        geom.set_lon(wgs[1])
                    else:
                        geom.set_lat(y)  # TODO: check order of lattitude and longitude
                        geom.set_lon(x)
                    asset2.set_geometry_with_type(geom)
        else:
            geom = asset.get_geometry()

            if not geom:
                geom = esdl.Point()
                x = center[0]+(-0.5+random.random())*1000
                y = center[1]+(-0.5+random.random())*1000
                if x > 180 or y > 180:  # Assume RD
                    rdwgs = RDWGSConverter()
                    wgs = rdwgs.fromRdToWgs([x, y])
                    geom.set_lat(wgs[0])
                    geom.set_lon(wgs[1])
                else:
                    geom.set_lat(y)     # TODO: check order of lattitude and longitude
                    geom.set_lon(x)
                asset.set_geometry_with_type(geom)


def generate_profile_info(profile):
    profile_class = type(profile).__name__
    profile_type = profile.get_profileType()
    profile_name = profile.get_name()
    if profile_class == 'SingleValue':
        value = profile.get_value()
        profile_info = {'class': 'SingleValue', 'value': value, 'type': profile_type}
    if profile_class == 'InfluxDBProfile':
        multiplier = profile.get_multiplier()
        measurement = profile.get_measurement()
        field = profile.get_field()
        profile_name = 'UNKNOWN'
        for p in esdl_config.esdl_config['influxdb_profile_data']:
            if p['measurement'] == measurement and p['field'] == field:
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
    print('Updating locations')
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
#  Get connections information for an asset
# ---------------------------------------------------------------------------------------------------------------------
def get_connected_to_info(asset):
    mapping = session['port_to_asset_mapping']
    asset_dict = session['asset_dict']
    print(asset_dict)
    result = []

    ports = asset.get_port()
    for p in ports:
        pname = p.get_name()
        pid = p.get_id()
        ptype = type(p).__name__

        ct_list = []
        conn_to = p.get_connectedTo()
        if conn_to:
            conn_to_list = conn_to.split(' ')
            for conn_port_id in conn_to_list:
                conn_asset_id = mapping[conn_port_id]['asset_id']
                conn_asset = asset_dict[conn_asset_id]
                ct_list.append({'pid': conn_port_id, 'aid': conn_asset.get_id(), 'atype': type(conn_asset).__name__, 'aname': conn_asset.get_name()})

        result.append({'pid': pid, 'ptype': ptype, 'pname': pname, 'ct_list': ct_list})

    print(result)

    return result


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
    conn_list = session["conn_list"]

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
                conn_list.append(
                    {'from-port-id': p.get_id(), 'from-asset-id': asset.get_id(),
                     'from-asset-coord': [asset_geom.get_lat(),asset_geom.get_lon()],
                     'to-port-id': cond_port.get_id(), 'to-asset-id': conductor.get_id(),
                     'to-asset-coord': [first_point.get_lat(),first_point.get_lon()]})

    else:
        # connect asset with last_point of conductor

        cond_port = conductor.get_port()[1]
        for p in asset.get_port():
            if not type(p).__name__ == type(cond_port).__name__:
                print('connect asset with last_point')
                connect_ports(p, cond_port)
                emit('add_new_conn',
                     [[asset_geom.get_lat(), asset_geom.get_lon()], [last_point.get_lat(), last_point.get_lon()]])
                conn_list.append(
                    {'from-port-id': p.get_id(), 'from-asset-id': asset.get_id(),
                     'from-asset-coord': [asset_geom.get_lat(), asset_geom.get_lon()],
                     'to-port-id': cond_port.get_id(), 'to-asset-id': conductor.get_id(),
                     'to-asset-coord': [last_point.get_lat(), last_point.get_lon()]})

    session["conn_list"] = conn_list


def connect_asset_with_asset(asset1, asset2):
    conn_list = session["conn_list"]

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
            # find InPort on other asset
            for p in ports2:
                if isinstance(p, esdl.InPort):
                    # connect p and ports1[0]
                    print('connect p and ports1[0]')
                    connect_ports(p, ports1[0])
                    p1 = ports1[0]
                    p2 = p
                    emit('add_new_conn',
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No InPort found on asset2')
                return
        else:
            # find OutPort on other asset
            for p in ports2:
                if isinstance(p, esdl.OutPort):
                    # connect p and ports1[0]
                    print('connect p and ports1[0]')
                    connect_ports(p, ports1[0])
                    p1 = ports1[0]
                    p2 = p
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
            # find InPort on other asset
            for p in ports1:
                if isinstance(p, esdl.InPort):
                    # connect p and ports2[0]
                    print('connect p and ports2[0]')
                    connect_ports(p, ports2[0])
                    p1 = p
                    p2 = ports2[0]
                    emit('add_new_conn',
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No InPort found on asset1')
                return
        else:
            # find OutPort on other asset
            for p in ports1:
                if isinstance(p, esdl.OutPort):
                    # connect p and ports2[0]
                    print('connect p and ports2[0]')
                    connect_ports(p, ports2[0])
                    p1 = p
                    p2 = ports2[0]
                    emit('add_new_conn',
                         [[asset1_geom.get_lat(), asset1_geom.get_lon()],
                          [asset2_geom.get_lat(), asset2_geom.get_lon()]])
                    found = 1
            if not found:
                send_alert('UNSUPPORTED - No OutPort found in asset1')
                return
    else:
        send_alert('UNSUPPORTED - Cannot determine what ports to connect')
        return

    if found:
        conn_list.append(
            {'from-port-id': p1.get_id(), 'from-asset-id': asset1.get_id(),
             'from-asset-coord': [asset1_geom.get_lat(), asset1_geom.get_lon()],
             'to-port-id': p2.get_id(), 'to-asset-id': asset2.get_id(),
             'to-asset-coord': [asset2_geom.get_lat(), asset2_geom.get_lon()]})

    session["conn_list"] = conn_list


def connect_conductor_with_conductor(conductor1, conductor2):
    conn_list = session["conn_list"]

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
        conn_list.append(
            {'from-port-id': conn1.get_id(), 'from-asset-id': conductor1.get_id(),
             'from-asset-coord': [conn_pnt1.get_lat(), conn_pnt1.get_lon()],
             'to-port-id': conn2.get_id(), 'to-asset-id': conductor2.get_id(),
             'to-asset-coord': [conn_pnt2.get_lat(), conn_pnt2.get_lon()]})

        session["conn_list"] = conn_list
    else:
        send_alert('UNSUPPORTED - Cannot connect two ports of same type')


def get_asset_attributes(asset):
    asset_attrs = copy.deepcopy(vars(asset))
    # method_list = [func for func in dir(asset) if callable(getattr(asset, func)) and func.startswith("set_")]

    # TODO: check which attributes must be filtered (bacause they cannot be easily edited)
    if 'area' in asset_attrs:
        asset_attrs.pop('area', None)
    if 'containingBuilding' in asset_attrs:
        asset_attrs.pop('containingBuilding', None)
    if 'controlStrategy' in asset_attrs:
        asset_attrs.pop('controlStrategy', None)
    if 'costInformation' in asset_attrs:
        asset_attrs.pop('costInformation', None)
    if 'dataSource' in asset_attrs:
        asset_attrs.pop('dataSource', None)
    if 'extensiontype_' in asset_attrs:
        asset_attrs.pop('extensiontype_', None)
    if 'geometry' in asset_attrs:
        asset_attrs.pop('geometry', None)
    if 'isOwnedBy' in asset_attrs:
        asset_attrs.pop('isOwnedBy', None)
    if 'KPIs' in asset_attrs:
        asset_attrs.pop('KPIs', None)
    if 'original_tagname_' in asset_attrs:
        asset_attrs.pop('original_tagname_', None)
    if 'parent_object_' in asset_attrs:
        asset_attrs.pop('parent_object_', None)
    if 'port' in asset_attrs:
        asset_attrs.pop('port', None)
    if 'profile' in asset_attrs:
        asset_attrs.pop('profile', None)
    if 'sector' in asset_attrs:
        asset_attrs.pop('sector', None)

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
        new_cond1.set_name(conductor.get_name() + '_a')
        new_cond2.set_name(conductor.get_name() + '_b')

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
        # create port list
        port_list = []
        for p in new_cond1.get_port():
            port_list.append(
                {'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': p.get_connectedTo()})
        esdl_assets_to_be_added.append(['line', 'asset', new_cond1.get_name(), new_cond1.get_id(), type(new_cond1).__name__, coords, port_list])
        coords = []
        for point in line2.get_point():
            coords.append([point.get_lat(), point.get_lon()])
        port_list = []
        for p in new_cond2.get_port():
            port_list.append(
                {'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': p.get_connectedTo()})
        esdl_assets_to_be_added.append(['line', 'asset', new_cond2.get_name(), new_cond2.get_id(), type(new_cond2).__name__, coords, port_list])

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
            joint.set_name('Joint_'+joint_id[:4])
            inp = esdl.InPort(name='In')
            joint_inp_id = str(uuid.uuid4())
            inp.set_id(joint_inp_id)
            outp = esdl.OutPort(name='Out')
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
        print('assets to be added: {}'.format(esdl_assets_to_be_added))
        emit('add_esdl_objects', {'list': esdl_assets_to_be_added, 'zoom': False})
        emit('clear_connections')
        emit('add_connections', conn_list)

        session['port_to_asset_mapping'] = mapping
        session['conn_list'] = conn_list
        session['asset_dict'] = asset_dict
    else:
        send_alert('UNSUPPORTED: Conductor is not of type esdl.Line!')


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
            if boundary:
                geometry = create_geometry_from_geom(boundary)
                area.set_geometry(geometry)

            # boundary = get_boundary_from_service(area_scope, area_id)
            # if boundary:
            #    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})

    boundaries = get_subboundaries_from_service(scope, subscope, identifier)
    # result (boundaries) is an ARRAY of:
    # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
    # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

    if not boundaries:
        send_alert('Error processing boundary information or no boundary information returned')

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

    print('Ready processing boundary information')

    session['es_edit'] = es_edit


# ---------------------------------------------------------------------------------------------------------------------
#  Control Strategies
# ---------------------------------------------------------------------------------------------------------------------
def get_control_strategies(es):
    strategies = []
    services = es.get_services()
    if services:
        services_list = services.get_service()
        for service in services_list:
            if isinstance(service, esdl.ControlStrategy):
                strategies.append(service)
    return strategies


def get_control_strategy_for_asset(asset_id):
    es = session['es_edit']
    asset_dict = session['asset_dict']

    strategies = get_control_strategies(es)

    for strategy in strategies:
        cs_aid = strategy.get_energyAsset()
        if cs_aid == asset_id:
            return strategy

    return None


def add_control_strategy_for_asset(asset_id, cs):
    es = session['es_edit']

    services = es.get_services()
    if not services:
        services = esdl.Services()
        es.set_services(services)

    services_list = services.get_service()
    for service in services_list:
        if isinstance(service, esdl.ControlStrategy):
            if service.get_energyAsset() == asset_id:
                services_list.remove(service)

    services.add_service_with_type(cs)


def add_drivenby_control_strategy_for_asset(asset_id, control_strategy, port_id):
    asset_dict = session['asset_dict']

    module = importlib.import_module('model.esdl_sup')
    class_ = getattr(module, control_strategy)
    cs = class_()

    asset = asset_dict[asset_id]
    asset_name = asset.get_name()
    if not asset_name:
        asset_name = 'unknown'

    cs.set_id(str(uuid.uuid4()))
    cs.set_name(control_strategy + ' for ' + asset_name)
    cs.set_energyAsset(asset_id)

    if control_strategy == 'DrivenByDemand':
        cs.set_outPort(port_id)
    if control_strategy == 'DrivenBySupply':
        cs.set_inPort(port_id)

    add_control_strategy_for_asset(asset_id, cs)


def add_storage_control_strategy_for_asset(asset_id, mcc, mdc):
    asset_dict = session['asset_dict']

    cs = esdl.StorageStrategy()

    asset = asset_dict[asset_id]
    asset_name = asset.get_name()
    if not asset_name:
        asset_name = 'unknown'

    cs.set_id(str(uuid.uuid4()))
    cs.set_name('StorageStrategy for ' + asset_name)
    cs.set_energyAsset(asset_id)

    mcc_sv = esdl.SingleValue()
    mcc_sv.set_id(str(uuid.uuid4()))
    mcc_sv.set_name('marginalChargeCosts for ' + asset_name)
    mcc_sv.set_value(str2float(mcc))
    cs.set_marginalChargeCosts(mcc_sv)

    mdc_sv = esdl.SingleValue()
    mdc_sv.set_id(str(uuid.uuid4()))
    mdc_sv.set_name('marginalChargeCosts for ' + asset_name)
    mdc_sv.set_value(str2float(mdc))
    cs.set_marginalDischargeCosts(mdc_sv)

    add_control_strategy_for_asset(asset_id, cs)


def get_storage_marginal_costs(asset_id):
    asset_dict = session['asset_dict']
    asset = asset_dict[asset_id]

    es = session['es_edit']

    services = es.get_services()
    if services:
        services_list = services.get_service()
        for service in services_list:
            if isinstance(service, esdl.StorageStrategy):
                if service.get_energyAsset() == asset_id:
                    mcc_sv = service.get_marginalChargeCosts()
                    mdc_sv = service.get_marginalDischargeCosts()
                    if mcc_sv:
                        mcc = mcc_sv.get_value()
                    else:
                        mcc = 0
                    if mdc_sv:
                        mdc = mdc_sv.get_value()
                    else:
                        mdc = 0
                    return mcc, mdc

    return 0, 0


def remove_control_strategy_for_asset(asset_id):
    es = session['es_edit']

    services_collection = es.get_services()
    if services_collection:
        services = services_collection.get_service()
        for service in services:
            if isinstance(service, esdl.ControlStrategy):
                if service.get_energyAsset() == asset_id:
                    services.remove(service)


# ---------------------------------------------------------------------------------------------------------------------
#  Marginal Costs
# ---------------------------------------------------------------------------------------------------------------------
def set_marginal_costs_for_asset(asset_id, marginal_costs):
    asset_dict = session['asset_dict']
    asset = asset_dict[asset_id]
    asset_name = asset.get_name()
    if not asset_name:
        asset_name = asset.get_id()

    ci = asset.get_costInformation()
    if not ci:
        ci = esdl.CostInformation()
        asset.set_costInformation(ci)

    mc = ci.get_marginalCosts()
    if not mc:
        mc = esdl.SingleValue()
        mc.set_id(str(uuid.uuid4()))
        mc.set_name(asset_name+'-MarginalCosts')

    mc.set_value(marginal_costs)
    ci.set_marginalCosts(mc)


def get_marginal_costs_for_asset(asset_id):
    asset_dict = session['asset_dict']
    asset = asset_dict[asset_id]

    ci = asset.get_costInformation()
    if ci:
        mc = ci.get_marginalCosts()
        if mc:
            return mc.get_value()

    return None


def str2float(string):
    try:
        f = float(string)
        return f
    except:
        return 0.0

def str2int(string):
    try:
        i = int(string)
        return i
    except:
        return 0

# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('command', namespace='/esdl')
def process_command(message):
    print ('received: ' + message['cmd'])
    print (message)
    print (session)
    mapping = session['port_to_asset_mapping']
    asset_dict = session['asset_dict']
    es_edit = session['es_edit']
    # test to see if this should be moved down:
    #  session.modified = True
    # print (session['es_edit'].get_instance()[0].get_area().get_name())

    if message['cmd'] == 'add_asset':
        area_bld_id = message['area_bld_id']
        asset_id = message['asset_id']
        assettype = message['asset']
        asset_name = message['asset_name']

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an OutPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['GenericProducer', 'GeothermalSource', 'PVInstallation', 'PVParc', 'WindTurbine']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            outp = esdl.OutPort()
            port_id = str(str(uuid.uuid4()))
            outp.set_id(port_id)
            outp.set_name('Out')
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['Battery', 'ElectricityDemand', 'EVChargingStation', 'GenericConsumer', 'HeatingDemand',
                         'MobilityDemand', 'UTES']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            port_id = str(str(uuid.uuid4()))
            inp.set_id(port_id)
            inp.set_name('In')
            asset.add_port_with_type(inp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[port_id] = {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}

        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort and an OutPort
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['EConnection', 'ElectricityNetwork', 'Electrolyzer', 'GConnection', 'GasHeater',
                         'GasNetwork', 'GenericConversion', 'HeatNetwork', 'HeatPump', 'Joint', 'Transformer', 'PowerPlant']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            in_port_id = str(uuid.uuid4())
            inp.set_id(in_port_id)
            inp.set_name('In')
            asset.add_port_with_type(inp)
            outp = esdl.OutPort()
            out_port_id = str(uuid.uuid4())
            outp.set_id(out_port_id)
            outp.set_name('Out')
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[in_port_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}
            mapping[out_port_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}
        # -------------------------------------------------------------------------------------------------------------
        #  Add assets with a point location and an InPort and two OutPorts
        # -------------------------------------------------------------------------------------------------------------
        if assettype in ['CHP', 'FuelCell']:
            module = importlib.import_module('model.esdl_sup')
            class_ = getattr(module, assettype)
            asset = class_()

            inp = esdl.InPort()
            in_port_id = str(uuid.uuid4())
            inp.set_id(in_port_id)
            inp.set_name('In')
            asset.add_port_with_type(inp)
            outp = esdl.OutPort()
            out_eport_id = str(uuid.uuid4())
            outp.set_id(out_eport_id)
            outp.set_name('E Out')
            asset.add_port_with_type(outp)
            outp = esdl.OutPort()
            out_hport_id = str(uuid.uuid4())
            outp.set_id(out_hport_id)
            outp.set_name('H Out')
            asset.add_port_with_type(outp)

            point = esdl.Point()
            point.set_lon(message['lng'])
            point.set_lat(message['lat'])
            asset.set_geometry_with_type(point)

            mapping[in_port_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}
            mapping[out_eport_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}
            mapping[out_hport_id] = {"asset_id": asset_id, "coord": (message['lat'], message['lng'])}

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
            inp.set_name('In')
            outp = esdl.OutPort()
            outp_id = str(uuid.uuid4())
            outp.set_id(outp_id)
            outp.set_name('Out')
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
        asset.set_name(asset_name)

        if not add_asset_to_area(es_edit, asset, area_bld_id):
            add_asset_to_building(es_edit, asset, area_bld_id)

        # TODO: check / solve cable as Point issue?cmd
        # if assettype not in ['ElectricityCable', 'Pipe']:
        port_list = []
        asset_to_be_added_list = []
        ports = asset.get_port()
        for p in ports:
            port_list.append(
                {'name': p.get_name(), 'id': p.get_id(), 'type': type(p).__name__, 'conn_to': p.get_connectedTo()})

        if assettype not in ['ElectricityCable', 'Pipe']:
            capability_type = get_asset_capability_type(asset)
            asset_to_be_added_list.append(['point', 'asset', asset.get_name(), asset.get_id(), type(asset).__name__, message['lat'], message['lng'], port_list, capability_type])
        else:
            coords = []
            i = 0
            prev_lat = 0
            prev_lng = 0
            while i < len(polyline_data):
                coord = polyline_data[i]

                # Don't understand why, but sometimes coordinates come in twice
                if prev_lat != coord['lat'] and prev_lng != coord['lng']:
                    coords.append([coord['lat'] ,coord['lng']])

                    prev_lat = coord['lat']
                    prev_lng = coord['lng']
                i += 1

            asset_to_be_added_list.append(['line', 'asset', asset.get_name(), asset.get_id(), type(asset).__name__, coords, port_list])

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

    if message['cmd'] == 'connect_ports':
        port1_id = message['port1id']
        port2_id = message['port2id']

        asset1_id = mapping[port1_id]['asset_id']
        asset2_id = mapping[port2_id]['asset_id']
        asset1_port_location = mapping[port1_id]['coord']
        asset2_port_location = mapping[port2_id]['coord']

        asset1 = asset_dict[asset1_id]
        asset2 = asset_dict[asset2_id]

        port1 = None
        port2 = None
        for p in asset1.get_port():
            if p.get_id() == port1_id:
                port1 = p

        for p in asset2.get_port():
            if p.get_id() == port2_id:
                port2 = p

        if port1 and port2:
            # add type check on ports
            if type(port1).__name__ == type(port2).__name__:
                send_alert('Cannot connect ports of the same type. One should be an InPort and one should be an OutPort')
            else:
                connect_ports(port1, port2)

                emit('add_new_conn',
                     [[asset1_port_location[0], asset1_port_location[1]], [asset2_port_location[0], asset2_port_location[1]]])

                conn_list = session["conn_list"]
                conn_list.append({'from-port-id': port1_id, 'from-asset-id': asset1_id,
                                  'from-asset-coord': [asset1_port_location[0], asset1_port_location[1]],
                                  'to-port-id': port2_id, 'to-asset-id': asset2_id,
                                  'to-asset-coord': [asset2_port_location[0], asset2_port_location[1]]})
                session["conn_list"] = conn_list
        else:
            send_alert('Serious error connecting ports')

    if message['cmd'] == 'get_object_info':
        object_id = message['id']
        asspot = message['asspot']
        area = es_edit.get_instance()[0].get_area()

        if asspot == 'asset':
            asset = find_asset(area, object_id)
            print('Get info for asset ' + asset.get_id())
            attrs_sorted = get_asset_attributes(asset)
            name = asset.get_name()
            connected_to_info = get_connected_to_info(asset)
        else:
            pot = find_potential(area, object_id)
            print('Get info for potential ' + pot.get_id())
            attrs_sorted = get_potential_attributes(pot)
            name = pot.get_name()
            connected_to_info = []

        if name is None: name = ''
        emit('asset_info', {'id': object_id, 'name': name, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info})

    if message['cmd'] == 'get_conductor_info':
        asset_id = message['id']
        latlng = message['latlng']
        area = es_edit.get_instance()[0].get_area()
        asset = find_asset(area, asset_id)
        connected_to_info = get_connected_to_info(asset)
        print('Get info for conductor ' + asset.get_id())
        attrs_sorted = get_asset_attributes(asset)
        name = asset.get_name()
        if name is None: name = ''
        emit('asset_info', {'id': asset_id, 'name': name, 'latlng': latlng, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info})

    if message['cmd'] == 'set_asset_param':
        asset_id = message['id']
        param_name = message['param_name']
        param_value = message['param_value']

        area = es_edit.get_instance()[0].get_area()

        asset = find_asset(area, asset_id)
        print('Set param '+ param_name +' for asset ' + asset_id + ' to value '+ param_value)

        # TODO: Find nice way to set al parameters based on their names
        # TODO: Take care of int, float, string (and ENUM?)
        if param_name in ['aggregated', 'name', 'originalIdInSource', 'description', 'prodType', 'shortName']:
            getattr(asset, 'set_' + param_name)(param_value)
        if param_name in ['aggregationCount']:
            getattr(asset, 'set_' + param_name)(str2int(param_value))
        if param_name in ['COP', 'power', 'efficiency', 'electricalEfficiency', 'heatEfficiency', 'surfaceArea']:
            getattr(asset, 'set_'+param_name)(str2float(param_value))

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
                        emit('port_profile_info', {'port_id': port_id, 'profile_info': profile_info})
                    else:
                        emit('port_profile_info', {'port_id': port_id, 'profile_info': {'class': 'SingleValue', 'value': 1, 'type': 'ENERGY_IN_TJ'}})

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
            esdl_profile.set_value(str2float(multiplier_or_value))
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
                    esdl_profile.set_multiplier(str2float(multiplier_or_value))
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

    if message['cmd'] == 'add_port':
        direction = message['direction']
        asset_id = message['asset_id']
        pname = message['pname']

        asset = asset_dict[asset_id]
        if direction == 'in':
            port = esdl.InPort()
        else:
            port = esdl.OutPort()
        pid = str(uuid.uuid4())
        port.set_id(pid)
        port.set_name(pname)

        geom = asset.get_geometry()
        if isinstance(geom, esdl.Point):
            lat = geom.get_lat()
            lon = geom.get_lon()
            coord = (lat, lon)
            mapping[pid] = {'asset_id': asset.get_id(), 'coord': coord}
            asset.add_port_with_type(port)
        else:
            send_alert('ERROR: Adding port not supported yet! asset doesn\'t have geometry esdl.Point')

    if message['cmd'] == 'remove_port':
        pid = message['port_id']

        asset_id = mapping[pid]['asset_id']
        asset = asset_dict[asset_id]

        remove_idx = None
        ports = asset.get_port()

        for p in ports:
            if p.get_id() == pid:
                _remove_port_references(p)
                ports.remove(p)

    if message['cmd'] == 'remove_connection':
        from_asset_id = message['from_asset_id']
        from_asset = asset_dict[from_asset_id]
        from_port_id = message['from_port_id']
        to_asset_id = message['to_asset_id']
        to_asset = asset_dict[to_asset_id]
        to_port_id = message['to_port_id']
        print('Removing connection {}#{} -> {}#{}'.format(from_asset.get_name(), from_port_id, to_asset.get_name(), to_port_id))
        # remove reference at both sides (this is quite ugly in generateDS-based ESDL...)
        for p in from_asset.get_port():
            if p.get_id() == from_port_id:
                connected_to = p.get_connectedTo()
                if connected_to:
                    connected_to_list = connected_to.split(' ')
                    new_connected_to_list = []
                    for conn_id in connected_to_list:
                        if conn_id != to_port_id:
                            # add non-affected connection to new list
                            new_connected_to_list.append(conn_id)
                    p.set_connectedTo(' '.join(new_connected_to_list))

        for p in to_asset.get_port():
            if p.get_id() == to_port_id:
                connected_to = p.get_connectedTo()
                if connected_to:
                    connected_to_list = connected_to.split(' ')
                    new_connected_to_list = []
                    for conn_id in connected_to_list:
                        if conn_id != from_port_id:
                            # add non-affected connection to new list
                            new_connected_to_list.append(conn_id)
                    p.set_connectedTo(' '.join(new_connected_to_list))

        # refresh connections in gui
        conn_list = session['conn_list']
        new_list = []
        print(conn_list)
        for conn in conn_list:
            if (conn['from-port-id'] != from_port_id or conn['from-asset-id'] != from_asset_id or \
                    conn['to-port-id'] != to_port_id or conn['to-asset-id'] != to_asset_id) and \
                    (conn['from-port-id'] != to_port_id or conn['from-asset-id'] != to_asset_id or \
                    conn['to-port-id'] != from_port_id or conn['to-asset-id'] != from_asset_id):
                # Remove both directions from -> to and to -> from as we don't know how they are stored in the list
                # does not matter, as a connection is unique
                new_list.append(conn)  # add connections that we are not interested in
            else:
                print(' - removed {}'.format(conn))
        session['conn_list'] = new_list  # set new connection list
        emit('clear_connections')  # update gui
        emit('add_connections', new_list)

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

    if message['cmd'] == 'add_carrier':
        # en_carr: socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, emission: carr_emission, encont: carr_encont, encunit: carr_encunit});
        # el_comm: socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, voltage: carr_voltage});
        # g_comm: socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, pressure: carr_pressure});
        # h_comm: socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name, suptemp: carr_suptemp, rettemp: carr_rettemp});
        # en_comm: socket.emit('command', {cmd: 'add_carrier', type: carr_type, name: carr_name});
        carr_type = message['type']
        carr_name = message['name']
        carr_id = str(uuid.uuid4())

        if carr_type == 'en_carr':
            carr_emission = message['emission']
            carr_encont = message['encont']
            carr_encunit = message['encunit']   # MJpkg MJpNm3 MJpMJ
            carr_sofm = message['sofm']
            carr_rentype = message['rentype']

            carrier = esdl.EnergyCarrier(id = carr_id, name = carr_name, emission = str2float(carr_emission),
                        energyContent = str2float(carr_encont), energyCarrierType = carr_rentype, stateOfMatter = carr_sofm)

            if carr_encunit == 'MJpkg':
                encont_qandu = esdl.QuantityAndUnitType(physicalQuantity = 'ENERGY', multiplier = 'MEGA', unit = 'JOULE',
                                                      perMultiplier = 'KILO', perUnit = 'GRAM')
            elif carr_encunit == 'MJpNm3':
                encont_qandu = esdl.QuantityAndUnitType(physicalQuantity = 'ENERGY', multiplier = 'MEGA', unit = 'JOULE',
                                                      perUnit = 'CUBIC_METRE')
            elif carr_encunit == 'MJpMJ':
                encont_qandu = esdl.QuantityAndUnitType(physicalQuantity = 'ENERGY', multiplier = 'MEGA', unit = 'JOULE',
                                                      perMultiplier = 'MEGA', perUnit = 'JOULE')

            emission_qandu = esdl.QuantityAndUnitType(physicalQuantity = 'EMISSION', multiplier = 'KILO', unit = 'GRAM',
                                                  perMultiplier = 'GIGA', perUnit = 'JOULE')

            carrier.set_energyContentUnit(encont_qandu)
            carrier.set_emissionUnit(emission_qandu)

        if carr_type == 'el_comm':
            carr_voltage = message['voltage']
            carrier = esdl.ElectricityCommodity(id = carr_id, name = carr_name, voltage = str2float(carr_voltage))
        if carr_type == 'g_comm':
            carr_pressure = message['pressure']
            carrier = esdl.GasCommodity(id = carr_id, name = carr_name, pressure = str2float(carr_pressure))
        if carr_type == 'h_comm':
            carr_suptemp = message['suptemp']
            carr_rettemp = message['rettemp']
            carrier = esdl.HeatCommodity(id = carr_id, name = carr_name, supplyTemperature = str2float(carr_suptemp), returnTemperature = str2float(carr_rettemp))
        if carr_type == 'en_comm':
            carrier = esdl.EnergyCarrier(id = carr_id, name = carr_name)

        esi = es_edit.get_energySystemInformation()
        if not esi:
            esi_id = str(uuid.uuid4())
            esi = esdl.EnergySystemInformation()
            esi.set_id(esi_id)
            es_edit.set_energySystemInformation(esi)

        ecs = esi.get_carriers()
        if not ecs:
            ecs_id = str(uuid.uuid4())
            ecs = esdl.Carriers()
            ecs.set_id(ecs_id)
            esi.set_carriers(ecs)

        ecs.add_carrier_with_type(carrier)

        carrier_list = get_carrier_list(es_edit)
        emit('carrier_list', carrier_list)

    if message['cmd'] == 'set_building_color_method':
        session["color_method"] = message['method']
        print(session["color_method"])

        instance = es_edit.get_instance()
        if instance:
            top_area = instance[0].get_area()
            if top_area:
                emit('clear_ui', {'layer': 'buildings'})
                emit('clear_ui', {'layer': 'areas'})
                find_boundaries_in_ESDL(top_area)

    if message['cmd'] == 'get_storage_strategy_info':
        asset_id = message['asset_id']

        mcc, mdc = get_storage_marginal_costs(asset_id)
        emit('storage_strategy_window', {'asset_id': asset_id, 'mcc': mcc, 'mdc': mdc})

    if message['cmd'] == 'set_control_strategy':
        # socket.emit('command', {'cmd': 'set_control_strategy', 'strategy': control_strategy, 'asset_id': asset_id, 'port_id': port_id});
        strategy = message['strategy']
        asset_id = message['asset_id']

        if strategy == 'StorageStrategy':
            mcc = message['marg_ch_costs']
            mdc = message['marg_disch_costs']
            add_storage_control_strategy_for_asset(asset_id, mcc, mdc)
        else:
            port_id = message['port_id']
            add_drivenby_control_strategy_for_asset(asset_id, strategy, port_id)

    if message['cmd'] == 'set_marginal_costs_get_info':
        asset_id = message['asset_id']

        mc = get_marginal_costs_for_asset(asset_id)
        emit('marginal_costs', {'asset_id': asset_id, 'mc': mc})

    if message['cmd'] == 'set_marg_costs':
        asset_id = message['asset_id']
        mc = str2float(message['marg_costs'])

        set_marginal_costs_for_asset(asset_id, mc)

    if message['cmd'] == 'layer':
        pass

    if message['cmd'] == 'run_ESSIM_simulation':
        print('ESSIM simulation command received')
        # Create the HTTP POST to start the simulation
        if start_ESSIM():
            emit('show_simulation_progress_window', {'simulation': 'ESSIM'})
        # start_checking_ESSIM_progress()
        # check_ESSIM_progress()

    if message['cmd'] == 'validate_for_ESSIM':
        print('validation for ESSIM command received')
        res = validate_ESSIM(es_edit)
        emit('results_validation_for_ESSIM', res)

    if message['cmd'] == 'calculate_ESSIM_KPIs':
        # session['simulationRun'] = '5d10f273783bac5eff4575e8'

        if 'simulationRun' in session:
            sdt = datetime.strptime(essim_config['start_datetime'], '%Y-%m-%dT%H:%M:%S%z')
            edt = datetime.strptime(essim_config['end_datetime'], '%Y-%m-%dT%H:%M:%S%z')

            influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
            influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')

            kpi_results = ESSIM_KPIs(es_edit, session['simulationRun'], influxdb_startdate, influxdb_enddate)
            res = kpi_results.calculate_kpis()
            emit('show_ESSIM_KPIs', res)
        else:
            send_alert('No simulation id defined')

    if message['cmd'] == 'add_layer':
        id = message['id']
        descr = message['descr']
        url = message['url']
        name = message['name']
        visible = message['visible']

        layer = {
            "description": descr,
            "url": url,
            "layer_name": name,
            "layer_ref": None,
            "visible": visible
        }

        wms_layers.add_wms_layer(id, layer)

    if message['cmd'] == 'remove_layer':
        id = message['id']
        wms_layers.remove_wms_layer(id)

    session['es_edit'] = es_edit
    session['asset_dict'] = asset_dict
    session.modified = True


# ---------------------------------------------------------------------------------------------------------------------
#  Initialization after new or load energy system
# ---------------------------------------------------------------------------------------------------------------------
def create_empty_energy_system(es_title, es_description, inst_title, area_title):
    es = esdl.EnergySystem()
    es_id = str(uuid.uuid4())
    es.set_id(es_id)
    es.set_name(es_title)
    es.set_description(es_description)

    instance = esdl.Instance()
    instance.set_id(str(uuid.uuid4()))
    instance.set_name(inst_title)
    es.add_instance(instance)

    area = esdl.Area()
    area.set_id(str(uuid.uuid4()))
    area.set_name(area_title)
    instance.set_area(area)

    return es


def process_energy_system(es):
    asset_list = []
    area_bld_list = []
    conn_list = []
    mapping = {}

    area = es.get_instance()[0].get_area()
    emit('clear_ui')
    find_boundaries_in_ESDL(area)       # also adds coordinates to assets if possible

    asset_dict = create_asset_dict(area)
    carrier_list = get_carrier_list(es)

    create_port_to_asset_mapping(area, mapping)
    process_area(asset_list, area_bld_list, conn_list, mapping, area, 0)

    emit('es_title', es.get_name())
    emit('add_esdl_objects', {'list': asset_list, 'zoom': True})
    emit('area_bld_list', area_bld_list)
    emit('add_connections', conn_list)
    emit('carrier_list', carrier_list)

    session['es_title'] = es.get_name()
    session['es_edit'] = es
    session['es_id'] = es.get_id()
    session['es_descr'] = es.get_description()
    # session['es_start'] = 'new'

    session['port_to_asset_mapping'] = mapping
    session['conn_list'] = conn_list
    session['carrier_list'] = carrier_list
    session['asset_dict'] = asset_dict
    session['color_method'] = 'building type'

    session.modified = True
    print('session variables set')
    print('ed_id: ', session['es_id'])


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
        if top_area_name == '': top_area_name = 'Untitled area'

        es_edit = create_empty_energy_system(title, description, 'Untitled instance', top_area_name)
        process_energy_system(es_edit)

        session['es_email'] = email

    if message['cmd'] == 'load_esdl_from_file':
        file_content = message['file_content']
        if file_content.startswith('<?xml'):
            # remove the <?xml encoding='' stuff, as the parseString doesn't like encoding in there
            file_content = file_content.split('\n', 1)[1]
        try:
            es_load = esdl.parseString(file_content, silence=True)
            es_edit = es_load
        except Exception as e:
            send_alert('Error interpreting ESDL from file - Exception: '+str(e))

        process_energy_system(es_edit)
        # start_ESSIM()
        # check_ESSIM_progress()

    if message['cmd'] == 'get_list_from_store':
        try:
            result = requests.get(store_url)
        except:
            send_alert('Error accessing ESDL store')
            return

        data = result.json()
        store_list = []
        for es in data:
            store_list.append({'id': es['id'], 'title': es['title']})

        emit('store_list', store_list)

    if message['cmd'] == 'load_esdl_from_store':
        es_id = message['id']

        es_load = load_ESDL_EnergySystem(es_id)
        if es_load:
            es_edit = es_load

        process_energy_system(es_edit)

    if message['cmd'] == 'store_esdl':
        es_edit = session['es_edit']
        es_id = session['es_id']

        store_ESDL_EnergySystem(es_id, es_edit)

    if message['cmd'] == 'save_esdl':
        es_edit = session['es_edit']
        es_id = session['es_id']
        try:
            write_energysystem_to_file('./static/EnergySystem.esdl', es_edit)
            # TODO: do we need to flush??
            emit('and_now_press_download_file')
        except Exception as e:
            send_alert('Error saving ESDL file to filesystem - exception: '+str(e))

    if message['cmd'] == 'download_esdl':
        es_edit = session['es_edit']
        name = session['es_title'].replace(' ', '_')

        send_ESDL_as_file(es_edit, name)


# ---------------------------------------------------------------------------------------------------------------------
#  Connect from browser
#   - initialize energysystem information
#   - send info to browser
# ---------------------------------------------------------------------------------------------------------------------
def initialize_app():
    session.permanent = True
    print('Client connected: ', request.sid)

    if 'es_edit' in session:
        print ('Energysystem in memory - reloading client data')
        es_edit = session['es_edit']
    else:
        print ('No energysystem in memory - generating empty energysystem')
        es_edit = create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area')

    process_energy_system(es_edit)
    session.modified = True


@socketio.on('connect', namespace='/esdl')
def on_connect():
    print("Websocket connection established")
    emit('profile_info', esdl_config.esdl_config['influxdb_profile_data'])
    emit('control_strategy_config', esdl_config.esdl_config['control_strategies'])
    emit('wms_layer_list', wms_layers.get_layers())

    initialize_app()


# ---------------------------------------------------------------------------------------------------------------------
#  Disconnect
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect', namespace='/esdl')
def on_disconnect():
    print('Client disconnected: {}'.format(request.sid))


# ---------------------------------------------------------------------------------------------------------------------
#  Start application
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    parse_esdl_config()
    print("starting App")
    socketio.run(app, debug=settings.FLASK_DEBUG, host=settings.FLASK_SERVER_HOST, port=settings.FLASK_SERVER_PORT)

