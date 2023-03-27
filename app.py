#!/usr/bin/env python

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

import importlib
import json
import urllib
import uuid
import traceback
from datetime import datetime
from pprint import pprint
from warnings import warn

import jwt
import requests
from flask import Flask, Response, redirect, render_template, request, send_from_directory, session
from flask_executor import Executor
from flask_oidc import OpenIDConnect
from flask_session import Session
from flask_socketio import SocketIO, emit
from pyecore.ecore import EDate

import src.esdl_config as esdl_config
import src.settings as settings
from esdl import esdl
from esdl.esdl_handler import EnergySystemHandler
from esdl.processing import ESDLAsset, ESDLEcore, ESDLEnergySystem, ESDLGeometry, ESDLQuantityAndUnits
from esdl.processing.ESDLAsset import get_asset_capability_type
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from extensions.bag import BAG
from extensions.boundary_service import BoundaryService
from extensions.es_statistics import ESStatisticsService
from extensions.esdl_api import ESDL_API
from extensions.esdl_browser import ESDLBrowser
from extensions.esdl_compare import ESDLCompare
from extensions.esdl_drive import ESDLDrive
from extensions.esdl_merge import ESDLMerge
from extensions.essim import ESSIM
from extensions.essim_sensitivity import ESSIMSensitivity
from extensions.etm_local import ETMLocal
from extensions.heatnetwork import HeatNetwork
from extensions.ibis import IBISBedrijventerreinen
from extensions.ielgas import IELGAS
from extensions.mapeditor_settings import MAPEDITOR_UI_SETTINGS, MapEditorSettings
from extensions.pico_rooftoppv_potential import PICORooftopPVPotential
from extensions.port_profile_viewer import PortProfileViewer
from extensions.profiles import Profiles
from extensions.session_manager import del_session, delete_sessions_on_disk, get_handler, get_session, \
    get_session_for_esid, schedule_session_clean_up, set_handler, set_session, set_session_for_esid, valid_session
from extensions.settings_storage import SettingsStorage
from extensions.shapefile_converter import ShapefileConverter
from extensions.spatial_operations import SpatialOperations
from extensions.time_dimension import TimeDimension
# from extensions.vesta import Vesta
from extensions.workflow import Workflow
from src.asset_draw_toolbar import AssetDrawToolbar
from src.assets_to_be_added import AssetsToBeAdded
from src.datalayer_api import DataLayerAPI
from src.edr_assets import EDRAssets
from src.esdl2shapefile import ESDL2Shapefile
from src.esdl_helper import asset_state_to_ui, generate_profile_info, get_asset_and_coord_from_port_id, \
    get_asset_from_port_id, get_connected_to_info, get_port_profile_info, get_tooltip_asset_attrs, \
    update_carrier_conn_list, add_spatial_attributes
from src.esdl_services import ESDLServices
from src.essim_kpis import ESSIM_KPIs
from src.essim_validation import validate_ESSIM
from src.log import get_logger
from src.process_es_area_bld import get_building_information, process_energy_system, get_building_connections
from src.user_logging import UserLogging
from src.version import __long_version__ as mapeditor_version
from src.view_modes import ViewModes
from src.wms_layers import WMSLayers
from src.table_editor import TableEditor
from src.esdl_file_io import ESDLFileIO
from src.release_notes import ReleaseNotes
from src.custom_icons import CustomIcons
from utils.datetime_utils import parse_date

print('MapEditor version {}'.format(mapeditor_version))
logger = get_logger(__name__)

if settings.USE_GEVENT:
    import gevent.monkey
    gevent.monkey.patch_all()
    logger.info("Using GEvent")

#TODO fix send_file in uwsgi
# debugging with pycharm:
#https://stackoverflow.com/questions/21257568/debugging-a-uwsgi-python-application-using-pycharm/25822477

user_actions_logging = UserLogging()
if settings.settings_storage_config["host"] is None or settings.settings_storage_config["host"] == "":
    logger.error("Settings storage is not configured. Aborting...")
    exit(1)
settings_storage = SettingsStorage(database_uri='mongodb://' + settings.settings_storage_config["host"] + ':' + settings.settings_storage_config["port"])


# handler to retrieve ESDL documentation
esdl_doc = EcoreDocumentation(esdlEcoreFile="esdl/esdl.ecore")


def is_running_in_uwsgi():
    try:
        import uwsgi
        a = uwsgi.opt
        logger.info("uWSGI startup options: {}".format(a))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------------------------------------------------
#  Application definition, configuration and setup of simple file server
# ---------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = b'\xc3g\x19\xbf\x8e\xa0\xe7\xc8\x9a/\xae%\x04g\xbe\x9f\xaex\xb5\x8c\x81f\xaf`' #os.urandom(24)   #'secret!'
app.config['SESSION_COOKIE_NAME'] = 'ESDL-WebEditor-session'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 60*60*24 # 1 day in seconds
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True # make sure errors are logged for tasks run in threads

logger.info("Socket.IO Async mode: {}".format(settings.ASYNC_MODE))
logger.info('Running inside uWSGI: {}'.format(is_running_in_uwsgi()))

socketio = SocketIO(app, async_mode=settings.ASYNC_MODE, manage_session=False, path='/socket.io', logger=settings.FLASK_DEBUG)
# logging.getLogger('engineio').setLevel(logging.WARNING)  # don't print all the messages

# remove existing sessions when restarting, existing sessions will give errors
# as associated ESDLs are not stored in the session and the OpenId connect info is wrong
delete_sessions_on_disk(app.config['SESSION_FILE_DIR'])

# fix sessions with socket.io. see: https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
Session(app)


executor = Executor(app)

#extensions
schedule_session_clean_up()
wms_layers = WMSLayers(app, socketio, settings_storage)
HeatNetwork(app, socketio)
IBISBedrijventerreinen(app, socketio)
ESDLBrowser(app, socketio, esdl_doc)
BAG(app, socketio)
BoundaryService(app, socketio, settings_storage)
esdl_api = ESDL_API(app, socketio)
ESDLCompare(app, socketio)
ESDLMerge(app, socketio, executor)
essim_kpis = ESSIM_KPIs(app, socketio)
essim = ESSIM(app, socketio, executor, essim_kpis, settings_storage)
ESSIMSensitivity(app, socketio, settings_storage, essim)
# Vesta(app, socketio, settings_storage)
Workflow(app, socketio, settings_storage)
ESStatisticsService(app, socketio)
MapEditorSettings(app, socketio, settings_storage)
profiles = Profiles(app, socketio, executor, settings_storage)
ESDLDrive(app, socketio, executor)
ShapefileConverter(app, socketio, executor)
time_dimension = TimeDimension(app, socketio, executor, settings_storage)
IELGAS(app, socketio, settings_storage)
ETMLocal(app, socketio, settings_storage)
PortProfileViewer(app, socketio, settings_storage)
esdl_services = ESDLServices(app, socketio, settings_storage)
PICORooftopPVPotential(app, socketio)
SpatialOperations(app, socketio)
DataLayerAPI(app, socketio, esdl_doc)
ViewModes(app, socketio, settings_storage)
edr_assets = EDRAssets(app, socketio, settings_storage)
AssetsToBeAdded(app, socketio)
AssetDrawToolbar(app, socketio, settings_storage)
TableEditor(app, socketio, esdl_doc, settings_storage)
ESDLFileIO(app, socketio, executor)
ReleaseNotes(app, socketio, settings_storage)
ESDL2Shapefile(app)
custom_icons = CustomIcons(app, socketio, settings_storage)


#TODO: check secret key with itsdangerous error and testing and debug here

app.config.update({
    'TESTING': True,
    'DEBUG': True,
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'esdl-mapeditor',
    'OIDC_SCOPES': ['openid', 'email', 'profile', 'groups', 'microprofile-jwt'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_CLIENT_SECRETS': settings.OIDC_CLIENT_SECRETS
})

try:
    oidc = OpenIDConnect(app)
except Exception as e:
    logger.exception("Something went wrong when connecting to Keycloak")
    import sys
    sys.exit(1)


# TEMPORARY SOLUTION TO DISABLE BROWSER CACHING DURING TESTING
@app.after_request
def add_header(r: Response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    if r.content_type == 'image/png': # images are allowed to be cached.
        return r
    if settings.FLASK_DEBUG:    # only prevent caching when debugging
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
    store_enabled = settings.esdl_store_config or settings.mondaine_hub_config
    return render_template('index.html', store_enabled=store_enabled)


"""
# test for OpenID connect authentication against KeyCloak
@app.route('/test')
@oidc.require_login
def test_authentication():
    if oidc.user_loggedin:
        user_email = oidc.user_getfield('email')
        user_groups = oidc.user_getfield('user_group')
        logger.debug('user: {}, user groups: {}'.format(user_email, user_groups))
        whole_token = oidc.get_access_token()
        if whole_token:
            jwt_tkn = jwt.decode(whole_token, key=settings.IDM_PUBLIC_KEY, algorithms='RS256', audience='account',
                                 verify=True)
            pprint(jwt_tkn)
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
    logger.info('client_id is set to %s' % session['client_id'])
    if oidc.user_loggedin:
        if session['client_id'] == None:
            warn('WARNING: No client_id in session!!')

        whole_token = oidc.get_access_token()
        logger.debug(f"whole_token: {whole_token}")
        if whole_token:
            try:
                jwt_tkn = jwt.decode(whole_token, algorithms='RS256', verify=False)
                pprint(jwt_tkn)
            except Exception as e:
                logger.exception(f"error in decoding token: {str(e)}")
        # if role in access_token['resource_access'][client]['roles']:

        user_email = oidc.user_getfield('email')

        logger.info("************* USER LOGIN (" + user_email + ") at " + str(datetime.now()))
        user_actions_logging.store_logging(user_email, "login", "", "", "", {})

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
        set_session('jwt-token', whole_token)

        user_fullname = oidc.user_getfield('name')
        set_session('user-fullname', user_fullname)

        esdl_store_enabled = not(settings.esdl_store_config["hostname"] is None or settings.esdl_store_config["hostname"] == "")
        mondaine_hub_enabled = not(settings.mondaine_hub_config["hostname"] is None or settings.mondaine_hub_config["hostname"] == "")
        store_enabled = esdl_store_enabled or mondaine_hub_enabled
        esdl_drive_enabled = not(settings.esdl_drive_config["hostname"] is None or settings.esdl_drive_config["hostname"] == "")
        edr_enabled = not(settings.edr_config["host"] is None or settings.edr_config["host"] == "")
        essim_enabled = not(settings.essim_config["ESSIM_host"] is None or settings.essim_config["ESSIM_host"] == "")
        boundary_service_enabled = not(settings.boundaries_config["host"] is None or settings.boundaries_config["host"] == "")
        statistics_service_enabled = not(settings.statistics_settings_config["host"] is None or settings.statistics_settings_config["host"] == "")
        bag_service_enabled = not(settings.bag_config["host"] is None or settings.bag_config["host"] == "")
        ibis_service_enabled = not(settings.ibis_config["host"] is None or settings.ibis_config["host"] == "")

        logger.info("store:{} drive:{} edr:{} bound:{} stat:{} bag:{} ibis:{}".format(store_enabled, esdl_drive_enabled,
            edr_enabled, boundary_service_enabled, statistics_service_enabled,bag_service_enabled, ibis_service_enabled))

        return render_template('editor.html',async_mode=socketio.async_mode,
                               role=role,
                               store_enabled=store_enabled,
                               esdl_drive_enabled=esdl_drive_enabled,
                               edr_enabled=edr_enabled,
                               essim_enabled=essim_enabled,
                               boundary_service_enabled=boundary_service_enabled,
                               statistics_service_enabled=statistics_service_enabled,
                               bag_service_enabled=bag_service_enabled,
                               ibis_service_enabled=ibis_service_enabled,
                               debug=settings.FLASK_DEBUG,
                               version=mapeditor_version
                               )
    else:
        return render_template('index.html')
        # to enable working offline without IDM:
        # - comment the @oidc.require_login above this method
        # - comment the line above: return render_template('index.html')
        # - uncomment the following line:
        # return render_template('editor.html', async_mode=socketio.async_mode, role=role)


"""
Checks the OpenID connect session status
And refreshes if necessary?
"""
@app.route('/auth_status')
#@oidc.require_login
def auth_status():
    from flask import g
    #logger.debug("Global token: {}".format(g.oidc_id_token))
    status: Response = oidc.authenticate_or_redirect()
    if status is None:
        if oidc.user_loggedin:
            curr_token = get_session('jwt-token')
            if oidc.get_access_token() is not None:
                if curr_token is not None and curr_token == oidc.get_access_token():
                    return {'valid': True, 'reason': "Unchanged"}
                else:
                    logger.info("Refreshed access token for {}".format(oidc.user_getfield('email')))
                    set_session('jwt-token', oidc.get_access_token())
                    return {'valid': True, 'reason': "Refreshed"}
            else:
                # this is the case when we restarted the app, but the browser still has a valid cookie and
                # seems still authorized, while the token has not been refreshed or is accessible via oidc.
                #if g.oidc_id_token is not None:
                    # update oidc with session info
                    #oidc.credentials_store[g.oidc_id_token['sub']] = g.oidc_id_token
                    #logger.debug("Setting cookie access token ", oidc.get_access_token())
                    #set_session('jwt-token', oidc.get_access_token())
                    #return {'valid': True, 'reason': "Updated token"}
                g.oidc_id_token = None
                oidc.logout()
                status: Response = oidc.redirect_to_auth_server('/editor')
                uri = status.headers["Location"]
                return {'valid': False, 'reason': "Token expired or not available", 'redirect_uri': uri}
        else:
            oidc.logout()
            return {'valid': False, 'reason': "Not logged in"}
    else:
        status: Response = oidc.redirect_to_auth_server('/editor') # get redirect for /editor, not /auth_status
        uri = status.headers["Location"]
        return {'valid': False, 'reason': "Authentication required", 'redirect_uri': uri}
        # return status  # returns a redirect, but that is consumed by the browser because of a 302 status


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
        my_es = esh.get_energy_system(es_id=active_es_id)
        esh.update_version(es_id=active_es_id)
        if my_es.esdlVersion is None or my_es.esdlVersion == '':
            my_es.esdlVersion = esdl_doc.get_esdl_version()
        try:
            name = my_es.name
        except:
            name = my_es.id
        if name is None or name == '':
            name = "UntitledEnergySystem"
        name = '{}.esdl'.format(name)
        logger.info('Sending file %s' % name)

        user_email = get_session('user-email')
        user_actions_logging.store_logging(user_email, "download esdl", name, "", "", {})
        content = esh.to_string(es_id=active_es_id)

        #wrapped_io = FileWrapper(stream)
        #logger.debug(content)
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
    # logger.debug('in serve_static(): '+ path)
    return send_from_directory('static', path)


# @app.route('/edr_assets')
# def get_edr_assets():
#     edr_url = settings.edr_config['EDR_host']+'/store/tagged?tag=asset'
#     # logger.debug('accessing URL: '+edr_url)
#
#     try:
#         r = requests.get(edr_url)
#         if r.status_code == 200:
#             result = json.loads(r.text)
#             asset_list = []
#             for a in result:
#                 asset = {'id': a["id"], 'title': a["title"], 'description': a["description"]}
#                 asset_list.append(asset)
#
#             return (jsonify({'asset_list': asset_list})), 200
#         else:
#             logger.error('code: ', r.status_code)
#             send_alert('Error in getting the EDR assets')
#             abort(500, 'Error in getting the EDR assets')
#     except Exception as e:
#         logger.error('Exception: ')
#         logger.error(e)
#         send_alert('Error accessing EDR API')
#         abort(500, 'Error accessing EDR API')


# ---------------------------------------------------------------------------------------------------------------------
#  File I/O and ESDL Store API calls
# ---------------------------------------------------------------------------------------------------------------------
if settings.esdl_store_config is not None and settings.esdl_store_config != "":
    default_store_url = settings.esdl_store_config['hostname'] + '/store/'
else:
    default_store_url = None
if settings.mondaine_hub_config is not None and settings.mondaine_hub_config != "":
    mondaine_hub_url = settings.mondaine_hub_config['hostname'] + '/store/'
else:
    mondaine_hub_url = None


def create_ESDL_store_item(id, esh, title, description, email):
    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    if store_url:
        esdlstr = esh.to_string()
        try:
            payload = {'id': id, 'title': title, 'description': description, 'email':email, 'esdl': esdlstr}
            requests.post(store_url, data=payload)
        except Exception as e:
            send_alert('Error accessing ESDL store:' + str(e))


def load_ESDL_EnergySystem(store_id):
    store_item = load_store_item(store_id)
    if store_item:
        esdlstr = store_item['esdl']

        del store_item['esdl']
        set_session('store_item_metadata', store_item)
        emit('store_item_metadata', store_item)

        try:
            esh = get_handler()
            es, parse_info = esh.load_from_string(esdl_string=esdlstr, name=store_item['title'])
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                send_alert("Warnings while opening {}:\n\n{}".format(store_item['title'], info))
            return esh
        except Exception as e:
            send_alert('Error interpreting ESDL file from store: ' + str(e))
            return None
    else:
        return None


def import_ESDL_EnergySystem(store_id):
    store_item = load_store_item(store_id)
    if store_item:
        esdlstr = store_item['esdl']

        del store_item['esdl']
        set_session('store_item_metadata', store_item)
        emit('store_item_metadata', store_item)

        try:
            esh = get_handler()
            imported_es, parse_info = esh.add_from_string(esdl_string=esdlstr, name=store_item['title'])
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                send_alert("Warnings while opening {}:\n\n{}".format(store_item['title'], info))
            return imported_es
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

    if store_url:
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
            logger.error('Accessing store return status: '+str(r.status_code))
            send_alert('Error accessing ESDL store:' + str(r))
            return None
    else:
        return None


def update_store_item(store_id, title, descr, email, tags, esh):
    role = get_session('user-role')
    if 'mondaine' in role:
        store_url = mondaine_hub_url
    else:
        store_url = default_store_url

    if store_url:
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

    if store_url:
        esdlstr = esh.to_string()

        payload = {'id': store_id, 'title': title, 'description': descr, 'email': email, 'tags': tags, 'esdl': esdlstr}
        try:
            r = requests.post(store_url, data=payload)
        except Exception as e:
            send_alert('Error saving ESDL file to store: ' + str(e))

        if r.status_code != 201:
            send_alert('Error saving ESDL file to store. Error code: ' + str(r.status_code))


# ---------------------------------------------------------------------------------------------------------------------
#  parse the ESDL config file
# ---------------------------------------------------------------------------------------------------------------------
def parse_esdl_config():
    esdlc = esdl_config.esdl_config
    logger.info('Configuration found: {}'.format(esdlc))


# ---------------------------------------------------------------------------------------------------------------------
#  Send alert to client UI
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    logger.warning(message)
    emit('alert', message, namespace='/esdl')


# FIXME: pyecore
def _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)
    processed_assets.append(asset_id)

    port_list = []

    for p in asset.port:
        p.carrier = esh.get_by_id(active_es_id, carrier_id) #FIXME pyecore
        conn_to = p.connectedTo
        if conn_to:
            for conn_port in conn_to:
                conn_asset = get_asset_from_port_id(esh, active_es_id, conn_port.id)
                if isinstance(conn_asset, esdl.Transport) and not isinstance(conn_asset, esdl.HeatExchange) \
                        and not isinstance(conn_asset, esdl.Transformer):
                    if conn_asset.id not in processed_assets:
                        _set_carrier_for_connected_transport_assets(conn_asset.id, carrier_id, processed_assets)
                else:
                    conn_asset_port_list = []
                    for conn_asset_port in conn_asset.port:
                        if conn_asset_port.id == conn_port.id:
                            conn_asset_port.carrier = p.carrier
                            for conn_to_same_port in conn_asset_port.connectedTo:
                                if conn_to_same_port.id is not p.id: # don't traverse back to the original port
                                    conn_to_same_port_asset = get_asset_from_port_id(esh, active_es_id, conn_to_same_port.id)
                                    if not conn_to_same_port_asset.id in processed_assets:
                                        _set_carrier_for_connected_transport_assets(conn_to_same_port_asset.id, carrier_id, processed_assets)
                        conn_asset_port_list.append({'name': conn_asset_port.name, 'id': conn_asset_port.id,
                            'type': type(conn_asset_port).__name__, 'conn_to': [pt.id for pt in conn_asset_port.connectedTo],
                            'carrier': conn_asset_port.carrier.id if conn_asset_port.carrier else None})
                    # also update the ports of the 'leaf' asset (recursion stops here)
                    emit('update_asset', {'asset_id': conn_asset.id, 'ports': conn_asset_port_list})
        port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                          'conn_to': [pt.id for pt in p.connectedTo], 'carrier': p.carrier.id if p.carrier else None})
    # update the asset ports in the gui, if the carrier has changed.
    emit('update_asset', {'asset_id': asset.id, 'ports': port_list})


def set_carrier_for_connected_transport_assets(asset_id, carrier_id):
    processed_assets = []  # List of asset_id's that are processed
    _set_carrier_for_connected_transport_assets(asset_id, carrier_id, processed_assets)
    # logger.debug(processed_assets)




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


# TODO: Not used now, should we keep the conn_list updated? --> Yes, now we do! For redrawing when selecting carriers
# 13-1-2020: Commented out: energycarrier info for port not added yet because function is not used at the moment.
#def add_connection_to_list(conn_list, from_port_id, from_asset_id, from_asset_coord, to_port_id, to_asset_id, to_asset_coord):
#    conn_list.append(
#        {'from-port-id': from_port_id, 'from-asset-id': from_asset_id, 'from-asset-coord': from_asset_coord,
#         'to-port-id': to_port_id, 'to-asset-id': to_asset_id, 'to-asset-coord': to_asset_coord})


def update_asset_connection_locations(asset: esdl.Asset, lat, lon):
    active_es_id = get_session('active_es_id')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')
    ass_id = asset.id
    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            c['from-asset-coord'] = (lat, lon)
        if c['to-asset-id'] == ass_id:
            c['to-asset-coord'] = (lat, lon)

    emit('clear_connections')   # clear current active layer connections
    add_to_building = False
    if asset.containingBuilding:
        # building editor is open, so only update building connections.
        building = asset.containingBuilding
        bld_info = get_building_information(building)
        conn_list = bld_info["conn_list"]
        add_to_building = True
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list, 'add_to_building': add_to_building})


def update_transport_connection_locations(ass_id, asset, coords):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    conn_list = get_session_for_esid(active_es_id, 'conn_list')

    # logger.debug('Updating locations')
    for c in conn_list:
        if c['from-asset-id'] == ass_id:
            port_id = c['from-port-id']
            port_ass_map = get_asset_and_coord_from_port_id(esh, active_es_id, port_id)
            c['from-asset-coord'] = port_ass_map['coord']
        if c['to-asset-id'] == ass_id:
            port_id = c['to-port-id']
            port_ass_map = get_asset_and_coord_from_port_id(esh, active_es_id, port_id)
            c['to-asset-coord'] = port_ass_map['coord']

    emit('clear_connections')   # clear current active layer connections
    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})


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


# ---------------------------------------------------------------------------------------------------------------------
#  Create connections between assets
# ---------------------------------------------------------------------------------------------------------------------
def connect_ports(port1, port2):
    port1.connectedTo.append(port2)


def split_conductor(conductor, location, mode, conductor_container):
    active_es_id = get_session('active_es_id')
    conn_list = get_session_for_esid(active_es_id, 'conn_list')
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
        logger.debug('segment min = {}'.format(min_dist_segm))
        for point in list(points):
            if segm_ctr == min_dist_segm:
                new_point = esdl.Point(lon=middle_point.lon, lat=middle_point.lat, elevation=middle_point.elevation)
                line1.point.append(new_point)
                line2.point.append(new_point.clone())
            if segm_ctr < min_dist_segm:
                line1.point.append(point)
            else:
                line2.point.append(point)
            segm_ctr += 1

        # find old ports and connections
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

        # create two conductors of same type as conductor that is splitted by duplicating the original
        # e.g. also copy over the pipe material
        new_cond1 = conductor.deepcopy()
        new_cond2 = conductor.deepcopy()
        if new_cond1.name == new_cond1.eClass.name + '_' + new_cond1.id[:4]:
            new_cond1.name = new_cond1.eClass.name + '_' + new_cond1_id[:4]
            new_cond2.name = new_cond2.eClass.name + '_' + new_cond2_id[:4]
        else:
            new_cond2.name = new_cond1.name + '_b'
            new_cond1.name = new_cond1.name + '_a'
        new_cond1.id = new_cond1_id
        new_cond1.port.clear()  # remove existing port, as we add previous used ports later
        new_cond2.id = new_cond2_id
        new_cond2.port.clear()
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
        new_cond1.length = round(length, 2)

        start = line2.point[0]
        length = 0
        for i in range(1, len(line2.point)):
            length += ESDLGeometry.distance((start.lat, start.lon), (line2.point[i].lat, line2.point[i].lon)) * 1000
            start = line2.point[i]
        new_cond2.length = round(length, 2)

        logger.debug('split-conductor: line1 length={}, line2 length={}'.format(new_cond1.length, new_cond2.length))
        # assign line geometry to the correct conductor
        new_cond1.geometry = line1
        new_cond2.geometry = line2

        # remove conductor from container (area or building) and add new two conductors
        assets = conductor_container.asset
        assets.remove(conductor)
        esh.remove_object_from_dict(active_es_id, conductor)
        conductor_container.asset.append(new_cond1)
        conductor_container.asset.append(new_cond2)

        # create list of ESDL assets to be added to UI
        esdl_assets_to_be_added = []
        coords1 = []
        for point in line1.point:
            coords1.append([point.lat, point.lon])
        port_list = []
        carrier = None
        if port1.carrier: carrier = port1.carrier
        if port2.carrier: carrier = port2.carrier
        carrier_id = carrier.id if carrier is not None else None
        for p in new_cond1.port:
            p.carrier = carrier
            port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                              'conn_to': [p.id for p in p.connectedTo], 'carrier': carrier_id})
        state = asset_state_to_ui(new_cond1)
        tooltip_asset_attrs = get_tooltip_asset_attrs(new_cond1, 'line')
        add_spatial_attributes(new_cond1, tooltip_asset_attrs)
        esdl_assets_to_be_added.append(['line', 'asset', new_cond1.name, new_cond1.id, type(new_cond1).__name__,
                                        coords1, tooltip_asset_attrs, state, port_list])
        coords2 = []
        for point in line2.point:
            coords2.append([point.lat, point.lon])
        port_list = []

        for p in new_cond2.port:
            p.carrier = carrier
            port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                              'conn_to': [p.id for p in p.connectedTo], 'carrier': carrier_id})
        state = asset_state_to_ui(new_cond2)
        tooltip_asset_attrs = get_tooltip_asset_attrs(new_cond2, 'line')
        add_spatial_attributes(new_cond2, tooltip_asset_attrs)
        esdl_assets_to_be_added.append(['line', 'asset', new_cond2.name, new_cond2.id, type(new_cond2).__name__,
                                        coords2, tooltip_asset_attrs, state, port_list])

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
            conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': carrier_id,
                              'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                              'to-port-id': new_port1_id, 'to-port-carrier': carrier_id, 'to-asset-id': new_cond2_id,
                              'to-asset-coord': (middle_point.lat, middle_point.lon)})

        if mode == 'add_joint':
            joint_id = str(uuid.uuid4())
            joint = esdl.Joint(id=joint_id, name='Joint_'+joint_id[:4])
            inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
            outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
            if carrier:
                inp.carrier = carrier
                outp.carrier = carrier

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

            port_list = []
            for p in joint.port:
                p.carrier = carrier
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                                  'conn_to': [p.id for p in p.connectedTo], 'carrier': carrier_id})
            capability_type = ESDLAsset.get_asset_capability_type(joint)
            state = asset_state_to_ui(joint)
            tooltip_asset_attrs = get_tooltip_asset_attrs(joint, 'marker')
            esdl_assets_to_be_added.append(['point', 'asset', joint.name, joint.id, type(joint).__name__,
                                            [middle_point.lat, middle_point.lon], tooltip_asset_attrs, state, port_list,
                                            capability_type, {}])

            conn_list.append({'from-port-id': new_port2_id, 'from-port-carrier': carrier_id,
                              'from-asset-id': new_cond1_id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                              'to-port-id': new_port2_conn_to_id, 'to-port-carrier': carrier_id,
                              'to-asset-id': joint.id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})
            conn_list.append({'from-port-id': new_port1_conn_to_id, 'from-port-carrier': carrier_id,
                              'from-asset-id': joint.id, 'from-asset-coord': (middle_point.lat, middle_point.lon),
                              'to-port-id': new_port1_id, 'to-port-carrier': carrier_id,
                              'to-asset-id': new_cond2_id, 'to-asset-coord': (middle_point.lat, middle_point.lon)})

        # now send new objects to UI
        emit('add_esdl_objects', {'es_id': active_es_id, 'asset_pot_list': esdl_assets_to_be_added, 'zoom': False})
        emit('clear_connections')   # clear current active layer connections
        emit('delete_esdl_object', {'asset_id': conductor.id}) # remove original condutor from map
        emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})
    else:
        send_alert('UNSUPPORTED: Conductor is not of type esdl.Line!')


# ---------------------------------------------------------------------------------------------------------------------
#  Update ESDL coordinates on movement of assets in browser
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('update-coord', namespace='/esdl')
def update_coordinates(message):
    # This function can also be called when the geometry of an asset is of type esdl.Polygon, because
    # the asset on the leaflet map is both represented as a Polygon and a Point (to connect, to attach menus)

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    obj_id = message['id']
    coords = message['coordinates']

    object = esh.get_by_id(active_es_id, obj_id)
    # object can be an EnergyAsset, Building, Potential or Note
    if object:
        if isinstance(object, esdl.Note):
            geom = object.mapLocation
        else:
            geom = object.geometry

        if isinstance(geom, esdl.Point):
            point = esdl.Point(lon=float(coords['lng']), lat=float(coords['lat']))
            if isinstance(object, esdl.Note):
                object.mapLocation = point
            else:
                object.geometry = point
        # elif isinstance(geom, esdl.Polygon):
            # Do nothing in case of a polygon
            # only update the connection locations and mappings based on the center of the polygon
            # that is given as a parameter.

        # update coordinates in asset_list
        asset_list = get_session_for_esid(active_es_id, 'asset_list')
        for a in asset_list:
            if a[3] == obj_id:
                a[5] = [coords['lat'], coords['lng']]
                break # ready searching

        if isinstance(object, (esdl.EnergyAsset, esdl.AbstractBuilding)):
            # Update locations of connections on moving assets
            update_asset_connection_locations(object, coords['lat'], coords['lng'])

            # TODO: Check if this is still required: Ewoud: No
            #if message['asspot'] == 'building':
            #    send_alert("Assets in building with locations are not updated yet")


@socketio.on('update-line-coord', namespace='/esdl')
def update_line_coordinates(message):
    # logger.debug ('received polyline: ' + str(message['id']) + ':' + str(message['polyline']))
    ass_id = message['id']

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, ass_id)

    if asset:
        ports = asset.port
        polyline_data = message['polyline']
        # logger.debug(polyline_data)
        # logger.debug(type(polyline_data))
        polyline_length = float(message['length'])
        asset.length = polyline_length

        line = esdl.Line()
        for i in range(0, len(polyline_data)):
            coord = polyline_data[i]
            point = esdl.Point(lon=coord['lng'], lat=coord['lat'])
            line.point.append(point)
        asset.geometry = line

        # update coordinates in asset_list
        asset_list = get_session_for_esid(active_es_id, 'asset_list')
        for a in asset_list:
            if a[3] == ass_id:
                a[5] = [(coord['lat'], coord['lng']) for coord in polyline_data]
                break  # ready searching

        update_transport_connection_locations(ass_id, asset, polyline_data)


@socketio.on('update-polygon-coord', namespace='/esdl')
def update_polygon_coordinates(message):
    # logger.debug ('received polygon: ' + str(message['id']) + ':' + str(message['polygon']))
    ass_id = message['id']

    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, ass_id)

    if asset:
        polygon_data = message['polygon']
        # logger.debug(polygon_data)
        # logger.debug(type(polygon_data))
        polygon_area = int(message['polygon_area'])
        asset.surfaceArea = polygon_area

        polygon_data = ESDLGeometry.remove_duplicates_in_polygon(polygon_data)
        polygon_data = ESDLGeometry.remove_latlng_annotation_in_array_of_arrays(polygon_data)
        polygon_data = ESDLGeometry.exchange_polygon_coordinates(polygon_data)  # --> [lon, lat]
        polygon = ESDLGeometry.convert_pcoordinates_into_polygon(polygon_data)  # expects [lon, lat]
        asset.geometry = polygon

        polygon_center = ESDLGeometry.calculate_polygon_center(polygon)
        update_polygon_asset_connection_locations(ass_id, polygon_center)


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


def remove_marginal_costs_for_asset(asset_id):
    active_es_id = get_session('active_es_id')
    esh = get_handler()
    asset = esh.get_by_id(active_es_id, asset_id)

    ci = asset.costInformation
    if ci:
        mc = ci.marginalCosts
        if mc:
            mc.delete()


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


@executor.job
def call_process_energy_system(esh, filename=None, es_title=None, app_context=None, force_update_es_id=None, zoom=True):
    process_energy_system(esh, filename, es_title, app_context, force_update_es_id, zoom)


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('command', namespace='/esdl')
def process_command(message):
    logger.info('received: ' + message['cmd'])
    if not valid_session():
        send_alert("Session has timed out, please refresh")
        return
    #logger.debug (message)
    #logger.debug (session)

    user_email = get_session('user-email')
    user_actions_logging.store_logging(user_email, "command", message['cmd'], json.dumps(message), "", {})

    active_es_id = get_session('active_es_id')
    if active_es_id is None:
        send_alert('Serious error: no active es id found. Please report')
        return

    esh = get_handler()
    if esh is None:
        logger.error('ERROR finding EnergySystemHandler, Session issue??')
    area_bld_list = get_session_for_esid(active_es_id, 'area_bld_list')

    es_edit = esh.get_energy_system(es_id=active_es_id)
    # test to see if this should be moved down:
    #  session.modified = True
    # logger.debug (get_handler().instance[0].area.name)

    if message['cmd'] == 'add_object':
        area_bld_id = message['area_bld_id']
        asset_id = message['asset_id']
        object_type = message['object']
        asset_name = message['asset_name']
        asset = None

        shape = message['shape']
        geometry = ESDLGeometry.create_ESDL_geometry(shape)

        if object_type == 'Area':
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
                    esh.add_object_to_dict(active_es_id, new_area)
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
                class_ = type(asset)
                object_type = class_.__name__
                print(asset)
                # Check if any IDs were 'accidentally' set in EDR model template and replace them by a new unique ID
                # If no ID was set, assign no new ID either
                for c in asset.eContents:
                    if c.eClass.findEStructuralFeature('id'):
                        if c.eGet('id'):
                            c.eSet('id', str(uuid.uuid4()))
            else:
                asset_drawing_mode = get_session('asset_drawing_mode')
                if asset_drawing_mode == 'asset_from_measures':
                    asset_from_measure_id = get_session('asset_from_measure_id')
                    asset = AssetsToBeAdded.get_instance_of_measure_with_asset_id(es_edit, asset_from_measure_id)
                    atba = AssetsToBeAdded.get_instance()
                    atba.reduce_ui_asset_count(es_edit, asset_from_measure_id)
                    class_ = type(asset)
                    object_type = class_.__name__
                else:
                    module = importlib.import_module('esdl.esdl')
                    class_ = getattr(module, object_type)
                    asset = class_()

            if issubclass(class_, esdl.Potential):
                potential = class_()
                potential.id = asset_id
                potential.name = asset_name
                potential.geometry = geometry

                add_to_building = False
                if not ESDLAsset.add_object_to_area(es_edit, potential, area_bld_id):
                    ESDLAsset.add_object_to_building(es_edit, potential, area_bld_id)
                    add_to_building = True

                potentials_to_be_added = []
                if isinstance(geometry, esdl.Point):
                    potentials_to_be_added.append(
                        ['point', 'potential', potential.name, potential.id, type(potential).__name__,
                         [geometry.lat, geometry.lon]])
                elif isinstance(geometry, esdl.Polygon):
                    coords = ESDLGeometry.parse_esdl_subpolygon(potential.geometry.exterior, False)  # [lon, lat]
                    coords = ESDLGeometry.exchange_coordinates(coords)
                    potentials_to_be_added.append(
                        ['polygon', 'potential', potential.name, potential.id, type(potential).__name__, coords])

                if potentials_to_be_added:
                    emit('add_esdl_objects', {'es_id': es_edit.id, 'add_to_building': add_to_building,
                                              'asset_pot_list': potentials_to_be_added, 'zoom': False})

                esh.add_object_to_dict(active_es_id, potential)
            else:
                asset.id = asset_id
                asset.name = asset_name
                asset.geometry = geometry

                if isinstance(geometry, esdl.Point):
                    port_loc = (shape['coordinates']['lat'], shape['coordinates']['lng'])
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

                # Set port existence booleans
                no_out_port = True
                no_in_port = True
                if isinstance(asset, esdl.EnergyAsset):
                    for p in asset.port:
                        if isinstance(p, esdl.OutPort):
                            no_out_port = False
                        if isinstance(p, esdl.InPort):
                            no_in_port = False

                if not isinstance(asset, esdl.AbstractBuilding):
                    # -------------------------------------------------------------------------------------------------------------
                    #  Add assets with a polyline geometry and an InPort and an OutPort
                    # -------------------------------------------------------------------------------------------------------------
                    if object_type in ['ElectricityCable', 'Pipe']:
                        # Assume pipes and cables never have ports (coming out of the EDR)
                        inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                        asset.port.append(inp)
                        outp = esdl.OutPort(id=str(uuid.uuid4()), name='Out')
                        asset.port.append(outp)
                        asset.length = float(shape['length']) if 'length' in shape else 0.0
                        print(message)
                        # automatically connect the conductor to the ports that have been clicked
                        if 'connect_ports' in message and message['connect_ports'] != '':
                            connect_ports_msg = message['connect_ports']
                            start_port = None
                            end_port = None
                            from_port1 = None
                            to_port1 = None
                            from_port2 = None
                            to_port2 = None
                            if 'asset_start_port' in connect_ports_msg:
                                asset_start_port = connect_ports_msg['asset_start_port']
                                start_port = esh.get_by_id(active_es_id, asset_start_port)
                            if 'asset_end_port' in connect_ports_msg:
                                asset_end_port = connect_ports_msg['asset_end_port']
                                end_port = esh.get_by_id(active_es_id, asset_end_port)

                            # cannot connect to same port type
                            if start_port is not None and end_port is not None and \
                                    type(start_port) == type(end_port):
                                other_type = esdl.InPort.eClass.name if isinstance(start_port, esdl.OutPort) \
                                    else esdl.OutPort.eClass.name
                                send_alert(
                                    "Please connect the {} to an {}".format(object_type, other_type))
                                return

                            require_reversed = False  # to indicate the coordinates of the line need reversal
                            if start_port is not None:
                                if isinstance(start_port, esdl.OutPort):
                                    inp.connectedTo.append(start_port)
                                    from_port1 = inp
                                    to_port1 = start_port
                                elif isinstance(start_port, esdl.InPort):
                                    outp.connectedTo.append(start_port)
                                    from_port1 = outp
                                    to_port1 = start_port
                                    require_reversed = True
                            if end_port is not None:
                                if isinstance(end_port, esdl.InPort):
                                    outp.connectedTo.append(end_port)
                                    from_port2 = outp
                                    to_port2 = end_port
                                elif isinstance(end_port, esdl.OutPort):
                                    inp.connectedTo.append(end_port)
                                    from_port2 = inp
                                    to_port2 = end_port
                                    require_reversed = True

                            if require_reversed:
                                line: esdl.Line = asset.geometry  # reverse coordinate to change direction of line
                                point = list(line.point)  # copy list
                                line.point.clear()
                                for p in point:
                                    line.point.insert(0, p)  # reverse list of coordinates

                            # Send connections
                            add_to_building = False  # TODO: Fix using this inside buildings
                            conn_list = get_session_for_esid(active_es_id, 'conn_list')
                            carrier_id = None
                            if start_port:
                                if isinstance(start_port, esdl.InPort):
                                    asset1_port_location = asset.geometry.point[-1]
                                else:
                                    asset1_port_location = asset.geometry.point[0]
                                if start_port.carrier is not None:
                                    carrier_id = start_port.carrier.id
                                    inp.carrier = start_port.carrier
                                    outp.carrier = start_port.carrier
                                    if end_port is not None and end_port.carrier is None:
                                        # in case of a joint: set the carrier for all ports
                                        if isinstance(end_port.energyasset, esdl.Joint):
                                            for p in end_port.energyasset.port:
                                                p.carrier = start_port.carrier if p.carrier is None else p.carrier
                                        else:
                                            end_port.carrier = start_port.carrier

                            if end_port:
                                if isinstance(end_port, esdl.InPort):
                                    asset2_port_location = asset.geometry.point[-1]
                                else:
                                    asset2_port_location = asset.geometry.point[0]
                                if end_port.carrier is not None and carrier_id is None:  # no start_port carrier
                                    carrier_id = end_port.carrier.id
                                    inp.carrier = end_port.carrier
                                    outp.carrier = end_port.carrier
                                    if start_port is not None and start_port.carrier is None:
                                        # in case of a joint: set the carrier for all ports
                                        if isinstance(start_port.energyasset, esdl.Joint):
                                            for p in start_port.energyasset.port:
                                                p.carrier = end_port.carrier if p.carrier is None else p.carrier
                                        else:
                                            start_port.carrier = end_port.carrier

                            # send messages to update connections and start port / end port marker colors based on
                            # the carriers
                            if start_port:
                                conn_message = {'from-port-id': from_port1.id,
                                                'from-port-carrier': from_port1.carrier.id if from_port1.carrier else None,
                                                'from-asset-id': from_port1.eContainer().id,
                                                'from-asset-coord': [asset1_port_location.lat, asset1_port_location.lon],
                                                'to-port-id': to_port1.id,
                                                'to-port-carrier': to_port1.carrier.id if to_port1.carrier else None,
                                                'to-asset-id': to_port1.eContainer().id,
                                                'to-asset-coord': [asset1_port_location.lat, asset1_port_location.lon]}
                                conn_list.append(conn_message)
                                emit('add_connections', {"es_id": active_es_id, "conn_list": [conn_message]})

                                # update ports of from_port asset
                                from_asset = start_port.eContainer()
                                port_list = []
                                for p in from_asset.port:
                                    port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                                                      'conn_to': [pt.id for pt in p.connectedTo],
                                                      'carrier': p.carrier.id if p.carrier else None})
                                emit('update_asset', {'asset_id': from_asset.id, 'ports': port_list})

                            if end_port:
                                conn_message = {'from-port-id': from_port2.id,
                                     'from-port-carrier': from_port2.carrier.id if from_port2.carrier else None,
                                     'from-asset-id': from_port2.eContainer().id,
                                     'from-asset-coord': [asset2_port_location.lat, asset2_port_location.lon],
                                     'to-port-id': to_port2.id,
                                     'to-port-carrier': to_port2.carrier.id if to_port2.carrier else None,
                                     'to-asset-id': to_port2.eContainer().id,
                                     'to-asset-coord': [asset2_port_location.lat, asset2_port_location.lon]}
                                conn_list.append(conn_message)
                                emit('add_connections', {"es_id": active_es_id, "conn_list": [conn_message]})

                                # update ports of from_port asset
                                to_asset = end_port.eContainer()
                                port_list = []
                                for p in to_asset.port:
                                    port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                                                      'conn_to': [pt.id for pt in p.connectedTo],
                                                      'carrier': p.carrier.id if p.carrier else None})
                                emit('update_asset', {'asset_id': to_asset.id, 'ports': port_list})

                    # -------------------------------------------------------------------------------------------------------------
                    #  Add assets with an InPort and two OutPorts (either point or polygon)
                    # -------------------------------------------------------------------------------------------------------------
                    elif object_type in ['CHP', 'FuelCell']:
                        # Assume CHPs and FuelCells never have ports (coming out of the EDR)
                        inp = esdl.InPort(id=str(uuid.uuid4()), name='In')
                        asset.port.append(inp)

                        e_outp = esdl.OutPort(id=str(uuid.uuid4()), name='E Out')
                        asset.port.append(e_outp)
                        h_outp = esdl.OutPort(id=str(uuid.uuid4()), name='H Out')
                        asset.port.append(h_outp)

                    else:
                        capability = ESDLAsset.get_asset_capability_type(asset)

                        # The view mode influences if single or double ports are added
                        double_line_mode = False
                        view_modes = ViewModes.get_instance()
                        if view_modes.get_user_settings(user_email)['mode'] == 'CHESS':
                            double_line_mode = True

                        # For producers, consumers (and storage) check if a port already exists (coming from the EDR)
                        if capability == 'Producer':
                            if no_out_port:
                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='Out'))
                            if double_line_mode:
                                if no_in_port:
                                    asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='In'))
                        elif capability in ['Consumer', 'Storage']:
                            if no_in_port:
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='In'))
                            if double_line_mode:
                                if no_out_port:
                                    asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='Out'))
                        elif capability == 'Conversion':
                            if object_type == "HeatPump" and double_line_mode:
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='PrimIn'))
                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='PrimOut'))
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='SecIn'))
                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='SecOut'))
                            else:
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='In'))
                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='Out'))
                        elif capability == 'Transport':
                            if object_type == 'HeatExchange' or object_type == 'Transformer':
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='PrimIn'))
                                if double_line_mode:
                                    asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='PrimOut'))

                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='SecOut'))
                                if double_line_mode:
                                    asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='SecIn'))
                            else:
                                asset.port.append(esdl.InPort(id=str(uuid.uuid4()), name='In'))
                                asset.port.append(esdl.OutPort(id=str(uuid.uuid4()), name='Out'))
                        else:
                            logger.error('Unknown asset capability {}'.format(capability))
                else:
                    # Update drop down list with areas and buildings
                    add_bld_to_area_bld_list(asset, area_bld_id, area_bld_list)
                    emit('area_bld_list', {'es_id': active_es_id, 'area_bld_list': area_bld_list})

                add_to_building = False
                if not ESDLAsset.add_object_to_area(es_edit, asset, area_bld_id):
                    ESDLAsset.add_object_to_building(es_edit, asset, area_bld_id)
                    add_to_building = True

                asset_to_be_added_list = []
                buildings_to_be_added_list = []

                # TODO: check / solve cable as Point issue?
                if not isinstance(asset, esdl.AbstractBuilding):
                    port_list = []
                    ports = asset.port
                    for p in ports:
                        connTo_ids = list(o.id for o in p.connectedTo)
                        carrier_id = p.carrier.id if p.carrier else None
                        port_list.append(
                            {'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': connTo_ids,
                             'carrier': carrier_id})

                # Collect extra attributes that might be required to draw specific icons, ...
                extra_attributes = dict()
                extra_attributes['assetType'] = asset.assetType

                if isinstance(asset, esdl.AbstractBuilding):
                    if isinstance(geometry, esdl.Point):
                        buildings_to_be_added_list.append(['point', asset.name, asset.id, type(asset).__name__,
                                                           [shape['coordinates']['lat'], shape['coordinates']['lng']],
                                                           False, {}, extra_attributes])
                    elif isinstance(geometry, esdl.Polygon):
                        coords = ESDLGeometry.parse_esdl_subpolygon(asset.geometry.exterior, False)  # [lon, lat]
                        coords = ESDLGeometry.exchange_coordinates(coords)                           # --> [lat, lon]
                        boundary = ESDLGeometry.create_boundary_from_geometry(geometry)
                        buildings_to_be_added_list.append(['polygon', asset.name, asset.id, type(asset).__name__,
                                                           boundary["coordinates"], False, {}, extra_attributes])
                    emit('add_building_objects', {'es_id': es_edit.id, 'building_list': buildings_to_be_added_list,
                                                  'zoom': False})
                else:
                    capability_type = ESDLAsset.get_asset_capability_type(asset)
                    state = asset_state_to_ui(asset)
                    if isinstance(geometry, esdl.Point):
                        tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'marker')
                        add_spatial_attributes(asset, tooltip_asset_attrs)
                        asset_to_be_added_list.append(['point', 'asset', asset.name, asset.id, type(asset).__name__,
                                                       [shape['coordinates']['lat'], shape['coordinates']['lng']],
                                                       tooltip_asset_attrs, state, port_list, capability_type,
                                                       extra_attributes])
                    elif isinstance(geometry, esdl.Polygon):
                        coords = ESDLGeometry.parse_esdl_subpolygon(asset.geometry.exterior, False)  # [lon, lat]
                        coords = ESDLGeometry.exchange_coordinates(coords)                           # --> [lat, lon]
                        # logger.debug(coords)
                        tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'polygon')
                        add_spatial_attributes(asset, tooltip_asset_attrs)
                        asset_to_be_added_list.append(
                            ['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords,
                             tooltip_asset_attrs, state, port_list, capability_type, extra_attributes])
                    elif isinstance(geometry, esdl.Line):
                        coords = []
                        for point in geometry.point:
                            coords.append([point.lat, point.lon])
                        tooltip_asset_attrs = get_tooltip_asset_attrs(asset, 'line')
                        add_spatial_attributes(asset, tooltip_asset_attrs)
                        asset_to_be_added_list.append(['line', 'asset', asset.name, asset.id, type(asset).__name__,
                                                       coords, tooltip_asset_attrs, state, port_list])

                    #logger.debug(asset_to_be_added_list)
                    emit('add_esdl_objects', {'es_id': es_edit.id, 'add_to_building': add_to_building,
                                              'asset_pot_list': asset_to_be_added_list, 'zoom': False})

                    asset_list = get_session_for_esid(es_edit.id, 'asset_list')
                    for al_asset in asset_to_be_added_list:
                        asset_list.append(al_asset)

                esh.add_object_to_dict(es_edit.id, asset)
                if hasattr(asset, 'port'):
                    for added_port in asset.port:
                        esh.add_object_to_dict(es_edit.id, added_port)
                set_handler(esh)

    if message['cmd'] == 'remove_object':
        # removes asset or potential from EnergySystem
        obj_id = message['id']
        if obj_id:
            # asset = ESDLAsset.find_asset(es_edit.instance[0].area, obj_id)
            # asset can also be any other object in ESDL
            asset = esh.get_by_id(active_es_id, obj_id)
            if isinstance(asset, esdl.AbstractBuilding):
                # Update drop down list with areas and buildings
                remove_ab_from_area_bld_list(asset.id, area_bld_list)
                emit('area_bld_list', {'es_id': active_es_id, 'area_bld_list': area_bld_list})
            if asset:
                # Try to remove control strategy for EnergyAssets (and not for buildings)
                if isinstance(asset, esdl.EnergyAsset):
                    remove_control_strategy_for_asset(asset.id)
            ESDLAsset.remove_object_from_energysystem(es_edit, obj_id)
            esh.remove_object_from_dict(es_edit.id, asset, True)
            # remove from asset dict
            asset_list = get_session_for_esid(active_es_id, 'asset_list')
            asset_list[:] = [a for a in asset_list if a[3] != obj_id] # filter list in place
            conn_list = get_session_for_esid(active_es_id, 'conn_list')
            conn_list[:] = [c for c in conn_list
                            if not ((c['from-asset-id'] == obj_id) or (c['to-asset-id'] == obj_id))]  # xor: filter list in place



        else:
            send_alert('Asset or potential without an id cannot be removed')

    if message['cmd'] == 'add_note':
        id = message['id']
        location = message['location']
        author = message['author']
        note = esdl.Note(id=id, author=author)

        dt = parse_date(message['date'])
        if dt:
            note.date = EDate.from_string(str(dt))
        else:
            send_alert('Invalid datetime format')
        point = esdl.Point(lat=location['lat'], lon=location['lng'])
        note.mapLocation = point
        esh.add_object_to_dict(es_edit.id, note)

        esi = es_edit.energySystemInformation
        if not esi:
            esi = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
            es_edit.energySystemInformation = esi
            esh.add_object_to_dict(es_edit.id, esi)

        notes = esi.notes
        if not notes:
            notes = esdl.Notes(id=str(uuid.uuid4()))
            esi.notes = notes
            esh.add_object_to_dict(es_edit.id, notes)

        notes.note.append(note)
        esh.add_object_to_dict(es_edit.id, note)

    if message['cmd'] == 'remove_area':
        area_id = message['id']
        if area_id:
            top_area = es_edit.instance[0].area
            if top_area:
                if top_area.id == area_id:
                    send_alert('Can not remove top level area')
                elif not ESDLEnergySystem.remove_area(top_area, area_id):
                    send_alert('Area could not be removed')

    if message['cmd'] == 'get_asset_ports':
        asset_id = message['id']
        port_list = []
        if asset_id:
            asset = ESDLAsset.find_asset(es_edit.instance[0].area, asset_id)
            ports = asset.port
            for p in ports:
                port_list.append({'id': p.id, 'type': type(p).__name__})
            emit('portlist', port_list)

    if message['cmd'] == 'connect_ports':
        port1_id = message['port1id']
        port2_id = message['port2id']

        # still not optimal, but done to get rid of mapping, optimize later
        asset_and_coord1 = get_asset_and_coord_from_port_id(esh, active_es_id, port1_id)
        asset_and_coord2 = get_asset_and_coord_from_port_id(esh, active_es_id, port2_id)
        asset1 = asset_and_coord1['asset']
        asset2 = asset_and_coord2['asset']
        asset1_port_location = asset_and_coord1['coord']
        asset2_port_location = asset_and_coord2['coord']

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

                # emit('add_new_conn', {'es_id': es_edit.id, 'add_to_building': add_to_building,
                #                       'from-port-id': port1_id, 'to-port-id': port2_id,
                #                       'new_conn': [[asset1_port_location[0], asset1_port_location[1]],
                #                                    [asset2_port_location[0], asset2_port_location[1]]]})

                # propagate carrier
                if not port2.carrier and port1.carrier:
                    if isinstance(port2.energyasset, esdl.Joint):
                        for p in port2.energyasset.port:    # porpagate carrier in case of a joint
                            p.carrier = port1.carrier if p.carrier is None else p.carrier
                    else:
                        port2.carrier = port1.carrier
                elif port2.carrier and not port1.carrier:
                    if isinstance(port1.energyasset, esdl.Joint):
                        for p in port1.energyasset.port:    # porpagate carrier in case of a joint
                            p.carrier = port1.carrier if p.carrier is None else p.carrier
                    else:
                        port1.carrier = port2.carrier

                p1_carr_id = port1.carrier.id if port1.carrier else None
                p2_carr_id = port2.carrier.id if port2.carrier else None

                conn_list = get_session_for_esid(active_es_id, 'conn_list')
                conn_message = {'from-port-id': port1_id, 'from-port-carrier': p1_carr_id, 'from-asset-id': asset1.id,
                                  'from-asset-coord': [asset1_port_location[0], asset1_port_location[1]],
                                  'to-port-id': port2_id, 'to-port-carrier': p2_carr_id, 'to-asset-id': asset2.id,
                                  'to-asset-coord': [asset2_port_location[0], asset2_port_location[1]]}
                conn_list.append(conn_message)
                emit('add_connections', {"es_id": active_es_id, "conn_list": [conn_message], "add_to_building": add_to_building})

                # update ports of assets that are connected

                port_list = []
                for p in asset1.port:
                    port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                                      'conn_to': [pt.id for pt in p.connectedTo],
                                      'carrier': p.carrier.id if p.carrier else None})
                emit('update_asset', {'asset_id': asset1.id, 'ports': port_list})
                port_list = []
                for p in asset2.port:
                    port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__,
                                      'conn_to': [pt.id for pt in p.connectedTo],
                                      'carrier': p.carrier.id if p.carrier else None})
                emit('update_asset', {'asset_id': asset2.id, 'ports': port_list})

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
            logger.debug('Get info for asset ' + asset.id)
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
            pot = esh.get_by_id(es_edit.id, object_id)
            logger.debug('Get info for potential ' + pot.id)
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
        logger.debug('Get info for conductor ' + asset.id)
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
                    logger.debug("================== NO CONTROL STRATEGY ===================")
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
        if 'id' not in message or message['id'] is None:
            fragment = message['fragment']
            asset_id = None
        else:
            fragment = None
            asset_id = message['id']
        param_name = message['param_name']
        param_value = message['param_value']

        if asset_id is None:
            resource = esh.get_resource(active_es_id)
            assets = [resource.resolve(fragment)]
        else:
            if isinstance(asset_id, list):
                assets = []
                for ass_id in asset_id:
                    assets.append(esh.get_by_id(active_es_id, ass_id))
            else:
                assets = [esh.get_by_id(active_es_id, asset_id)]

        for asset in assets:
            logger.debug('Set param '+ param_name + ' for class ' + asset.eClass.name + ' to value '+ str(param_value))

            try:
                attribute = asset.eClass.findEStructuralFeature(param_name)
                if attribute is not None:
                    if attribute.many:
                        #length = len(param_value)
                        eCollection = asset.eGet(param_name)
                        eCollection.clear()  # TODO no support for multi-select of enums
                        print('after clear', eCollection)
                        if not isinstance(param_value, list):
                            param_value = [param_value]
                        for item in param_value:
                            parsed_value = attribute.eType.from_string(item)
                            eCollection.append(parsed_value)
                    else:
                        if param_value == "" or param_value is None:
                            parsed_value = attribute.eType.default_value
                        else:
                            parsed_value = attribute.eType.from_string(param_value)
                        if attribute.name == 'id':
                            esh.remove_object_from_dict(active_es_id, asset)
                            asset.eSet(param_name, parsed_value)
                            esh.add_object_to_dict(active_es_id, asset)
                        else:
                            asset.eSet(param_name, parsed_value)

                else:
                    send_alert('Error setting attribute {} of {} to {}, unknown attribute'.format(param_name, asset.name, param_value))
            except Exception as e:
                logger.error('Error setting attribute {} of {} to {}, caused by {}'.format(param_name, asset.name, param_value, str(e)))
                send_alert('Error setting attribute {} of {} to {}, caused by {}'.format(param_name, asset.name, param_value, str(e)))
                traceback.print_exc()

        # update gui, only if necessary for EnergyAssets, and Ports
        # and EnergySystem ans
        # update_gui = False
        # update_asset = asset
        # if isinstance(asset, esdl.EnergySystem):
        #     #emit()
        #     # todo find out how to update energy system name and update Area name in dropdown
        #     pass
        # elif isinstance(asset, esdl.EnergyAsset):
        #     if param_name == esdl.EnergyAsset.name.name:
        #         update_gui = True
        #     if param_name == esdl.EnergyAsset.state.name:
        #         update_gui = True
        # elif isinstance(asset, esdl.Port):
        #     update_gui = True
        #     update_asset = asset.energyasset
        #
        # if update_gui:
        #     emit('delete_esdl_object', {'asset_id': update_asset.id})
        #     asset_ui, conn_list = energy_asset_to_ui(esh, active_es_id, update_asset)
        #     emit("add_esdl_objects",
        #          {
        #             "es_id": active_es_id,
        #             "asset_pot_list": [asset_ui],
        #             "zoom": False,
        #          })
        #     emit("add_connections",{"es_id": active_es_id, "conn_list": conn_list})

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

        asset = get_asset_from_port_id(esh, active_es_id, port_id)
        if asset:
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

            profiles = Profiles.get_instance().get_profiles()['profiles']
            for pkey in profiles:
                p = profiles[pkey]

                if p['profile_uiname'] == profile_class:
                    esdl_profile = esdl.InfluxDBProfile()
                    esdl_profile.multiplier = str2float(multiplier)

                    esdl_profile.measurement = p['measurement']
                    esdl_profile.field = p['field']
                    if 'host' in p and p['host']:
                        esdl_profile.host = p['host']
                        if 'port' in p and p['port']:
                           esdl_profile.port = int(p['port'])
                    else:
                        esdl_profile.host = settings.profile_database_config['protocol'] + "://" + \
                            settings.profile_database_config['host']
                        esdl_profile.port = int(settings.profile_database_config['port'])

                    esdl_profile.database = p['database']
                    esdl_profile.filters = settings.profile_database_config['filters']

                    if 'start_datetime' in p:
                        dt = parse_date(p['start_datetime'])
                        if dt:
                            esdl_profile.startDate = EDate.from_string(str(dt))
                        else:
                            send_alert('Invalid datetime format')
                    if 'end_datetime' in p:
                        dt = parse_date(p['end_datetime'])
                        if dt:
                            esdl_profile.endDate = EDate.from_string(str(dt))
                        else:
                            send_alert('Invalid datetime format')

        if quap_type == 'predefined_qau':
            # socket.emit('command', {cmd: 'add_profile_to_port', port_id: port_id, value: profile_mult_value,
            #    profile_class: profile_class, quap_type: qaup_type, predefined_qau: predefined_qau});
            predefined_qau = message["predefined_qau"]
            for pqau in esdl_config.esdl_config['predefined_quantity_and_units']:
                if pqau['id'] == predefined_qau:
                    try:
                        # check if predefined qau is already present in the ESDL
                        qau = esh.get_by_id(active_es_id, predefined_qau)
                    except KeyError:
                        qau = ESDLQuantityAndUnits.build_qau_from_dict(pqau)
                        esi_qau = ESDLQuantityAndUnits.get_or_create_esi_qau(esh, active_es_id)
                        esi_qau.quantityAndUnit.append(qau)
                        esh.add_object_to_dict(active_es_id, qau)
                        #qau.id = str(uuid.uuid4()) # generate new id for predifined qua otherwise double ids appear
                    break
            # make a reference instead of a direct link
            qau_ref = esdl.QuantityAndUnitReference(reference=qau)
            esdl_profile.profileQuantityAndUnit = qau_ref
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

        asset = get_asset_from_port_id(esh, active_es_id, port_id)
        if asset:
            ports = asset.port
            for p in ports:
                if p.id == port_id:
                    # p.profile = esdl_profile
                    ESDLAsset.add_profile_to_port(p, esdl_profile)

    if message['cmd'] == 'remove_profile_from_port':
        port_id = message['port_id']
        profile_id = message['profile_id']

        asset = get_asset_from_port_id(esh, active_es_id, port_id)
        if asset:
            ports = asset.port
            for p in ports:
                if p.id == port_id:
                    # p.profile = esdl_profile
                    ESDLAsset.remove_profile_from_port(p, profile_id)

    if message['cmd'] == 'add_port' or message['cmd'] == 'add_port_with_id':
        # merge add_port and add_port_with_id. Why on earth were there two messages for the same thing!
        # frontend should be adapted to only send one of these: todo
        # ptype and direction do the same thing!
        asset_id = message['asset_id']
        pname = message['pname']
        pid = str(uuid.uuid4())
        if 'pid' in message:
            pid = message['pid']
        if 'ptype' in message:
            ptype = message['ptype']
        if 'direction' in message:
            direction = message['direction']
            ptype = 'InPort' if direction == 'in' else 'OutPort'

        asset = esh.get_by_id(es_edit.id, asset_id)
        if ptype == 'InPort':
            port = esdl.InPort(id=pid, name=pname)
        else:
            port = esdl.OutPort(id=pid, name=pname)

        geom = asset.geometry
        if len(asset.port) >= 6:
            send_alert('ERROR: MapEditor cannot visualize assets with more than 6 ports.')
        if isinstance(geom, esdl.Line) and len(asset.port) >= 2:
            send_alert('ERROR: Line geometries cannot have more than two ports.')
        elif isinstance(geom, esdl.Line) and len(asset.port) == 1 and asset.port[0].eClass.name == ptype:
            send_alert('ERROR: Line cannot have ports of the same type.')
        else:
            if isinstance(geom, esdl.Line) and isinstance(port, esdl.InPort):
                asset.port.insert(0, port)  # insert InPort always at beginning as this is the convention
            else:
                asset.port.append(port)
            esh.add_object_to_dict(active_es_id, port)
            port_list = []
            for p in asset.port:
                port_list.append(
                    {'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [p.id for p in p.connectedTo]})
            emit('update_asset', {'asset_id': asset.id, 'ports': port_list})


    if message['cmd'] == 'remove_port':
        pid = message['port_id']
        asset = get_asset_from_port_id(esh, active_es_id, pid)
        ports = asset.port

        port_list = []
        for p in set(ports):
            if p.id == pid:
                esh.remove_object_from_dict(active_es_id, p, recursive=True)
                ports.remove(p) # remove from list
                p.delete()  # delete from esdl (e.g. if other ports refer to this port, they will be updated)
                            # question is why is this necessary in pyecore and isn't this done automatically
                            # as p is not contained anymore and you get dangling references.
            else:
                carrier_id = p.carrier.id if p.carrier else None
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': [pt.id for pt in p.connectedTo], 'carrier': carrier_id})
        emit('update_asset', {'asset_id': asset.id, 'ports': port_list})

    if message['cmd'] == 'remove_connection_portids': # user clicked remove connection by right-clicking on connection
        building_id = message['building_id'] if 'building_id' in message else None
        from_port_id = message['from_port_id']
        from_port: esdl.Port = esh.get_by_id(es_edit.id, from_port_id)
        to_port_id = message['to_port_id']
        to_port: esdl.Port = esh.get_by_id(es_edit.id, to_port_id)
        from_port.connectedTo.remove(to_port)

        from_asset_id = from_port.eContainer().id
        to_asset_id = to_port.eContainer().id

        # refresh connections in gui
        #active_es_id = get_session('active_es_id')
        conn_list = get_session_for_esid(es_edit.id, 'conn_list')
        new_list = []
        #print(conn_list)
        for conn in conn_list:
            if (conn['from-port-id'] != from_port_id or conn['from-asset-id'] != from_asset_id or
                    conn['to-port-id'] != to_port_id or conn['to-asset-id'] != to_asset_id) and \
                    (conn['from-port-id'] != to_port_id or conn['from-asset-id'] != to_asset_id or
                    conn['to-port-id'] != from_port_id or conn['to-asset-id'] != from_asset_id):
                # Remove both directions from -> to and to -> from as we don't know how they are stored in the list
                # does not matter, as a connection is unique
                new_list.append(conn)  # add connections that we are not interested in
            else:
                print(' - removed {}'.format(conn))
        set_session_for_esid(es_edit.id, 'conn_list', new_list)  # set new connection list
        if building_id:
            # building editor is open, so only update building connections.
            building = esh.get_by_id(es_edit.id, building_id)
            bld_info = get_building_information(building)
            bld_conn_list = bld_info["conn_list"]
            emit('clear_connections', {'id': building_id})   # clear current active layer connections
            emit('add_connections', {'es_id': es_edit.id, 'conn_list': bld_conn_list, 'add_to_building': True})
        if from_port.energyasset.containingBuilding is None or to_port.energyasset.containingBuilding is None:
            # only clear main map connections if not both assets are in a building
            emit('clear_connections', {'id': active_es_id})   # clear current active layer connections
            emit('add_connections', {'es_id': active_es_id, 'conn_list': new_list})

    if message['cmd'] == 'remove_connection':
        # socket.emit('command', {cmd: 'remove_connection', from_asset_id: from_asset_id, from_port_id: from_port_id,
        #                         to_asset_id: to_asset_id, to_port_id: to_port_id, 'building_id': building_id});
        from_asset_id = message['from_asset_id']
        from_port_id = message['from_port_id']
        from_port = esh.get_by_id(es_edit.id, from_port_id)
        to_asset_id = message['to_asset_id']
        to_port_id = message['to_port_id']
        building_id = message['building_id'] if 'building_id' in message else None
        to_port = esh.get_by_id(es_edit.id, to_port_id)
        from_port.connectedTo.remove(to_port)

        # refresh connections in gui
        #active_es_id = get_session('active_es_id')
        conn_list = get_session_for_esid(es_edit.id, 'conn_list')
        new_list = []
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
        if building_id:
            # building editor is open, so only update building connections.
            building = esh.get_by_id(es_edit.id, building_id)
            bld_info = get_building_information(building)
            conn_list = bld_info["conn_list"]
            emit('clear_connections', {'id': building_id})   # clear connection of building editor
            emit('add_connections', {'es_id': es_edit.id, 'conn_list': conn_list, 'add_to_building': True})

        # always clear the main layer, as the connection edited can be at two maps at the same time
        # only clear main map if the assets are not part of a containingBuilding
        if from_port.energyasset.containingBuilding is None or to_port.energyasset.containingBuilding is None:
            emit('clear_connections', {'id': es_edit.id})   # clear main layer layer connections
            emit('add_connections', {'es_id': es_edit.id, 'conn_list': new_list, 'add_to_building': False})

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

        update_carrier_conn_list()

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
                encont_qandu=esdl.QuantityAndUnitType(
                    physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                    multiplier=esdl.MultiplierEnum.MEGA,
                    unit=esdl.UnitEnum.JOULE,
                    perMultiplier=esdl.MultiplierEnum.KILO,
                    perUnit=esdl.UnitEnum.GRAM)
            elif carr_encunit == 'MJpNm3':
                encont_qandu=esdl.QuantityAndUnitType(
                    physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                    multiplier=esdl.MultiplierEnum.MEGA,
                    unit=esdl.UnitEnum.JOULE,
                    perUnit=esdl.UnitEnum.CUBIC_METRE)
            elif carr_encunit == 'MJpMJ':
                encont_qandu=esdl.QuantityAndUnitType(
                    physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                    multiplier=esdl.MultiplierEnum.MEGA,
                    unit=esdl.UnitEnum.JOULE,
                    perMultiplier=esdl.MultiplierEnum.MEGA,
                    perUnit=esdl.UnitEnum.JOULE)

            emission_qandu=esdl.QuantityAndUnitType(
                physicalQuantity=esdl.PhysicalQuantityEnum.EMISSION,
                multiplier=esdl.MultiplierEnum.KILO,
                unit=esdl.UnitEnum.GRAM,
                perMultiplier=esdl.MultiplierEnum.GIGA,
                perUnit=esdl.UnitEnum.JOULE)

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
        return True

    if message['cmd'] == 'remove_carrier':
        carrier_id = message['carrier_id']

        carrier = esh.get_by_id(es_edit.id, carrier_id)
        carrier.delete()

        conn_list = get_session_for_esid(es_edit.id, 'conn_list')
        for c in conn_list:
            if c['from-port-carrier'] == carrier_id:
                c['from-port-carrier'] = None
            if c['to-port-carrier'] == carrier_id:
                c['to-port-carrier'] = None

        emit('clear_connections')  # clear current active layer connections
        emit('add_connections', {'es_id': es_edit.id, 'conn_list': conn_list})

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

    # if message['cmd'] == 'set_marginal_costs_get_info':
    #     asset_id = message['asset_id']
    #     mc = get_marginal_costs_for_asset(asset_id)
    #     emit('marginal_costs', {'asset_id': asset_id, 'mc': mc})

    if message['cmd'] == 'set_marg_costs':
        asset_id = message['asset_id']
        mc = str2float(message['marg_costs'])
        set_marginal_costs_for_asset(asset_id, mc)

    if message['cmd'] == 'remove_marg_costs':
        asset_id = message['asset_id']
        remove_marginal_costs_for_asset(asset_id)

    if message['cmd'] == 'layer':
        pass

    if message['cmd'] == 'run_ESSIM_simulation':
        logger.debug('ESSIM simulation command received')
        sim_descr = message['sim_description']
        sim_start_datetime = message['sim_start_datetime']
        sim_end_datetime = message['sim_end_datetime']
        essim_kpis = message['essim_kpis']
        essim_loadflow = message['essim_loadflow']
        # Create the HTTP POST to start the simulation
        if not essim.run_simulation(sim_descr, sim_start_datetime, sim_end_datetime, essim_kpis, essim_loadflow):
            emit('simulation_not_started')

    if message['cmd'] == 'validate_for_ESSIM':
        logger.debug('validation for ESSIM command received')
        res = validate_ESSIM(es_edit)
        emit('results_validation_for_ESSIM', res)

    # if message['cmd'] == 'calculate_ESSIM_KPIs':
        # session['simulationRun'] = '5d10f273783bac5eff4575e8'
        # ESSIM_config = settings.essim_config
        #
        # simulation_run = get_session('simulationRun')
        # if simulation_run:
        #
        #     active_simulation = get_session('active_simulation')
        #     if active_simulation:
        #         sdt = datetime.strptime(active_simulation['startDate'], '%Y-%m-%dT%H:%M:%S%z')
        #         edt = datetime.strptime(active_simulation['endDate'], '%Y-%m-%dT%H:%M:%S%z')
        #     else:
        #         send_alert('No active_simulation! This should not happen, please report. However, you can continue')
        #         sdt = datetime.strptime(ESSIM_config['start_datetime'], '%Y-%m-%dT%H:%M:%S%z')
        #         edt = datetime.strptime(ESSIM_config['end_datetime'], '%Y-%m-%dT%H:%M:%S%z')
        #
        #     influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
        #     influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')
        #
        #     calc_ESSIM_KPIs.submit(es_edit, simulation_run, influxdb_startdate, influxdb_enddate)
        # else:
        #     send_alert('No simulation id defined - run an ESSIM simulation first')

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
        edr_asset_str = edr_assets.get_asset_from_EDR(edr_asset_id)
        if edr_asset_str:
            edr_asset = ESDLAsset.load_asset_from_string(edr_asset_str)
            edr_asset_name = edr_asset.name
            edr_asset_type = type(edr_asset).__name__
            edr_asset_cap = get_asset_capability_type(edr_asset)
            emit('place_edr_asset', edr_asset_type)
            set_session('adding_edr_assets', edr_asset_str)

            recently_used_edr_assets = get_session('recently_used_edr_assets')
            if recently_used_edr_assets:
                current_edr_asset_in_list = False
                for edra in recently_used_edr_assets:
                    if edra['edr_asset_id'] == edr_asset_id:
                        current_edr_asset_in_list = True

                if not current_edr_asset_in_list and len(recently_used_edr_assets) == 5:
                    recently_used_edr_assets.pop()     # Remove last element

                if not current_edr_asset_in_list:
                    recently_used_edr_assets.insert(0, {
                        'edr_asset_id': edr_asset_id,
                        'edr_asset_name': edr_asset_name,
                        'edr_asset_type': edr_asset_type,
                        'edr_asset_cap': edr_asset_cap,
                        'edr_asset_str': edr_asset_str
                    })
            else:
                recently_used_edr_assets = list()
                recently_used_edr_assets.append({
                    'edr_asset_id': edr_asset_id,
                    'edr_asset_name': edr_asset_name,
                    'edr_asset_type': edr_asset_type,
                    'edr_asset_cap': edr_asset_cap,
                    'edr_asset_str': edr_asset_str
                })
                set_session('recently_used_edr_assets', recently_used_edr_assets)

            emit('recently_used_edr_assets', recently_used_edr_assets)
        else:
            send_alert('Error getting ESDL model from EDR')

    if message['cmd'] == 'set_asset_drawing_mode':
        mode = message['mode']
        set_session('asset_drawing_mode', mode)
        if mode == 'empty_assets':
            set_session('adding_edr_assets', None)
            set_session('asset_from_measure_id', None)
        if mode == 'edr_asset':
            edr_asset_info = message['edr_asset_info']
            # If you select an asset from the EDR directly, ESDL string is cached.
            # AssetDrawToolbar EDR assets that are stored in mongo, do not have the ESDL string stored.
            if 'edr_asset_str' not in edr_asset_info:
                edr_asset_id = edr_asset_info['edr_asset_id']
                edr_asset_info['edr_asset_str'] = edr_assets.get_asset_from_EDR(edr_asset_id)
            set_session('adding_edr_assets', edr_asset_info['edr_asset_str'])
        if mode == 'asset_from_measures':
            asset_from_measure_id = message['asset_from_measure_id']
            set_session('asset_from_measure_id', asset_from_measure_id)

    if message['cmd'] == 'query_esdl_service':
        params = message['params']
        logger.debug("received query_esdl_service command with params: {}".format(params))
        query_esdl_services.submit(params)

    if message['cmd'] == 'redraw_connections': # set_carrier_color
        # this is called when a carrier color is changed and the gui needs to be refreshed
        # best would be to do this fully in the front end (no changes in the ESDL model)
        # but that does not contain enough information yet to do this.
        conn_list = get_session_for_esid(active_es_id, 'conn_list')
        emit('clear_connections')  # clear current active layer connections
        emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})

        asset_list = get_session_for_esid(active_es_id, 'asset_list')
        emit('clear_ui', {'layer': 'assets'})  # clear current active layer assets
        emit('add_esdl_objects', {'es_id': active_es_id, 'asset_pot_list': asset_list, 'zoom': False})

    if message['cmd'] == 'building_editor':
        bld_id = message['id']
        building = esh.get_by_id(active_es_id, bld_id)
        bld_info = get_building_information(building)
        emit('building_information', bld_info)
        emit('add_esdl_objects',
             {'es_id': active_es_id, 'add_to_building': True, 'asset_pot_list': bld_info["asset_list"],
              'zoom': False})
        emit('add_connections', {'es_id': active_es_id, 'add_to_building': True, 'conn_list': bld_info["conn_list"]})

    if message['cmd'] == 'get_building_connections':
        bld_id = message['id']
        building = esh.get_by_id(active_es_id, bld_id)
        return get_building_connections(building)

    if message['cmd'] == 'accept_received_esdl':
        user_email = get_session('user-email')
        received_esdls = esdl_api.get_esdl_for_user(user_email)
        if received_esdls:
            for received_esdl in received_esdls:
                filename = 'ESDL from '+received_esdl['sender']
                esh = get_handler()

                try:
                    result, parse_info = esh.add_from_string(name=filename, esdl_string=urllib.parse.unquote(received_esdl['esdl']))
                    if len(parse_info) > 0:
                        info = ''
                        for line in parse_info:
                            info += line + "\n"
                        send_alert("Warnings while opening {}:\n\n{}".format(filename, info))

                    call_process_energy_system.submit(esh, filename)  # run in seperate thread
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

    if message['cmd'] == 'refresh_esdl':
        print('refresh_esdl')
        esh = get_handler()
        call_process_energy_system.submit(esh, force_update_es_id=es_edit.id, zoom=False)  # run in seperate thread

    set_handler(esh)
    session.modified = True


@executor.job
def query_esdl_services(params):
    esh = get_handler()
    logger.debug('calling service')
    try:
        esdl_service_ok, esdl_service_result = esdl_services.call_esdl_service(params)
    except Exception as exc:
        logger.exception("Exception when querying ESDL service")
        esdl_service_ok = False
        esdl_service_result = str(exc)

    logger.debug('emitting result to browser')
    if esdl_service_ok:
        if esdl_service_result is not None:
            emit('esdl_service_result', esdl_service_result)
    else:
        message = 'Error calling service'
        if isinstance(esdl_service_result, str):
            message += ': ' + esdl_service_result
        send_alert(message)
    # logger.debug('processing energy system')
    call_process_energy_system.submit(esh)


@socketio.on('set_active_es_id', namespace='/esdl')
def set_active_es_id(id):
    set_session('active_es_id', id)
    logger.debug("========== Setting active es_id to {} =============".format(id))


# ---------------------------------------------------------------------------------------------------------------------
#  React on commands from the browser (add, remove, ...)
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('file_command', namespace='/esdl')
def process_file_command(message):
    logger.info('received: ' + message['cmd'])
    es_info_list = get_session("es_info_list")

    if message['cmd'] == 'new_esdl':
        name = message['name']
        description = message['description']
        instance_name = message['instance_name']
        top_area_name = message['top_area_name']
        if name == '': name = 'New Energy System'
        if instance_name == '': instance_name = 'Untitled instance'
        if top_area_name == '': top_area_name = 'Untitled area'
        filename = 'Unknown'
        esh = EnergySystemHandler()
        es = esh.create_empty_energy_system(name, description, instance_name, top_area_name, esdlVersion=esdl_doc.get_esdl_version())
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')
        call_process_energy_system.submit(esh, filename)

        del_session('store_item_metadata')
        emit('store_item_metadata', {})
        set_session('active_es_id', es.id)
        set_session('es_filename', filename)

    if message['cmd'] == 'load_esdl_from_file':
        file_content = message['file_content']
        filename = message['filename']
        esh = EnergySystemHandler()

        try:
            result, parse_info = esh.load_from_string(esdl_string=file_content, name=filename)
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                send_alert("Warnings while opening {}:\n\n{}".format(filename, info))
        except Exception as e:
            logger.exception(f"Error opening {filename}")
            send_alert("Error opening {}. Exception is: {}".format(filename, e))
            emit('clear_ui')
            return

        es = esh.get_energy_system()
        set_handler(esh)
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')
        call_process_energy_system.submit(esh, filename) # run in seperate thread
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
            imported_es, parse_info = esh.add_from_string(name=filename, esdl_string=file_content)
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                send_alert("Warnings while opening {}:\n\n{}".format(filename, info))
            call_process_energy_system.submit(esh, filename)  # run in seperate thread
            set_session('active_es_id', imported_es.id)
            set_session('es_filename', filename)
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
            logger.error('Error accessing ESDL store' + str(e))
            send_alert('Error accessing ESDL store' + str(e))
            return

        data = result.json()
        store_list = []
        for store_item in data:
            store_list.append({'id': store_item['id'], 'title': store_item['title']})

        sorted_store_list = sorted(store_list, key=lambda x: x['title'], reverse=False)

        emit('store_list', sorted_store_list)

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
            call_process_energy_system.submit(esh, None, title)
        else:
            send_alert('Error loading ESDL file with id {} from store'.format(store_id))

    if message['cmd'] == 'import_esdl_from_store':
        store_id = message['id']

        imported_es = import_ESDL_EnergySystem(store_id)
        if imported_es:
            if imported_es.name:
                title = 'Store name: ' + imported_es.name + ', store id: ' + store_id
            else:
                title = 'Store id: ' + store_id

            esh = get_handler()
            call_process_energy_system.submit(esh, None, title)  # run in seperate thread
            set_session('active_es_id', imported_es.id)
            set_session('es_filename', title)

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
    logger.info('Client connected: {}'.format(request.sid))

    if 'client_id' in session:
        logger.info('Energysystem in memory - reloading client data')
        esh = get_handler()
    else:
        logger.info('No energysystem in memory - generating empty energysystem')
        esh = EnergySystemHandler()
        esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area',
                                       esdlVersion=esdl_doc.get_esdl_version())

    # TODO: discuss how to set active_es_id for the first time after a client connects
    es_list = esh.get_energy_systems()
    if es_list:
        last_es = es_list[-1]
        set_session('active_es_id', last_es.id)
    else:
        # This happens when there is an exception in loading an EnergySystem
        logger.error("No energy systems in esh list - Edwin and Ewoud discuss!!")
        esh.create_empty_energy_system('Untitled EnergySystem', '', 'Untitled Instance', 'Untitled Area',
                                       esdlVersion=esdl_doc.get_esdl_version())

    es_info_list = {}
    set_session("es_info_list", es_info_list)
    emit('clear_ui')
    emit('clear_esdl_layer_list')
    call_process_energy_system.submit(esh, None, None) # run in a seperate thread


@socketio.on('connect', namespace='/esdl')
def connect():
    logger.info("Websocket connection established")

    if 'id' in session:
        logger.debug('- Old socketio id={}, new socketio id={}'.format(session['id'], request.sid))
    else:
        logger.debug('- Old socketio id={}, new socketio id={}'.format(None, request.sid))
    session['id'] = request.sid
    set_session('socketio_sid', request.sid)

    # Client ID is used to retrieve session variables in handler_manager
    # So this is a very important session variable!!
    if 'client_id' in session:
        logger.debug('- Client id: {}'.format(session['client_id']))
    else:
        logger.debug('- No client id in session')
    if not valid_session():
        send_alert("Session has timed out, please refresh")


def get_qau_information():
    qau_info = dict()
    qau_info['generic'] = ESDLQuantityAndUnits.get_qau_information()
    qau_info['profile_type_enum_values'] = ESDLQuantityAndUnits.get_profile_type_enum_values()
    qau_info['predefined_qau'] = esdl_config.esdl_config['predefined_quantity_and_units']
    return qau_info


def get_carrier_color_dict():
    me_settings = MapEditorSettings.get_instance()
    me_ui_setting = me_settings.get_system_setting(MAPEDITOR_UI_SETTINGS)
    if me_ui_setting:
        if 'carrier_colors' in me_ui_setting:
            return me_ui_setting['carrier_colors']
    return None


@socketio.on('initialize', namespace='/esdl')
def browser_initialize():
    user_email = get_session('user-email')
    role = get_session('user-role')

    view_modes = ViewModes.get_instance()
    view_modes.initialize_user(user_email)

    me_settings = MapEditorSettings.get_instance()
    user_settings = me_settings.get_user_settings(user_email)
    set_session('user_settings', user_settings)

    logger.info('Send initial information to client')
    emit('user_settings', user_settings)
    emit('control_strategy_config', esdl_config.esdl_config['control_strategies'])
    emit('carrier_color_dict', get_carrier_color_dict())
    emit('wms_layer_list', wms_layers.get_layers())
    emit('cap_pot_list', ESDLAsset.get_objects_list())
    emit('qau_information', get_qau_information())
    emit('esdl_services', esdl_services.get_user_services_list(user_email, role))
    emit('user_info', {'email': user_email})
    initialize_app()


# ---------------------------------------------------------------------------------------------------------------------
#  Disconnect
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect', namespace='/esdl')
def on_disconnect():
    logger.info('Client disconnected: {}'.format(request.sid))


# ---------------------------------------------------------------------------------------------------------------------
#  Error logging
# ---------------------------------------------------------------------------------------------------------------------
@socketio.on_error_default
def default_error_handler(e):
    logger.error('Error in SocketIO handler: '+str(e))
    import traceback
    logger.error('Socket IO message: {}'.format(request.event["message"]))  # "my error event"
    logger.error('Socket IO arguments: {}'.format(request.event["args"]))
    traceback.print_exc()


# ---------------------------------------------------------------------------------------------------------------------
#  Start application
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    parse_esdl_config()
    logger.info("Starting ESDL MapEditor application")

    user_actions_logging.store_logging("System", "application start", "", "", "", {})
    socketio.run(app, debug=settings.FLASK_DEBUG, host=settings.FLASK_SERVER_HOST, port=settings.FLASK_SERVER_PORT, use_reloader=True)
