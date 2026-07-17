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
import copy
import csv
import datetime
import locale
import math
import re
import threading
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
import pytz
from flask import Flask
from flask_executor import Executor
from flask_socketio import SocketIO, emit
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from pyecore.ecore import EDate
from requests.exceptions import ConnectionError

import src.log as log
import src.settings as settings
from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import build_qau_from_dict, get_or_create_esi_qau
from esdl.profiles.data_configurations.credentials import Credentials
from esdl.profiles.datatableprofilemanager import DataTableProfileManager
from esdl.profiles.influxdbprofilemanager import ConnectionSettings, InfluxDBProfileManager
from esdl.units.parser import qau_to_string
from esdlproject.ProjectManager import load_external_string
from extensions.panel_service import create_panel, get_panel_service_datasource
from extensions.profile_server import ProfileServerTypeEnum, InfluxDBConnectionSettings, PostgreSQLConnectionSettings, \
    InfluxDBServer, PostgreSQLServer
from extensions.session_manager import get_session, get_project_manager
from extensions.settings_storage import SettingType, SettingsStorage
from src.edr_client import EDRClient
from src.roles import is_mapeditor_admin
from utils.datetime_utils import parse_date
from utils.utils import str2float, timed

logger = log.get_logger(__name__)

PROFILES_LIST = 'PROFILES'  # To store profiles
PROFILES_SETTINGS = 'PROFILES_SETTINGS'  # To store information about profiles servers, ...
profiles = None

dt_str_format = '%Y-%m-%d %H:%M:%S'

@dataclass
class AssetPortsProfilesRequest:
    es_id: str
    asset_id: str

@dataclass
class ProfileVizOptions:
    """The dataclass specifies profile trace visualization overrides options."""
    start_datetime: Optional[datetime.datetime | str] = None
    """Timezone aware start datetime. If a string is given, it is converted into a timezone aware datetime object."""
    end_datetime: Optional[datetime.datetime | str] = None
    """Timezone aware end datetime. If a string is given, it is converted into a timezone aware datetime object."""
    multiplier: Optional[float] = None
    """If specified, scale the profile trace based on this value; otherwise, based on ESDL profile instance multiplier attribute."""
    max_datapoints: Optional[int] = None
    """If specified, downsample profile datapoints to approximately the given value."""

    def __post_init__(self):
        if isinstance(self.start_datetime, str):
            self.start_datetime = _dt_str_to_tz_aware_datetime(self.start_datetime)

        if isinstance(self.end_datetime, str):
            self.end_datetime = _dt_str_to_tz_aware_datetime(self.end_datetime)

    def __setattr__(self, key, value):
        if key in ("start_datetime", "end_datetime") and isinstance(value, str): 
            value = _dt_str_to_tz_aware_datetime(value)
        super().__setattr__(key, value)

@dataclass
class ProfileTracesRequest:
    es_id: str
    profile_ids: List[str]
    viz_options: Optional[ProfileVizOptions]

@dataclass
class ProfileTraceDtpRequest:
    dtp_obj: dict
    """A dict (frontend object) that can be converted into an esdl.DataTableProfile"""
    viz_options: Optional[ProfileVizOptions]

class ProfileClassEnum(Enum):
    """Supported profile classes for profile creation and update"""
    SINGLEVALUE = "SingleValue"
    INFLUXDBPROFILE = "InfluxDBProfile"
    DATATABLEPROFILE = "DataTableProfile"

@dataclass
class AddProfileRequest:
    es_id: str
    profile_container_id: str
    """The container id for which the profile will be attached to. e.g. Port id"""
    profileClass: ProfileClassEnum
    profileObj: dict
    """A dict (frontend object) that can be converted into an ESDL profile class e.g, esdl.DataTableProfile, esdl.SingleValue"""

    def __post_init__(self):
        if isinstance(self.profileClass, str):
            self.profileClass = ProfileClassEnum(self.profileClass)

@dataclass
class ReplaceProfileRequest(AddProfileRequest):
    """Used when replacing an existing profile with a new one."""
    existing_profile_id: str
    """ID of the existing profile to be replaced"""

@dataclass
class UpdateProfileRequest:
    es_id: str
    profile_id: str
    profileClass: ProfileClassEnum
    updates: dict

    def __post_init__(self):
        if isinstance(self.profileClass, str):
            self.profileClass = ProfileClassEnum(self.profileClass)

def send_alert(message):
    logger.warning(message)
    # emit('alert', message, namespace='/esdl')


class Profiles:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.csv_files = dict()
        self.register()

        self.EDR_profiles_cache = dict()
        # Do this in the background cause it takes long.
        threading.Thread(target=self.update_edr_profiles_cache, daemon=True).start()

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

    @timed
    def update_edr_profiles_cache(self):
        """Generate EDR profiles list."""
        logger.info("Starting generation of EDR profiles cache")
        try:
            edr_profiles = self.generate_EDR_profiles_list()
            self.EDR_profiles_cache = edr_profiles
            logger.info("EDR profiles cache generated successfully", num_profiles=len(edr_profiles))
        except Exception:
            logger.exception("Error generating EDR profiles cache")

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
                host=profile_info["host"] if profile_info["host"] != "" else None,
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
                    # print(content)
                    self.csv_files[uuid]['content'][pos:len(content)] = content
                    self.csv_files[uuid]['pos'] = pos + len(content)
                    if self.csv_files[uuid]['pos'] >= size:
                        # print("Upload complete:", str(bytearray(self.csv_files[uuid]['content'])))

                        ba = bytearray(self.csv_files[uuid]['content'])
                        csv = ba.decode(encoding='utf-8-sig')
                        emit('csv_upload_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                                 'success': True})
                        self.executor.submit(self.process_csv_file, name, uuid, csv)
                    else:
                        # print("Requesting next chunk", str(bytearray(self.csv_files[uuid]['content'])))
                        emit('csv_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos']})

        @self.socketio.on('get_profiles_settings', namespace='/esdl')
        def get_profiles_settings():
            with self.flask_app.app_context():
                prof_settings = self.get_profiles_settings()

                # Only communicate the name to the frontend
                ui_prof_settings_list = list()
                for p in prof_settings['profiles_servers']:
                    ui_prof_settings_list.append({"name": p["name"]})

                return {"profiles_servers": ui_prof_settings_list}

        @self.socketio.on('get_profile_settings_as_dtp_objects', namespace='/esdl')
        def _get_profile_settings_as_dtp_objects():
            """
            Retrieve and return stored profile settings
            via converting them into DataTableProfile-like response objects.
            """
            return self.get_profile_settings_as_dtp_objects()

        @self.socketio.on("get_asset_ports_profiles", namespace="/esdl")
        def _get_asset_ports_profiles(params: dict):
            """Return asset-associated ports profiles in a dict for a given asset id."""
            req = AssetPortsProfilesRequest(**params)
            return Profiles.get_asset_ports_profiles(req.es_id, req.asset_id)
        
        @self.socketio.on('get_profile_traces', namespace='/esdl')
        def _get_profile_traces_from_profile_ids(params: dict):
            """Return ESDL profile traces (or error messages) for a given ESDL profile ids."""
            req = ProfileTracesRequest(**params)
            req.viz_options = ProfileVizOptions(**req.viz_options)
            return Profiles.get_profile_traces_from_profile_ids(req)

        @self.socketio.on('get_profile_trace_from_dtp_obj', namespace='/esdl')
        def _get_profile_trace_from_dtp_obj(params: dict):
            """
            Return a profile trace for a given DataTableProfile-like object.
            This can be used to request a profile trace from a publicly registered profile, such as EDR.
            """
            req = ProfileTraceDtpRequest(**params)
            viz_options = ProfileVizOptions(**req.viz_options)
            return Profiles.get_profile_trace_from_dtp_obj(req.dtp_obj, viz_options)

        @self.socketio.on('add_esdl_profile', namespace='/esdl')
        def _add_esdl_profile(params: dict) -> dict:
            """Add a new profile to a given profile container in an ESDL."""
            try:
                req = AddProfileRequest(**params)
                Profiles.add_esdl_profile(req.es_id, req.profile_container_id, req.profileClass, req.profileObj)
                return {"success": True, "message": f"Successfully added profile."}
            except Exception as e: 
                return {"success": False, "message": str(e)}
            
        @self.socketio.on('replace_esdl_profile', namespace='/esdl')
        def _replace_esdl_profile(params: dict) -> dict:
            """Replace a profile in a given profile container in an ESDL."""
            try:
                req = ReplaceProfileRequest(**params)
                Profiles.replace_esdl_profile(req.es_id, req.profile_container_id, req.existing_profile_id, req.profileClass, req.profileObj)
                return {"success": True, "message": f"Successfully replaced profile."}
            except Exception as e:
                return {"success": False, "message": str(e)}

        @self.socketio.on('update_esdl_profile', namespace='/esdl')
        def _update_esdl_profile(params: dict) -> dict:
            """Update an existing ESDL profile for a given profile id and updates dict."""
            try:
                req = UpdateProfileRequest(**params)
                Profiles.update_esdl_profile(req.es_id, req.profile_id, req.profileClass, req.updates)
                return {"success": True, "message": f"Successfully updated profile."}
            except Exception as e: 
                return {"success": False, "message": str(e)}

    def update_profiles_list(self):
        emit('update_profiles_list', self.get_profiles())

    def format_datetime(self, dt):
        date, time = dt.split(" ")
        day, month, year = date.split("-")
        ndate = year + "-" + month + "-" + day
        ntime = time + ":00+0000"
        return ndate + "T" + ntime

    def guess_profile_server_type(self, profile_settings) -> ProfileServerTypeEnum:
        if "type" in profile_settings:
            return profile_settings["type"]
        else:
            if ("port" in profile_settings and str(profile_settings["port"]) == "8086") or \
                    ("host" in profile_settings and "influxdb" in profile_settings["host"]):
                return ProfileServerTypeEnum.INFLUXDB
            elif ("port" in profile_settings and str(profile_settings["port"]) == "5432") or \
                    ("host" in profile_settings and "postgres" in profile_settings["host"]):
                return ProfileServerTypeEnum.POSTGRESQL

    def process_csv_file(self, name, uuid, content):
        logger.debug("Processing csv file(s) (threaded): {}".format(name))

        try:
            self.import_profile_csv(
                name,
                content,
                self.csv_files[uuid]['group'],
                int(self.csv_files[uuid]['profiles_server_index']),
                self.csv_files[uuid]['prof_aggr_type'],
            )
            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                         'success': True})
        except Exception as e:
            logger.exception("Error processing CSV")
            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                         'success': False, 'error': str(e)})

        # clean up
        del (self.csv_files[uuid])

    def import_profile_csv(self, name, content, group="Standard profiles", profiles_server_index=0,
                           prof_aggr_type="sum", emit_update=True):
        logger.info("process CSV")
        csv_file_name_without_extension = name.split('.')[0]

        try:
            csv_file = StringIO(content)
            dialect = csv.Sniffer().sniff(csv_file.read(4096))
            if dialect.delimiter == ',':
                raise ValueError(f"CSV file '{name}' uses comma ',' as delimiter. Please use semicolon ';' to avoid parsing errors.")
            csv_file = StringIO(content)
            reader = csv.reader(csv_file, dialect)
        except csv.Error:
            # If format cannot be determined automatically, try ; as a default
            csv_file = StringIO(content)
            reader = csv.reader(csv_file, delimiter=';')

        column_names = next(reader)
        num_fields = len(column_names)
        timeseries_data = []

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
                    raise (Exception("CSV contains duplicate datetimes ({}). Check timezone and daylight saving".
                                     format(dt_string)))
            previous_datetime = aware_dt

            if not start_datetime:
                start_datetime = dt_string
            else:
                end_datetime = dt_string

            timeseries_data.append({
                "time": dt_string,
                "fields": fields
            })

        logger.info("CSV processing finished, now writing to database...")

        with self.flask_app.app_context():
            if group == "Standard profiles":
                profiles_settings = self.get_profiles_system_settings()
            else:
                profiles_settings = self.get_profiles_settings()
            host = profiles_settings['profiles_servers'][profiles_server_index]['host']
            port = int(profiles_settings['profiles_servers'][profiles_server_index]['port'])
            database = profiles_settings['profiles_servers'][profiles_server_index]['database']

            profile_server_type_str = self.guess_profile_server_type(profiles_settings['profiles_servers'][profiles_server_index])
            profile_server_type = ProfileServerTypeEnum(profile_server_type_str)
            if profile_server_type == ProfileServerTypeEnum.INFLUXDB:
                influxdb_profile_server = InfluxDBServer(
                    connection_settings=InfluxDBConnectionSettings(
                        host=host,
                        port=port,
                        username=profiles_settings['profiles_servers'][profiles_server_index]['username'],
                        password=profiles_settings['profiles_servers'][profiles_server_index]['password'],
                        database=database,
                        ssl=profiles_settings['profiles_servers'][profiles_server_index]['ssl_enabled'],
                    )
                )

                influxdb_profile_server.connect()
                influxdb_profile_server.convert_data(data=timeseries_data, measurement=csv_file_name_without_extension)
                influxdb_profile_server.write_data()

                # Get or create a datasource in Grafana using the panalservice
                if profiles_settings['profiles_servers'][profiles_server_index]['ssl_enabled']:
                    protocol = "https://"
                else:
                    protocol = "http://"
                profiles_server_host = f"{protocol}{host}:{port}"
                datasource = get_panel_service_datasource(
                    database=database,
                    host=profiles_server_host,
                    username=profiles_settings['profiles_servers'][profiles_server_index]['username'],
                    password=profiles_settings['profiles_servers'][profiles_server_index]['password'],
                )

            elif profile_server_type == ProfileServerTypeEnum.POSTGRESQL:
                postgres_profile_server = PostgreSQLServer(
                    connection_settings=PostgreSQLConnectionSettings(
                        host=host,
                        port=port,
                        username=profiles_settings['profiles_servers'][profiles_server_index]['username'],
                        password=profiles_settings['profiles_servers'][profiles_server_index]['password'],
                        database=database,
                        ssl=profiles_settings['profiles_servers'][profiles_server_index]['ssl_enabled'] if "ssl_enabled" in profiles_settings['profiles_servers'][profiles_server_index] else False,
                    )
                )

                postgres_profile_server.connect()
                postgres_profile_server.convert_data(data=timeseries_data, table_name=csv_file_name_without_extension)
                postgres_profile_server.write_data()

        # Store profile information in settings
        logger.info("Store profile information in settings")

        profile_count = 0
        for i in range(1, num_fields):
            field = column_names[i]

            # Stop if empty column was found
            if field.strip() == '':
                break

            profile_name = csv_file_name_without_extension + '_' + field
            profile_id = str(uuid4())
            setting_type, project_name = self.get_setting_type_project_name(group)
            setting_type = SettingType(setting_type)
            identifier = self._get_identifier(setting_type, project_name)
            if identifier is not None and self.settings_storage.has(setting_type, identifier, PROFILES_LIST):
                profiles = self.settings_storage.get(setting_type, identifier, PROFILES_LIST)
                for existing_id, existing_profile in profiles.items():
                    if existing_profile.get('profile_uiname') == profile_name:
                        profile_id = existing_id
                        break

            # Create a dictionary with all relevant information about the new profile
            profile = self.create_new_profile(
                group=group,
                uiname=profile_name,
                multiplier=1,
                database_type=profile_server_type.value,
                host=host,
                port=port,
                database=database,
                profile_type="",
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )

            if profile_server_type == ProfileServerTypeEnum.INFLUXDB:
                self.add_influxdb_details(profile, csv_file_name_without_extension, field)
            elif profile_server_type == ProfileServerTypeEnum.POSTGRESQL:
                self.add_postgres_details(profile, csv_file_name_without_extension, field)

            if profile_server_type == ProfileServerTypeEnum.INFLUXDB:
                # Create a grafana panel for visualization and add the embedURL to the dictionary
                profile["embedUrl"] = create_panel(
                    graph_title=group + " - " + field,
                    axis_title="",
                    datasource=datasource,
                    host=profiles_server_host,
                    database=database,
                    measurement=csv_file_name_without_extension,
                    field=field,
                    filters=[],
                    qau=None,
                    prof_aggr_type=prof_aggr_type,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime
                )
            # Store the new profile in the profiles settings
            self.add_profile(profile_id, profile, emit_update)

    def add_profile(self, profile_id, profile, emit_update=True):
        setting_type = SettingType(profile['setting_type'])
        project_name = profile['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, PROFILES_LIST):
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_LIST)
        else:
            profiles = dict()
        profiles[profile_id] = profile
        self.settings_storage.set(setting_type, identifier, PROFILES_LIST, profiles)
        if emit_update:
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
            logger.info('Deleting profile', profile=profiles[profile_id])
            del (profiles[profile_id])
            self.settings_storage.set(setting_type, identifier, PROFILES_LIST, profiles)
            # TODO: also remove record from DB?

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
        if is_mapeditor_admin():
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
        if is_mapeditor_admin():
            dpg['groups'][1]['readonly'] = False

        possible_groups = dpg["groups"]
        possible_groups.extend(self._create_group_profiles_for_projects(user_group))
        return possible_groups

    def _create_group_profiles_for_projects(self, groups):
        project_list = list()
        if groups is not None:
            for group in groups:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                json = {"setting_type": SettingType.PROJECT.value, "project_name": identifier,
                        "name": "Project profiles for " + group, "readonly": False}
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

    def determine_database_credentials(self, host, port, database):
        # Whenever the port profile viewer is called based on information (host / database) in the ESDL InfluxDB profile
        # this functions tries to see if the credentials are stored in the profile server settings

        # Example profile server configuration in MongoDB
        #       {
        #         "name": "Standard profiles server",
        #         "host": "influxdb",
        #         "port": "8086",
        #         "username": "admin",
        #         "password": "admin",
        #         "database": "energy_profiles",
        #         "ssl_enabled": false
        #       }

        with self.flask_app.app_context():
            profiles_settings = self.get_profiles_settings()

            for prof_server in profiles_settings['profiles_servers']:
                if prof_server["host"] == host and prof_server["port"] == str(port):
                    return {
                        "username": prof_server["username"],
                        "password": prof_server["password"]
                    }

        return None

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

        edr_profiles = dict()
        edr_client = EDRClient.get_instance()

        if not edr_client.EDR_config.get('host'):
            return edr_profiles

        field_map = {
            "id": "id",
            "label": "title",
            "description": "description",
            "embedUrl": "graphURL",
            "esdl": "esdl"
        }
        return_code, profile_list = edr_client.get_EDR_profiles_list(field_map=field_map, include_esdl=True)

        if return_code == 200:
            logger.info(f"- Retrieved {len(profile_list['item_list'])} profiles from the EDR.")
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

                profile, parse_info = load_external_string(esdlstr)
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

    def create_new_profile(self, group, uiname, multiplier, database_type, host, port, database, profile_type, start_datetime,
                           end_datetime):
        setting_type, project_name = self.get_setting_type_project_name(group)
        profile = {
            "setting_type": setting_type,
            "project_name": project_name,
            "profile_uiname": uiname,
            "multiplier": multiplier,
            "type": database_type,
            "host": host,
            "port": int(port),
            "database": database,
            "profileType": profile_type,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "embedUrl": None
        }
        return profile

    def add_influxdb_details(self, profile, measurement, field):
        profile["measurement"] = measurement
        profile["field"] = field
        return profile

    def add_postgres_details(self, profile, table, column):
        profile["table"] = table
        profile["column"] = column
        return profile

    def get_profiles_settings(self):
        profiles_settings = dict()
        if self.settings_storage.has_system(PROFILES_SETTINGS):
            profiles_settings.update(self.settings_storage.get_system(PROFILES_SETTINGS))

        user = get_session('user-email')
        user_group = get_session('user-group')

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

    @staticmethod
    def get_profiles_for_asset_type(es_id: str, asset_types: list[type(esdl.Asset)]) -> list:
        """Build a list of all profiles of specific asset types in the ESDL file.
        """
        logger.info(es_id)
        pm = get_project_manager()
        energy_system = pm.get_energy_system_by_id(es_id)

        instance = energy_system.instance[0]
        profiles = []
        if instance and instance.area:
            for asset in instance.area.asset:
                if isinstance(asset, tuple(asset_types)):
                    for port in getattr(asset, 'port', []):
                        for profile in getattr(port, 'profile', []):
                            profiles.append(profile)
                    for inner_asset in getattr(asset, 'asset', []):
                        for port in getattr(inner_asset, 'port', []):
                            for profile in getattr(port, 'profile', []):
                                profiles.append(profile)

        return profiles

    @staticmethod
    def get_profile_of_asset_with_field(asset: esdl.Asset, field: str) -> esdl.GenericProfile | None:
        """Get the profile from an asset which matches a specified field.
        """
        for port in getattr(asset, 'port', []):
            for profile in getattr(port, 'profile', []):
                if profile.field == field:
                    return profile
        return None

    @staticmethod
    def connect_to_animation_profiles_database(es_id: str):
        anim_profiles = Profiles.get_profiles_for_asset_type(es_id, [esdl.ElectricityCable, esdl.Pipe])
        if not anim_profiles:
            return None

        # make sure all cable/pipe profiles are in the same database
        try:
            Profiles.check_if_profiles_have_same_host_port_database(anim_profiles)
        except IOError as ioe:
            error_message = f"Could not load animation data: \n{ioe.message}"
            logger.error(error_message)
            raise ConnectionError(error_message)

        # get influxdb host, port, database from first cable/pipe
        profile = anim_profiles[0]
        influxdb_host = profile.host
        influxdb_port = profile.port
        database = profile.database

        # get credentials (if available)
        credentials = Profiles.get_instance().determine_database_credentials(influxdb_host, influxdb_port, database)
        if credentials:
            influxdb_client = InfluxDBClient(
                host=influxdb_host,
                port=influxdb_port,
                database=database,
                username=credentials["username"],
                password=credentials["password"],
            )
        else:
            influxdb_client = InfluxDBClient(host=influxdb_host, port=influxdb_port, database=database)
        if not influxdb_client:
            raise ConnectionError(f"Could not connect to influxdb '{influxdb_host}' to database '{database}'")

        return influxdb_client

    @staticmethod
    def check_if_profiles_have_same_host_port_database(profile_list):
        used_host = None
        used_port = None
        used_database = None

        general_error_message = "profiles should be in the same host, port and database."
        for p in profile_list:
            edited_host = p.host.lower().replace("http://", "").replace("https://", "")
            if used_host and edited_host != used_host:
                raise IOError(
                    f"{general_error_message}"
                    f"\nDifferent host:port found: '{used_host}:{used_port}' and '{edited_host}:{p.port}'."
                )
            else:
                used_host = edited_host

            if used_port and p.port != used_port and p.port != 0:
                raise IOError(
                    f"{general_error_message}"
                    f"\nDifferent host:port found: '{used_host}:{used_port}' and '{edited_host}:{p.port}'."
                )
            else:
                used_port = p.port

            if used_database and p.database != used_database:
                raise IOError(
                    f"{general_error_message}\nDifferent databases found: '{used_database}' and '{p.database}'."
                )
            else:
                used_database = p.database

        return True

    @staticmethod
    def get_animation_fields(esdl_id: str) -> Optional[list[str]]:
        # Get all fields available for all 'Pipe' and/or 'ElectricityCable' assets.
        try:
            influxdb_client = Profiles.connect_to_animation_profiles_database(esdl_id)

            if not influxdb_client:
                return None

            query_collections_with_asset_id = 'SHOW TAG VALUES WITH KEY="assetId"'
            collections_with_asset_id = influxdb_client.query(query_collections_with_asset_id)
            carrier_ids = collections_with_asset_id.keys()[0]

            if not carrier_ids:
                return None

            fields = []
            for carrier_id in carrier_ids:
                tag_fields_query = f'SHOW TAG KEYS FROM "{carrier_id}"'
                result = influxdb_client.query(tag_fields_query)
                tag_fields = ["time"] + [point["tagKey"] for point in result.get_points()]

                all_fields_query = (
                    f'SELECT * FROM "{carrier_id}" '
                    f"WHERE \"assetClass\" = 'Pipe' OR \"assetClass\" = 'ElectricityCable' LIMIT 1"
                )
                result = influxdb_client.query(all_fields_query)
                for point in result.get_points():
                    fields += [key for key in point.keys() if key not in tag_fields and key not in fields]
        except ConnectionError as nre:
            emit(
                "alert",
                f"Could not connect to influxdb '{influxdb_client._host}:{influxdb_client._port}'"
                f" for time series animation data retrieval.",
                namespace="/esdl",
            )
            return None
        except InfluxDBClientError as ie:
            emit(
                "alert",
                f"Could get data from influxdb '{influxdb_client._host}:{influxdb_client._port}'"
                f" for time series animation data retrieval: '{str(ie)}'.",
                namespace="/esdl",
            )
            return None
        except Exception as e:
            # No animation data
            logger.info(f"No animation data found due to error: {e}")
            return None

        return fields
    
    def get_profile_settings_as_dtp_objects(self) -> List[dict]:
        """
        Retrieve all stored profile settings from MongoDB and convert them into
        DataTableProfile-like response objects. This normalizes both
        InfluxDB-based and PostgreSQL-based stored profiles into a unified structure
        so the frontend can reliably consume a consistent API format.

        The returned list contains objects of the form:
            {
                "profileObj": <serialized DataTableProfile>,
                "metadata": {
                    "profileSettingId": <profile setting id string>
                    "profileDisplayedName": <profile displayed name>
                    "profileGroupName": <group name>
                }
            }

        :return: List of standardized DataTableProfile-like and metadata objects.
        """

        profile_settings = []

        # Retrieve stored profile groups and profile records
        profile_groups = self.get_profiles()['groups']
        stored_profiles = self.get_profiles()['profiles']

        # Track duplicates: {display_name: count}
        name_counter = {}

        for id, p in stored_profiles.items():
            dtp = esdl.DataTableProfile(
                id=p.get("id"),
                name=p.get("name"),
                tableName=p.get("table") or p.get("measurement"),
                columnName=p.get("column") or p.get("field"),
                filter=None,
                multiplier=float(p.get("multiplier")),
                startDate=_dt_str_to_tz_aware_datetime(p.get("start_datetime")),
                endDate=_dt_str_to_tz_aware_datetime(p.get("end_datetime")),
                profileType=esdl.ProfileTypeEnum.from_string(p.get("profileType")),
                profileQuantityAndUnit=None
            )

            dtp.configuration = esdl.DatabaseConfiguration(
                database=p.get("database"),
                type=esdl.DatabaseTypeEnum.from_string(p.get("type", "INFLUXDB")),
                host=p.get("host"),
                port=int(p.get("port")) if str(p.get("port")).isdigit() else None
            )

            # Serialize for frontend
            serialized_profile = Profiles.serialize_datatableprofile(dtp)

            # Profile metadata
            db_type = serialized_profile["configuration"]["type"]
            table_name = serialized_profile["tableName"]
            col_name = serialized_profile["columnName"]

            # Base display name
            base_name = f"{db_type}: {table_name}.{col_name}"

            # TODO: better uniqueness handling?
            # Ensure uniqueness
            if base_name not in name_counter:
                name_counter[base_name] = 1
                profile_displayed_name = base_name
            else:
                name_counter[base_name] += 1
                profile_displayed_name = f"{base_name} ({name_counter[base_name]})"

            setting_type = p.get("setting_type")
            group_display_name = next(
                (g["name"] for g in profile_groups if g["setting_type"] == setting_type),
                None
            )

            profile_settings.append({
                "profileObj": serialized_profile,
                "metadata": {
                    "profileSettingId": id,
                    "profileDisplayedName": profile_displayed_name,
                    "profileGroupName": group_display_name
                }
            })

        return profile_settings

    @staticmethod
    def get_profile_influxdb_settings(host: str, port: int, database: str, profiles_settings: dict) -> ConnectionSettings | None:
        """
        Retrieve InfluxDB connection settings for a given profile host, port, and database.

        If the profile is hosted on a publicly accessible server, 
        it additionally checks the InfluxDB connectivity and constructs the connection settings.
        """
        settings = None

        # Find profile server information for the InfluxDBProfile
        for prof_server in profiles_settings.get("profiles_servers", []):
            if prof_server["host"] in host and prof_server["port"] == str(port):
                settings = ConnectionSettings(
                    host=prof_server["host"],
                    port=port,
                    database=database,
                    username=prof_server["username"],
                    password=prof_server["password"],
                    ssl=prof_server.get("ssl_enabled", False),
                    verify_ssl=prof_server.get("ssl_enabled", False),
                )
                break

        # Check additionally if the profile is hosted on a public accessible server
        if settings is None:
            # Ensure host part only (without http:// or https://) 
            host_loc = urlparse(host).netloc if host.startswith(('http://', 'https://')) else host
            settings = ConnectionSettings(
                    host=host_loc,
                    port=port,
                    database=database,
                    username="",
                    password="",
                    ssl=True,
                    verify_ssl=True,
                )
        # TODO: performance issue with _test_influxdb_connection?
        if _test_influxdb_connection(settings):
            return settings
        
        return None

    @staticmethod
    def get_profile_postgres_settings(host: str, port: int, database: str, profiles_settings: dict) -> PostgreSQLConnectionSettings | None:
        """
        Retrieve PostgreSQL connection settings for a given profile host, port, and database.
        """
        settings = None

        # Find profile server information for the PostgreSQL
        for prof_server in profiles_settings.get("profiles_servers", []):
            if (prof_server.get("type") and ProfileServerTypeEnum(prof_server["type"]) == ProfileServerTypeEnum.POSTGRESQL and
                prof_server["host"] in host and prof_server["port"] == str(port)):
                settings = PostgreSQLConnectionSettings(
                    host=prof_server["host"],
                    port=port,
                    database=database,
                    username=prof_server["username"],
                    password=prof_server["password"],
                )
                break
        # TODO: performance issue with _test_postgresql_connection?
        if settings is not None and _test_postgresql_connection(settings):
            return settings
        
        return None

    @staticmethod
    def influxdbprofile_to_datatableprofile(profile: esdl.InfluxDBProfile) -> esdl.DataTableProfile:
        """The method translates InfluxDBProfile into DataTableProfile."""

        dtp = esdl.DataTableProfile(
            id=profile.id,
            name=profile.name,
            tableName=profile.measurement,
            columnName=profile.field,
            filter=profile.filters,
            multiplier=profile.multiplier,
            startDate=profile.startDate,
            endDate=profile.endDate,
            profileType=profile.profileType,
            profileQuantityAndUnit=_clone_qau(profile.profileQuantityAndUnit)
        )

        dtp.configuration = esdl.DatabaseConfiguration(
            database=profile.database,
            type=esdl.DatabaseTypeEnum.INFLUXDB,
            host=profile.host,
            port=profile.port,
            tls=False
        )

        return dtp
    
    @staticmethod

    def get_asset_ports_profiles(es_id: str, asset_id: str) -> dict:
        """
        Retrieve and return all profiles attached to the ports of a given asset in an ESDL.
        """
        pm = get_project_manager()

        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)
        if not asset:
            raise AssetNotFoundError(f"Asset (id={asset_id}) from ESDL (id={es_id}) not found.")
        if not isinstance(asset, esdl.ConnectableAsset):
            raise AssetNotFoundError(f"Asset (id={asset_id}) from ESDL (id={es_id}) is of unsupported type {asset.eClass.name}.")
      
        ports_profiles = []
        for port in asset.port:
            profiles = []
            for profile in port.profile:
                serialized_profile = Profiles.serialize_esdl_profile(profile)
                profiles.append(serialized_profile)

            ports_profiles.append(
                {
                    "port_id": port.id,
                    "port_name": port.name,
                    "port_type": type(port).__name__,
                    "port_profiles": profiles
                }
            )

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "ports_profiles": ports_profiles
        }


    @staticmethod
    def get_profile_traces_from_profile_ids(req: ProfileTracesRequest) -> Dict[str, List[Dict[str, Any]]]:
        """Return a dictionary with profile traces or error messages."""

        results = {"traces": [], "errors": []}

        for profile_id in req.profile_ids:
            try:
                trace = Profiles.get_esdl_profile_trace_from_id(req.es_id, profile_id, req.viz_options)
                results["traces"].append({
                    "profile_id": profile_id,
                    "trace": trace
                })
            except Exception as e:
                results["errors"].append({
                    "profile_id": profile_id,
                    "error": str(e)
                })

        return results
    
    @staticmethod
    def get_esdl_profile_trace_from_id(es_id: str, profile_id: str, viz_options: Optional[ProfileVizOptions]) -> dict:
        """Retrieve a single profile trace for a given ESDL profile ID."""
        pm = get_project_manager()

        profile = pm.get_by_id(es_id, profile_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile (id={profile_id}) from ESDL (id={es_id}) not found.")
        
        if isinstance(profile, esdl.TimeSeriesProfile):
            return Profiles.get_timeseriesprofile_trace(profile, viz_options)
        elif isinstance(profile, esdl.DataTableProfile):
            dtp = profile
        elif isinstance(profile, esdl.InfluxDBProfile):
            dtp = Profiles.influxdbprofile_to_datatableprofile(profile)
        else:
            raise ProfileClassError(f"Unsupported profile (id={profile_id}) class: {type(profile).__name__}")

        return Profiles.get_datatableprofile_trace(dtp, viz_options)

    def get_profile_trace_from_dtp_obj(dtp_obj: dict, viz_options: Optional[ProfileVizOptions]) -> dict:
        """
        Convert a frontend DataTableProfile-like object (dict) into an ESDL DataTableProfile,
        then retrieve its profile trace.

        Parameters
        ----------
        dtp_obj : dict
            Dictionary containing DataTableProfile-like fields, including a nested
            'configuration' dict with database connection info.
        viz_options : Optional[ProfileVizOptions]
            Visualization options that may override profile attributes.
        """        
        results = {"traces": [], "errors": []}

        try:
            dtp = _create_dtp_from_dtp_obj(dtp_obj)
            dtp.configuration = _create_databaseconfiguration_from_config_obj(dtp_obj.get("configuration"))
            trace = Profiles.get_datatableprofile_trace(dtp, viz_options)
            results["traces"].append({
                "profile_id": None,
                "trace": trace
            })
        except Exception as e:
            results["errors"].append({
                "profile_id": None,
                "error": str(e)
            })
        
        return results

    @staticmethod
    def get_timeseriesprofile_trace(tsp: esdl.TimeSeriesProfile, viz_options: Optional[ProfileVizOptions]) -> dict:
        """Return a trace dict for a TimeSeriesProfile."""
        base_start = tsp.startDateTime
        step = datetime.timedelta(seconds=tsp.timestep)

        if viz_options and viz_options.start_datetime is not None:
            start_dt = viz_options.start_datetime
        else:
            start_dt = base_start

        if viz_options and viz_options.end_datetime is not None:
            end_dt = viz_options.end_datetime
        else:
            end_dt = base_start + step * (len(tsp.values) - 1)

        if start_dt.tzinfo is not None and base_start.tzinfo is None:
            tz = start_dt.tzinfo
            base_start = base_start.replace(tzinfo=tz)

        full_datetimes = [base_start + i * step for i in range(len(tsp.values))]
        sliced_indices = [i for i, dt in enumerate(full_datetimes) if start_dt <= dt <= end_dt]

        if not sliced_indices:
            return {
                "name": tsp.name,
                "x": [],
                "y": [],
            }

        return {
            "name": tsp.name,
            "x": [full_datetimes[i].strftime(dt_str_format) for i in sliced_indices],
            "y": [tsp.values[i] for i in sliced_indices],
        }

    @staticmethod
    def get_datatableprofile_trace(dtp: esdl.DataTableProfile, viz_options: Optional[ProfileVizOptions]) -> dict:
        """
        Load and return a profile trace in a dict.

        If viz_options is provided, they override the inherent attributes of the DataTableProfile instance.
        """

        # Apply visualization overrides
        if viz_options and viz_options.start_datetime is not None:
            start_dt = viz_options.start_datetime
        else:
            start_dt = dtp.startDate

        if viz_options and viz_options.end_datetime is not None:
            end_dt = viz_options.end_datetime
        else:
            end_dt = dtp.endDate

        multiplier = viz_options.multiplier if viz_options and viz_options.multiplier is not None else dtp.multiplier
        max_datapoints = viz_options.max_datapoints if viz_options and viz_options.max_datapoints is not None else None

        # groupby_interval to be used for profile downsampling
        groupby_interval_sec = _calculate_profile_groupby_interval(start_dt, end_dt, max_datapoints)
        
        # Profile connection settings retrieved from MongoDB
        profiles_settings = Profiles.get_instance().get_profiles_settings()

        dtp_config: esdl.DatabaseConfiguration = dtp.configuration

        # --- INFLUXDB HANDLING ---
        # NOTE: InfluxDB profile will be phased out eventually.
        if dtp_config.type == esdl.DatabaseTypeEnum.INFLUXDB:
            influxdb_settings = Profiles.get_profile_influxdb_settings(
                host=dtp_config.host,
                port=dtp_config.port,
                database=dtp_config.database,
                profiles_settings=profiles_settings
            )
            if influxdb_settings is None:
                raise InfluxDBConnectionError(f"Unable to retrieve credentials to connect to InfluxDB database at \
                                                {dtp_config.host}:{dtp_config.port}/{dtp_config.database}")
            try:
                influxdb_pm = InfluxDBProfileManager(influxdb_settings)

                query_filters = _parse_profile_filter(dtp.filter)

                influxdb_pm.load_influxdb(
                    measurement=dtp.tableName,
                    fields=[dtp.columnName],
                    from_datetime=start_dt,
                    to_datetime=end_dt,
                    filters=query_filters,
                    groupby_interval_sec=groupby_interval_sec
                )
                # profile_data_list: a list of lists, with each list structure to be [datetime, field value, ...]
                datetime_profile = influxdb_pm.profile_data_list

                if len(datetime_profile) == 0:
                    raise EmptyProfileWarning(f"Profile [{dtp.columnName}] has no data.")

                datetimes, values = [], []
                for datetime, value, *_ in datetime_profile:
                    # skip when value is None (this can occur when downsampling is applied)
                    if value is None:
                        continue

                    datetimes.append(datetime.strftime(dt_str_format)) 
                    values.append(value * multiplier)

                return {
                    "name": dtp.columnName,
                    "x": datetimes,
                    "y": values,
                }
            except Exception as e:
                raise ProfileTraceLoadError(f"Failed to load influxdb profile trace: {e}") from e
        
        # --- POSTGRES HANDLING ---
        elif dtp_config.type == esdl.DatabaseTypeEnum.POSTGRESQL:
            postgres_settings = Profiles.get_profile_postgres_settings(
                host=dtp_config.host,
                port=dtp_config.port,
                database=dtp_config.database,
                profiles_settings=profiles_settings
            )
            if postgres_settings is None:
                raise PostgreSQLConnectionError(f"Unable to retrieve credentials to connect to Postgres database at \
                                                {dtp_config.host}:{dtp_config.port}/{dtp_config.database}")
            try:
                db_config_id = f"{dtp_config.host}:{dtp_config.port}/{dtp_config.database}"
                if dtp.configuration.id is None:
                    dtp.configuration.id = db_config_id
                
                cred_dict = Credentials.create_dict(
                    id=dtp.configuration.id,
                    username=postgres_settings.username,
                    password=postgres_settings.password
                )

                dtp_viz = copy.deepcopy(dtp)
                dtp_viz.configuration = copy.deepcopy(dtp.configuration)

                query_filters = None
                if dtp_viz.filter:
                    query_filters = _parse_profile_filter(dtp.filter, as_dict=True)

                profile_values, header, metadata = DataTableProfileManager.query(
                    data_table_profile=dtp_viz,
                    credentials_dict=cred_dict,
                    table_name=dtp_viz.tableName,
                    column_name=dtp_viz.columnName,
                    start_date=start_dt,
                    end_date=end_dt,
                    additional_filters=query_filters,
                    multiplier=multiplier,
                    downsample_bucket_sec=groupby_interval_sec or None,
                    column_based=True
                )

                if len(profile_values[0]) == 0:
                    raise EmptyProfileWarning(f"Profile [{dtp.columnName}] has no data.")

                datetimes = [dt.strftime(dt_str_format) for dt in profile_values[0]]
                values = profile_values[1]

                return {
                    "name": dtp.columnName,
                    "x": datetimes,
                    "y": values,
                }
            except Exception as e:
                raise ProfileTraceLoadError(f"Failed to load postgres profile trace: {e}") from e
            
        
        # --- UNSUPPORTED TYPE ---
        logger.error(f"Unsupported datatableprofile configuration type: {dtp.configuration.type}")

        return {}

    @staticmethod
    def add_esdl_profile(es_id: str, profile_container_id: str, profile_class: ProfileClassEnum, profile_obj: dict) -> None:
        """Add a new profile to a given profile container in an ESDL."""
        pm = get_project_manager()

        profile_container = pm.get_by_id(es_id, profile_container_id)
        if not profile_container:
            raise ProfileContainerNotFoundError(f"Unable to attach profile to a given container (id={profile_container_id}) from ESDL (id={es_id}).")

        try:
            new_profile = Profiles.construct_esdl_profile_instance(es_id, profile_class, profile_obj)
            profile_container.eGet("profile").append(new_profile)
            pm.add_object_to_dict(es_id, new_profile)
        except Exception as e:
            raise ProfileCreateError(f"An error occurs while adding profile: {e}") from e

    @staticmethod
    def replace_esdl_profile(
        es_id: str,
        profile_container_id: str,
        existing_profile_id: str,
        profile_class: ProfileClassEnum,
        profile_obj: dict
    ) -> None:
        """Replace an existing profile in a given profile container with a new one."""
        pm = get_project_manager()

        existing_profile = pm.get_by_id(es_id, existing_profile_id)
        if not existing_profile:
            raise ProfileNotFoundError(f"Profile (id={existing_profile_id}) from ESDL (id={es_id}) not found.")

        profile_container = pm.get_by_id(es_id, profile_container_id)
        if not profile_container:
            raise ProfileContainerNotFoundError(
                f"Unable to replace profile in container (id={profile_container_id}) from ESDL (id={es_id})."
            )

        try:
            new_profile = Profiles.construct_esdl_profile_instance(es_id, profile_class, profile_obj)
            profiles = profile_container.eGet("profile")
            index = profiles.index(existing_profile)
            profiles[index] = new_profile
            pm.remove_object_from_dict(es_id, existing_profile)
            pm.add_object_to_dict(es_id, new_profile)
        except Exception as e:
            raise ProfileCreateError(f"An error occurred while replacing profile: {e}") from e

    @staticmethod
    def update_esdl_profile(es_id: str, profile_id: str, profile_class: ProfileClassEnum, updates: dict) -> None:
        """Update attributes of an existing profile in an ESDL."""
        pm = get_project_manager()

        profile = pm.get_by_id(es_id, profile_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile (id={profile_id}) from ESDL (id={es_id}) not found.")

        try:
            if isinstance(profile_class, str):
                profile_class = ProfileClassEnum(profile_class)

            if profile_class == ProfileClassEnum.SINGLEVALUE:
                if "name" in updates:
                    profile.name = updates["name"]
                if "value" in updates:
                    profile.value = float(updates["value"])
            else:
                if "multiplier" in updates:
                    profile.multiplier = float(updates["multiplier"])

            if "profileType" in updates:
                profile.profileType = esdl.ProfileTypeEnum.from_string(updates["profileType"])
            if "profileQuantityAndUnit" in updates:
                qau_obj = updates["profileQuantityAndUnit"]
                profile_qau = _convert_qau_obj_into_profile_qau(es_id, qau_obj)
                if profile_qau:
                    profile.profileQuantityAndUnit = profile_qau

        except Exception as e:
            raise ProfileUpdateError(f"An error occurs while updating profile (id={profile_id}): {e}") from e

    @staticmethod
    def serialize_esdl_profile(profile: esdl.DataTableProfile | esdl.InfluxDBProfile | esdl.TimeSeriesProfile | esdl.SingleValue) -> Dict[str, Any]:
        """
        An utiltiy function to convert an ESDL profile instance (DataTableProfile, InfluxDBProfile, TimeSeriesProfile, or SingleValue)
        into a dictionary structure suitable for API responses.

        :param profile: An ESDL profile instance.
        :return: A dict with structure as:
            {
                "profileClass": <string>,
                "profileObj": <serialized profile object>
            }
        """
        profile_class = type(profile).__name__

        if isinstance(profile, esdl.DataTableProfile):
            dtp = profile
        elif isinstance(profile, esdl.InfluxDBProfile):
            dtp = Profiles.influxdbprofile_to_datatableprofile(profile)
        elif isinstance(profile, esdl.TimeSeriesProfile):
            return {
                "profileClass": profile_class,
                "profileObj": Profiles.serialize_timeseriesprofile(profile) 
            }
        elif isinstance(profile, esdl.SingleValue):
            return {
                "profileClass": profile_class,
                "profileObj": Profiles.serialize_singlevalue(profile)
            }
        else:
            raise ProfileClassError(f"Unsupported profile class: {profile_class}")

        return {
            "profileClass": profile_class,
            "profileObj": Profiles.serialize_datatableprofile(dtp)
        }
    
    @staticmethod
    def serialize_datatableprofile(dtp: esdl.DataTableProfile) -> dict:
        """Return a dict representation of `DataTableProfile` for client consumption."""

        qau_dict = Profiles.serialize_qau(getattr(dtp, "profileQuantityAndUnit", None))

        dt_fmt = "%Y-%m-%dT%H:%M:%S%z"

        return {
            "id": dtp.id,
            "name": dtp.name,
            "schema": dtp.schema,
            "tableName": dtp.tableName,
            "columnName": dtp.columnName,
            "startDate": dtp.startDate.strftime(dt_fmt) if dtp.startDate else None,
            "endDate": dtp.endDate.strftime(dt_fmt) if dtp.endDate else None,
            "filter": dtp.filter,
            "multiplier": dtp.multiplier,
            "profileType": _get_enum_name(dtp.profileType),
            "profileQuantityAndUnit": qau_dict,
            "configuration": {
                "database": dtp.configuration.database,
                "type": _get_enum_name(dtp.configuration.type),
                "host": dtp.configuration.host,
                "port": dtp.configuration.port,
                "tls": dtp.configuration.tls
            }
        }

    @staticmethod
    def serialize_timeseriesprofile(tsp: esdl.TimeSeriesProfile) -> dict:
        """Return a dict representation of `TimeSeriesProfile` for client consumption."""

        qau_dict = Profiles.serialize_qau(getattr(tsp, "profileQuantityAndUnit", None))

        dt_fmt = "%Y-%m-%dT%H:%M:%S%z"

        return {
            "id": tsp.id,
            "name": tsp.name,
            "profileType": _get_enum_name(tsp.profileType),
            "startDateTime": tsp.startDateTime.strftime(dt_fmt) if tsp.startDateTime else None,
            "timestep": tsp.timestep,
            "profileQuantityAndUnit": qau_dict,
            "values": tsp.values
        }

    @staticmethod
    def serialize_singlevalue(sv: esdl.SingleValue) -> dict:
        """Return a dict representation of `SingleValue` for client consumption."""

        qau_dict = Profiles.serialize_qau(getattr(sv, "profileQuantityAndUnit", None))

        return {
            "id": sv.id,
            "name": sv.name,
            "profileType": _get_enum_name(sv.profileType),
            "profileQuantityAndUnit": qau_dict,
            "value": sv.value
        }

    @staticmethod
    def serialize_qau(qau: esdl.QuantityAndUnitType | esdl.QuantityAndUnitReference) -> dict | None:
        """
        Return a dict representation for QuantityAndUnit.
        """
        if not qau:
            return None

        if isinstance(qau, esdl.QuantityAndUnitReference):
            qau = qau.reference

        return {
            "id": qau.id,
            "description": qau.description if qau.description else qau_to_string(qau),
            "physicalQuantity": _get_enum_name(qau.physicalQuantity),
            "unit": _get_enum_name(qau.unit),
            "multiplier": _get_enum_name(qau.multiplier),
            "perUnit": _get_enum_name(qau.perUnit),
            "perMultiplier": _get_enum_name(qau.perMultiplier),
            "perTimeUnit": _get_enum_name(qau.perTimeUnit)
        }
    
    @staticmethod
    def construct_esdl_profile_instance(es_id: str,
                                        profile_class: ProfileClassEnum | str,
                                        profile_obj: dict
                                        ) -> esdl.SingleValue | esdl.DataTableProfile | esdl.InfluxDBProfile:
        """
        An utiltiy function which constructs an ESDL profile instance (SingleValue, DataTableProfile, or
        InfluxDBProfile) from a profile_obj dictionary. This method also parses and attaches
        the profile's QuantityAndUnit (QAU) if present.
        """
        if isinstance(profile_class, str):
            profile_class = ProfileClassEnum(profile_class)

        # Extract QAU if present
        profile_qau = None
        qau_obj = profile_obj.get("profileQuantityAndUnit")
        if qau_obj:
            profile_qau = _convert_qau_obj_into_profile_qau(es_id, qau_obj)
            profile_obj["profileQuantityAndUnit"] = None

        if profile_class == ProfileClassEnum.SINGLEVALUE:
            profile = esdl.SingleValue(
                name=profile_obj.get("name"),
                value=float(profile_obj.get("value")),
                profileType=esdl.ProfileTypeEnum.from_string(profile_obj.get("profileType"))
            )
        elif profile_class == ProfileClassEnum.DATATABLEPROFILE:
            db_config = _create_databaseconfiguration_from_config_obj(profile_obj.get("configuration"))
            dtp = _create_dtp_from_dtp_obj(profile_obj)
            dtp.configuration = _get_or_add_esi_databaseconfiguration(es_id, db_config)
            profile = dtp
        elif profile_class == ProfileClassEnum.INFLUXDBPROFILE:
            cfg = profile_obj.get("configuration")
            profile = esdl.InfluxDBProfile(
                host=cfg.get("host"),
                port=cfg.get("port"),
                database=cfg.get("database"),
                measurement=profile_obj.get("tableName"),
                field=profile_obj.get("columnName"),
                filters=profile_obj.get("filter"),
                multiplier=float(profile_obj.get("multiplier")),
                startDate=_dt_str_to_tz_aware_datetime(profile_obj.get("startDate")),
                endDate=_dt_str_to_tz_aware_datetime(profile_obj.get("endDate")),
                profileType=esdl.ProfileTypeEnum.from_string(profile_obj.get("profileType"))
            )
        else:
            raise ProfileClassError(f"Unsupported profile class: {profile_class}")

        if not profile:
            raise ProfileCreateError("An error occurred while creating an ESDL profile")
    
        profile.id = str(uuid4())

        if profile_qau:
            profile.profileQuantityAndUnit = profile_qau

        return profile


default_profile_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal profiles",
         "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value,
         "name": "Standard profiles", "readonly": True},
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

# ------------------------------------------------ #
# ---------------- Util functions ---------------- #
# ------------------------------------------------ #

def _clone_qau(qau):
    """A util function which returns a deep clone of qau."""
    if not qau:
        return None

    if isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    return qau.deepcopy()

def _get_enum_name(enum_obj):
    """A util function to get the ENUM name string."""
    enum_name = getattr(enum_obj, "name", None)
    if enum_name == "NONE" or enum_name == "None":
        return None
    return enum_name

def _test_influxdb_connection(settings: ConnectionSettings) -> bool:
    """Return True if the InfluxDB instance is reachable."""
    client = None
    try:
        client = InfluxDBClient(
            host=settings.host,
            port=settings.port,
            database=settings.database,
            username=settings.username,
            password=settings.password,
            ssl=settings.ssl,
            verify_ssl=settings.verify_ssl,
            retries=1,
            timeout=2,
        )
        # Simple connectivity test
        client.get_list_database()
        return True
    except (ConnectionError, TimeoutError) as e:
        raise InfluxDBConnectionError(f"Unable to reach InfluxDB database at {settings.host}:{settings.port}/{settings.database} - {e}")
    finally:
        if client:
            client.close()

def _test_postgresql_connection(settings: PostgreSQLConnectionSettings) -> bool:
    """Return True if the PostgreSQL instance is reachable."""
    try:
        conn = psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname=settings.database,
            user=settings.username,
            password=settings.password,
            connect_timeout=3
        )
        conn.close()
        return True
    except psycopg.OperationalError as e:
        raise PostgreSQLConnectionError(f"Unable to reach PostgreSQL database at {settings.host}:{settings.port}/{settings.database} - {e}")

def _create_dtp_from_dtp_obj(dtp_obj: dict) -> esdl.DataTableProfile:
    """
    Convert a frontend DataTableProfile-like object (dict) into an ESDL DataTableProfile.

    Parameters
    ----------
    dtp_obj : dict
        Dictionary containing DataTableProfile-like fields.
    """

    dtp = esdl.DataTableProfile(
        tableName=dtp_obj.get("tableName"),
        columnName=dtp_obj.get("columnName"),
        filter=dtp_obj.get("filter"),
        multiplier=float(dtp_obj.get("multiplier")),
        startDate=_dt_str_to_tz_aware_datetime(dtp_obj.get("startDate")),
        endDate=_dt_str_to_tz_aware_datetime(dtp_obj.get("endDate")),
        profileType=esdl.ProfileTypeEnum.from_string(dtp_obj.get("profileType"))
    )

    return dtp

def _create_databaseconfiguration_from_config_obj(config_obj: dict) -> esdl.DatabaseConfiguration:
    """
    Convert a frontend DatabaseConfiguration-like object (dict) into an ESDL DatabaseConfiguration.

    Parameters
    ----------
    config_obj : dict
        Dictionary containing DatabaseConfiguration-like fields.
    """

    db_config = esdl.DatabaseConfiguration(
        id=config_obj.get("id"),
        name=config_obj.get("name"),
        database=config_obj.get("database"),
        type=esdl.DatabaseTypeEnum.from_string(config_obj.get("type")),
        host=config_obj.get("host"),
        port=int(config_obj.get("port")),
        tls=bool(config_obj.get("tls")) if config_obj.get("tls") else None
    )

    return db_config

def _get_or_add_esi_databaseconfiguration(es_id: str, db_config: esdl.DatabaseConfiguration):
    """
    Return an existing DatabaseConfiguration from EnergySystemInformation if present.
    Otherwise, add the given DatabaseConfiguration (or reuse a duplicate) and return it.
    """
    pm = get_project_manager()

    if not db_config.id:
        db_config.id = str(uuid4())

    try:
        return pm.get_by_id(es_id, db_config.id)
    except KeyError:
        pass

    es: esdl.EnergySystem = pm.get_energy_system_by_id(es_id)
    if not es.energySystemInformation:
        esi: esdl.EnergySystemInformation = esdl.EnergySystemInformation(id=str(uuid4()))
        es.energySystemInformation = esi
        pm.add_object_to_dict(es_id, esi)
    if not es.energySystemInformation.dataconfigurations:
        dataconfigs = esdl.DataConfigurations(id=str(uuid4()))
        es.energySystemInformation.dataconfigurations = dataconfigs
        pm.add_object_to_dict(es_id, dataconfigs)

    configs = es.energySystemInformation.dataconfigurations.configurations
    duplicate = next(
        (
            cfg for cfg in configs
            if isinstance(cfg, esdl.DatabaseConfiguration)
            and cfg.database == db_config.database
            and cfg.type == db_config.type
            and cfg.host == db_config.host
            and cfg.port == db_config.port
        ),
        None
    )

    if duplicate:
        return duplicate

    configs.append(db_config)
    pm.add_object_to_dict(es_id, db_config)

    return db_config

def _convert_qau_obj_into_profile_qau(es_id: str, qau_obj: dict):
    """Convert a qau dict into an ESDL QuantityAndUnitReference."""
    pm = get_project_manager()

    predefined_qau_id = qau_obj.get("id")
    if predefined_qau_id:
        try:
            qau = pm.get_by_id(es_id, predefined_qau_id)
        except KeyError:
            qau = build_qau_from_dict(qau_obj)
    else:
        qau = build_qau_from_dict(qau_obj)

    if not qau.description:
        qau.description = qau_to_string(qau)

    applied_qau = None
    esi_qau_container = get_or_create_esi_qau(pm, es_id)
    for esi_qau in esi_qau_container.quantityAndUnit:
        if esi_qau.description == qau.description:
            applied_qau = esi_qau
            break

    if applied_qau is None:
        applied_qau = qau
        esi_qau_container.quantityAndUnit.append(applied_qau)
        pm.add_object_to_dict(es_id, applied_qau)

    return esdl.QuantityAndUnitReference(reference=applied_qau)

def _dt_str_to_tz_aware_datetime(dt_str: str, default_tz=datetime.timezone.utc) -> datetime.datetime:
    """
    Parse a datetime string using parse_date() utility,
    and ensure the result is timezone-aware by applying `default_tz`
    when no timezone is present.
    """
    dt = parse_date(dt_str)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)

    return dt

def _parse_profile_filter(filter: Optional[str], as_dict: bool = False) -> List[Dict[str, str]] | Dict[str, str]:
    """Parse profile filter string into a list of dicts or a dict."""
    if not filter:
        return {} if as_dict else []

    pattern = r'"?(\w+)"?\s*=\s*["\']([^"\']*)["\']'
    matches = re.findall(pattern, filter)

    if not matches:
        logger.error(f"Failed to parse filter string: {filter}")
        return {} if as_dict else []

    if as_dict:
        return {k: v for k, v in matches}

    return [{"tag": k, "value": v} for k, v in matches]

def _calculate_profile_groupby_interval(start: datetime.datetime, end: datetime.datetime, max_points: Optional[int]) -> Optional[int]:
    """A util function to determine profile downsampling groupby interval."""

    if not max_points:
        return None
    time_delta_sec = (end - start).total_seconds()
    # To round to common (readable) interval: 1s, 30s, 1m, 30m, 1h, 6h, 12h, 1d
    common_intervals = [1, 30, 60, 1800, 3600, 21600, 43200, 86400]
    interval_sec = math.ceil(time_delta_sec / max_points)
    return min(common_intervals, key=lambda x: abs(x - interval_sec))

class AssetNotFoundError(Exception):
    pass

class ProfileNotFoundError(Exception):
    pass

class ProfileClassError(Exception):
    pass

class InfluxDBConnectionError(Exception):
    pass

class ProfileTraceLoadError(Exception):
    pass

class ProfileCreateError(Exception):
    pass

class ProfileContainerNotFoundError(Exception):
    pass

class ProfileUpdateError(Exception):
    pass

class EmptyProfileWarning(Exception):
    pass

class PostgreSQLConnectionError(Exception):
    pass