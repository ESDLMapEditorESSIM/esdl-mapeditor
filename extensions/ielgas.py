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

from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, set_session
from extensions.settings_storage import SettingsStorage
from influxdb import InfluxDBClient
import src.settings as settings
import src.log as log

logger = log.get_logger(__name__)

IELGAS_SYSTEM_CONFIG = 'IELGAS_SYSTEM_CONFIG'
IELGAS_USER_CONFIG = 'IELGAS_USER_CONFIG'

IELGAS_DEFAULT_SYSTEM_CONFIG = {
    'database_host': settings.ielgas_config["host"],
    'database_port': 8086,
    'database_name': 'i-elgas'
}

IELAG_DEFAULT_USER_CONFIG = {
    'measurements': ['electricity_network', 'methane_network', 'hydrogen_network'],
    'simulationRun': 'start_test_run'
}

FIELD_NAME = 'allocationEnergy'
CAPABILITY_FILTER = 'Transport'


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    logger.warn(message)
    emit('alert', message, namespace='/esdl')


# ---------------------------------------------------------------------------------------------------------------------
#  IELGAS
# ---------------------------------------------------------------------------------------------------------------------
class IELGAS:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.plugin_settings = self.get_settings()
        self.database_client = None
        self.register()

    def get_settings(self):
        if self.settings_storage.has_system(IELGAS_SYSTEM_CONFIG):
            return self.settings_storage.get_system(IELGAS_SYSTEM_CONFIG)
        else:
            ielgas_plugin_settings = IELGAS_DEFAULT_SYSTEM_CONFIG
            self.settings_storage.set_system(IELGAS_SYSTEM_CONFIG, ielgas_plugin_settings)
            return ielgas_plugin_settings

    def register(self):
        logger.info('Registering IELGAS extension')

        # @self.socketio.on('initialize_ielgas_extension', namespace='/esdl')
        # def initialize_ielgas_extension():
        #     user = get_session('user-email')
        #     user_settings = self.get_user_settings(user)
        #     set_session('ielgas_settings', user_settings)
        #
        # @self.socketio.on('get_ielgas_settings', namespace='/esdl')
        # def get_ielgas_settings():
        #     user = get_session('user-email')
        #     user_settings = self.get_user_settings(user)
        #     return user_settings
        #
        # @self.socketio.on('set_ielgas_setting', namespace='/esdl')
        # def get_ielgas_settings(setting):
        #     user = get_session('user-email')
        #     self.set_user_setting(user, setting['name'], setting['value'])

        @self.socketio.on('ielgas_monitor_asset', namespace='/esdl')
        def ielgas_monitor_asset(info):
            asset_id = info['id']
            ielgas_monitor_ids = get_session('ielgas_monitor_ids')
            if asset_id in ielgas_monitor_ids:
                ielgas_monitor_ids.remove(asset_id)
            else:
                ielgas_monitor_ids.append(asset_id)
            set_session('ielgas_monitor_ids', ielgas_monitor_ids)

        @self.socketio.on('request_ielgas_ldc', namespace='/esdl')
        def request_ielgas_ldc(info):
            asset_id = info['id']
            # set_session('ielgas_monitor_id', asset_id)
            active_es_id = get_session('active_es_id')
            esh = get_handler()
            asset = esh.get_by_id(active_es_id, asset_id)
            asset_name = asset.name
            power = None
            if hasattr(asset, 'power'):
                power = asset.power
            elif hasattr(asset, 'capacity'):
                power = asset.capacity
            power_pos = None
            power_neg = None

            self.database_client = InfluxDBClient(host=self.plugin_settings['database_host'],
                                                      port=self.plugin_settings['database_port'],
                                                      database=self.plugin_settings['database_name'])

            user = get_session('user-email')
            user_config = self.get_user_settings(user)

            results = dict()
            measurements = user_config['measurements']
            for m in measurements:
                try:
                    query = 'SELECT "'+FIELD_NAME+'" FROM "' + m + '" WHERE assetId=\'' + asset_id + '\''
                    logger.debug(query)
                    res = self.database_client.query(query)
                    if res:
                        results = res
                        break
                except Exception as e:
                    logger.error('error with query: ', str(e))

            first_key = list(results.keys())[0]
            series = results[first_key]

            ldc_series = []
            for item in series:
                ldc_series.append(item['allocationEnergy'])
            ldc_series.sort(reverse=True)

            ldc_series_decimate = []
            for idx, item in enumerate(ldc_series):
                if idx % 40 == 0:
                    ldc_series_decimate.append(item * 1e6)
                    if item > 0:
                        power_pos = power
                    if item < 0:
                        power_neg = -power

            emit('ldc-data', {'asset_name': asset_name, 'ldc_series': ldc_series_decimate, 'power_pos': power_pos,
                              'power_neg': power_neg})

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, IELGAS_USER_CONFIG):
            return self.settings_storage.get_user(user, IELGAS_USER_CONFIG)
        else:
            user_settings = IELAG_DEFAULT_USER_CONFIG
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, IELGAS_USER_CONFIG, settings)

    def get_user_setting(self, user, name):
        user_settings = self.get_user_settings(user)
        if name in user_settings:
            return user_settings[name]
        else:
            return None

    def set_user_setting(self, user, name, value):
        user_settings = self.get_user_settings(user)
        user_settings[name] = value
        self.set_user_settings(user, user_settings)
