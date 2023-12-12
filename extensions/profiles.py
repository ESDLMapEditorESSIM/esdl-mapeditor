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
import base64
import datetime

import pytz
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_executor import Executor
from pyecore.ecore import EDate

from esdl import esdl
from esdl.esdl_handler import EnergySystemHandler
from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
from extensions.panel_service import create_panel, get_panel_service_datasource
from influxdb import InfluxDBClient
import copy
import src.log as log
import csv
import locale
from io import StringIO
from uuid import uuid4
import src.settings as settings
from src.edr_client import EDRClient
from utils.datetime_utils import parse_date
from utils.utils import str2float

logger = log.get_logger(__name__)


PROFILES_LIST = 'PROFILES'                  # To store profiles
PROFILES_SETTINGS = 'PROFILES_SETTINGS'     # To store information about profiles servers, ...
profiles = None


def send_alert(message):
    print(message)
    # emit('alert', message, namespace='/esdl')


class Profiles:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.csv_files = dict()
        self.register()

        self.EDR_profiles_cache = self.generate_EDR_profiles_list()

        if settings.profile_database_config['host'] is None or settings.profile_database_config['host'] == "":
            logger.error("Profile database is not configured. Aborting...")
            exit(1)

        # add initial profiles when not in the system settings
        if not self.settings_storage.has_system(PROFILES_LIST):
            self.settings_storage.set_system(PROFILES_LIST, default_profiles)
            logger.info('Updated default profile list in settings storage')

        # create system profile settings when not yet available
        self.get_profiles_system_settings()

        global profiles
        if profiles:
            logger.error("ERROR: Only one Profiles object can be instantiated")
        else:
            profiles = self

    @staticmethod
    def get_instance():
        global profiles
        return profiles

    def register(self):
        logger.info('Registering Profiles extension')

        @self.socketio.on('get_profiles_list', namespace='/esdl')
        def get_profiles_list():
            with self.flask_app.app_context():
                # print("getting profiles list")
                return self.get_profiles()

        @self.socketio.on('get_profile_group_list', namespace='/esdl')
        def get_profile_group_list():
            with self.flask_app.app_context():
                return self.get_profile_groups()

        @self.socketio.on('remove_profile', namespace='/esdl')
        def click_remove_profile(profile_id):
            if isinstance(profile_id, list):
                for pid in profile_id:
                    self.remove_profile(pid)
            else:
                self.remove_profile(profile_id)

        @self.socketio.on('add_profile', namespace='/esdl')
        def click_add_profile(profile_info):
            with self.flask_app.app_context():
                id = str(uuid4())
                group = profile_info['group']
                if group == SettingType.USER.value:
                    profile_info['setting_type'] = SettingType.USER.value
                    profile_info['project_name'] = self._get_identifier(group)
                elif group == SettingType.SYSTEM.value:
                    profile_info['setting_type'] = SettingType.SYSTEM.value
                    profile_info['project_name'] = self._get_identifier(group)
                else:
                    profile_info['setting_type'] = SettingType.PROJECT.value
                    profile_info['project_name'] = group
                del profile_info['group']
                # print(profile_info)
                self.add_profile(id, profile_info)

        @self.socketio.on('save_profile', namespace='/esdl')
        def click_save_profile(profile_info):
            with self.flask_app.app_context():
                id = profile_info['id']
                group = profile_info['group']
                if group == SettingType.USER.value:
                    profile_info['setting_type'] = SettingType.USER.value
                    profile_info['project_name'] = self._get_identifier(group)
                elif group == SettingType.SYSTEM.value:
                    profile_info['setting_type'] = SettingType.SYSTEM.value
                    profile_info['project_name'] = self._get_identifier(group)
                else:
                    profile_info['setting_type'] = SettingType.PROJECT.value
                    profile_info['project_name'] = group
                del profile_info['group']
                # print(profile_info)
                self.add_profile(id, profile_info)

        @self.socketio.on('test_profile', namespace='/esdl')
        def click_test_profile(profile_info):
            embedUrl = create_panel(
                graph_title=profile_info["profile_uiname"],
                axis_title="",
                host=None,
                database=profile_info["database"],
                measurement=profile_info["measurement"],
                field=profile_info["field"],
                filters=profile_info["filters"],
                qau=None,
                prof_aggr_type="sum",
                start_datetime=profile_info["start_datetime"],
                end_datetime=profile_info["end_datetime"]
            )
            return embedUrl

        @self.socketio.on('profile_csv_upload', namespace='/esdl')
        def profile_csv_upload(message):
            with self.flask_app.app_context():
                message_type = message['message_type']  # start, next_chunk, done
                if message_type == 'start':
                    # start of upload
                    filetype = message['filetype']
                    name = message['name']
                    uuid = message['uuid']
                    size = message['size']
                    group = message['group']

                    self.csv_files[uuid] = message
                    self.csv_files[uuid]['pos'] = 0
                    self.csv_files[uuid]['content'] = []
                    self.csv_files[uuid]['group'] = group
                    logger.debug('Uploading CSV file {}, size={}'.format(name, size))
                    emit('csv_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos']})

                elif message_type == 'next_chunk':
                    name = message['name']
                    uuid = message['uuid']
                    size = message['size']
                    content = message['content']
                    pos = message['pos']
                    #print(content)
                    self.csv_files[uuid]['content'][pos:len(content)] = content
                    self.csv_files[uuid]['pos'] = pos + len(content)
                    if self.csv_files[uuid]['pos'] >= size:
                        #print("Upload complete:", str(bytearray(self.csv_files[uuid]['content'])))

                        ba = bytearray(self.csv_files[uuid]['content'])
                        csv = ba.decode(encoding='utf-8-sig')
                        emit('csv_upload_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                                 'success': True})
                        self.executor.submit(self.process_csv_file, name, uuid, csv)
                    else:
                        #print("Requesting next chunk", str(bytearray(self.csv_files[uuid]['content'])))
                        emit('csv_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos']})

        @self.socketio.on('get_profiles_settings', namespace='/esdl')
        def get_profiles_settings():
            with self.flask_app.app_context():
                return self.get_profiles_settings()

    def update_profiles_list(self):
        emit('update_profiles_list', self.get_profiles())

    def format_datetime(self, dt):
        date, time = dt.split(" ")
        day, month, year = date.split("-")
        ndate = year + "-" + month + "-" + day
        ntime = time + ":00+0000"
        return ndate + "T" + ntime

    def process_csv_file(self, name, uuid, content):
        logger.debug("Processing csv file(s) (threaded): ".format(name))

        tz_string = datetime.datetime.now().astimezone().tzname()

        try:
            logger.info("process CSV")
            measurement = name.split('.')[0]

            try:
                csv_file = StringIO(content)
                dialect = csv.Sniffer().sniff(csv_file.read(4096))
                csv_file = StringIO(content)
                reader = csv.reader(csv_file, dialect)
            except:
                # If format cannot be determined automatically, try ; as a default
                csv_file = StringIO(content)
                reader = csv.reader(csv_file, delimiter=';')

            column_names = next(reader)
            num_fields = len(column_names)
            json_body = []

            locale.setlocale(locale.LC_ALL, '')
            start_datetime = None
            end_datetime = ""
            previous_datetime = None

            for row in reader:
                fields = {}
                for i in range(1, num_fields):
                    if row[i]:
                        fields[column_names[i]] = locale.atof(row[i])

                dt = parse_date(row[0])
                try:
                    aware_dt = pytz.utc.localize(dt)  # Assume timezone is UTC if no TZ was given (as asked in the UI)
                except ValueError:  # ValueError: Not naive datetime (tzinfo is already set)
                    aware_dt = dt

                dt_string = aware_dt.strftime('%Y-%m-%dT%H:%M:%S%z')

                if previous_datetime:
                    if previous_datetime == aware_dt:
                        raise(Exception("CSV contains duplicate datetimes ({}). Check timezone and daylight saving".
                                        format(dt_string)))
                previous_datetime = aware_dt

                if not start_datetime:
                    start_datetime = dt_string
                else:
                    end_datetime = dt_string

                json_body.append({
                    "measurement": measurement,
                    "time": dt_string,
                    "fields": fields
                })

            logger.info("CSV processing finished, now writing to database...")

            with self.flask_app.app_context():
                profiles_settings = self.get_profiles_settings()
                profiles_server_index = int(self.csv_files[uuid]['profiles_server_index'])

                database = profiles_settings['profiles_servers'][profiles_server_index]['database']
                client = InfluxDBClient(
                    host=profiles_settings['profiles_servers'][profiles_server_index]['host'],
                    port=profiles_settings['profiles_servers'][profiles_server_index]['port'],
                    username=profiles_settings['profiles_servers'][profiles_server_index]['username'],
                    password=profiles_settings['profiles_servers'][profiles_server_index]['password'],
                    database=database,
                    ssl=profiles_settings['profiles_servers'][profiles_server_index]['ssl_enabled'],
                )

            available_databases = client.get_list_database()
            # if database not in client.get_list_database():
            if not(any(db['name'] == database for db in available_databases)):
                logger.debug('Database does not exist, creating a new one')
                client.create_database(database)
            client.write_points(points=json_body, database=database, batch_size=100)

            if profiles_settings['profiles_servers'][profiles_server_index]['ssl_enabled']:
                protocol = "https://"
            else:
                protocol = "http://"
            profiles_server_host = protocol + \
                                   profiles_settings['profiles_servers'][profiles_server_index]['host'] + \
                                   ":" + \
                                   profiles_settings['profiles_servers'][profiles_server_index]['port']
            datasource = get_panel_service_datasource(
                database=database,
                host=profiles_server_host,
                username=profiles_settings['profiles_servers'][profiles_server_index]['username'],
                password=profiles_settings['profiles_servers'][profiles_server_index]['password'],
            )

            logger.info("Store profile information in settings")

            # Store profile information in settings
            group = self.csv_files[uuid]['group']
            prof_aggr_type = self.csv_files[uuid]['prof_aggr_type']
            for i in range(1, num_fields):
                field = column_names[i]

                # Stop if empty column was found
                if field.strip() == '':
                    break
                # Create a dictionary with all relevant information about the new profile
                profile = self.create_new_profile(
                    group=group,
                    uiname=measurement+'_'+field,
                    multiplier=1,
                    database=database,
                    measurement=measurement,
                    field=field,
                    profile_type="",
                    start_datetime=start_datetime,
                    end_datetime=end_datetime
                )
                if profiles_server_index != 0:  # Only non standard profiles server
                    profile['host'] = profiles_settings['profiles_servers'][profiles_server_index]['host']
                    profile['port'] = profiles_settings['profiles_servers'][profiles_server_index]['port']

                # Create a grafana panel for visualization and add the embedURL to the dictionary
                profile["embedUrl"] = create_panel(
                    graph_title=group + " - " + field,
                    axis_title="",
                    datasource=datasource,
                    host=profiles_server_host,
                    database=database,
                    measurement=measurement,
                    field=field,
                    filters=[],
                    qau=None,
                    prof_aggr_type=prof_aggr_type,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime
                )
                # Store the new profile in the profiles settings
                self.add_profile(str(uuid4()), profile)

            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                     'success': True})
        except Exception as e:
            logger.exception("Error processing CSV")
            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                     'success': False, 'error': str(e)})

        # clean up
        del (self.csv_files[uuid])

    def add_profile(self, profile_id, profile):
        setting_type = SettingType(profile['setting_type'])
        project_name = profile['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, PROFILES_LIST):
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_LIST)
        else:
            profiles = dict()
        profiles[profile_id] = profile
        self.settings_storage.set(setting_type, identifier, PROFILES_LIST, profiles)
        self.update_profiles_list()

    def remove_profile(self, profile_id):
        # as we only have an ID, we don't know if it is a user, project or system profile
        # get the whole list, so we can find out the setting_type
        profile = self.get_profiles()['profiles'][profile_id]
        setting_type = SettingType(profile['setting_type'])
        if 'project_name' in profile:
            proj_name = profile['project_name']
        else:
            proj_name = None
        identifier = self._get_identifier(setting_type, proj_name)
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, PROFILES_LIST):
            # update profile dict
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_LIST)
            print('Deleting profile {}'.format(profiles[profile_id]))
            del(profiles[profile_id])
            self.settings_storage.set(setting_type, identifier, PROFILES_LIST, profiles)

    def _get_identifier(self, setting_type: SettingType, project_name=None):
        if setting_type is None:
            return
        elif setting_type == SettingType.USER:
            identifier = get_session('user-email')
        elif setting_type == SettingType.PROJECT:
            if project_name is not None:
                identifier = project_name.replace(' ', '_')
            else:
                identifier = 'unnamed project'
        elif setting_type == SettingType.SYSTEM:
            identifier = SettingsStorage.SYSTEM_NAME_IDENTIFIER
        else:
            return None
        return identifier

    def get_profiles(self):
        # gets the default list and adds the user profiles
        all_profiles = dict()
        if self.settings_storage.has_system(PROFILES_LIST):
            all_profiles.update(self.settings_storage.get_system(PROFILES_LIST))

        user = get_session('user-email')
        user_group = get_session('user-group')
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')
        # print('User: ', user)
        # print('Groups: ', user_group)
        # print('Roles: ', role)
        # print('Mapeditor roles: ', mapeditor_role)
        if user is not None and self.settings_storage.has_user(user, PROFILES_LIST):
            # add user profiles if available
            all_profiles.update(self.settings_storage.get_user(user, PROFILES_LIST))

        edr_profiles = self.get_EDR_profiles()
        if edr_profiles:
            all_profiles.update(edr_profiles)

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, PROFILES_LIST):
                    # add project profiles if available
                    all_profiles.update(self.settings_storage.get_project(identifier, PROFILES_LIST))

        # generate message
        message = copy.deepcopy(default_profile_groups)
        possible_groups = message["groups"]
        # if enough rights, mark Standard profiles editable
        if mapeditor_role and 'mapeditor-admin' in mapeditor_role:
            for g in possible_groups:
                if g['setting_type'] == SettingType.SYSTEM.value:
                    g['readonly'] = False
        possible_groups.extend(self._create_group_profiles_for_projects(user_group))
        message["profiles"] = all_profiles
        # print(message)
        return message

    def get_profile_groups(self):
        user_group = get_session('user-group')
        dpg = copy.deepcopy(default_profile_groups)

        # Make system profiles editable for the MapEditor admin role
        mapeditor_role = get_session('user-mapeditor-role')
        if 'mapeditor-admin' in mapeditor_role:
            dpg['groups'][1]['readonly'] = False

        possible_groups = dpg["groups"]
        possible_groups.extend(self._create_group_profiles_for_projects(user_group))
        return possible_groups

    def _create_group_profiles_for_projects(self, groups):
        project_list = list()
        if groups is not None:
            for group in groups:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                json = {"setting_type": SettingType.PROJECT.value, "project_name": identifier, "name": "Project profiles for " + group, "readonly": False}
                project_list.append(json)
        return project_list

    def get_setting_type_project_name(self, group):
        if group.startswith("Project profiles for "):
            group_name = group.replace("Project profiles for ", "")
            identifier = self._get_identifier(SettingType.PROJECT, group_name)
            return SettingType.PROJECT.value, identifier
        elif group == "Standard profiles":
            identifier = self._get_identifier(SettingType.SYSTEM)
            return SettingType.SYSTEM.value, identifier
        elif group == "EDR profiles":
            pass
        else:
            identifier = self._get_identifier(SettingType.USER)
            return SettingType.USER.value, identifier

    def get_EDR_profiles(self):
        return self.EDR_profiles_cache

    def generate_EDR_profiles_list(self):
        # {
        #     'setting_type': 'project',
        #     'project_name': 'CES_NZKG',
        #     'profile_uiname': 'profielen CES_Reserve_profiel4',
        #     'multiplier': 1,
        #     'database': 'energy_profiles',
        #     'measurement': 'profielen CES',
        #     'field': 'Reserve_profiel4',
        #     'profileType': '',
        #     'start_datetime': '2014-12-31T23:00:00+0000',
        #     'end_datetime': '2015-12-31T22:00:00+0000',
        #     'embedUrl': 'https://panel-service.hesi.energy/grafana/d-solo/12lC8xg7z/project-profiles-for-ces_nzkg-reserve_profiel4?panelId=1&from=1420066800000&to=1451599200000&theme=light'
        # }
        esh = EnergySystemHandler()

        edr_profiles = dict()
        edr_client = EDRClient.get_instance()

        field_map = {
            "id": "id",
            "label": "title",
            "description": "description",
            "embedUrl": "graphURL",
            "esdl": "esdl"
        }
        return_code, profile_list = edr_client.get_EDR_profiles_list(field_map=field_map, include_esdl=True)

        if return_code == 200:
            for p in profile_list["item_list"]:
                if not p["id"].startswith("/edr/Public/Profiles"):
                    continue
                    
                p.update({
                    "setting_type": "EDR",
                    "project_name": "",
                    "profile_uiname": p["id"].replace("/edr/Public/Profiles", "EDR").replace(".edd", ""),
                    "profileType": ""
                })

                profile_esdl = p["esdl"]
                esdlstr_base64_bytes = profile_esdl.encode("utf-8")
                esdlstr_bytes = base64.decodebytes(esdlstr_base64_bytes)
                esdlstr = esdlstr_bytes.decode("utf-8")

                profile, parse_info = esh.load_from_string(esdlstr)
                p.update({
                    "host": profile.host,
                    "port": profile.port,
                    "database": profile.database,
                    "measurement": profile.measurement,
                    "field": profile.field,
                    "multiplier": profile.multiplier,
                    "profileType": "",
                    "start_datetime": profile.startDate.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "end_datetime": profile.endDate.strftime("%Y-%m-%dT%H:%M:%S%z"),
                })

                del p["esdl"]
                profile_id = p["id"]
                del p["id"]
                edr_profiles[profile_id] = p

        # {
        #      'id': '/edr/Public/Test/standard_profiles - E3A [ENERGY in %].edd',
        #      'title': 'standard_profiles - E3A [ENERGY in %]', 'description': None,
        #      'tags': [],
        #      'version': '1',
        #      'author': None,
        #      'validityYear': None,
        #      'graphURL': 'http://localhost:6530/d-solo/lniEYFS4k/standard_profiles-e3a-energy-in?panelId=1&from=1546297200000&to=1577829600000&theme=light',
        #      'esdl': 'PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPGVzZGw6SW5mbHV4REJQcm9maWxlIHhtbG5zOnhzaT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS9YTUxTY2hlbWEtaW5zdGFuY2UiIHhtbG5zOmVzZGw9Imh0dHA6Ly93d3cudG5vLm5sL2VzZGwiIG5hbWU9InN0YW5kYXJkX3Byb2ZpbGVzIC0gRTNBIFtFTkVSR1kgaW4gJV0iIGlkPSIwNmE2MjAzYS02YmViLTQ1NTItOGRjZi00NmMzMTc5N2EwODkiIHN0YXJ0RGF0ZT0iMjAxOC0xMi0zMVQyMzowMDowMC4wMDArMDAwMCIgZW5kRGF0ZT0iMjAxOS0xMi0zMVQyMjowMDowMC4wMDArMDAwMCIgaG9zdD0iaHR0cDovL2xvY2FsaG9zdCIgcG9ydD0iNjU4NiIgZGF0YWJhc2U9ImVkcl9wcm9maWxlcyIgbWVhc3VyZW1lbnQ9InN0YW5kYXJkX3Byb2ZpbGVzIiBmaWVsZD0iRTNBIj4KICA8cHJvZmlsZVF1YW50aXR5QW5kVW5pdCB4c2k6dHlwZT0iZXNkbDpRdWFudGl0eUFuZFVuaXRUeXBlIiBwaHlzaWNhbFF1YW50aXR5PSJFTkVSR1kiIHVuaXQ9IlBFUkNFTlQiIGlkPSJhOTRkODBhZC0xODA5LTQyYjQtYjBiYS03MWMxZjNjNzI1ZDIiLz4KPC9lc2RsOkluZmx1eERCUHJvZmlsZT4K',
        #      'image': None,
        #      'esdlType': 'InfluxDBProfile',
        #      'lastChanged': 1665672977928,
        #      'publicationDate': 1665672977928,
        #      'history': [{'user': 'edwin.matthijssen@tno.nl', 'commitMessage': 'No commit message', 'timestamp': 1665672977928}],
        #      'annotation': None
        #  }

        return edr_profiles

    def create_new_profile(self, group, uiname, multiplier, database, measurement, field, profile_type, start_datetime, end_datetime):
        setting_type, project_name = self.get_setting_type_project_name(group)
        profile = {
            "setting_type": setting_type,
            "project_name": project_name,
            "profile_uiname": uiname,
            "multiplier": multiplier,
            "database": database,
            "measurement": measurement,
            "field": field,
            "profileType": profile_type,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "embedUrl": None
        }
        return profile
    
    def get_profiles_settings(self):
        profiles_settings = dict()
        if self.settings_storage.has_system(PROFILES_SETTINGS):
            profiles_settings.update(self.settings_storage.get_system(PROFILES_SETTINGS))

        user = get_session('user-email')
        user_group = get_session('user-group')
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')

        if user is not None and self.settings_storage.has_user(user, PROFILES_SETTINGS):
            # add user profiles settings if available
            profiles_settings.update(self.settings_storage.get_user(user, PROFILES_SETTINGS))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, PROFILES_SETTINGS):
                    # add project profiles server settings if available
                    # Note: this is a specific implementation for a dict element with a list of servers. When
                    #       additional settings must be added, this implementation must be extended.
                    project_profiles_settings = self.settings_storage.get_project(identifier, PROFILES_SETTINGS)
                    if 'profiles_servers' in project_profiles_settings:
                        profiles_settings['profiles_servers'].extend(project_profiles_settings['profiles_servers'])

        return profiles_settings

    def get_profiles_system_settings(self):
        if self.settings_storage.has_system(PROFILES_SETTINGS):
            profiles_settings = self.settings_storage.get_system(PROFILES_SETTINGS)
        else:
            profiles_settings = dict()
            profiles_settings["profiles_servers"] = [{
                "name": "Standard profiles server",
                "host": settings.profile_database_config['host'],
                "port": settings.profile_database_config['port'],
                "username": settings.profile_database_config['upload_user'],
                "password": settings.profile_database_config['upload_password'],
                "database": settings.profile_database_config['database'],
                "ssl_enabled": True if settings.profile_database_config['protocol'] == 'https' else False,
            }]
            self.settings_storage.set_system(PROFILES_SETTINGS, profiles_settings)
        return profiles_settings

    def create_esdl_influxdb_profile(self, profile_uiname, multiplier):
        profiles = self.get_profiles()['profiles']
        esdl_profile = None
        for pkey in profiles:
            p = profiles[pkey]

            if p['profile_uiname'] == profile_uiname:
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
                break

        return esdl_profile


default_profile_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal profiles", "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value, "name": "Standard profiles", "readonly": True},
        {"setting_type": "EDR", "project_name": "EDR profiles", "name": "EDR profiles", "readonly": True}
    ]
}

default_profiles = {
    # "Test": {
    #     "setting_type": SettingType.SYSTEM.value,
    #     "profile_uiname": "Test",
    #     "multiplier": 1,
    #     "database": "energy_profiles",
    #     "measurement": "test",
    #     "field": "value",
    #     "profileType": "ENERGY_IN_TJ",
    #     "start_datetime": "2015-01-01T00:00:00.000000+0100",
    #     "end_datetime": "2016-01-01T00:00:00.000000+0100",
    #     "embedUrl": ""
    # }
}
