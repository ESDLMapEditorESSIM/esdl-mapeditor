#!/usr/bin/env python
import os
import time
import logging
import threading
from sys import getsizeof
from warnings import warn
from flask_executor import Executor
from flask import Flask, render_template, session, request, send_from_directory, jsonify, abort, send_file, redirect, Response, stream_with_context
from flask_socketio import SocketIO, emit
from flask_session import Session
from werkzeug.wsgi import FileWrapper
from flask_oidc import OpenIDConnect
import jwt
import requests
import urllib
import uuid
import math
import copy
import json
import importlib
import random
import re
from datetime import datetime

from utils.RDWGSConverter import RDWGSConverter
from essim_validation import validate_ESSIM
from essim_kpis import ESSIM_KPIs
from wms_layers import WMSLayers
from esdl.esdl_handler import EnergySystemHandler
from esdl.processing import ESDLGeometry, ESDLAsset, ESDLEcore, ESDLQuantityAndUnits, ESDLEnergySystem
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl import esdl
from extensions.heatnetwork import HeatNetwork
from extensions.ibis import IBISBedrijventerreinen
from extensions.bag import BAG
from extensions.boundaries import Boundaries
from extensions.esdl_browser import ESDLBrowser
from extensions.session_manager import set_handler, get_handler, get_session, set_session, del_session, schedule_session_clean_up, valid_session, get_session_for_esid, set_session_for_esid
import esdl_config
from esdl_helper import generate_profile_info
import settings
from edr_assets import EDR_assets
from esdl_services import ESDLServices
from esdl_profiles import ESDLProfiles
from pyecore.ecore import EDate
from user_logging import UserLogging
from extensions.user_settings import UserSettings
from extensions.esdl_api import ESDL_API
from extensions.esdl_compare import ESDLCompare
from extensions.essim import ESSIM
from extensions.vesta import Vesta

logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(threadName)s] - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
if settings.FLASK_DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
#logging.getLogger("werkzeug")

if os.environ.get('GEIS'):
    import gevent.monkey
    gevent.monkey.patch_all()

#TODO fix send_file in uwsgi
# debugging with pycharm:
#https://stackoverflow.com/questions/21257568/debugging-a-uwsgi-python-application-using-pycharm/25822477

esdl_services = ESDLServices()
esdl_profiles = ESDLProfiles()
user_actions_logging = UserLogging()
user_settings = UserSettings(database_uri='mongodb://'+settings.user_settings_config["host"] + ':' + settings.user_settings_config["port"])
wms_layers = WMSLayers(user_settings)

AREA_LINECOLOR = 'blue'
AREA_FILLCOLOR = 'red'

# ---------------------------------------------------------------------------------------------------------------------
#  File I/O and ESDL Store API calls
# ---------------------------------------------------------------------------------------------------------------------

# ESDL_STORE_PORT = '3003'
# store_url = 'http://' + GEIS_CLOUD_IP + ':' + ESDL_STORE_PORT + '/store/'
default_store_url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.ESDL_STORE_PORT + '/store/'
mondaine_hub_url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.MONDAINE_HUB_PORT + '/store/'
# mondaine_hub_url = 'https://mondaine-hub.hesi.energy'+ '/store/'

# handler to retrieve E
esdl_doc = EcoreDocumentation(esdlEcoreFile="esdl/esdl.ecore")

def write_energysystem_to_file(filename, esh):
    active_es_id = get_session('active_es_id')
    esh.save(es_id = active_es_id, filename=filename)


def create_ESDL_store_item(id, esh, title, description, email):

    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    esdlstr = esh.to_string()
    try:
        payload = {'id': id, 'title': title, 'description': description, 'email':email, 'esdl': esdlstr}
        requests.post(store_url, data=payload)
    except Exception as e:
        send_alert('Error accessing ESDL store:' + str(e))


# TODO: move to EDR plugin (not EDR! :-))
def load_ESDL_EnergySystem(store_id):

    store_item = load_store_item(store_id)
    if store_item:
        esdlstr = store_item['esdl']

        del store_item['esdl']
        set_session('store_item_metadata', store_item)
        emit('store_item_metadata', store_item)

        try:
            esh = get_handler()
            esh.load_from_string(esdl_string=esdlstr, name=store_item['title'])
            return esh
        except Exception as e:
            send_alert('Error interpreting ESDL file from store: ' + str(e))
            return None
    else:
        return None


def load_store_item(store_id):
    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    url = store_url + store_id + '?format=xml'
    try:
        r = requests.get(url)
    except Exception as e:
        send_alert('Error accessing ESDL store:' + str(e))
        return None

    if r.status_code == 200:
        result = json.loads(r.text)
        if len(result) > 0:
            return result
        else:
            return None
    else:
        print('Accessing store return status: '+str(r.status_code))
        send_alert('Error accessing ESDL store:' + str(r))
        return None


def update_store_item(store_id, title, descr, email, tags, esh):
    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    esdlstr = esh.to_string()

    payload = {'id': store_id, 'title': title, 'description': descr, 'email': email, 'tags': tags, 'esdl': esdlstr}
    try:
        requests.put(store_url + store_id, data=payload)
    except Exception as e:
        send_alert('Error saving ESDL file to store: ' + str(e))


def create_new_store_item(store_id, title, descr, email, tags, esh):
    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    esdlstr = esh.to_string()

    payload = {'id': store_id, 'title': title, 'description': descr, 'email': email, 'tags': tags, 'esdl': esdlstr}
    try:
        r = requests.post(store_url, data=payload)
    except Exception as e:
        send_alert('Error saving ESDL file to store: ' + str(e))

    if r.status_code != 201:
        send_alert('Error saving ESDL file to store. Error code: ' + str(r.status_code))


def send_ESDL_as_file(esh, name):
    esh.save(filename='/tmp/temp.xmi')


# ---------------------------------------------------------------------------------------------------------------------
#  GEIS Boundary service access
# ---------------------------------------------------------------------------------------------------------------------
boundary_service_mapping = {
    'ZIPCODE': 'zipcodes',
    'NEIGHBOURHOOD': 'neighbourhoods',
    'DISTRICT': 'districts',
    'MUNICIPALITY': 'municipalities',
    'REGION': 'regions',
    'PROVINCE': 'provinces',
    'COUNTRY': 'countries'
}

#create a cache for the boundary service
boundary_cache = dict()


def is_valid_boundary_id(id):
    return re.match('PV[0-9]{2,2}|RES[0-9]{2,2}|GM[0-9]{4,4}|WK[0-9]{6,6}|BU[0-9]{8,8}', id.upper())


def get_boundary_from_service(scope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """
    if is_valid_boundary_id(id):
        time.sleep(0.01) # yield a little concurrency when running this in a thread
        if id in boundary_cache:
            # print('Retrieve boundary from cache', id)
            # res_boundary = copy.deepcopy(boundary_cache[id])   # this doesn't solve messing up cache
            # return res_boundary
            return boundary_cache[id]

        try:
            # url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(scope)] + '/' + id
            url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[scope.name] + '/' + id

            # print('Retrieve from boundary service', id)
            r = requests.get(url)
            if len(r.text) > 0:
                reply = json.loads(r.text)
                # geom = reply['geom']

            # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
            # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
            # 'tCode': 'GM0003', 'tName': 'Appingedam'}
                boundary_cache[id] = reply
                return reply
            else:
                print("WARNING: Empty response for GEIS boundary service for {} with id {}".format(scope.name, id))
                return None

        except Exception as e:
            print('ERROR in accessing GEIS boundary service for {} with id {}: {}'.format(scope.name, id, e))
            return None
    else:
        return None


def get_subboundaries_from_service(scope, subscope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param subscope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    if is_valid_boundary_id(id):
        try:
            url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[subscope.name]\
                  + '/' + boundary_service_mapping[scope.name] + '/' + id
            r = requests.get(url)
            reply = json.loads(r.text)
            # print(reply)

            # ARRAY OF:
            # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
            # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

            return reply
        except Exception as e:
            print('ERROR in accessing GEIS boundary service for {} with id {}, subscope {}: {}'.format(scope.name, id, subscope.name, str(e)))
            return {}
    else:
        return {}


def preload_subboundaries_in_cache(top_area_scope, sub_area_scope, top_area_id):
    sub_boundaries = get_subboundaries_from_service(top_area_scope, sub_area_scope, top_area_id)

    for sub_boundary in sub_boundaries:
        code = sub_boundary['code']
        geom = sub_boundary['geom']
        if code and geom:
            boundary_cache[code] = sub_boundary


def preload_area_subboundaries_in_cache(top_area):
    top_area_scope = top_area.scope
    # fix bug in that the top area does not have an id
    if top_area.id is None:
        top_area.id = str(uuid.uuid4())
    top_area_id = top_area.id

    sub_areas = top_area.area
    if sub_areas:
        first_sub_area = sub_areas[0]
        sub_area_scope = first_sub_area.scope

        if top_area_scope and sub_area_scope and is_valid_boundary_id(top_area_id):
            preload_subboundaries_in_cache(top_area_scope, sub_area_scope, top_area_id)


# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
def create_building_KPIs(building):
    # Assume this is a building, see if there are buildingUnits to find usage ('gebruiksdoel')
    # For now, use first BuildingUnit ...
    # TODO: Improve to use most 'dominant' (based on area?) Or introduce 'mixed' category?
    KPIs = {}

    try:
        largest_bunit_floorArea = 0
        largest_bunit_type = None

        for basset in building.asset:
            if isinstance(basset, esdl.BuildingUnit):
                if basset.floorArea > largest_bunit_floorArea:
                    largest_bunit_floorArea = basset.floorArea
                    btypes = []
                    for gd in basset.type:
                        btypes.append(gd.name)
                    largest_bunit_type = ", ".join(btypes)

        if largest_bunit_type:
            KPIs["buildingType"] = largest_bunit_type
    except:
        pass

    try:
        if building.buildingYear > 0:
            KPIs["buildingYear"] = building.buildingYear
    except:
        pass

    try:
        if building.floorArea > 0:
            KPIs["floorArea"] = building.floorArea
    except:
        pass

    if building.KPIs:
        for kpi in building.KPIs.kpi:
            KPIs[kpi.name] = kpi.value

    return KPIs


def find_area_info_geojson(building_list, area_list, this_area):
    area_id = this_area.id
    area_name = this_area.name
    if not area_name: area_name = ""
    area_scope = this_area.scope
    area_geometry = this_area.geometry
    boundary_wgs = None

    geojson_KPIs = {}
    area_KPIs = this_area.KPIs
    if area_KPIs:
        for kpi in area_KPIs.kpi:
            geojson_KPIs[kpi.name] = kpi.value

    if area_geometry:
        if isinstance(area_geometry, esdl.Polygon):
            boundary_wgs = ESDLGeometry.create_boundary_from_geometry(area_geometry)
            area_list.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    # bug in ESDL genaration with 'get_boundary_info': convert_coordinates_into_subpolygon now
                    # handles order of lat-lon correctly. Exchanging not required anymore
                    # "coordinates": ESDLGeometry.exchange_polygon_coordinates(boundary_wgs['coordinates'])
                    "coordinates": boundary_wgs['coordinates']
                },
                "properties": {
                    "id": area_id,
                    "name": area_name,
                    "KPIs": geojson_KPIs
                }
            })
        if isinstance(area_geometry, esdl.MultiPolygon):
            boundary_wgs = ESDLGeometry.create_boundary_from_geometry(area_geometry)
            for i in range(0, len(boundary_wgs['coordinates'])):
                if len(boundary_wgs['coordinates']) > 1:
                    area_id_number = " ({} of {})".format(i + 1, len(boundary_wgs['coordinates']))
                else:
                    area_id_number = ""
                area_list.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        # bug in ESDL genaration with 'get_boundary_info': convert_coordinates_into_subpolygon now
                        # handles order of lat-lon correctly. Exchanging not required anymore
                        # "coordinates":  ESDLGeometry.exchange_polygon_coordinates(boundary_wgs['coordinates'][i])
                        "coordinates":  boundary_wgs['coordinates'][i]
                    },
                    "properties": {
                        "id": area_id + area_id_number,
                        "name": area_name,
                        "KPIs": geojson_KPIs
                    }
                })
    else:
        # simple hack to check if ID is not a UUID and area_scope is defined --> then query GEIS for boundary
        if area_id and area_scope.name != 'UNDEFINED':
            if len(area_id) < 20:
                # print('Finding boundary from GEIS service')
                boundary_wgs = get_boundary_from_service(area_scope, str.upper(area_id))
                if boundary_wgs:
                    # this really prevents messing up the cache
                    # tmp = copy.deepcopy(boundary_rd)
                    # tmp['coordinates'] = ESDLGeometry.convert_mp_rd_to_wgs(tmp['coordinates'])    # Convert to WGS
                    # boundary_wgs = tmp
                    for i in range(0, len(boundary_wgs['geom']['coordinates'])):
                        if len(boundary_wgs['geom']['coordinates']) > 1:
                            area_id_number = " ({} of {})".format(i+1, len(boundary_wgs['geom']['coordinates']))
                        else:
                            area_id_number = ""
                        area_list.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": boundary_wgs['geom']['coordinates'][i]
                            },
                            "properties": {
                                "id": str.upper(area_id) + area_id_number,
                                "name": boundary_wgs['name'],
                                "KPIs": geojson_KPIs
                            }
                        })

                    # small hack:
                    # get_boundary_from_service returns different struct than create_boundary_from_geometry
                    boundary_wgs = boundary_wgs['geom']

    # assign random coordinates if boundary is given and area contains assets without coordinates
    # and gives assets within buildings a proper coordinate
    update_asset_geometries3(this_area, boundary_wgs)

    assets = this_area.asset
    for asset in assets:
        if isinstance(asset, esdl.AbstractBuilding):
            pass
            # name = asset.name
            # if not name:
            #     name = ''
            # id = asset.id
            # if not id:
            #     id = ''
            # asset_geometry = asset.geometry
            # if asset_geometry:
            #     if isinstance(asset_geometry, esdl.Polygon):
            #
            #         # Assume this is a building, see if there are buildingUnits to find usage ('gebruiksdoel')
            #         # For now, use first BuildingUnit ...
            #         # TODO: Improve to use most 'dominant' (based on area?) Or introduce 'mixed' category?
            #         KPIs = {}
            #         for basset in asset.asset:
            #             if isinstance(basset, esdl.BuildingUnit):
            #                 try:
            #                     KPIs["buildingType"] = basset.type.name
            #                 except:
            #                     pass
            #
            #         try:
            #             if asset.buildingYear > 0:
            #                 KPIs["buildingYear"] = asset.buildingYear
            #         except:
            #             pass
            #
            #         try:
            #             if asset.floorArea > 0:
            #                 KPIs["floorArea"] = asset.floorArea
            #         except:
            #             pass
            #
            #
            #         bld_boundary = ESDLGeometry.create_boundary_from_contour(asset_geometry)
            #         building_list.append({
            #             "type": "Feature",
            #             "geometry": {
            #                 "type": "Polygon",
            #                 "coordinates": bld_boundary['coordinates']
            #             },
            #             "properties": {
            #                 "id": id,
            #                 "name": name,
            #                 "KPIs": KPIs
            #             }
            #         })
        else: # No AbstractBuilding
            asset_geometry = asset.geometry
            name = asset.name
            if asset_geometry:
               if isinstance(asset_geometry, esdl.WKT):
                        emit('area_boundary', {'info-type': 'WKT', 'boundary': asset_geometry.value,
                                               'crs': asset_geometry.CRS, 'color': 'grey', 'name': name,
                                               'boundary_type': 'asset'})

    potentials = this_area.potential
    for potential in potentials:
        potential_geometry = potential.geometry
        potential_name = potential.name
        if potential_geometry:
            if isinstance(potential_geometry, esdl.WKT):
                # print(potential_geometry)
                emit('pot_boundary', {'info-type': 'WKT', 'boundary': potential_geometry.value,
                                      'crs': potential_geometry.CRS, 'color': 'grey', 'name': potential_name,
                                      'boundary_type': 'potential'})

    areas = this_area.area
    for area in areas:
        find_area_info_geojson(building_list, area_list, area)


def create_area_info_geojson(area):
    building_list = []
    area_list = []
    print("- Finding ESDL boundaries...")
    preload_area_subboundaries_in_cache(area)
    find_area_info_geojson(building_list, area_list, area)
    print("- Done")
    return area_list, building_list


def find_boundaries_in_ESDL(top_area):
    print("Finding area and building boundaries in ESDL")
    # _find_more_area_boundaries(top_area)
    area_list, building_list = create_area_info_geojson(top_area)

    # Sending an empty list triggers removing the legend at client side
    print('- Sending boundary information to client, size={}'.format(getsizeof(area_list)))
    emit('geojson', {"layer": "area_layer", "geojson": area_list})
    print('- Sending asset information to client, size={}'.format(getsizeof(building_list)))
    emit('geojson', {"layer": "bld_layer", "geojson": building_list})


def add_missing_coordinates(area):
    min_lat = float("inf")
    max_lat = -float("inf")
    min_lon = float("inf")
    max_lon = -float("inf")

    for child in area.eAllContents():
        point = None
        if isinstance(child, esdl.Polygon):
            if child.CRS != "Simple": point = child.exterior.point[0]     # take first coordinate of exterior of polygon
        if isinstance(child, esdl.Point):
            if child.CRS != "Simple": point = child
        if point:
            if point.lat < min_lat: min_lat = point.lat
            if point.lat > max_lat: max_lat = point.lat
            if point.lon < min_lon: min_lon = point.lon
            if point.lon > max_lon: max_lon = point.lon
            point = None

    delta_x = max_lon - min_lon
    delta_y = max_lat - min_lat
    center = [(min_lon + max_lon)/2, (min_lat + max_lat)/2]
    RD_coords = (max_lat > 180 and max_lon > 180)               # boolean indicating if RD CRS is used

    for child in area.eAllContents():
        if isinstance(child, esdl.EnergyAsset) or isinstance(child, esdl.AggregatedBuilding) or isinstance(child, esdl.Building):
            if not child.geometry:
                child.geometry = calc_random_location_around_center(center, delta_x / 4, delta_y / 4, RD_coords)


def is_running_in_uwsgi():
    try:
        import uwsgi
        a = uwsgi.opt
        print("uWSGI startup options: {}".format(a))
        return True
    except Exception as e:
        return False

# ---------------------------------------------------------------------------------------------------------------------
#  Application definition, configuration and setup of simple file server
# ---------------------------------------------------------------------------------------------------------------------
if settings.FLASK_DEBUG:
    logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config['SECRET_KEY'] = b'\xc3g\x19\xbf\x8e\xa0\xe7\xc8\x9a/\xae%\x04g\xbe\x9f\xaex\xb5\x8c\x81f\xaf`' #os.urandom(24)   #'secret!'
app.config['SESSION_COOKIE_NAME'] = 'ESDL-WebEditor-session'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24 # 1 day in seconds
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True # make sure errors are logged for tasks run in threads

print("Socket.IO Async mode: ", settings.ASYNC_MODE)
print('Running inside uWSGI: ', is_running_in_uwsgi())

socketio = SocketIO(app, async_mode=settings.ASYNC_MODE, manage_session=False, path='/socket.io', logger=settings.FLASK_DEBUG)
logging.getLogger('engineio').setLevel(logging.WARNING) # don't print all the messages
# fix sessions with socket.io. see: https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
Session(app)
executor = Executor(app)

#extensions
schedule_session_clean_up()
HeatNetwork(app, socketio)
IBISBedrijventerreinen(app, socketio)
ESDLBrowser(app, socketio, esdl_doc)
BAG(app, socketio)
Boundaries(app, socketio)
esdl_api = ESDL_API(app, socketio)
ESDLCompare(app, socketio)
essim_kpis = ESSIM_KPIs(app, socketio)
essim = ESSIM(app, socketio, user_settings)
Vesta(app, socketio, user_settings)

#TODO: check secret key with itsdangerous error and testing and debug here

app.config.update({
    'TESTING': True,
    'DEBUG': True,
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'esdl-mapeditor',
    'OIDC_SCOPES': ['openid', 'email', 'profile', 'groups', 'microprofile-jwt', 'resource_access'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_CLIENT_SECRETS': settings.OIDC_CLIENT_SECRETS
})

oidc = OpenIDConnect(app)


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


@app.before_request
def before_request():
    # store session id
    session['client_id'] = request.cookies.get(app.config['SESSION_COOKIE_NAME'])  # get cookie id


@app.route('/')
def index():
    return render_template('index.html', dir_settings=settings.dir_settings)


"""
# test for OpenID connect authentication against KeyCloak
import pprint
@app.route('/test')
@oidc.require_login
def test_authentication():
    if oidc.user_loggedin:
        user_email = oidc.user_getfield('email')
        user_groups = oidc.user_getfield('user_group')
        print('user: {}, user groups: {}'.format(user_email, user_groups))
        whole_token = oidc.get_access_token()
        if whole_token:
            jwt_tkn = jwt.decode(whole_token, key=settings.IDM_PUBLIC_KEY, algorithms='RS256', audience='account',
                                 verify=True)
            pprint.pprint(jwt_tkn)
            return jwt_tkn
        else:
            return "Hello world!"

    else:
        return "Not logged in"
"""

@app.route('/editor')
@oidc.require_login
def editor():
    #session['client_id'] = request.cookies.get(app.config['SESSION_COOKIE_NAME']) # get cookie id
    #set_session('client_id', session['client_id'])
    print('client_id is set to %s' % session['client_id'])
    if oidc.user_loggedin:
        if session['client_id'] == None:
            warn('WARNING: No client_id in session!!')

        user_email = oidc.user_getfield('email')

        print("************* USER LOGIN (" + user_email + ") at " + str(datetime.now()))
        user_actions_logging.store_logging(user_email, "login", "", "", "", {})

        whole_token = oidc.get_access_token()
        print("whole_token: ", whole_token)
        if whole_token:
            try:
                jwt_tkn = jwt.decode(whole_token,key=settings.IDM_PUBLIC_KEY, algorithms='RS256', audience='account', verify=False)
                import pprint
                pprint.pprint(jwt_tkn)
            except Exception as e:
                print("error in decoding token: ", str(e))
        # if role in access_token['resource_access'][client]['roles']:

        userinfo = oidc.user_getinfo(['role'])
        role = []
        if 'role' in userinfo:
            role = userinfo['role'].split(',')

        # find roles in for the mapeditor client
        mapeditor_role = []
        client = oidc.client_secrets.get('client_id')
        resource_access = oidc.user_getfield('resource_access')
        if resource_access is not None and client in resource_access:
            if 'roles' in resource_access[client]:
                mapeditor_role = resource_access[client]['roles']
        set_session('user-group', oidc.user_getfield('user_group'))
        set_session('user-role', role)
        set_session('user-email', user_email)
        set_session('user-mapeditor-role', mapeditor_role)
        return render_template('editor.html', async_mode=socketio.async_mode, dir_settings=settings.dir_settings, role=role)
    else:
        return render_template('index.html', dir_settings=settings.dir_settings)
        # to enable working offline without IDM:
        # - comment the @oidc.require_login above this method
        # - comment the line above: return render_template('index.html', dir_settings=settings.dir_settings)
        # - uncomment the following line:
        # return render_template('editor.html', async_mode=socketio.async_mode, dir_settings=settings.dir_settings, role='essim')


@app.route('/logout')
def logout():
    user_email = get_session('user-email')
    user_actions_logging.store_logging(user_email, "logout", "", "", "", {})

    """Performs local logout by removing the session cookie. and does a logout at the IDM"""
    oidc.logout()
    #This should be done automatically! see issue https://github.com/puiterwijk/flask-oidc/issues/88
    return redirect(oidc.client_secrets.get('issuer') + '/protocol/openid-connect/logout?redirect_uri=' + request.host_url)

# Cant find out why send_file does not work in uWSGI with threading.
# Now we send manually the ESDL as string, which is (probably) not efficient.
# This still works with a 1.6 MB file... Not sure if this scales any further...
@app.route('/esdl')
def download_esdl():
    """Sends the current ESDL file to the browser as an attachment"""
    esh = get_handler()
    active_es_id = get_session('active_es_id')

    try:
        #stream = esh.to_bytesio()
        content = esh.to_string(es_id=active_es_id)
        my_es = esh.get_energy_system(es_id=active_es_id)
        try:
            name = my_es.name
        except:
            name = my_es.id
        if name is None:
            name = "UntitledEnergySystem"
        name = '{}.esdl'.format(name)
        print('Sending file %s' % name)

        user_email = get_session('user-email')
        user_actions_logging.store_logging(user_email, "download esdl", name, "", "", {})

        #wrapped_io = FileWrapper(stream)
        #print(content)
        headers = dict()
        #headers['Content-Type'] =  'application/esdl+xml'
        headers['Content-Disposition'] = 'attachment; filename="{}"'.format(name)
        headers['Content-Length'] = len(content)
        return Response(content, mimetype='application/esdl+xml', direct_passthrough=True, headers=headers)
        #return send_file(stream, as_attachment=True, mimetype='application/esdl+xml', attachment_filename=name)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Error sending ESDL file, due to {}".format(e)


@app.route('/<path:path>')
def serve_static(path):
    # print('in serve_static(): '+ path)
    return send_from_directory('static', path)


@app.route('/edr_assets')
def get_edr_assets():
    edr_url = 'https://edr.hesi.energy/store/tagged?tag=asset'
    # print('accessing URL: '+edr_url)

    try:
        r = requests.get(edr_url)
        if r.status_code == 200:
            result = json.loads(r.text)
            asset_list = []
            for a in result:
                asset = {'id': a["id"], 'title': a["title"], 'description': a["description"]}
                asset_list.append(asset)

            return (jsonify({'asset_list': asset_list})), 200
        else:
            print('code: ', r.status_code)
            send_alert('Error in getting the EDR assets')
            abort(500, 'Error in getting the EDR assets')
    except Exception as e:
        print('Exception: ')
        print(e)
        send_alert('Error accessing EDR API')
        abort(500, 'Error accessing EDR API')


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
    emit('alert', message, namespace='/esdl')


# FIXME: pyecore
# def _remove_port_references(port):
#     mapping = session['port_to_asset_mapping']
#     asset_dict = session['asset_dict']
#
#     p_id = port.id
#     connected_to = port.connectedTo
#     if connected_to:
#         connected_to_list = connected_to.split(' ')
#         for conns in connected_to_list:
#             # conns now contains the id's of the port this port is referring to
#             ass_info = mapping[conns]
#             # asset = find_asset(area, ass_info['asset_id'])    # find_asset doesn't look for asset in top level area
#             asset = asset_dict[ass_info['asset_id']]
#             asset_ports = asset.port
#             for p_remove_ref in asset_ports:
#                 conn_to = p_remove_ref.connectedTo
#                 conn_tos = conn_to.split(' ')
#                 if p_id in conn_tos:
#                     conn_tos.remove(p_id)
#                 # FIXME: doesn't work in pyECORE
#                 conn_to = ' '.join(conn_tos)
#                 p_remove_ref.connectedTo = conn_to

        # FIXME: pyecore
def _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets):
    active_es_id = get_session('active_es_id')
    mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    processed_assets.append(asset_id)
    for p in asset.port:
        p.carrier = esh.get_by_id(active_es_id, carrier_id) #FIXME pyecore
        conn_to = p.connectedTo
        if conn_to:
            for conn_port in conn_to:
                conn_asset_id = mapping[conn_port.id]['asset_id']
                conn_asset = esh.get_by_id(active_es_id, conn_asset_id)
                if isinstance(conn_asset, esdl.Transport) and not isinstance(conn_asset, esdl.HeatExchange) \
                        and not isinstance(conn_asset, esdl.Transformer):
                    if conn_asset_id not in processed_assets:
                        _set_carrier_for_connected_transport_assets(conn_asset_id, carrier_id, processed_assets)
                else:
                    for conn_asset_port in conn_asset.port:
                        if conn_asset_port.id == conn_port.id:
                            conn_asset_port.carrier = p.carrier

def set_carrier_for_connected_transport_assets(asset_id, carrier_id):
    processed_assets = []  # List of asset_id's that are processed
    _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets)
    # print(processed_assets)

# ---------------------------------------------------------------------------------------------------------------------
#  Initialize
#  TODO: find out what should be here :-)
# ---------------------------------------------------------------------------------------------------------------------
def initialize():
    # TODO: fix
    set_session('port_to_asset_mapping', {})


# ---------------------------------------------------------------------------------------------------------------------
#  Builds up a dictionary from asset_id to asset
# ---------------------------------------------------------------------------------------------------------------------
# FIXME: pyecore, not needed: use esh.get_by_id(id)
# def _create_building_asset_dict(asset_dict, building):
#     for basset in building.asset:
#         asset_dict[basset.id] = basset
#
#
# def _create_area_asset_dict(esh, asset_dict, area):
#     for ar in area.area:
#         _create_area_asset_dict(esh, asset_dict, ar)
#     for asset in area.asset:
#         asset_dict[asset.id] = asset
#         if isinstance(asset, esdl.AbstractBuilding):
#             _create_building_asset_dict(esh, asset_dict, asset)
#
#
# def create_asset_dict(esh, area):
#     asset_dict = dict()
#     _create_area_asset_dict(esh, area)
#
#     return asset_dict


# ---------------------------------------------------------------------------------------------------------------------
#  Builds up a mapping from ports to assets
# ---------------------------------------------------------------------------------------------------------------------
def create_building_port_to_asset_mapping(building, mapping):
    for basset in building.asset:
        if isinstance(basset, esdl.AbstractBuilding):
            create_building_port_to_asset_mapping(basset, mapping)
        else:
            geom = basset.geometry
            ports = basset.port
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.lat
                    lon = geom.lon
                    coord = (lat, lon)
                    for p in ports:
                        mapping[p.id] = {'asset_id': basset.id, 'coord': coord}
                if isinstance(geom, esdl.Line):
                    points = geom.point
                    if ports:
                        first = (points[0].lat, points[0].lon)
                        last = (points[len(points)-1].lat, points[len(points)-1].lon)
                        mapping[ports[0].id] = {'asset_id': basset.id, 'coord': first}
                        mapping[ports[1].id] = {'asset_id': basset.id, 'coord': last}
            else:
                # TODO: Implement recursively
                bld_geom = None
                if building.geometry:
                    bld_geom = building.geometry
                elif building.containingBuilding:
                    if building.containingBuilding.geometry:
                        bld_geom = building.containingBuilding.geometry
                bld_coord = ()
                if bld_geom:
                    if isinstance(bld_geom, esdl.Point):
                        bld_coord = (bld_geom.lat, bld_geom.lon)
                    elif isinstance(bld_geom, esdl.Polygon):
                        bld_coord = ESDLGeometry.calculate_polygon_center(bld_geom)

                for p in ports:
                    mapping[p.id] = {'asset_id': basset.id, 'coord': bld_coord}


# FIXME: pyecore not necessary anymore
def create_port_to_asset_mapping(area, mapping):
    # process subareas
    for ar in area.area:
        create_port_to_asset_mapping(ar, mapping)

    # process assets in area
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            create_building_port_to_asset_mapping(asset, mapping)
        else:
            if isinstance(asset, esdl.EnergyAsset):
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


# ---------------------------------------------------------------------------------------------------------------------
#  Build up initial information about energysystem to send to browser
# ---------------------------------------------------------------------------------------------------------------------
def generate_point_in_area(boundary):
    return


def update_building_asset_geometries(building, avail_locations):
    for basset in building.asset:
        if isinstance(basset, esdl.EnergyAsset):
            geom = basset.geometry
            if not geom:
                location = avail_locations.pop(0)
                geom = esdl.Point(lon=location[1], lat=location[0])
                basset.geometry = geom


def update_area_asset_geometries(area, avail_locations):
    # process subareas
    for ar in area.area:
        update_area_asset_geometries(ar, avail_locations)

    # process assets in area
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            update_building_asset_geometries(asset, avail_locations)
        if isinstance(asset, esdl.EnergyAsset):
            geom = asset.geometry
            if not geom:
                location = avail_locations.pop(0)
                geom = esdl.Point()
                geom = esdl.Point(lon=location[1], lat=location[0])
                asset.geometry = geom


def count_building_assets_and_potentials(building):
    # TODO: Error: BuildingUnits are taken into account
    # TODO: add potentials
    num = len(building.asset)

    for basset in building.asset:
        if isinstance(basset, esdl.AbstractBuilding):
            num += count_building_assets_and_potentials(basset)

    return num


def count_assets_and_potentials(area):
    num = len(area.asset)
    num += len(area.potential)

    for ar_asset in area.asset:
        if isinstance(ar_asset, esdl.AbstractBuilding):
            num += count_building_assets_and_potentials(ar_asset)

    for ar in area.area:
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


def calc_center_and_size(coords):
    min_x = float("inf")
    min_y = float("inf")
    max_x = -float("inf")
    max_y = -float("inf")

    for c in coords:
        if c[0] < min_x: min_x = c[0]
        if c[1] < min_y: min_y = c[1]
        if c[0] > max_x: max_x = c[0]
        if c[1] > max_y: max_y = c[1]

    delta_x = max_x - min_x
    delta_y = max_y - min_y

    return [(min_x + max_x) / 2, (min_y + max_y) / 2], delta_x, delta_y


def calc_random_location_around_center(center, delta_x, delta_y, convert_RD_to_WGS):
    geom = esdl.Point()
    x = center[0] + ((-0.5 + random.random()) * delta_x / 2)
    y = center[1] + ((-0.5 + random.random()) * delta_y / 2)
    if convert_RD_to_WGS and (x > 180 or y > 180):  # Assume RD
        rdwgs = RDWGSConverter()
        wgs = rdwgs.fromRdToWgs([x, y])
        geom.lat = wgs[0]
        geom.lon = wgs[1]
    else:
        geom.lat = y
        geom.lon = x
    return geom


def calc_building_assets_location(building):
    """
    Calculate the locations of assets in buildings when they are not given
    The building editor uses a 500x500 pixel canvas
    Rules:
    - Assets of type AbstractConnection are placed in the left-most column
    - Other transport assets in the second column
    - Then production, conversion and storage
    - And finally demand
    """
    num_conns = 0
    num_transp = 0
    num_prod_conv_stor = 0
    num_cons = 0
    for basset in building.asset:
        if isinstance(basset, esdl.AbstractConnection):
            num_conns = num_conns + 1
        elif isinstance(basset, esdl.Transport):
            num_transp = num_transp + 1
        if isinstance(basset, esdl.Producer) or isinstance(basset, esdl.Conversion) or isinstance(basset, esdl.Storage):
            num_prod_conv_stor = num_prod_conv_stor + 1
        if isinstance(basset, esdl.Consumer):
            num_cons = num_cons + 1

    num_cols = 0
    if num_conns > 0: num_cols = num_cols + 1
    if num_transp > 0: num_cols = num_cols + 1
    if num_prod_conv_stor > 0: num_cols = num_cols + 1
    if num_cons > 0: num_cols = num_cols + 1

    if num_cols > 0:
        column_width = 500 / (num_cols + 1)
        column_idx = 1
        column_conns_x = int(num_conns > 0) * column_idx * column_width
        column_idx += (num_conns > 0)
        column_transp_x = int(num_transp> 0) * column_idx * column_width
        column_idx += (num_transp > 0)
        column_pcs_x = int(num_prod_conv_stor > 0) * column_idx * column_width
        column_idx += (num_prod_conv_stor > 0)
        column_cons_x = int(num_cons > 0) * column_idx * column_width
        column_idx += (num_cons > 0)

        row_conns_height = 500 / (num_conns + 1)
        row_transp_height = 500 / (num_transp + 1)
        row_pcs_height = 500 / (num_prod_conv_stor + 1)
        row_cons_height = 500 / (num_cons + 1)

        row_conns_idx = 1
        row_transp_idx = 1
        row_pcs_idx = 1
        row_cons_idx = 1

        for basset in building.asset:
            if not basset.geometry:
                if isinstance(basset, esdl.AbstractConnection):
                    basset.geometry = esdl.Point(lon=column_conns_x , lat=row_conns_idx * row_conns_height, CRS="Simple")
                    row_conns_idx = row_conns_idx + 1
                elif isinstance(basset, esdl.Transport):
                    basset.geometry = esdl.Point(lon=column_transp_x , lat=row_transp_idx * row_transp_height, CRS="Simple")
                    row_transp_idx = row_transp_idx + 1
                if isinstance(basset, esdl.Producer) or isinstance(basset, esdl.Conversion) or isinstance(basset, esdl.Storage):
                    basset.geometry = esdl.Point(lon=column_pcs_x , lat=row_pcs_idx * row_pcs_height, CRS="Simple")
                    row_pcs_idx = row_pcs_idx + 1
                if isinstance(basset, esdl.Consumer):
                    basset.geometry = esdl.Point(lon=column_cons_x, lat=row_cons_idx * row_cons_height, CRS="Simple")
                    row_cons_idx = row_cons_idx + 1


def update_asset_geometries3(area, boundary):
    if boundary:
        coords = boundary['coordinates']
        type = boundary['type']
        # print(coords)
        # print(type)

        if type == 'Polygon':
            outer_polygon = coords[0]       # Take exterior polygon
        elif type == 'MultiPolygon':
            outer_polygon = coords[0][0]    # Assume first polygon is most relevant and then take exterior polygon
        else:
            send_alert('Non supported polygon')

        center, delta_x, delta_y = calc_center_and_size(outer_polygon)
        # print(center)

    # TODO: An area with a building, with buildingunits (!) with assets is not supported yet
    for asset in area.asset:
        geom = asset.geometry
        if not geom and boundary:
            asset.geometry = calc_random_location_around_center(center, delta_x, delta_y, True)

        if isinstance(asset, esdl.AbstractBuilding):
            calc_building_assets_location(asset)

            # for asset2 in asset.asset:
            #     geom = asset2.geometry
            #     if not geom:
            #         # Building editor uses a 500x500 canvas
            #         asset2.geometry = calc_random_location_around_center([250,250], 500, 500, False)


def get_control_strategy_info(asset):
    control_strategy = asset.controlStrategy
    if control_strategy:
        cs_info = {
            'id': control_strategy.id,
            'name': control_strategy.name,
            'type': type(control_strategy).__name__
        }
        if isinstance(control_strategy, esdl.DrivenByDemand):
            if control_strategy.outPort:
                cs_info['out_port_id'] = control_strategy.outPort.id
        if isinstance(control_strategy, esdl.DrivenBySupply):
            if control_strategy.inPort:
                cs_info['in_port_id'] = control_strategy.inPort.id
        if isinstance(control_strategy, esdl.DrivenByProfile):
            if control_strategy.port:
                cs_info['port_id'] = control_strategy.port.id
            if control_strategy.profile:
                cs_info['profile_id'] = control_strategy.profile.id
        if isinstance(control_strategy, esdl.StorageStrategy):
            mcc, mdc = get_storage_marginal_costs(asset.id)
            cs_info['marginal_charge_costs'] = mcc
            cs_info['marginal_discharge_costs'] = mdc
        if isinstance(control_strategy, esdl.CurtailmentStrategy):
            cs_info['max_power'] = control_strategy.maxPower
        if isinstance(control_strategy, esdl.PIDController):
            cs_info['kp'] = control_strategy.Kp
            cs_info['ki'] = control_strategy.Ki
            cs_info['kd'] = control_strategy.Kd

        return cs_info
    else:
        return {}


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


def process_building(es_id, asset_list, building_list, area_bld_list, conn_list, port_asset_mapping, building, bld_editor, level):
    esh = get_handler()

    # Add building to list that is shown in a dropdown at the top
    area_bld_list.append(['Building', building.id, building.name, level])

    # Determine if building has assets
    building_has_assets = False
    if building.asset:
        for basset in building.asset:
            if isinstance(basset, esdl.EnergyAsset):
                building_has_assets = True
                break

    # Generate information for drawing building (as a point or a polygon)
    if isinstance(building, esdl.Building) or isinstance(building, esdl.AggregatedBuilding):
        geometry = building.geometry
        bld_KPIs = create_building_KPIs(building)
        if geometry:
            if isinstance(geometry, esdl.Point):
                building_list.append(
                    ['point', building.name, building.id, type(building).__name__, [geometry.lat, geometry.lon], building_has_assets, bld_KPIs])
                bld_coord = (geometry.lat, geometry.lon)
            elif isinstance(geometry, esdl.Polygon):
                coords = ESDLGeometry.parse_esdl_subpolygon(building.geometry.exterior, False)  # [lon, lat]
                coords = ESDLGeometry.exchange_coordinates(coords)  # --> [lat, lon]
                # building_list.append(['polygon', building.name, building.id, type(building).__name__, coords, building_has_assets])
                boundary = ESDLGeometry.create_boundary_from_geometry(geometry)
                building_list.append(['polygon', building.name, building.id, type(building).__name__, boundary['coordinates'], building_has_assets, bld_KPIs])
                # bld_coord = coords
                bld_coord = ESDLGeometry.calculate_polygon_center(geometry)
    elif building.containingBuilding:       # BuildingUnit
        bld_geom = building.containingBuilding.geometry
        if bld_geom:
            if isinstance(bld_geom, esdl.Point):
                bld_coord = (bld_geom.lat, bld_geom.lon)
            elif isinstance(bld_geom, esdl.Polygon):
                bld_coord = ESDLGeometry.calculate_polygon_center(bld_geom)

    # Iterate over all assets in building to gather all required information
    for basset in building.asset:
        if isinstance(basset, esdl.AbstractBuilding):
            process_building(es_id, asset_list, building_list, area_bld_list, conn_list, port_asset_mapping, basset, bld_editor, level + 1)
        else:
            # Create a list of ports for this asset
            port_list = []
            ports = basset.port
            for p in ports:
                conn_to = p.connectedTo
                conn_to_id_list = [ct.id for ct in conn_to]
                # TODO: add profile_info and carrier
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to_id_list})

            geom = basset.geometry
            coord = ()
            if geom:    # Individual asset in Building has its own geometry information
                if isinstance(geom, esdl.Point):
                    lat = geom.lat
                    lon = geom.lon
                    coord = (lat, lon)

                    capability_type = ESDLAsset.get_asset_capability_type(basset)
                    if bld_editor:
                        asset_list.append(['point', 'asset', basset.name, basset.id, type(basset).__name__, [lat, lon], port_list, capability_type])
                else:
                    send_alert("Assets within buildings with geometry other than esdl.Point are not supported")

            # Inherit geometry from containing building
            # if level > 0:
            #     coord = bld_coord

            ports = basset.port
            for p in ports:
                p_carr_id = None
                if p.carrier:
                    p_carr_id = p.carrier.id
                conn_to = p.connectedTo
                if conn_to:
                    for pc in conn_to:
                        in_different_buildings = False
                        pc_asset = port_asset_mapping[pc.id]
                        try:
                            pc_asset_real = esh.get_by_id(es_id, pc_asset['asset_id'])
                        except:
                            print("Exception occurred")
                            print("es_id: {}".format(es_id))
                            print("current building asset id: {}".format(basset.id))
                            print("connected-to-asset info: {}".format(pc_asset))
                            print("connected-to-asset ID: {}".format(pc_asset['asset_id']))
                            continue

                        # If the asset the current asset connects to, is in a building...
                        if pc_asset_real.containingBuilding:
                            bld_pc_asset = pc_asset_real.containingBuilding
                            bld_basset = basset.containingBuilding
                            # If the asset is in a different building ...
                            if not bld_pc_asset == bld_basset:
                                in_different_buildings = True
                                if bld_pc_asset.geometry:
                                    if bld_editor:
                                        # ... connect to the left border
                                        pc_asset_coord = (coord[0], 0)
                                    else:
                                        # ... use the building coordinate instead of the asset coordinate
                                        if isinstance(bld_pc_asset.geometry, esdl.Point):
                                            pc_asset_coord = (bld_pc_asset.geometry.lat, bld_pc_asset.geometry.lon)
                                        elif isinstance(bld_pc_asset.geometry, esdl.Polygon):
                                            pc_asset_coord = ESDLGeometry.calculate_polygon_center(bld_pc_asset.geometry)

                                    # If connecting to a building outside of the current, replace current asset
                                    # coordinates with building coordinates too
                                    if not bld_editor:
                                        coord = bld_coord
                            else:
                                # asset is in the same building, use asset's own coordinates
                                pc_asset_coord = pc_asset['coord']
                        else:
                            # other asset is not in a building
                            if bld_editor:
                                # ... connect to the left border
                                pc_asset_coord = (coord[0], 0)
                            else:
                                # ... just use asset's location
                                pc_asset_coord = pc_asset['coord']

                        pc_carr_id = None
                        if pc.carrier:
                            pc_carr_id = pc.carrier.id
                        # Add connections if we're editing a building or if the connection is between two different buildings
                        # ( The case of an asset in an area that is connected with an asset in a building is handled
                        #   in process_area (now all connections are added twice, from both sides) )
                        if bld_editor or in_different_buildings:
                            conn_list.append({'from-port-id': p.id, 'from-port-carrier': p_carr_id, 'from-asset-id': basset.id, 'from-asset-coord': coord,
                                'to-port-id': pc.id, 'to-port-carrier': pc_carr_id, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})


def process_area(es_id, asset_list, building_list, area_bld_list, conn_list, port_asset_mapping, area, level):
    esh = get_handler()

    area_bld_list.append(['Area', area.id, area.name, level])

    # process subareas
    for ar in area.area:
        process_area(es_id, asset_list, building_list, area_bld_list, conn_list, port_asset_mapping, ar, level+1)

    # process assets in area
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            process_building(es_id, asset_list, building_list, area_bld_list, conn_list, port_asset_mapping, asset, False, level+1)
        if isinstance(asset, esdl.EnergyAsset):
            port_list = []
            ports = asset.port
            for p in ports:
                p_asset = port_asset_mapping[p.id]
                p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
                conn_to_ids = [cp.id for cp in p.connectedTo]
                profile = p.profile
                profile_info_list = []
                p_carr_id = None
                if p.carrier:
                    p_carr_id = p.carrier.id
                if profile:
                    profile_info_list = generate_profile_info(profile)
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to_ids, 'profile': profile_info_list, 'carrier': p_carr_id})
                if conn_to_ids:
                    for pc in p.connectedTo:
                        pc_asset = port_asset_mapping[pc.id]
                        try:
                            pc_asset_real = esh.get_by_id(es_id, pc_asset['asset_id'])
                        except:
                            print("Exception occurred")
                            print("es_id: {}".format(es_id))
                            print("current asset id: {}".format(asset.id))
                            print("connected-to-asset info: {}".format(pc_asset))
                            print("connected-to-asset ID: {}".format(pc_asset['asset_id']))
                            continue
                        if pc_asset_real.containingBuilding:
                            bld_pc_asset = pc_asset_real.containingBuilding
                            if bld_pc_asset.geometry:
                                if isinstance(bld_pc_asset.geometry, esdl.Point):
                                    pc_asset_coord = (bld_pc_asset.geometry.lat, bld_pc_asset.geometry.lon)
                                elif isinstance(bld_pc_asset.geometry, esdl.Polygon):
                                    pc_asset_coord = ESDLGeometry.calculate_polygon_center(bld_pc_asset.geometry)
                        else:
                            pc_asset_coord = pc_asset['coord']

                        pc_carr_id = None
                        if pc.carrier:
                            pc_carr_id = pc.carrier.id
                        conn_list.append({'from-port-id': p.id, 'from-port-carrier': p_carr_id, 'from-asset-id': p_asset['asset_id'], 'from-asset-coord': p_asset_coord,
                                          'to-port-id': pc.id, 'to-port-carrier': pc_carr_id, 'to-asset-id': pc_asset['asset_id'], 'to-asset-coord': pc_asset_coord})

            geom = asset.geometry
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.lat
                    lon = geom.lon

                    capability_type = ESDLAsset.get_asset_capability_type(asset)
                    asset_list.append(['point', 'asset', asset.name, asset.id, type(asset).__name__, [lat, lon], port_list, capability_type])
                if isinstance(geom, esdl.Line):
                    coords = []
                    for point in geom.point:
                        coords.append([point.lat, point.lon])
                    asset_list.append(['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list])
                if isinstance(geom, esdl.Polygon):
                    # if isinstance(asset, esdl.WindParc) or isinstance(asset, esdl.PVParc) or isinstance(asset, esdl.WindPark) or isinstance(asset, esdl.PVPark):
                    coords = ESDLGeometry.parse_esdl_subpolygon(geom.exterior, False)   # [lon, lat]
                    coords = ESDLGeometry.exchange_coordinates(coords)                  # --> [lat, lon]
                    capability_type = ESDLAsset.get_asset_capability_type(asset)
                    # print(coords)
                    asset_list.append(['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list, capability_type])

    for potential in area.potential:
        geom = potential.geometry
        if geom:
            if isinstance(geom, esdl.Point):
                lat = geom.lat
                lon = geom.lon

                asset_list.append(
                    ['point', 'potential', potential.name, potential.id, type(potential).__name__, [lat, lon]])
            # if isinstance(geom, esdl.Polygon):
            #     coords = []
            #     for point in geom.point:
            #         coords.append([point.lat, point.lon])
            #     asset_list.append(['line', asset.name, asset.id, type(asset).__name__, coords, port_list])


def add_bld_to_area_bld_list(bld_to_add, to_area_or_bld_id, ab_list):
    # area_bld_list.append(['Building', building.id, building.name, level])
    for idx, rcv_ab in enumerate(ab_list):
        if rcv_ab[1] == to_area_or_bld_id:
            ab_list.insert(idx+1, ['Building', bld_to_add.id, bld_to_add.name, rcv_ab[3] + 1])


def add_area_to_area_bld_list(area_to_add, to_area_id, ab_list):
    # area_bld_list.append(['Area', area.id, area.name, level])
    for idx, rcv_ab in enumerate(ab_list):
        if rcv_ab[1] == to_area_id:
            ab_list.insert(idx+1, ['Area', area_to_add.id, area_to_add.name, rcv_ab[3] + 1])


def remove_ab_from_area_bld_list(ab_id, ab_list):
    for idx, ab in enumerate(ab_list):
        if ab[1] == ab_id:
            ab_list.pop(idx)
            return


def get_building_information(building):
    asset_list = []
    building_list = []
    bld_list = []
    conn_list = []

    active_es_id = get_session('active_es_id')
    port_to_asset_mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')

    process_building(active_es_id, asset_list, building_list, bld_list, conn_list, port_to_asset_mapping, building, True, 0)
    return {
        "id": building.id,
        "asset_list": asset_list,
        "building_list": building_list,
        "aera_bld_list": bld_list,
        "conn_list": conn_list
    }

# TODO: Not used now, should we keep the conn_list updated? --> Yes, now we do! For redrawing when selecting carriers
# 13-1-2020: Commented out: energycarrier info for port not added yet because function is not used at the moment.
#def add_connection_to_list(conn_list, from_port_id, from_asset_id, from_asset_coord, to_port_id, to_asset_id, to_asset_coord):
#    conn_list.append(
#        {'from-port-id': from_port_id, 'from-asset-id': from_asset_id, 'from-asset-coord': from_asset_coord,
#         'to-port-id': to_port_id, 'to-asset-id': to_asset_id, 'to-asset-coord': to_asset_coord})


def update_mapping(asset, coord):
    active_es_id = get_session('active_es_id')
    mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    ports = asset.port
    for p in ports:
        mapping[p.id] = {'asset_id': asset.id, 'coord': coord}
    # TODO: can be removed
    set_session_for_esid(active_es_id, 'port_to_asset_mapping', mapping)


def update_asset_connection_locations(ass_id, lat, lon):
    active_es_id = get_session('active_es_id')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')
    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            c['from-asset-coord'] = (lat, lon)
        if c['to-asset-id'] == ass_id:
            c['to-asset-coord'] = (lat, lon)

    emit('clear_connections')   # clear current active layer connections
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})
    # TODO: can be removed
    set_session_for_esid(active_es_id, 'conn_list', conn_list)


def update_transport_connection_locations(ass_id, asset, coords):
    active_es_id = get_session('active_es_id')
    mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')

    # print('Updating locations')
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

    # TODO: es.id?
    emit('clear_connections')   # clear current active layer connections
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})

    set_session_for_esid(active_es_id, 'conn_list', conn_list)


def update_polygon_asset_connection_locations(ass_id, coords):
    active_es_id = get_session('active_es_id')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')
    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            c['from-asset-coord'] = coords
        if c['to-asset-id'] == ass_id:
            c['to-asset-coord'] = coords

    emit('clear_connections')   # clear current active layer connections
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})

    set_session_for_esid(active_es_id, 'conn_list', conn_list)


# mapping[ports[1].id] = {'asset_id': asset.id, 'coord': last, 'pos': 'last'}




# ---------------------------------------------------------------------------------------------------------------------
#  Get connections information for an asset
# ---------------------------------------------------------------------------------------------------------------------
def get_connected_to_info(asset):
    #mapping = session['port_to_asset_mapping']
    #asset_dict = session['asset_dict']
    #print(asset_dict)
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
                ct_list.append({'pid': conn_port.id, 'aid': conn_asset.id, 'atype': type(conn_asset).__name__, 'aname': conn_asset.name})

        result.append({'pid': p.id, 'ptype': ptype, 'pname': p.name, 'pcarr': pcarr, 'ct_list': ct_list})
    #print(result)
    return result


# ---------------------------------------------------------------------------------------------------------------------
#  Create connections between assets
# ---------------------------------------------------------------------------------------------------------------------
def connect_ports(port1, port2):
    port1.connectedTo.append(port2)

    # port1conn = port1.connectedTo
    # port2conn = port2.connectedTo
    # if port1conn:
    #     port1.set_connectedTo(port1conn + ' ' + port2.id)
    # else:
    #     port1.set_connectedTo(port2.id)
    # if port2conn:
    #     port2.set_connectedTo(port2conn + ' ' + port1.id)
    # else:
    #     port2.set_connectedTo(port1.id)


# def connect_asset_with_conductor(asset, conductor):
#     conn_list = get_session("conn_list")
#     es_id = get_session("es_id")
#
#     asset_geom = asset.geometry
#     cond_geom = conductor.geometry
#
#     if isinstance(cond_geom, esdl.Line):
#         points = cond_geom.point
#         first_point = points[0]
#         last_point = points[len(points) - 1]
#     else:
#         send_alert('UNSUPPORTED - conductor geometry is not a Line')
#         return
#
#     if not isinstance(asset_geom, esdl.Point):
#         send_alert('UNSUPPORTED - asset geometry is not a Point')
#         return
#
#     if (distance((asset_geom.lat, asset_geom.lon), (first_point.lat, first_point.lon)) <
#             distance((asset_geom.lat, asset_geom.lon), (last_point.lat, last_point.lon))):
#         # connect asset with first_point of conductor
#
#         cond_port = conductor.port[0]
#         for p in asset.port:
#             if not type(p).__name__ == type(cond_port).__name__:
#                 print('connect asset with first_point')
#                 connect_ports(p, cond_port)
#                 emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset_geom.lat,asset_geom.lon],[first_point.lat,first_point.lon]]})
#                 conn_list.append(
#                     {'from-port-id': p.id, 'from-asset-id': asset.id,
#                      'from-asset-coord': [asset_geom.lat,asset_geom.lon],
#                      'to-port-id': cond_port.id, 'to-asset-id': conductor.id,
#                      'to-asset-coord': [first_point.lat,first_point.lon]})
#
#     else:
#         # connect asset with last_point of conductor
#
#         cond_port = conductor.port[1]
#         for p in asset.port:
#             if not type(p).__name__ == type(cond_port).__name__:
#                 print('connect asset with last_point')
#                 connect_ports(p, cond_port)
#                 emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset_geom.lat, asset_geom.lon], [last_point.lat, last_point.lon]]})
#                 conn_list.append(
#                     {'from-port-id': p.id, 'from-asset-id': asset.id,
#                      'from-asset-coord': [asset_geom.lat, asset_geom.lon],
#                      'to-port-id': cond_port.id, 'to-asset-id': conductor.id,
#                      'to-asset-coord': [last_point.lat, last_point.lon]})
#
#     set_session("conn_list", conn_list)


# def connect_asset_with_asset(asset1, asset2):
#     conn_list = get_session("conn_list")
#     es_id = get_session("es_id")
#
#     ports1 = asset1.port
#     num_ports1 = len(ports1)
#     asset1_geom = asset1.geometry
#     ports2 = asset2.port
#     num_ports2 = len(ports2)
#     asset2_geom = asset2.geometry
#
#     if not isinstance(asset1_geom, esdl.Point) or not isinstance(asset2_geom, esdl.Point):
#         send_alert('UNSUPPORTED - asset geometry is not a Point')
#         return
#
#     if num_ports1 == 1:
#         found = None
#         if isinstance(ports1[0], esdl.OutPort):
#             # find InPort on other asset
#             for p in ports2:
#                 if isinstance(p, esdl.InPort):
#                     # connect p and ports1[0]
#                     print('connect p and ports1[0]')
#                     connect_ports(p, ports1[0])
#                     p1 = ports1[0]
#                     p2 = p
#                     emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset1_geom.lat, asset1_geom.lon],
#                           [asset2_geom.lat, asset2_geom.lon]]})
#                     found = 1
#             if not found:
#                 send_alert('UNSUPPORTED - No InPort found on asset2')
#                 return
#         else:
#             # find OutPort on other asset
#             for p in ports2:
#                 if isinstance(p, esdl.OutPort):
#                     # connect p and ports1[0]
#                     print('connect p and ports1[0]')
#                     connect_ports(p, ports1[0])
#                     p1 = ports1[0]
#                     p2 = p
#                     emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset1_geom.lat, asset1_geom.lon],
#                           [asset2_geom.lat, asset2_geom.lon]]})
#                     found = 1
#             if not found:
#                 send_alert('UNSUPPORTED - No OutPort found on asset2')
#                 return
#     elif num_ports2 == 1:
#         found = None
#         if isinstance(ports2[0], esdl.OutPort):
#             # find InPort on other asset
#             for p in ports1:
#                 if isinstance(p, esdl.InPort):
#                     # connect p and ports2[0]
#                     print('connect p and ports2[0]')
#                     connect_ports(p, ports2[0])
#                     p1 = p
#                     p2 = ports2[0]
#                     emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset1_geom.lat, asset1_geom.lon],
#                           [asset2_geom.lat, asset2_geom.lon]]})
#                     found = 1
#             if not found:
#                 send_alert('UNSUPPORTED - No InPort found on asset1')
#                 return
#         else:
#             # find OutPort on other asset
#             for p in ports1:
#                 if isinstance(p, esdl.OutPort):
#                     # connect p and ports2[0]
#                     print('connect p and ports2[0]')
#                     connect_ports(p, ports2[0])
#                     p1 = p
#                     p2 = ports2[0]
#                     emit('add_new_conn', {'es_id': es_id, 'new_conn': [[asset1_geom.lat, asset1_geom.lon],
#                           [asset2_geom.lat, asset2_geom.lon]]})
#                     found = 1
#             if not found:
#                 send_alert('UNSUPPORTED - No OutPort found in asset1')
#                 return
#     else:
#         send_alert('UNSUPPORTED - Cannot determine what ports to connect')
#         return
#
#     if found:
#         conn_list.append(
#             {'from-port-id': p1.id, 'from-asset-id': asset1.id,
#              'from-asset-coord': [asset1_geom.lat, asset1_geom.lon],
#              'to-port-id': p2.id, 'to-asset-id': asset2.id,
#              'to-asset-coord': [asset2_geom.lat, asset2_geom.lon]})
#
#     set_session("conn_list", conn_list)


# def connect_conductor_with_conductor(conductor1, conductor2):
#     conn_list = get_session("conn_list")
#     es_id = get_session("es_id")
#
#     c1points = conductor1.geometry.point
#     c1p0 = c1points[0]
#     c1p1 = c1points[len(c1points) - 1]
#     c2points = conductor2.geometry.point
#     c2p0 = c2points[0]
#     c2p1 = c2points[len(c2points) - 1]
#
#     dp = []
#     dp.append(distance((c1p0.lat,c1p0.lon),(c2p0.lat,c2p0.lon)))
#     dp.append(distance((c1p0.lat,c1p0.lon),(c2p1.lat,c2p1.lon)))
#     dp.append(distance((c1p1.lat,c1p1.lon),(c2p0.lat,c2p0.lon)))
#     dp.append(distance((c1p1.lat,c1p1.lon),(c2p1.lat,c2p1.lon)))
#
#     smallest = 0
#     for i in range(1,3):
#         if dp[i] < dp[smallest]:
#             smallest = i
#
#     if smallest == 0:
#         conn1 = conductor1.port[0]
#         conn2 = conductor2.port[0]
#         conn_pnt1 = c1p0
#         conn_pnt2 = c2p0
#     elif smallest == 1:
#         conn1 = conductor1.port[0]
#         conn2 = conductor2.port[1]
#         conn_pnt1 = c1p0
#         conn_pnt2 = c2p1
#     elif smallest == 2:
#         conn1 = conductor1.port[1]
#         conn2 = conductor2.port[0]
#         conn_pnt1 = c1p1
#         conn_pnt2 = c2p0
#     elif smallest == 3:
#         conn1 = conductor1.port[1]
#         conn2 = conductor2.port[1]
#         conn_pnt1 = c1p1
#         conn_pnt2 = c2p1
#
#     if not type(conn1).__name__ == type(conn2).__name__:
#         connect_ports(conn1, conn2)
#         emit('add_new_conn',
#              {'es_id': es_id, 'new_conn': [[conn_pnt1.lat, conn_pnt1.lon], [conn_pnt2.lat, conn_pnt2.lon]]})
#         conn_list.append(
#             {'from-port-id': conn1.id, 'from-asset-id': conductor1.id,
#              'from-asset-coord': [conn_pnt1.lat, conn_pnt1.lon],
#              'to-port-id': conn2.id, 'to-asset-id': conductor2.id,
#              'to-asset-coord': [conn_pnt2.lat, conn_pnt2.lon]})
#
#         set_session("conn_list", conn_list)
#     else:
#         send_alert('UNSUPPORTED - Cannot connect two ports of same type')


# def get_potential_attributes(potential):
#     potential_attrs = copy.deepcopy(vars(potential))
#     # method_list = [func for func in dir(potential) if callable(getattr(potential, func)) and func.startswith("set_")]
#
#     # TODO: check which attributes must be filtered (cannot be easily edited)
#     if 'geometry' in potential_attrs:
#         potential_attrs.pop('geometry', None)
#     if 'dataSource' in potential_attrs:
#         potential_attrs.pop('dataSource', None)
#     if 'quantityAndUnit' in potential_attrs:
#         potential_attrs.pop('quantityAndUnit', None)
#
#     attrs_sorted = sorted(potential_attrs.items(), key=lambda kv: kv[0])
#     return attrs_sorted



def split_conductor(conductor, location, mode, conductor_container):
    active_es_id = get_session('active_es_id')
    mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')
    #asset_dict = session['asset_dict']
    esh = get_handler()

    geometry = conductor.geometry
    conductor_type = type(conductor).__name__
    conductor_id = conductor.id
    middle_point = esdl.Point(lat=location['lat'], lon=location['lng']) #no elevation?

    if isinstance(geometry, esdl.Line):
        #create two seperate line segments
        line1 = esdl.Line()
        line2 = esdl.Line()

        #find piece of line where user clicked
        points = geometry.point
        begin_point = points[0]
        first_point = points[0] # make an additional copy
        # Ewoud: this code is not so nice since it manipulates the original geometry.point with points.pop(0) later on
        # this should be fixed, but not now (not time)

        # pyEcore: somehow using points[0] does something strange in the serialization to XML
        # instead of <point xsi:type="esdl:Point"> you get <esdl:Point lat=...> which is wrong
        # duplicating this point manually fixes this, probably because there is a reference to this point
        # elsewhere which gets serialized as an <esdl:Point>
        # officially we should duplicate all Point in this code
        line1.point.append(esdl.Point(lat=begin_point.lat, lon=begin_point.lon, elevation=begin_point.elevation))

        points.pop(0)
        min_dist = 1e99
        segm_ctr = 0
        min_dist_segm = 0
        for point in points:
            p1 = {'x': begin_point.lat, 'y': begin_point.lon}
            p2 = {'x': point.lat, 'y': point.lon}
            p =  {'x': location['lat'], 'y': location['lng']}
            dist = ESDLGeometry.distance_point_to_line(p, p1, p2)
            if dist < min_dist:
                min_dist = dist
                min_dist_segm = segm_ctr
            begin_point = point
            segm_ctr += 1

        # copy appropriate points in original conductor to either line1 or line2
        points = geometry.point
        segm_ctr = 0
        print('segment min = {}'.format(min_dist_segm))
        for point in points:
            if segm_ctr == min_dist_segm:
                new_point = esdl.Point(lon=middle_point.lon, lat=middle_point.lat, elevation=middle_point.elevation);
                line1.point.append(new_point)
                line2.point.append(new_point.clone())
            if segm_ctr < min_dist_segm:
                line1.point.append(point)
                prev_point = point
            else:
                line2.point.append(point)
            segm_ctr += 1

        end_point = point


        #find old ports and connections
        ports = conductor.port
        if len(ports) != 2:
            send_alert('UNSUPPORTED: Conductor doesn\'t have two ports!')
            return
        port1 = ports[0]        # reuse old conductor's ports; TODO: check what happens after deleting conductor
        port2 = ports[1]

        new_cond1_id = str(uuid.uuid4())
        new_cond2_id = str(uuid.uuid4())
        new_port1_id = str(uuid.uuid4())
        new_port2_id = str(uuid.uuid4())

        # create two conductors of same type as conductor that is splitted
        module = importlib.import_module('esdl.esdl')
        class_ = getattr(module, conductor_type)
        new_cond1 = class_(id=new_cond1_id, name=conductor.name + '_a')
        new_cond2 = class_(id=new_cond2_id, name=conductor.name + '_b')
        esh.add_object_to_dict(active_es_id, new_cond1)
        esh.add_object_to_dict(active_es_id, new_cond2)

        if type(port1).__name__ == "InPort":
            new_port2 = esdl.OutPort(id=new_port2_id, name='Out')
        else:
            new_port2 = esdl.InPort(id=new_port2_id, name='In')

        new_cond1.port.append(port1)
        new_cond1.port.append(new_port2)

        if type(port2).__name__ == "InPort":
            new_port1 = esdl.OutPort(id=new_port1_id, name='Out')
        else:
            new_port1 = esdl.InPort(id=new_port1_id, name='In')
        if mode == 'connect':
            new_port1.connectedTo.append(new_port2)
            new_port2.connectedTo.append(new_port1)
        new_cond2.port.append(new_port1)
        new_cond2.port.append(port2)

        esh.add_object_to_dict(active_es_id, new_port1)
        esh.add_object_to_dict(active_es_id, new_port2)

        # calculate line lengths
        start = line1.point[0]
        length = 0
        for i in range(1, len(line1.point)):
            length += ESDLGeometry.distance((start.lat, start.lon), (line1.point[i].lat, line1.point[i].lon)) * 1000
            start = line1.point[i]
        new_cond1.length = length

        start = line2.point[0]
        length = 0
        for i in range(1, len(line2.point)):
            length += ESDLGeometry.distance((start.lat, start.lon), (line2.point[i].lat, line2.point[i].lon)) * 1000
            start = line2.point[i]
        new_cond2.length = length

        print('split-conductor: line1 length={}, line2 length={}'.format(new_cond1.length, new_cond2.length))
        # assign line geometry to the correct conductor
        new_cond1.geometry = line1
        new_cond2.geometry = line2

        # remove conductor from container (area or building) and add new two conductors
        assets = conductor_container.asset
        assets.remove(conductor)
        conductor_container.asset.append(new_cond1)
        conductor_container.asset.append(new_cond2)

        # update port asset mappings for conductors
        mapping[port1.id] = {'asset_id': new_cond1_id, 'coord': (first_point.lat, first_point.lon), 'pos': 'first'}
        mapping[new_port2.id] = {'asset_id': new_cond1_id, 'coord': (middle_point.lat, middle_point.lon), 'pos': 'last'}
        mapping[new_port1.id] = {'asset_id': new_cond2_id, 'coord': (middle_point.lat, middle_point.lon), 'pos': 'first'}
        mapping[port2.id] = {'asset_id': new_cond2_id, 'coord': (end_point.lat, end_point.lon), 'pos': 'last'}

        # create list of ESDL assets to be added to UI
        esdl_assets_to_be_added = []
        coords1 = []
        for point in line1.point:
            coords1.append([point.lat, point.lon])
        port_list = []
        for p in new_cond1.port:
            port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
        esdl_assets_to_be_added.append(['line', 'asset', new_cond1.name, new_cond1.id, type(new_cond1).__name__, coords1, port_list])
        coords2 = []
        for point in line2.point:
            coords2.append([point.lat, point.lon])
        port_list = []
        for p in new_cond2.port:
            port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
        esdl_assets_to_be_added.append(['line', 'asset', new_cond2.name, new_cond2.id, type(new_cond2).__name__, coords2, port_list])

        # update asset id's of conductor with new_cond1 and new_cond2 in conn_list
        for c in conn_list:
            if c['from-asset-id'] == conductor_id and c['from-port-id'] == port1.id:
                c['from-asset-id'] = new_cond1_id
            if c['from-asset-id'] == conductor_id and c['from-port-id'] == port2.id:
                c['from-asset-id'] = new_cond2_id
            if c['to-asset-id'] == conductor_id and c['to-port-id'] == port1.id:
                c['to-asset-id'] = new_cond1_id
            if c['to-asset-id'] == conductor_id and c['to-port-id'] == port2.id:
                c['to-asset-id'] = new_cond2_id

        # create list of connections to be added to UI
        if mode == 'connect':
            conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': None, 'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                          'to-port-id': new_port1_id, 'to-port-carrier': None, 'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})

        if mode == 'add_joint':
            joint_id = str(uuid.uuid4())
            joint = esdl.Joint(id=joint_id, name='Joint_'+joint_id[:4])
            inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
            outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')

            if type(new_port2).__name__ == "OutPort":
                inp.connectedTo.append(new_port2)
                new_port2_conn_to_id = inp.id
            else:
                outp.connectedTo.append(new_port2)
                new_port2_conn_to_id = outp.id

            if type(new_port1).__name__ == "InPort":
                outp.connectedTo.append(new_port1)
                new_port1_conn_to_id = outp.id
            else:
                inp.connectedTo.append(new_port1)
                new_port1_conn_to_id = inp.id

            joint.port.append(inp)
            joint.port.append(outp)
            joint.geometry = middle_point
            conductor_container.asset.append(joint)
            esh.add_object_to_dict(active_es_id, joint)
            esh.add_object_to_dict(active_es_id, inp)
            esh.add_object_to_dict(active_es_id, outp)

            # Change port asset mappings
            mapping[inp.id] = {'asset_id': joint.id, 'coord': (middle_point.lat, middle_point.lon)}
            mapping[outp.id] = {'asset_id': joint.id, 'coord': (middle_point.lat, middle_point.lon)}

            port_list = []
            for p in joint.port:
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
            capability_type = ESDLAsset.get_asset_capability_type(joint)
            esdl_assets_to_be_added.append(['point', 'asset', joint.name, joint.id, type(joint).__name__, [middle_point.lat, middle_point.lon], port_list, capability_type])

            conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': None, 'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                          'to-port-id': new_port2_conn_to_id, 'to-port-carrier': None, 'to-asset-id': joint.id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})
            conn_list.append({'from-port-id': new_port1_conn_to_id, 'from-port-carrier': None, 'from-asset-id': joint.id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                          'to-port-id': new_port1_id, 'to-port-carrier': None, 'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})

        # now send new objects to UI
        emit('add_esdl_objects', {'es_id': active_es_id, 'asset_pot_list': esdl_assets_to_be_added, 'zoom': False})
        emit('clear_connections')   # clear current active layer connections
        emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})

        set_session_for_esid(active_es_id, 'port_to_asset_mapping', mapping)
        set_session_for_esid(active_es_id, 'conn_list', conn_list)
    else:
        send_alert('UNSUPPORTED: Conductor is not of type esdl.Line!')


# ---------------------------------------------------------------------------------------------------------------------
#  Update ESDL coordinates on movement of assets in browser
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('update-coord', namespace='/esdl')
def update_coordinates(message):
    # print("updating coordinates")
    # print('received: ' + str(message['id']) + ':' + str(message['lat']) + ',' + str(message['lng']) + ' - ' + str(message['asspot']))

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    es_edit = esh.get_energy_system(es_id=active_es_id)
    instance = es_edit.instance
    area = instance[0].area
    obj_id = message['id']

    if message['asspot'] == 'asset' or message['asspot'] == 'building':
        # fixme pyEcore: use get_by_id here (faster)
        # TODO: apparently assets are not always found when importing GEIS data
        asset = ESDLAsset.find_asset(area, obj_id)

        if asset:
            geom = asset.geometry
            if isinstance(geom, esdl.Point):
                point = esdl.Point(lon=float(message['lng']), lat=float(message['lat']))
                asset.geometry = point
            # elif isinstance(geom, esdl.Polygon):
                # Do nothing in case of a polygon
                # only update the connection locations and mappings based on the center of the polygon
                # that is given as a parameter.

        # Update locations of connections on moving assets
        update_asset_connection_locations(obj_id, message['lat'], message['lng'])
        update_mapping(asset, (message['lat'], message['lng']))
        if message['asspot'] == 'building':
            send_alert("Assets in building with locations are not updated yet")
    else:
        potential = ESDLAsset.find_potential(area, obj_id)
        if potential:
            point = esdl.Point(lon=float(message['lng']), lat=float(message['lat']))
            potential.geometry = point

    set_handler(esh)


@socketio.on('update-line-coord', namespace='/esdl')
def update_line_coordinates(message):
    # print ('received polyline: ' + str(message['id']) + ':' + str(message['polyline']))
    ass_id = message['id']

    active_es_id = get_session('active_es_id')
    port_to_asset_mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    esh = get_handler()
    es_edit = esh.get_energy_system(es_id=active_es_id)
    instance = es_edit.instance
    area = instance[0].area
    asset = ESDLAsset.find_asset(area, ass_id)

    if asset:
        ports = asset.port
        first_port = ports[0]
        last_port = ports[1]

        polyline_data = message['polyline']
        # print(polyline_data)
        # print(type(polyline_data))
        polyline_length = float(message['length'])
        asset.length = polyline_length

        line = esdl.Line()
        for i in range(0, len(polyline_data)):
            coord = polyline_data[i]

            point = esdl.Point(lon=coord['lng'], lat=coord['lat'])
            line.point.append(point)

            if i == 0:
                port_to_asset_mapping[first_port.id] = {'asset_id': asset.id, 'coord': (coord['lat'], coord['lng']), 'pos': 'first'}
            if i == len(polyline_data)-1:
                port_to_asset_mapping[last_port.id] = {'asset_id': asset.id, 'coord': (coord['lat'], coord['lng']), 'pos': 'last'}

        asset.geometry = line

        update_transport_connection_locations(ass_id, asset, polyline_data)

    set_handler(esh)    # TODO: required?
    set_session_for_esid(active_es_id, 'port_to_asset_mapping', port_to_asset_mapping)


@socketio.on('update-polygon-coord', namespace='/esdl')
def update_polygon_coordinates(message):
    # print ('received polygon: ' + str(message['id']) + ':' + str(message['polygon']))
    ass_id = message['id']

    active_es_id = get_session('active_es_id')
    port_to_asset_mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    esh = get_handler()
    es_edit = esh.get_energy_system(es_id=active_es_id)
    instance = es_edit.instance
    area = instance[0].area
    asset = ESDLAsset.find_asset(area, ass_id)

    if asset:
        polygon_data = message['polygon']
        # print(polygon_data)
        # print(type(polygon_data))
        polygon_area = int(message['polygon_area'])
        asset.surfaceArea = polygon_area

        polygon_data = ESDLGeometry.remove_duplicates_in_polygon(polygon_data)
        polygon_data = ESDLGeometry.remove_latlng_annotation_in_array_of_arrays(polygon_data)
        polygon_data = ESDLGeometry.exchange_polygon_coordinates(polygon_data)  # --> [lon, lat]
        polygon = ESDLGeometry.convert_pcoordinates_into_polygon(polygon_data)  # expects [lon, lat]
        asset.geometry = polygon

        polygon_center = ESDLGeometry.calculate_polygon_center(polygon)

        port_to_asset_mapping[asset.port[0].id] = {'asset_id': asset.id, 'coord': polygon_center}
        update_polygon_asset_connection_locations(ass_id, polygon_center)

    set_handler(esh)    # TODO: required?
    set_session_for_esid(active_es_id, 'port_to_asset_mapping', port_to_asset_mapping)


# ---------------------------------------------------------------------------------------------------------------------
#  Get boundary information
#
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('get_boundary_info', namespace='/esdl')
def get_boundary_info(info):
    print('get_boundary_info:')
    print(info)
    identifier = info["identifier"]
    toparea_name = info["toparea_name"]
    scope = info["scope"]
    subscope_enabled = info["subscope_enabled"]
    subscope = info["subscope"]
    select_subareas = info["select_subareas"]
    selected_subareas = info["selected_subareas"]
    initialize_ES = info["initialize_ES"]
    add_boundary_to_ESDL = info["add_boundary_to_ESDL"]

    if not is_valid_boundary_id(identifier):
        send_alert("Not a valid identifier. Try identifiers like PV27(Noord-Holland) or GM0060 (Ameland)")
        return

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    es_edit = esh.get_energy_system(es_id=active_es_id)
    instance = es_edit.instance
    area = instance[0].area

    area_list = []
    boundary = None
    if subscope_enabled:
        preload_subboundaries_in_cache(esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                       esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                       str.upper(identifier))
    else:
        boundary = get_boundary_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
        if boundary:
            geom = boundary['geom']
            # geometry = ESDLGeometry.create_geometry_from_geom()

            for i in range(0, len(geom['coordinates'])):
                if len(geom['coordinates']) > 1:
                    area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                else:
                    area_id_number = ""
                area_list.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": geom['coordinates'][i]
                    },
                    "properties": {
                        "id": area.id + area_id_number,
                        "name": area.name,
                        "KPIs": []
                    }
                })

    if initialize_ES:
        # change ID, name and scope of ES

        if select_subareas:
            area.id = "part of " + identifier
        else:
            area.id = identifier
        area.scope = esdl.AreaScopeEnum.from_string(str.upper(scope))
        area.name = toparea_name
        if add_boundary_to_ESDL:
            # returns boundary: { type: '', boundary: [[[[ ... ]]]] } (multipolygon in RD)
            if not boundary:    # check if already requested
                boundary = get_boundary_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
            if boundary:
                geometry = ESDLGeometry.create_geometry_from_geom(boundary['geom'])
                area.geometry = geometry

            # boundary = get_boundary_from_service(area_scope, area_id)
            # if boundary:
            #    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})

    if subscope_enabled:
        boundaries = get_subboundaries_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                                esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                                str.upper(identifier))
        # result (boundaries) is an ARRAY of:
        # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
        # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

        if not boundaries:
            send_alert('Error processing boundary information or no boundary information returned')

        for boundary in boundaries:
            geom = None
            try:
                # geom = json.loads(boundary["geom"])
                geom = boundary["geom"]
            except Exception as e:
                print('Error parsing JSON from GEIS boundary service: '+ str(e))

            if geom:
                # print('boundary["geom"]: ')
                # print(boundary["geom"])
                # print(boundary)

                skip_subarea = False
                if select_subareas and selected_subareas and boundary["code"] not in selected_subareas:
                    skip_subarea = True

                if not skip_subarea:
                    sub_area_id = boundary["code"]
                    sub_area_name = boundary["name"]

                    if initialize_ES:
                        sub_area = esdl.Area()
                        sub_area.id = sub_area_id
                        sub_area.name = sub_area_name
                        sub_area.scope = esdl.AreaScopeEnum.from_string(str.upper(subscope))

                        if add_boundary_to_ESDL:
                            geometry = ESDLGeometry.create_geometry_from_geom(geom)
                            sub_area.geometry = geometry

                        area.area.append(sub_area)
                        esh.add_object_to_dict(active_es_id, sub_area)

                    # print({'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': json.loads(geom)})
                    # boundary = create_boundary_from_contour(area_contour)
                    # emit('area_boundary', {'crs': 'WGS84', 'boundary': boundary})

                    # emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': geom, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

                    for i in range(0, len(geom['coordinates'])):
                        if len(geom['coordinates']) > 1:
                            area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                        else:
                            area_id_number = ""
                        area_list.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": geom['coordinates'][i]
                            },
                            "properties": {
                                "id": sub_area_id + area_id_number,
                                "name": sub_area_name,
                                "KPIs": []
                            }
                        })

    emit('geojson', {"layer": "area_layer", "geojson": area_list})

    print('Ready processing boundary information')

    set_handler(esh)


# ---------------------------------------------------------------------------------------------------------------------
#  Control Strategies
# ---------------------------------------------------------------------------------------------------------------------
def get_control_strategies(es):
    strategies = []
    services = es.services
    if services:
        services_list = services.service
        for service in services_list:
            if isinstance(service, esdl.ControlStrategy):
                strategies.append(service)
    return strategies


def get_control_strategy_for_asset(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    return asset.controlStrategy

    # strategies = get_control_strategies(es)
    # for strategy in strategies:
    #     cs_a = strategy.energyAsset
    #     if cs_a.id == asset_id:
    #         return strategy
    # return None


def add_control_strategy_for_asset(asset_id, cs):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    es = esh.get_energy_system(es_id=active_es_id)

    services = es.services
    if not services:
        services = esdl.Services()
        es.services = services

    services_list = services.service
    for service in set(services_list):
        if isinstance(service, esdl.ControlStrategy):
            if service.energyAsset.id == asset_id:
                services_list.remove(service)

    services.service.append(cs)


def add_drivenby_control_strategy_for_asset(asset_id, control_strategy, port_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()

    module = importlib.import_module('esdl.esdl')
    class_ = getattr(module, control_strategy)
    cs = class_()

    asset = esh.get_by_id(active_es_id, asset_id)
    asset_name = asset.name
    if not asset_name:
        asset_name = 'unknown'

    cs.id = str(uuid.uuid4())
    cs.name = control_strategy + ' for ' + asset_name
    cs.energyAsset = asset

    if control_strategy == 'DrivenByDemand':
        cs.outPort = next((p for p in esdl.Port.allInstances() if p.id == port_id), None)
    if control_strategy == 'DrivenBySupply':
        cs.inPort = next((p for p in esdl.Port.allInstances() if p.id == port_id), None)

    add_control_strategy_for_asset(asset_id, cs)


def add_storage_control_strategy_for_asset(asset_id, mcc, mdc):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    if not asset.name:
        asset.name = 'Unknown Asset'

    cs = esdl.StorageStrategy()
    cs.id = str(uuid.uuid4())
    cs.name = 'StorageStrategy for ' + asset.name
    cs.energyAsset = asset

    mcc_sv = esdl.SingleValue(id=str(uuid.uuid4()), name='marginalChargeCosts for ' + asset.name, value=str2float(mcc))
    cs.marginalChargeCosts = mcc_sv

    mdc_sv = esdl.SingleValue(id=str(uuid.uuid4()), name='marginalChargeCosts for ' + asset.name, value=str2float(mdc))
    cs.marginalDischargeCosts = mdc_sv

    add_control_strategy_for_asset(asset_id, cs)


def add_curtailment_control_strategy_for_asset(asset_id, max_power):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    if not asset.name:
        asset.name = 'Unknown Asset'

    cs = esdl.CurtailmentStrategy()
    cs.id = str(uuid.uuid4())
    cs.name = 'CurtailmentStrategy for ' + asset.name
    cs.energyAsset = asset

    cs.maxPower = str2float(max_power)

    add_control_strategy_for_asset(asset_id, cs)


def get_storage_marginal_costs(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    es = esh.get_energy_system(es_id=active_es_id)

    services = es.services
    if services:
        services_list = services.service
        for service in services_list:
            if isinstance(service, esdl.StorageStrategy):
                if service.energyAsset == asset:
                    mcc_sv = service.marginalChargeCosts
                    mdc_sv = service.marginalDischargeCosts
                    if mcc_sv:
                        mcc = mcc_sv.value
                    else:
                        mcc = 0
                    if mdc_sv:
                        mdc = mdc_sv.value
                    else:
                        mdc = 0
                    return mcc, mdc

    return 0, 0


def get_curtailment_max_power(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    es = esh.get_energy_system(es_id=active_es_id)

    services = es.services
    if services:
        services_list = services.service
        for service in services_list:
            if isinstance(service, esdl.CurtailmentStrategy):
                if service.energyAsset == asset:
                    return service.maxPower

    return 0


def remove_control_strategy_for_asset(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    cs = asset.controlStrategy
    if cs:
        cs.delete()

    #services_collection = es.services
    #if services_collection:
    #    services = services_collection.service
    #    for service in services:
    #        if isinstance(service, esdl.ControlStrategy):
    #            if service.energyAsset == asset_id:
    #                services.remove(service)


# ---------------------------------------------------------------------------------------------------------------------
#  Marginal Costs
# ---------------------------------------------------------------------------------------------------------------------
def set_marginal_costs_for_asset(asset_id, marginal_costs):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    asset_name = asset.name
    if not asset_name:
        asset_name = asset.id

    ci = asset.costInformation
    if not ci:
        ci = esdl.CostInformation()
        asset.costInformation = ci

    mc = ci.marginalCosts
    if not mc:
        mc = esdl.SingleValue()
        mc.id = str(uuid.uuid4())
        mc.name = asset_name + '-MarginalCosts'
        ci.marginalCosts = mc

    mc.value = marginal_costs


def get_marginal_costs_for_asset(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    ci = asset.costInformation
    if ci:
        mc = ci.marginalCosts
        if mc:
            return mc.value

    return None


def str2float(string):
    try:
        f = float(string)
        return f
    except:
        return 0.0


def get_first_last_of_line(line):
    first = ()
    last = ()

    i = 0
    for point in line.point:
        if i == 0:
            first = (point.lat, point.lon)
        i+=1

    last = (point.lat, point.lon)
    return first, last


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('command', namespace='/esdl')
def process_command(message):
    print ('received: ' + message['cmd'])
    if not valid_session():
        send_alert("Session has timed out, please refresh")
        return
    #print (message)
    #print (session)

    user_email = get_session('user-email')
    user_actions_logging.store_logging(user_email, "command", message['cmd'], json.dumps(message), "", {})

    active_es_id = get_session('active_es_id')
    if active_es_id is None:
        send_alert('Serious error: no active es id found. Please report')
        return

    esh = get_handler()
    if esh is None:
        print('ERROR finding esdlSystemHandler, Session issue??')
    mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')
    area_bld_list = get_session_for_esid(active_es_id, 'area_bld_list')

    es_edit = esh.get_energy_system(es_id=active_es_id)
    # test to see if this should be moved down:
    #  session.modified = True
    # print (get_handler().instance[0].area.name)

    if message['cmd'] == 'add_asset':
        area_bld_id = message['area_bld_id']
        asset_id = message['asset_id']
        assettype = message['asset']
        asset_name = message['asset_name']
        asset = None

        shape = message['shape']
        geometry = ESDLGeometry.create_ESDL_geometry(shape)

        if assettype == 'Area':
            if not isinstance(geometry, esdl.Polygon):
                send_alert('Areas with geometries other than polygons are not supported')
            else:
                if isinstance(geometry, esdl.Polygon):
                    new_area = esdl.Area(id=asset_id, name=asset_name)
                    new_area.geometry = geometry

                    # Update drop down list with areas and buildings
                    add_area_to_area_bld_list(new_area, area_bld_id, area_bld_list)
                    emit('area_bld_list', {'es_id': active_es_id, 'area_bld_list': area_bld_list})

                    # Add area to the indicated area
                    if not ESDLEnergySystem.add_area_to_area(es_edit, new_area, area_bld_id):
                        send_alert('Can not add area to building')

                    # Send new area shapes to the browser
                    area_list = []
                    boundary_wgs = ESDLGeometry.create_boundary_from_geometry(geometry)
                    area_list.append(ESDLGeometry.create_geojson(new_area.id, new_area.name, [], boundary_wgs))
                    emit('geojson', {"layer": "area_layer", "geojson": area_list})
                else:
                    send_alert('Can not add an area with another shap than a Polygon')
        else:
            edr_asset_str = get_session('adding_edr_assets')
            if edr_asset_str:
                asset = ESDLAsset.load_asset_from_string(edr_asset_str)
                # TODO: deepcopy does not work.
                # asset = copy.deepcopy(edr_asset)
                # Quick fix: session variable adding_edr_assets now contains ESDL string
                assettype = type(asset).__name__
            else:
                module = importlib.import_module('esdl.esdl')
                class_ = getattr(module, assettype)
                asset = class_()

            asset.id = asset_id
            asset.name = asset_name
            asset.geometry = geometry

            if isinstance(geometry, esdl.Point):
                port_loc = (shape['lat'], shape['lng'])
            elif isinstance(geometry, esdl.Polygon):
                port_loc = ESDLGeometry.calculate_polygon_center(geometry)

                polygon_area = int(shape['polygon_area'])

                if not isinstance(asset, esdl.AbstractBuilding):
                    if asset.surfaceArea:
                        if asset.power:
                            asset.power = asset.power * polygon_area / asset.surfaceArea
                            asset.surfaceArea = polygon_area
                    else:
                        asset.surfaceArea = polygon_area

            if not isinstance(asset, esdl.AbstractBuilding):
                # -------------------------------------------------------------------------------------------------------------
                #  Add assets with a polyline geometry and an InPort and an OutPort
                # -------------------------------------------------------------------------------------------------------------
                if assettype in ['ElectricityCable', 'Pipe']:
                    inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                    asset.port.append(inp)
                    outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
                    asset.port.append(outp)
                    asset.length = float(shape['length'])
                    first, last = get_first_last_of_line(geometry)
                    mapping[inp.id] = {'asset_id': asset_id, 'coord': first, 'pos': 'first'}
                    mapping[outp.id] = {'asset_id': asset_id, 'coord': last, 'pos': 'last'}

                # -------------------------------------------------------------------------------------------------------------
                #  Add assets with an InPort and two OutPorts (either point or polygon)
                # -------------------------------------------------------------------------------------------------------------
                elif assettype in ['CHP', 'FuelCell']:
                    inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                    asset.port.append(inp)

                    e_outp = esdl.OutPort(id=str(uuid.uuid4()), name='E Out')
                    asset.port.append(e_outp)
                    h_outp = esdl.OutPort(id=str(uuid.uuid4()), name='H Out')
                    asset.port.append(h_outp)

                    mapping[inp.id] = {"asset_id": asset_id, "coord": port_loc}
                    mapping[e_outp.id] = {"asset_id": asset_id, "coord": port_loc}
                    mapping[h_outp.id] = {"asset_id": asset_id, "coord": port_loc}

                else:
                    capability = ESDLAsset.get_asset_capability_type(asset)
                    if capability == 'Producer':
                        outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
                        asset.port.append(outp)
                        mapping[outp.id] = {'asset_id': asset_id, 'coord': port_loc}
                    elif capability in ['Consumer', 'Storage']:
                        inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                        asset.port.append(inp)
                        mapping[inp.id] = {'asset_id': asset_id, 'coord': port_loc}
                    elif capability in ['Conversion', 'Transport']:
                        inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                        asset.port.append(inp)
                        outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
                        asset.port.append(outp)
                        mapping[inp.id] = {"asset_id": asset_id, "coord": port_loc}
                        mapping[outp.id] = {"asset_id": asset_id, "coord": port_loc}
                    else:
                        print('Unknown asset capability ' % capability)
            else:
                # Update drop down list with areas and buildings
                add_bld_to_area_bld_list(asset, area_bld_id, area_bld_list)
                emit('area_bld_list', {'es_id': active_es_id, 'area_bld_list': area_bld_list})

            add_to_building = False
            if not ESDLAsset.add_asset_to_area(es_edit, asset, area_bld_id):
                ESDLAsset.add_asset_to_building(es_edit, asset, area_bld_id)
                add_to_building = True

            asset_to_be_added_list = []
            buildings_to_be_added_list = []

            # TODO: check / solve cable as Point issue?
            if not isinstance(asset, esdl.AbstractBuilding):
                port_list = []
                ports = asset.port
                for p in ports:
                    connTo_ids = list(o.id for o in p.connectedTo)
                    port_list.append(
                        {'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': connTo_ids})

            if isinstance(asset, esdl.AbstractBuilding):
                if isinstance(geometry, esdl.Point):
                    buildings_to_be_added_list.append(['point', asset.name, asset.id, type(asset).__name__, [shape['lat'], shape['lng']], False, {}])
                elif isinstance(geometry, esdl.Polygon):
                    coords = ESDLGeometry.parse_esdl_subpolygon(asset.geometry.exterior, False)  # [lon, lat]
                    coords = ESDLGeometry.exchange_coordinates(coords)                           # --> [lat, lon]
                    boundary = ESDLGeometry.create_boundary_from_geometry(geometry)
                    buildings_to_be_added_list.append(['polygon', asset.name, asset.id, type(asset).__name__, boundary["coordinates"], False, {}])
                    # buildings_to_be_added_list.append(['polygon', asset.name, asset.id, type(asset).__name__, coords])
                emit('add_building_objects', {'es_id': es_edit.id, 'building_list': buildings_to_be_added_list, 'zoom': False})
            else:
                capability_type = ESDLAsset.get_asset_capability_type(asset)

                # if assettype not in ['ElectricityCable', 'Pipe', 'PVParc', 'PVPark', 'WindParc', 'WindPark']:
                if isinstance(geometry, esdl.Point):
                    asset_to_be_added_list.append(['point', 'asset', asset.name, asset.id, type(asset).__name__, [shape['lat'], shape['lng']], port_list, capability_type])
                # elif assettype in ['PVParc', 'PVPark', 'WindParc', 'WindPark']:
                elif isinstance(geometry, esdl.Polygon):
                    coords = ESDLGeometry.parse_esdl_subpolygon(asset.geometry.exterior, False)  # [lon, lat]
                    coords = ESDLGeometry.exchange_coordinates(coords)                           # --> [lat, lon]
                    # print(coords)
                    asset_to_be_added_list.append(
                        ['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list, capability_type])
                # elif assettype in ['ElectricityCable', 'Pipe']:
                elif isinstance(geometry, esdl.Line):
                    coords = []
                    for point in geometry.point:
                        coords.append([point.lat, point.lon])
                    asset_to_be_added_list.append(['line', 'asset', asset.name, asset.id, type(asset).__name__, coords, port_list])

                #print(asset_to_be_added_list)
                emit('add_esdl_objects', {'es_id': es_edit.id, 'add_to_building': add_to_building, 'asset_pot_list': asset_to_be_added_list, 'zoom': False})

            esh.add_object_to_dict(es_edit.id, asset)
            if hasattr(asset, 'port'):
                for added_port in asset.port:
                    esh.add_object_to_dict(es_edit.id, added_port)
            set_handler(esh)

    if message['cmd'] == 'remove_object':        # TODO: remove form asset_dict
        # removes asset or potential from EnergySystem
        obj_id = message['id']
        if obj_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, obj_id)
            if isinstance(asset, esdl.AbstractBuilding):
                # Update drop down list with areas and buildings
                remove_ab_from_area_bld_list(asset.id, area_bld_list)
                emit('area_bld_list', {'es_id': active_es_id, 'area_bld_list': area_bld_list})
            if asset:
                # Try to remove control strategy for EnergyAssets (and not for buildings)
                if isinstance(asset, esdl.EnergyAsset):
                    remove_control_strategy_for_asset(asset.id)
            ESDLAsset.remove_object_from_energysystem(es_edit, obj_id)
            esh.remove_object_from_dict_by_id(es_edit.id, obj_id)
        else:
            send_alert('Asset or potential without an id cannot be removed')

    if message['cmd'] == 'get_asset_ports':
        asset_id = message['id']
        port_list = []
        if asset_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, asset_id)
            ports = asset.port
            for p in ports:
                port_list.append({id: p.id, type: type(p).__name__})
            emit('portlist', port_list)

    # if message['cmd'] == 'connect_assets':
    #     asset_id1 = message['id1']
    #     asset_id2 = message['id2']
    #     area = es_edit.instance[0].area
    #
    #     asset1 = ESDLAsset.find_asset(area, asset_id1)
    #     asset2 = ESDLAsset.find_asset(area, asset_id2)
    #     print('Connecting asset ' + asset1.id + ' and asset ' + asset2.id)
    #
    #     geom1 = asset1.geometry
    #     geom2 = asset2.geometry
    #
    #     if isinstance(asset1, esdl.AbstractConductor) or isinstance(asset2, esdl.AbstractConductor):
    #
    #         if isinstance(asset1, esdl.AbstractConductor):
    #             if isinstance(geom1, esdl.Line):
    #                 points = geom1.point
    #                 first_point1 = points[0]
    #                 last_point1 = points[len(points)-1]
    #                 first = 'line'
    #             if isinstance(geom1, esdl.Point): # in case of a Joint
    #                 point1=geom1
    #                 first='point'
    #         else:
    #             if isinstance(geom1, esdl.Point):
    #                 point1 = geom1
    #                 first = 'point'
    #
    #         if isinstance(asset2, esdl.AbstractConductor):
    #             if isinstance(geom2, esdl.Line):
    #                 points = geom2.point
    #                 first_point2 = points[0]
    #                 last_point2 = points[len(points)-1]
    #                 second = 'line'
    #             if isinstance(geom2, esdl.Point): # in case of a Joint
    #                 point2=geom2
    #                 second='point'
    #         else:
    #             if isinstance(geom2, esdl.Point):
    #                 point2 = geom2
    #                 second = 'point'
    #     else:
    #         point1 = geom1
    #         first = 'point'
    #         point2 = geom2
    #         second = 'point'
    #
    #     if first == 'point' and second == 'point':
    #         connect_asset_with_asset(asset1, asset2)
    #     if first == 'point' and second == 'line':
    #         connect_asset_with_conductor(asset1, asset2)
    #     if first == 'line' and second == 'point':
    #         connect_asset_with_conductor(asset2, asset1)
    #     if first == 'line' and second == 'line':
    #         connect_conductor_with_conductor(asset1, asset2)

    if message['cmd'] == 'connect_ports':
        port1_id = message['port1id']
        port2_id = message['port2id']

        asset1_id = mapping[port1_id]['asset_id']
        asset2_id = mapping[port2_id]['asset_id']
        asset1_port_location = mapping[port1_id]['coord']
        asset2_port_location = mapping[port2_id]['coord']

        asset1 = esh.get_by_id(es_edit.id, asset1_id)
        asset2 = esh.get_by_id(es_edit.id, asset2_id)

        port1 = None
        port2 = None
        for p in asset1.port:
            if p.id == port1_id:
                port1 = p
                break

        for p in asset2.port:
            if p.id == port2_id:
                port2 = p
                break

        if port1 and port2:
            # add type check on ports
            if type(port1).__name__ == type(port2).__name__:
                send_alert('Cannot connect ports of the same type. One should be an InPort and one should be an OutPort')
            else:
                connect_ports(port1, port2)

                add_to_building = False
                if asset1.containingBuilding:
                    asset1_bld_id = asset1.containingBuilding.id
                if asset2.containingBuilding:
                    if asset1.containingBuilding:
                        # assets both in buildings
                        if asset1_bld_id == asset2.containingBuilding.id:
                            # assets in same building
                            add_to_building = True
                        else:
                            # assets in different buildings
                            bld_asset1 = asset1.containingBuilding
                            asset1_port_location = (bld_asset1.geometry.lat, bld_asset1.geometry.lon)
                            bld_asset2 = asset2.containingBuilding
                            asset2_port_location = (bld_asset2.geometry.lat, bld_asset2.geometry.lon)
                            add_to_building = False
                    else:
                        # asset2 in building and asset1 not in building
                        bld_asset2 = asset2.containingBuilding
                        asset2_port_location = (bld_asset2.geometry.lat, bld_asset2.geometry.lon)
                        add_to_building = False
                else:
                    # asset2 not in building
                    if asset1.containingBuilding:
                        # asset1 in building and asset2 not in building
                        bld_asset1 = asset1.containingBuilding
                        asset1_port_location = (bld_asset1.geometry.lat, bld_asset1.geometry.lon)
                        add_to_building = False
                    else:
                        # both assets not in building
                        add_to_building = False

                emit('add_new_conn', {'es_id': es_edit.id, 'add_to_building': add_to_building,
                                      'new_conn': [[asset1_port_location[0], asset1_port_location[1]],
                                                   [asset2_port_location[0], asset2_port_location[1]]]})

                p1_carr_id = None
                if port1.carrier:
                    p1_carr_id = port1.carrier.id
                p2_carr_id = None
                if port2.carrier:
                    p2_carr_id = port2.carrier.id
                conn_list = get_session_for_esid(active_es_id, 'conn_list')
                conn_list.append({'from-port-id': port1_id, 'from-port-carrier': p1_carr_id, 'from-asset-id': asset1_id,
                                  'from-asset-coord': [asset1_port_location[0], asset1_port_location[1]],
                                  'to-port-id': port2_id, 'to-port-carrier': p2_carr_id, 'to-asset-id': asset2_id,
                                  'to-asset-coord': [asset2_port_location[0], asset2_port_location[1]]})
        else:
            send_alert('Serious error connecting ports')

    if message['cmd'] == 'get_object_info':
        object_id = message['id']
        asspot = message['asspot']
        area = es_edit.instance[0].area
        connected_to_info = []
        ctrl_strategy = None

        if asspot == 'asset':
            # asset = ESDLAsset.find_asset(area, object_id)
            asset = esh.get_by_id(es_edit.id, object_id)
            print('Get info for asset ' + asset.id)
            attrs_sorted = ESDLEcore.get_asset_attributes(asset, esdl_doc)
            name = asset.name
            if isinstance(asset, esdl.EnergyAsset):
                connected_to_info = get_connected_to_info(asset)
                if asset.controlStrategy:
                    ctrl_strategy = asset.controlStrategy.name
                else:
                    ctrl_strategy = None
                asset_class = 'EnergyAsset'
            else:
                asset_class = 'AbstractBuilding'
            asset_doc = asset.__doc__
        else:
            pot = ESDLAsset.find_potential(area, object_id)
            #asset = esh.get_by_id(es_edit.id, object_id)
            print('Get info for potential ' + pot.id)
            attrs_sorted = ESDLEcore.get_asset_attributes(pot, esdl_doc)
            name = pot.name
            connected_to_info = []
            ctrl_strategy = None
            asset_doc = pot.__doc__

        if name is None: name = ''
        emit('asset_info', {'id': object_id, 'name': name, 'class': asset_class, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info, 'ctrl_strategy': ctrl_strategy, 'asset_doc': asset_doc})

    if message['cmd'] == 'get_conductor_info':
        asset_id = message['id']
        latlng = message['latlng']
        area = es_edit.instance[0].area
        asset = ESDLAsset.find_asset(area, asset_id)
        connected_to_info = get_connected_to_info(asset)
        print('Get info for conductor ' + asset.id)
        attrs_sorted = ESDLEcore.get_asset_attributes(asset, esdl_doc)
        name = asset.name
        if name is None: name = ''
        asset_doc = asset.__doc__
        emit('asset_info', {'id': asset_id, 'name': name, 'class': 'EnergyAsset', 'latlng': latlng, 'attrs': attrs_sorted, 'connected_to_info': connected_to_info, 'asset_doc': asset_doc})

    if message['cmd'] == 'get_table_editor_info':
        producer_info_list = []
        consumer_info_list = []
        transport_info_list = []
        storage_info_list = []
        conversion_info_list = []

        energy_assets = esh.get_all_instances_of_type(esdl.EnergyAsset, active_es_id)

        for asset in energy_assets:
            attrs_sorted = ESDLEcore.get_asset_attributes(asset, esdl_doc)
            connected_to_info = get_connected_to_info(asset)
            strategy_info = get_control_strategy_info(asset)
            profile_info = get_port_profile_info(asset)
            mc_info = None
            ci = asset.costInformation
            if ci:
                mc = ci.marginalCosts
                if mc:
                    mc_info = mc.value
            name = asset.name
            if name is None: name = ''
            asset_doc = asset.__doc__
            asset_type = type(asset).__name__
            asset_info = {
                'id': asset.id,
                'name': name,
                'type': asset_type,
                'attrs': attrs_sorted,
                'connected_to_info': connected_to_info,
                'control_strategy': strategy_info,
                'marginal_costs': mc_info,
                'profile_info': profile_info,
                'asset_doc': asset_doc
            }
            if isinstance(asset, esdl.Producer):
                producer_info_list.append(asset_info)
            if isinstance(asset, esdl.Consumer):
                consumer_info_list.append(asset_info)
            if isinstance(asset, esdl.Transport):
                transport_info_list.append(asset_info)
            if isinstance(asset, esdl.Storage):
                storage_info_list.append(asset_info)
            if isinstance(asset, esdl.Conversion):
                if not strategy_info:
                    print("================== NO CONTROL STRATEGY ===================")
                conversion_info_list.append(asset_info)

        # Sort arrays on asset_type
        # attrs_sorted = sorted(attributes, key=lambda a: a['name'])
        producer_info_list = sorted(producer_info_list, key=lambda a: (a['type'], a['name']))
        consumer_info_list = sorted(consumer_info_list, key=lambda a: (a['type'], a['name']))
        transport_info_list = sorted(transport_info_list, key=lambda a: (a['type'], a['name']))
        storage_info_list = sorted(storage_info_list, key=lambda a: (a['type'], a['name']))
        conversion_info_list = sorted(conversion_info_list, key=lambda a: (a['type'], a['name']))

        emit('table_editor', {
            'producer': producer_info_list,
            'consumer': consumer_info_list,
            'transport': transport_info_list,
            'storage': storage_info_list,
            'conversion': conversion_info_list
        })

    if message['cmd'] == 'set_asset_param':
        if not 'id' in message:
            fragment = message['fragment']
            asset_id = None
        else:
            fragment = None
            asset_id = message['id']
        param_name = message['param_name']
        param_value = message['param_value']

        area = es_edit.instance[0].area

        #asset = ESDLAsset.find_asset(area, asset_id)
        if asset_id is None:
            resource = esh.get_resource(active_es_id)
            asset = resource.resolve(fragment)
        else:
            asset = esh.get_by_id(active_es_id, asset_id)
        print('Set param '+ param_name +' for class ' + asset.eClass.name + ' to value '+ param_value)

        try:
            attribute = asset.eClass.findEStructuralFeature(param_name)
            if attribute is not None:
                if param_value == "":
                    parsed_value = attribute.eType.default_value
                else:
                    parsed_value = attribute.eType.from_string(param_value)
                if attribute.many:
                    eOrderedSet = asset.eGet(param_name)
                    eOrderedSet.clear() #TODO no support for multi-select of enums
                    eOrderedSet.append(parsed_value)
                    asset.eSet(param_name, eOrderedSet)
                else:
                    if attribute.name == 'id':
                        esh.remove_object_from_dict(active_es_id, asset)
                        asset.eSet(param_name, parsed_value)
                        esh.add_object_to_dict(active_es_id, asset)
                    else:
                        asset.eSet(param_name, parsed_value)

            else:
                send_alert('Error setting attribute {} of {} to {}, unknown attribute'.format(param_name, asset.name, param_value))
        except Exception as e:
            print('Error setting attribute {} of {} to {}, caused by {}'.format(param_name, asset.name, param_value, str(e)))
            send_alert('Error setting attribute {} of {} to {}, caused by {}'.format(param_name, asset.name, param_value, str(e)))

    if message['cmd'] == 'set_area_bld_polygon':
        area_bld_id = message['area_bld_id']
        polygon_data = message['polygon']

        polygon = esdl.Polygon()
        exterior = esdl.SubPolygon()
        polygon.exterior = exterior

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
                point = esdl.Point(lat=coord['lat'], lon=coord['lng'])
                exterior.point.append(point)
                prev_lat = coord['lat']
                prev_lng = coord['lng']
            i += 1

        area = es_edit.instance[0].area
        area_selected = ESDLEnergySystem.find_area(area, area_bld_id)
        if area_selected:
            area_selected.geometry = polygon
        else:
            bld_selected = ESDLAsset.find_asset(area, area_bld_id)
            if bld_selected:
                bld_selected.geometry = polygon
            else:
                send_alert('SERIOUS ERROR: set_area_bld_polygon - connot find area or building')

    if message['cmd'] == 'split_conductor':
        cond_id = message['id']
        mode = message['mode']      # connect, add_joint, no_connect
        location_to_split = message['location']

        area = es_edit.instance[0].area
        conductor, container = ESDLAsset.find_asset_and_container(area, cond_id)

        split_conductor(conductor, location_to_split, mode, container)

    if message['cmd'] == 'get_port_profile_info':
        port_id = message['port_id']

        asset_id = mapping[port_id]['asset_id'] # {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}
        if asset_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, asset_id)
            ports = asset.port
            for p in ports:
                if p.id == port_id:
                    profile = p.profile
                    if profile:
                        profile_info_list = generate_profile_info(profile)
                        emit('port_profile_info', {'port_id': port_id, 'profile_info': profile_info_list})
                    else:
                        emit('port_profile_info', {'port_id': port_id, 'profile_info': []})

    if message['cmd'] == 'add_profile_to_port':
        port_id = message['port_id']
        profile_class = message['profile_class']
        quap_type = message["qaup_type"]

        if profile_class == 'SingleValue':
            value = message['value']
            esdl_profile = esdl.SingleValue()
            esdl_profile.value = str2float(value)
        elif profile_class == 'DateTimeProfile':
            esdl_profile = esdl.DateTimeProfile()
            # TODO: Determine how to deal with DateTimeProfiles in the UI
        else:
            # Assume all other options are InfluxDBProfiles
            multiplier = message['multiplier']

            profiles = esdl_config.esdl_config['influxdb_profile_data']
            for p in profiles:
                if p['profile_uiname'] == profile_class:
                    esdl_profile = esdl.InfluxDBProfile()
                    esdl_profile.multiplier = str2float(multiplier)

                    esdl_profile.measurement = p['measurement']
                    esdl_profile.field = p['field']
                    esdl_profile.host = esdl_config.esdl_config['profile_database']['host']
                    esdl_profile.port = int(esdl_config.esdl_config['profile_database']['port'])
                    esdl_profile.database = p['database']
                    esdl_profile.filters = esdl_config.esdl_config['profile_database']['filters']

                    if 'start_datetime' in p:
                        esdl_profile.startDate = EDate.from_string(p['start_datetime'])
                    if 'end_datetime' in p:
                        esdl_profile.endDate = EDate.from_string(p['end_datetime'])

        if quap_type == 'predefined_qau':
            # socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
            #    profile_class: profile_class, quap_type: qaup_type, predefined_qau: predefined_qau});
            predefined_qau = message["predefined_qau"]
            for pqau in esdl_config.esdl_config['predefined_quantity_and_units']:
                if pqau['id'] == predefined_qau:
                    qau = ESDLQuantityAndUnits.build_qau_from_dict(pqau)
            esdl_profile.profileQuantityAndUnit = qau
        elif quap_type == 'custom_qau':
            # socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
            #    profile_class: profile_class, quap_type: qaup_type, custom_qau: custom_qau});
            custom_qau = message["custom_qau"]
            qau = ESDLQuantityAndUnits.build_qau_from_dict(custom_qau)
            esdl_profile.profileQuantityAndUnit = qau
        elif quap_type == 'profiletype':
            # socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
            #    profile_class: profile_class, quap_type: qaup_type, profile_type: profile_type});
            profile_type = message['profile_type']
            esdl_profile.profileType = esdl.ProfileTypeEnum.from_string(profile_type)

        esdl_profile.id = str(uuid.uuid4())
        esh.add_object_to_dict(es_edit.id, esdl_profile)

        asset_id = mapping[port_id]['asset_id'] # {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}
        if asset_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, asset_id)
            ports = asset.port
            for p in ports:
                if p.id == port_id:
                    # p.profile = esdl_profile
                    ESDLAsset.add_profile_to_port(p, esdl_profile)

    if message['cmd'] == 'remove_profile_from_port':
        port_id = message['port_id']
        profile_id = message['profile_id']

        asset_id = mapping[port_id]['asset_id'] # {'asset_id': asset_id, 'coord': (message['lat'], message['lng'])}
        if asset_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, asset_id)
            ports = asset.port
            for p in ports:
                if p.id == port_id:
                    # p.profile = esdl_profile
                    ESDLAsset.remove_profile_from_port(p, profile_id)


    if message['cmd'] == 'add_port':
        direction = message['direction']
        asset_id = message['asset_id']
        pname = message['pname']

        asset = esh.get_by_id(es_edit.id, asset_id)
        if direction == 'in':
            port = esdl.InPort(id=str(uuid.uuid4()), name=pname)
        else:
            port = esdl.OutPort(id=str(uuid.uuid4()), name=pname)

        geom = asset.geometry
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon
            coord = (lat, lon)
            mapping[port.id] = {'asset_id': asset.id, 'coord': coord}
            asset.port.append(port)
            esh.add_object_to_dict(active_es_id, port)
            port_list = []
            for p in asset.port:
                port_list.append(
                    {'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
            emit('update_asset', {'asset_id': asset.id, 'ports': port_list})
        else:
            send_alert('ERROR: Adding port not supported yet! asset doesn\'t have geometry esdl.Point')

    if message['cmd'] == 'remove_port':
        pid = message['port_id']
        asset_id = mapping[pid]['asset_id']
        asset = esh.get_by_id(es_edit.id, asset_id)
        ports = asset.port

        port_list = []
        for p in set(ports):
            if p.id == pid:
                ports.remove(p)
            else:
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
        emit('update_asset', {'asset_id': asset.id, 'ports': port_list})

    if message['cmd'] == 'remove_connection':
        from_asset_id = message['from_asset_id']
        from_asset = esh.get_by_id(es_edit.id, from_asset_id)
        from_port_id = message['from_port_id']
        to_asset_id = message['to_asset_id']
        to_asset = esh.get_by_id(es_edit.id, to_asset_id)
        to_port_id = message['to_port_id']
        print('Removing connection {}#{} -> {}#{}'.format(from_asset.name, from_port_id, to_asset.name, to_port_id))

        # Aa.port[]->connectedTo->port[].Ab
        fromPort = ESDLAsset.find_port(from_asset.port, from_port_id)
        toPort = ESDLAsset.find_port(to_asset.port, to_port_id)
        fromPort.connectedTo.remove(toPort) # updates the opposite relation automatically


        # remove reference at both sides (this is quite ugly in generateDS-based ESDL...)
        # for p in from_asset.port:
        #     if p.id == from_port_id:
        #         connected_to = p.connectedTo
        #         if connected_to:
        #             connected_to_list = connected_to.split(' ')
        #             new_connected_to_list = []
        #             for conn_id in connected_to_list:
        #                 if conn_id != to_port_id:
        #                     # add non-affected connection to new list
        #                     new_connected_to_list.append(conn_id)
        #             p.set_connectedTo(' '.join(new_connected_to_list))
        #
        # for p in to_asset.port:
        #     if p.id == to_port_id:
        #         connected_to = p.connectedTo
        #         if connected_to:
        #             connected_to_list = connected_to.split(' ')
        #             new_connected_to_list = []
        #             for conn_id in connected_to_list:
        #                 if conn_id != from_port_id:
        #                     # add non-affected connection to new list
        #                     new_connected_to_list.append(conn_id)
        #             p.set_connectedTo(' '.join(new_connected_to_list))

        # refresh connections in gui
        active_es_id = get_session('active_es_id')
        conn_list = get_session_for_esid(active_es_id, 'conn_list')
        new_list = []
        #print(conn_list)
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
        set_session_for_esid(active_es_id, 'conn_list', new_list)  # set new connection list
        # TODO: send es.id with this message?
        emit('clear_connections')   # clear current active layer connections
        emit('add_connections', {'es_id': active_es_id, 'conn_list': new_list})

    if message['cmd'] == 'set_carrier':
        asset_id = message['asset_id']
        carrier_id = message['carrier_id']
        area = es_edit.instance[0].area

        if asset_id:
            asset = ESDLAsset.find_asset(area, asset_id)
            num_ports = len(asset.port)
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

            carrier.energyContentUnit = encont_qandu
            carrier.emissionUnit = emission_qandu

        if carr_type == 'el_comm':
            carr_voltage = message['voltage']
            carrier = esdl.ElectricityCommodity(id=carr_id, name=carr_name, voltage=str2float(carr_voltage))
        if carr_type == 'g_comm':
            carr_pressure = message['pressure']
            carrier = esdl.GasCommodity(id=carr_id, name=carr_name, pressure=str2float(carr_pressure))
        if carr_type == 'h_comm':
            carr_suptemp = message['suptemp']
            carr_rettemp = message['rettemp']
            carrier = esdl.HeatCommodity(id=carr_id, name=carr_name, supplyTemperature=str2float(carr_suptemp), returnTemperature=str2float(carr_rettemp))
        if carr_type == 'en_comm':
            carrier = esdl.EnergyCarrier(id=carr_id, name=carr_name)

        esh.add_object_to_dict(es_edit.id, carrier) # add carrier to ID list for easy retrieval

        esi = es_edit.energySystemInformation
        if not esi:
            esi_id = str(uuid.uuid4())
            esi = esdl.EnergySystemInformation()
            esi.id = esi_id
            es_edit.energySystemInformation = esi
        esh.add_object_to_dict(es_edit.id, esi)

        ecs = esi.carriers
        if not ecs:
            ecs_id = str(uuid.uuid4())
            ecs = esdl.Carriers(id=ecs_id)
            esi.carriers = ecs
        esh.add_object_to_dict(es_edit.id, ecs)
        ecs.carrier.append(carrier)

        carrier_list = ESDLEnergySystem.get_carrier_list(es_edit)
        emit('carrier_list', {'es_id': es_edit.id, 'carrier_list': carrier_list})

    if message['cmd'] == 'get_storage_strategy_info':
        asset_id = message['asset_id']

        mcc, mdc = get_storage_marginal_costs(asset_id)
        emit('storage_strategy_window', {'asset_id': asset_id, 'mcc': mcc, 'mdc': mdc})

    if message['cmd'] == 'get_curtailment_strategy_info':
        asset_id = message['asset_id']

        max_power = get_curtailment_max_power(asset_id)
        emit('curtailment_strategy_window', {'asset_id': asset_id, 'max_power': max_power})

    if message['cmd'] == 'set_control_strategy':
        # socket.emit('command', {'cmd': 'set_control_strategy', 'strategy': control_strategy, 'asset_id': asset_id, 'port_id': port_id});
        strategy = message['strategy']
        asset_id = message['asset_id']

        if strategy == 'StorageStrategy':
            mcc = message['marg_ch_costs']
            mdc = message['marg_disch_costs']
            add_storage_control_strategy_for_asset(asset_id, mcc, mdc)
        elif strategy == 'CurtailmentStrategy':
            max_power = message['max_power']
            add_curtailment_control_strategy_for_asset(asset_id, max_power)
        else:
            port_id = message['port_id']
            add_drivenby_control_strategy_for_asset(asset_id, strategy, port_id)

    if message['cmd'] == 'remove_control_strategy':
        asset_id = message['asset_id']
        remove_control_strategy_for_asset(asset_id)

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
        sim_descr = message['sim_description']
        sim_start_datetime = message['sim_start_datetime']
        sim_end_datetime = message['sim_end_datetime']
        # Create the HTTP POST to start the simulation
        if not essim.run_simulation(sim_descr, sim_start_datetime, sim_end_datetime):
            emit('simulation_not_started')
        # start_checking_ESSIM_progress()
        # check_ESSIM_progress()

    if message['cmd'] == 'validate_for_ESSIM':
        print('validation for ESSIM command received')
        res = validate_ESSIM(es_edit)
        emit('results_validation_for_ESSIM', res)

    if message['cmd'] == 'calculate_ESSIM_KPIs':
        # session['simulationRun'] = '5d10f273783bac5eff4575e8'
        ESSIM_config = settings.essim_config

        simulation_run = get_session('simulationRun')
        if simulation_run:
            sdt = datetime.strptime(ESSIM_config['start_datetime'], '%Y-%m-%dT%H:%M:%S%z')
            edt = datetime.strptime(ESSIM_config['end_datetime'], '%Y-%m-%dT%H:%M:%S%z')

            influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
            influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')

            calc_ESSIM_KPIs.submit(es_edit, simulation_run, influxdb_startdate, influxdb_enddate)
        else:
            send_alert('No simulation id defined - run an ESSIM simulation first')

    if message['cmd'] == 'add_layer':
        id = message['id']
        descr = message['descr']
        url = message['url']
        name = message['name']
        setting_type = message['setting_type']
        project_name = message['project_name']
        legend_url = message['legend_url']
        visible = message['visible']

        layer = {
            "description": descr,
            "url": url,
            "layer_name": name,
            "setting_type": setting_type,
            "project_name": project_name,
            "legend_url": legend_url,
            "layer_ref": None,
            "visible": visible
        }

        wms_layers.add_wms_layer(id, layer)

    if message['cmd'] == 'remove_layer':
        id = message['id']
        wms_layers.remove_wms_layer(id)

    if message['cmd'] == 'get_es_info':
        attributes = [
            {"id": 1, "name": "Energysystem name", "value": es_edit.name},
            {"id": 2, "name": "Energysystem description", "value": es_edit.description}
        ]
        emit('show_es_info', attributes)

    if message['cmd'] == 'set_es_info_param':
        id = message['id']
        value = message['value']

        if id == "1":
            es_edit.name = value
        if id == "2":
            es_edit.description = value
            es_edit.description = value

    if message['cmd'] == 'add_sector':
        name = message['name']
        descr = message['descr']
        code = message['code']
        ESDLEnergySystem.add_sector(es_edit, name, code, descr)
        sector_list = ESDLEnergySystem.get_sector_list(es_edit)
        emit('sector_list', {'es_id': es_edit.id, 'sector_list': sector_list})

    if message['cmd'] == 'remove_sector':
        id = message['id']
        esh = get_handler()
        ESDLEnergySystem.remove_sector(es_edit, id)
        sector_list = ESDLEnergySystem.get_sector_list(es_edit)
        emit('sector_list', {'es_id': es_edit.id, 'sector_list': sector_list})

    if message['cmd'] == 'set_sector':
        asset_id = message['asset_id']
        sector_id = message['sector_id']

        instance = es_edit.instance
        area = instance[0].area
        asset = ESDLAsset.find_asset(area, asset_id)

        esi = es_edit.energySystemInformation
        sectors = esi.sectors
        sector = sectors.sector
        for s in sector:
            if s.id == sector_id:
                asset.sector = s

    if message['cmd'] == 'get_edr_asset':
        edr_asset_id = message['edr_asset_id']
        edr_assets = EDR_assets()
        edr_asset_str = edr_assets.get_asset_from_EDR(edr_asset_id)
        if edr_asset_str:
            edr_asset = ESDLAsset.load_asset_from_string(edr_asset_str)
            edr_asset_type = type(edr_asset).__name__
            emit('place_edr_asset', edr_asset_type)
            set_session('adding_edr_assets', edr_asset_str)
        else:
            send_alert('Error getting ESDL model from EDR')

    if message['cmd'] == 'set_asset_drawing_mode':
        mode = message['mode']
        if mode == 'empty_assets':
            set_session('adding_edr_assets', None)

    if message['cmd'] == 'query_esdl_service':
        params = message['params']
        print(params)
        query_esdl_services.submit(params)

    if message['cmd'] == 'redraw_connections':
        conn_list = get_session_for_esid(active_es_id, 'conn_list')
        emit('clear_connections')  # clear current active layer connections
        emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})

        asset_list = get_session_for_esid(active_es_id, 'asset_list')
        emit('clear_ui', {'layer': 'assets'})  # clear current active layer assets
        emit('add_esdl_objects', {'es_id': active_es_id, 'asset_pot_list': asset_list, 'zoom': True})

    if message['cmd'] == 'building_editor':
        bld_id = message['id']
        building = esh.get_by_id(active_es_id, bld_id)
        bld_info = get_building_information(building)
        emit('building_information', bld_info)
        emit('add_esdl_objects',
             {'es_id': active_es_id, 'add_to_building': True, 'asset_pot_list': bld_info["asset_list"],
              'zoom': False})
        emit('add_connections', {'es_id': active_es_id, 'add_to_building': True, 'conn_list': bld_info["conn_list"]})

    if message['cmd'] == 'accept_received_esdl':
        user_email = get_session('user-email')
        received_esdls = esdl_api.get_esdl_for_user(user_email)
        if received_esdls:
            for received_esdl in received_esdls:
                filename = 'ESDL from '+received_esdl['sender']
                esh = get_handler()

                try:
                    result = esh.add_from_string(name=filename, esdl_string=urllib.parse.unquote(received_esdl['esdl']))
                    process_energy_system.submit(esh, filename)  # run in seperate thread
                    esdl_api.remove_esdls_for_user(user_email)
                except Exception as e:
                    logger.error("Error loading {}: {}".format(filename, e))
                    send_alert('Error interpreting ESDL from file - Exception: ' + str(e))

    if message['cmd'] == 'rename_energysystem':
        name = message['name']
        rename_es_id = message['remame_es_id']

        es_rename = esh.get_energy_system(es_id=rename_es_id)
        es_rename.name = name

    if message['cmd'] == 'remove_energysystem':
        remove_es_id = message['remove_es_id']
        esh.remove_energy_system(es_id=remove_es_id)

    set_handler(esh)
    session.modified = True


@executor.job
def calc_ESSIM_KPIs(es_edit, simulation_run, influxdb_startdate, influxdb_enddate):
    essim_kpis.init_simulation(es_edit, simulation_run, influxdb_startdate, influxdb_enddate)
    res = essim_kpis.calculate_kpis()
    # emit('show_ESSIM_KPIs', res)
    res_dict = essim_kpis.seperate_kpis(res)
    emit('essim-kpi-data', res_dict)


@executor.job
def query_esdl_services(params):
    esh = get_handler()
    print('calling service')
    esdl_service_ok, esdl_service_result = esdl_services.call_esdl_service(params)
    print('emitting result to browser')
    if esdl_service_ok:
        if esdl_service_result is not None:
            emit('esdl_service_result', esdl_service_result)
    else:
        send_alert('Error calling service')
    # print('processing energy system')
    process_energy_system.submit(esh)


# ---------------------------------------------------------------------------------------------------------------------
#  Initialization after new or load energy system
#  If this function is run through process_energy_system.submit(filename, es_title) it is executed
#  in a separate thread.
# ---------------------------------------------------------------------------------------------------------------------
@executor.job
def process_energy_system(esh, filename=None, es_title=None, app_context=None):
    # emit('clear_ui')
    print("Processing energysystems in esh")
    main_es = esh.get_energy_system()
    set_session('active_es_id', main_es.id)     # TODO: check if required here?
    es_list = esh.get_energy_systems()
    es_info_list = get_session("es_info_list")

    # emit('clear_esdl_layer_list')

    conn_list = []
    mapping = {}
    carrier_list = []
    sector_list = []

    for es in es_list:
        asset_list = []
        building_list = []
        area_bld_list = []
        conn_list = []
        mapping = {}

        if es.id is None:
            es.id = str(uuid.uuid4())

        if not es.id in es_info_list:
            print("- Processing energysystem with id {}".format(es.id))
            name = es.name
            if not name:
                title = 'Untitled Energysystem'
            else:
                title = name

            emit('create_new_esdl_layer', {'es_id': es.id, 'title': title})
            emit('set_active_layer_id', es.id)

            area = es.instance[0].area
            find_boundaries_in_ESDL(area)       # also adds coordinates to assets if possible
            carrier_list = ESDLEnergySystem.get_carrier_list(es)
            emit('carrier_list', {'es_id': es.id, 'carrier_list': carrier_list})
            sector_list = ESDLEnergySystem.get_sector_list(es)
            if sector_list:
                emit('sector_list', {'es_id': es.id, 'sector_list': sector_list})

            area_kpis = ESDLEnergySystem.process_area_KPIs(area)
            area_name = area.name
            if not area_name:
                area_name = title
            if area_kpis:
                emit('kpis', {'es_id': es.id, 'scope': area_name, 'kpi_list': area_kpis})

            # give all assets without geometry a random location around the center of the current energysystem
            # else create_port_to_asset_mapping won't work
            add_missing_coordinates(area)
            create_port_to_asset_mapping(area, mapping)
            process_area(es.id, asset_list, building_list, area_bld_list, conn_list, mapping, area, 0)

            emit('add_building_objects', {'es_id': es.id, 'building_list': building_list, 'zoom': False})
            emit('add_esdl_objects', {'es_id': es.id, 'asset_pot_list': asset_list, 'zoom': True})
            emit('area_bld_list', {'es_id': es.id,  'area_bld_list': area_bld_list})
            emit('add_connections', {'es_id': es.id, 'add_to_building': False, 'conn_list': conn_list})

            set_session_for_esid(es.id, 'port_to_asset_mapping', mapping)
            set_session_for_esid(es.id, 'conn_list', conn_list)
            set_session_for_esid(es.id, 'asset_list', asset_list)
            set_session_for_esid(es.id, 'area_bld_list', area_bld_list)

            # TODO: update asset_list???
            es_info_list[es.id] = {
                "processed": True
            }
        else:
            print("- Energysystem with id {} already processed".format(es.id))

    set_handler(esh)
    # emit('set_active_layer_id', main_es.id)

    # set_session('es_title',main_es.name)
    # set_session('es_descr', main_es.description)
    # session['es_start'] = 'new'

    # set_session('port_to_asset_mapping', mapping)
    # set_session('conn_list', conn_list)
    # set_session('carrier_list', carrier_list)

    #session.modified = True
    print('session variables set', session)
    # print('es_id: ', get_session('es_id'))


@socketio.on('set_active_es_id', namespace='/esdl')
def set_active_es_id(id):
    set_session('active_es_id', id)


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('file_command', namespace='/esdl')
def process_file_command(message):
    print ('received: ' + message['cmd'])
    es_info_list = get_session("es_info_list")

    if message['cmd'] == 'new_esdl':
        name = message['name']
        description = message['description']
        email = message['email']
        top_area_name = message['top_area_name']
        if top_area_name == '': top_area_name = 'Untitled area'
        filename = 'Unknown'
        esh = EnergySystemHandler()
        es = esh.create_empty_energy_system(name, description, 'Untitled instance', top_area_name)
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')
        process_energy_system.submit(esh, filename)

        del_session('store_item_metadata')
        emit('store_item_metadata', {})
        set_session('active_es_id', es.id)
        set_session('es_filename', filename)
        set_session('es_email', email)

    if message['cmd'] == 'load_esdl_from_file':
        file_content = message['file_content']
        filename = message['filename']
        esh = EnergySystemHandler()

        try:
            result = esh.load_from_string(esdl_string=file_content, name=filename)
        except Exception as e:
            send_alert("Error opening {}. Exception is: {}".format(filename, e))
            emit('clear_ui')
            return

        es = esh.get_energy_system()
        set_handler(esh)
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')
        process_energy_system.submit(esh, filename) # run in seperate thread
        #thread = threading.Thread(target=process_energy_system, args=(esh, None, None, current_app._get_current_object() ))
        #thread.start()

        del_session('store_item_metadata')
        emit('store_item_metadata', {})
        set_session('active_es_id', es.id)
        set_session('es_filename', filename)

    if message['cmd'] == 'import_esdl_from_file':
        file_content = message['file_content']
        filename = message['filename']
        esh = get_handler()

        try:
            result = esh.add_from_string(name=filename, esdl_string=file_content)
            process_energy_system.submit(esh, filename)  # run in seperate thread
        except Exception as e:
            logger.error("Error loading {}: {}".format(filename, e))
            send_alert('Error interpreting ESDL from file - Exception: ' + str(e))


    if message['cmd'] == 'get_list_from_store':
        role = get_session('user-role')
        if 'mondaine' in role:
            store_url = mondaine_hub_url + 'tagged?tag=map&take=1000'
        else:
            store_url = default_store_url+ 'tagged?tag=map&take=1000'

        try:
            result = requests.get(store_url)
        except Exception as e:
            print('Error accessing ESDL store' + str(e))
            send_alert('Error accessing ESDL store' + str(e))
            return

        data = result.json()
        store_list = []
        for store_item in data:
            store_list.append({'id': store_item['id'], 'title': store_item['title']})

        emit('store_list', store_list)

    if message['cmd'] == 'load_esdl_from_store':
        store_id = message['id']

        esh = load_ESDL_EnergySystem(store_id)
        if esh:
            es = esh.get_energy_system()
            if es.name:
                title = 'Store name: ' + es.name + ', store id: ' + store_id
            else:
                title = 'Store id: ' + store_id

            set_session('active_es_id', es.id)
            set_session('es_filename', title)  # TODO: separate filename and title
            es_info_list = {}
            set_session("es_info_list", es_info_list)
            emit('clear_ui')
            emit('clear_esdl_layer_list')
            process_energy_system.submit(esh, None, title)
        else:
            send_alert('Error loading ESDL file with id {} from store'.format(store_id))

    if message['cmd'] == 'store_esdl':
        title = message['store_title']
        descr = message['store_descr']
        email = message['store_email']

        tags = ['map']

        esh = get_handler()
        store_item_metadata = get_session('store_item_metadata')
        if store_item_metadata:
            store_id = store_item_metadata['id']
            update_store_item(store_id, title, descr, email, tags, esh)
        else:
            store_id = get_session('active_es_id')
            create_new_store_item(store_id, title, descr, email, tags, esh)

    # Do not store file_content in logging database
    if 'file_content' in message:
        del message['file_content']
    user_email = get_session('user-email')
    user_actions_logging.store_logging(user_email, "file-command", message['cmd'], json.dumps(message), "", {})

#    if message['cmd'] == 'save_esdl':
#        esh = get_handler()
#        try:
#            write_energysystem_to_file('./static/EnergySystem.esdl', esh)
#            # TODO: do we need to flush??
#            emit('and_now_press_download_file')
#        except Exception as e:
#            send_alert('Error saving ESDL file to filesystem - exception: '+str(e))

#    if message['cmd'] == 'download_esdl':
#        esh = get_handler()
#        name = get_session('es_title').replace(' ', '_')
#
#        send_ESDL_as_file(esh, name)


# ---------------------------------------------------------------------------------------------------------------------
#  Connect from browser
#   - initialize energysystem information
#   - send info to browser
# ---------------------------------------------------------------------------------------------------------------------
def initialize_app():
    session.permanent = True
    print('Client connected: ', request.sid)

    if 'client_id' in session:
        print ('Energysystem in memory - reloading client data')
        esh = get_handler()
    else:
        print ('No energysystem in memory - generating empty energysystem')
        esh = EnergySystemHandler()
        esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area')

    es_info_list = {}
    set_session("es_info_list", es_info_list)
    emit('clear_ui')
    emit('clear_esdl_layer_list')
    process_energy_system.submit(esh, None, None) # run in a seperate thread
    #thread = threading.Thread(target=process_energy_system, args=(esh,None,title,current_app._get_current_object()))
    #thread.start()
    #session.modified = True


@socketio.on('connect', namespace='/esdl')
def connect():
    print("Websocket connection established")

    if 'id' in session:
        print('- Old socketio id={}, new socketio id={}'.format(session['id'], request.sid))
    else:
        print('- Old socketio id={}, new socketio id={}'.format(None, request.sid))
    session['id'] = request.sid
    set_session('socketio_sid', request.sid)

    # Client ID is used to retrieve session variables in handler_manager
    # So this is a very important session variable!!
    if 'client_id' in session:
        print('- Client id: {}'.format(session['client_id']))
    else:
        print('- No client id in session')
    if not valid_session():
        send_alert("Session has timed out, please refresh")


def get_qau_information():
    qau_info = dict()
    qau_info['generic'] = ESDLQuantityAndUnits.get_qau_information()
    qau_info['profile_type_enum_values'] = ESDLQuantityAndUnits.get_profile_type_enum_values()
    qau_info['predefined_qau'] = esdl_config.esdl_config['predefined_quantity_and_units']
    return qau_info


@socketio.on('initialize', namespace='/esdl')
def browser_initialize():
    role = get_session('user-role')

    print('Send initial information to client')
    emit('profile_info', esdl_profiles.get_profiles_list(role))
    emit('control_strategy_config', esdl_config.esdl_config['control_strategies'])
    emit('wms_layer_list', wms_layers.get_layers())
    emit('capability_list', ESDLAsset.get_capabilities_list())
    emit('qau_information', get_qau_information())
    emit('esdl_services', esdl_services.get_services_list(role))
    initialize_app()


# ---------------------------------------------------------------------------------------------------------------------
#  Disconnect
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect', namespace='/esdl')
def on_disconnect():
    print('Client disconnected: {}'.format(request.sid))


# ---------------------------------------------------------------------------------------------------------------------
#  Error logging
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on_error_default
def default_error_handler(e):
    print('Error in SocketIO handler: %s' % e)
    import traceback
    print('\tSocket IO message: %s' % request.event["message"]) # "my error event"
    print('\tSocket IO arguments: {}'.format(request.event["args"]))
    traceback.print_exc()

# ---------------------------------------------------------------------------------------------------------------------
#  Start application
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    parse_esdl_config()
    print("Starting App")

    user_actions_logging.store_logging("System", "application start", "", "", "", {})
    socketio.run(app, debug=settings.FLASK_DEBUG, host=settings.FLASK_SERVER_HOST, port=settings.FLASK_SERVER_PORT, use_reloader=False)

