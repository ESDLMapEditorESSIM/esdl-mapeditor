from flask import Flask
from flask_socketio import SocketIO, emit
from flask_executor import Executor
from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
from influxdb import InfluxDBClient
import copy
import logging
import csv
import locale
from io import StringIO
from uuid import uuid4
import settings

logger = logging.getLogger(__name__)


PROFILES_SETTING = 'PROFILES'
profiles = None


class Profiles:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.csv_files = dict()
        self.register()

        # add initial profiles when not in the system settings
        if not self.settings_storage.has_system(PROFILES_SETTING):
            self.settings_storage.set_system(PROFILES_SETTING, default_profiles)
            print('Updated default profile list in settings storage')

        global profiles
        if profiles:
            print("ERROR: Only one Profiles object can be instantiated")
        else:
            profiles = self

    @staticmethod
    def get_instance():
        global profiles
        return profiles

    def register(self):
        print('Registering Profiles extension')

        @self.socketio.on('get_profiles_list', namespace='/esdl')
        def get_profiles_list():
            with self.flask_app.app_context():
                print("getting profiles list")
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
                print(profile_info)
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
                print(profile_info)
                self.add_profile(id, profile_info)

        @self.socketio.on('test_profile', namespace='/esdl')
        def click_test_profile(profile_info):
            print(profile_info)

        @self.socketio.on('profile_csv_upload', namespace='/esdl')
        def profile_csv_upload(message):
            with self.flask_app.app_context():
                message_type = message['message_type'] # start, next_chunk, done
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

    def format_datetime(self, dt):
        date, time = dt.split(" ")
        day, month, year = date.split("-")
        ndate = year + "-" + month + "-" + day
        ntime = time + ":00+0000"
        return ndate + "T" + ntime

    def process_csv_file(self, name, uuid, content):
        logger.debug("Processing csv file(s) (threaded): ".format(name))
        try:
            logger.info("process CSV")
            measurement = name.split('.')[0]

            csv_file = StringIO(content)
            reader = csv.reader(csv_file, delimiter=';')

            column_names = next(reader)
            num_fields = len(column_names)
            json_body = []

            locale.setlocale(locale.LC_ALL, '')
            start_datetime = None
            end_datetime = ""

            for row in reader:
                fields = {}
                for i in range(1, num_fields):
                    if row[i]:
                        fields[column_names[i]] = locale.atof(row[i])

                dt = self.format_datetime(row[0])
                if not start_datetime:
                    start_datetime = dt
                else:
                    end_datetime = dt

                json_body.append({
                    "measurement": measurement,
                    "time": dt,
                    "fields": fields
                })

            database = settings.profile_database_config['database']
            client = InfluxDBClient(
                host=settings.profile_database_config['host'],
                port=settings.profile_database_config['port'],
                username=settings.profile_database_config['upload_user'],
                password=settings.profile_database_config['upload_password'],
                database=database
            )
            if database not in client.get_list_database():
                client.create_database(database)

            client.write_points(points=json_body, database=database, batch_size=100)

            group = self.csv_files[uuid]['group']
            for i in range(1, num_fields):
                field = column_names[i]
                profile = self.create_new_profile(group, measurement+'_'+field, 1, database, measurement,
                                               field, "", start_datetime, end_datetime)
                self.add_profile(str(uuid4()), profile)

            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                     'success': True})
        except Exception as e:
            emit('csv_processing_done', {'name': name, 'uuid': uuid, 'pos': self.csv_files[uuid]['pos'],
                                     'success': False, 'error': str(e)})

        # clean up
        del (self.csv_files[uuid])

    def add_profile(self, profile_id, profile):
        setting_type = SettingType(profile['setting_type'])
        project_name = profile['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, PROFILES_SETTING):
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_SETTING)
        else:
            profiles = dict()
        profiles[profile_id] = profile
        self.settings_storage.set(setting_type, identifier, PROFILES_SETTING, profiles)

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
        if self.settings_storage.has(setting_type, identifier, PROFILES_SETTING):
            # update profile dict
            profiles = self.settings_storage.get(setting_type, identifier, PROFILES_SETTING)
            print('Deleting profile {}'.format(profiles[profile_id]))
            del(profiles[profile_id])
            self.settings_storage.set(setting_type, identifier, PROFILES_SETTING, profiles)

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
        if self.settings_storage.has_system(PROFILES_SETTING):
            all_profiles.update(self.settings_storage.get_system(PROFILES_SETTING))

        user = get_session('user-email')
        user_group = get_session('user-group')
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')
        # print('User: ', user)
        # print('Groups: ', user_group)
        # print('Roles: ', role)
        # print('Mapeditor roles: ', mapeditor_role)
        if user is not None and self.settings_storage.has_user(user, PROFILES_SETTING):
            # add user profiles if available
            all_profiles.update(self.settings_storage.get_user(user, PROFILES_SETTING))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, PROFILES_SETTING):
                    # add project profiles if available
                    all_profiles.update(self.settings_storage.get_project(identifier, PROFILES_SETTING))

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
        else:
            identifier = self._get_identifier(SettingType.USER)
            return SettingType.USER.value, identifier

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


default_profile_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal profiles", "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value, "name": "Standard profiles", "readonly": True}
    ]
}

#{"id": SettingType.PROJECT.value, "name": "Project Layers"},

default_profiles = {
    "Solar": {
        "setting_type": SettingType.SYSTEM.value,
        "profile_uiname": "Solar",
        "multiplier": 1,
        "database": "energy_profiles",
        "measurement": "solar_relative_2011-2016",
        "field": "value",
        "profileType": "ENERGY_IN_TJ",
        "start_datetime": "2015-01-01T00:00:00.000000+0100",
        "end_datetime": "2016-01-01T00:00:00.000000+0100",
        "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/u4uAX3PZk/solar?panelId=1&from=1420066800000&to=1451606400000&theme=light"
    },
    "NEDU_2015_E1A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity households (E1A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E1A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/INOZu3PWz/elektriciteit-huishoudens-2015-nedu-e1a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E1B": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity NEDU (E1B)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E1B",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/yCTWWalZz/nedu-electricity-e1b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E1C": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity NEDU (E1C)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E1C",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/lsiMW-_Zz/nedu-electricity-e1c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E2A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity NEDU (E2A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E2A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/quVnZa_Zk/nedu-electricity-e2a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E2B": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity NEDU (E2B)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E2B",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/BkC7Z-_Wz/nedu-electricity-e2b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E3A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity shops, office, education (E3A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E3A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/wEXMX3EWk/electricity-shops-office-education-e3a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E3B": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity prison (E3B)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E3B",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/44-vX3EZk/electricity-prison-e3b?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E3C": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity hotel, hospital (E3C)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E3C",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/iRXduqEZz/electricity-hotel-hospital-e3c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E3D": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity greenhouses (E3D)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E3D",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/G4HpXqEWz/electricity-greenhouses-e3d?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_E4A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Electricity NEDU (E4A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_elektriciteit_2015-2018",
       "field": "E4A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/EU5iZ-lWk/nedu-electricity-e4a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_G1A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Heating households (G1A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_aardgas_2015-2018",
       "field": "G1A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/Dw5-u3EWz/heating-households-g1a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_G2A": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Heating ... (G2A)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_aardgas_2015-2018",
       "field": "G2A",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/6IQBuqPWz/heating-g2a?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "NEDU_2015_G2C": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Heating ... (G2C)",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "nedu_aardgas_2015-2018",
       "field": "G2C",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/GI_Yu3PZz/heating-g2c?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "Constant": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Constant",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "constant",
       "field": "value",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/ZJn5rqPWk/constant?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "WoL": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Wind op land",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "wind-2015",
       "field": "Wind-op-land",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/eeD2r3PWk/wind-op-land?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "WoZ": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Wind op zee",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "wind-2015",
       "field": "Wind-op-zee",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/2C-A93EWk/wind-op-zee?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "Biomassa": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Biomassa",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "biomassa-2015",
       "field": "value",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/dyab9qPWz/biomassa?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "ECur": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Elektriciteit Curacao",
       "required_role": "curacao",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "elektr-curacao-2015",
       "field": "elektr",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/r8oLrqPWz/elektriciteit-curacao?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "WCur": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Wind Curacao",
       "required_role": "curacao",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "wind-curacao-2015",
       "field": "value",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/grafana/d-solo/KM5U93EZz/wind-curacao?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "nzkg-ind-cont": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "NZKG - Industrie (cont)",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "nzkg_profiles",
       "measurement": "tno_industrie_2015",
       "field": "INDUSTRY_CONT",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/VYfbZ-_Wk/nzkg-industrie-cont?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "nzkg-ind-day": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "NZKG - Industrie (day)",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "nzkg_profiles",
       "measurement": "tno_industrie_2015",
       "field": "INDUSTRY_DAY",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/AbIaW-_Zk/nzkg-industrie-day?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "nzkg-ind-dc": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "NZKG - Industrie (datacenter)",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "nzkg_profiles",
       "measurement": "tno_industrie_2015",
       "field": "INDUSTRY_DATACENTER",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/u4q-Z-lWk/nzkg-industrie-datacenter?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "nzkg-ind-tot": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "NZKG - Industrie (total)",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "nzkg_profiles",
       "measurement": "tno_industrie_2015",
       "field": "INDUSTRY_TOTAL",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/DiAfZalWz/nzkg-industrie-total?panelId=1&from=1420066800000&to=1451606400000&theme=light"
   },
   "GMw19": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "GM - Wind 2019",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "windspeed_genemuiden_100mtr",
       "field": "windspeed",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2019-01-01T00:00:00.000000+0100",
       "end_datetime": "2020-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/v4SBvsMMk/genemuiden-wind-2019?panelId=1&from=1546297200000&to=1577836800000&theme=light"
   },
   "ZonBilt19": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Zon - de Bilt 2019",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "zon-wind-debilt-2019",
       "field": "zonprofiel_procenten",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2019-01-01T00:00:00.000000+0100",
       "end_datetime": "2020-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/BZJwZX_Zz/zon-de-bilt-2019?panelId=1&from=1546297200000&to=1577836800000&theme=light"
   },
   "WindBilt19": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "Wind - de Bilt 2019",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "zon-wind-debilt-2019",
       "field": "windprofiel_procenten",
       "profileType": "ENERGY_IN_TJ",
       "start_datetime": "2019-01-01T00:00:00.000000+0100",
       "end_datetime": "2020-01-01T00:00:00.000000+0100",
       "embedUrl": "https://panel-service.hesi.energy/grafana/d-solo/-DS_WX_Zk/wind-de-bilt-2019?panelId=1&from=1546297200000&to=1577836800000&theme=light"
   },
   "Diemen-34-2020": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Diemen-34-2020",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Diemen-34-2020-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Hemweg-9-2020": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Hemweg-9-2020",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Hemweg-9-2020-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Velsen-24-2020": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Velsen-24-2020",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Velsen-24-2020-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Velsen-25-2020": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Velsen-25-2020",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Velsen-25-2020-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Diemen-34-2030": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Diemen-34-2030",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Diemen-34-2030-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Hemweg-9-2030": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Hemweg-9-2030",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Hemweg-9-2030-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Velsen-24-2030": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Velsen-24-2030",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Velsen-24-2030-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   },
   "Velsen-25-2030": {
       "setting_type": SettingType.SYSTEM.value,
       "profile_uiname": "EYE - NH - Velsen-25-2030",
       "required_role": "nzkg",
       "multiplier": 1,
       "database": "energy_profiles",
       "measurement": "eye_nh",
       "field": "Velsen-25-2030-MW",
       "profileType": "POWER_IN_MW",
       "start_datetime": "2015-01-01T00:00:00.000000+0100",
       "end_datetime": "2016-01-01T00:00:00.000000+0100",
       "embedUrl": ""
   }
}
