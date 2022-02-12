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
from flask_socketio import SocketIO
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_session
import src.log as log

logger = log.get_logger(__name__)


MAPEDITOR_SYSTEM_CONFIG = "MAPEDITOR_SYSTEM_CONFIG"
MAPEDITOR_USER_CONFIG = "MAPEDITOR_USER_CONFIG"
MAPEDITOR_UI_SETTINGS = 'ui_settings'

DEFAULT_SYSTEM_SETTING = {
    MAPEDITOR_UI_SETTINGS: {
        'carrier_colors': {}
    }
}

DEFAULT_USER_SETTING = {
    MAPEDITOR_UI_SETTINGS: {
        'tooltips': {
            'marker_tooltip_format': "({name})(<br>{power}W)(<br>COP: {COP})(<br>Eff: {efficiency})",
            'line_tooltip_format': "({name})( - {diameter})( - {power}W)( - {capacity})",
            'show_asset_information_on_map': False
        },
        'asset_bar': {
            'visible_on_startup': True
        },
        'services_toolbar': {
            'visible_on_startup': False
        },
        'spatial_buffers': {
            'visible_on_startup': True,
            'colors': {
                'RISK': '#ff0000',                  # red
                'ENVIRONMENT': '#00ff00',           # green
                'NOISE': '#0000ff',                 # blue
                'PARTICULATE_MATTER': '#000000',    # black
                'NOX_EMISSIONS': '#ffff00',         # yellow
            }
        },
    },
}

me_settings = None


class MapEditorSettings:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

        global me_settings
        if me_settings:
            logger.error("ERROR: Only one MapEditorSettings object can be instantiated")
        else:
            me_settings = self

    @staticmethod
    def get_instance():
        global me_settings
        return me_settings

    def register(self):
        logger.info("Registering MapEditor Settings extension")

        # Assumes the system setting is a list
        @self.socketio.on('mapeditor_system_settings_append_list', namespace='/esdl')
        def mapeditor_system_settings_append_list(info):
            setting_category = info['category']
            setting_name = info['name']
            setting_value = info['value']

            # TODO: figure out a way to replace settings
            sys_set = self.get_system_settings()
            cat = sys_set[setting_category]
            name_list = cat[setting_name]
            name_list.append(setting_value)
            self.set_system_settings(sys_set)

        @self.socketio.on('mapeditor_system_settings_set_dict_value', namespace='/esdl')
        def mapeditor_system_settings_set_dict_value(info):
            setting_category = info['category']
            setting_name = info['name']
            setting_key = info['key']
            setting_value = info['value']

            sys_set = self.get_system_settings()
            cat = sys_set[setting_category]
            name_dict = cat[setting_name]
            name_dict[setting_key] = setting_value
            self.set_system_settings(sys_set)

        @self.socketio.on('mapeditor_system_settings_get', namespace='/esdl')
        def mapeditor_system_settings_get(info):
            setting_category = info['category']
            setting_name = info['name']

            sys_set = self.get_system_settings()
            cat = sys_set[setting_category]
            return cat[setting_name]

        @self.socketio.on('mapeditor_user_ui_setting_get', namespace='/esdl')
        def mapeditor_user_ui_setting_get(info):
            category = info['category']
            name = info['name']

            user_email = get_session('user-email')
            res = self.get_user_ui_setting(user_email, category, name)
            return res

        @self.socketio.on('mapeditor_user_ui_setting_set', namespace='/esdl')
        def mapeditor_user_ui_setting_set(info):
            category = info['category']
            name = info['name']
            value = info['value']

            user_email = get_session('user-email')
            return self.set_user_ui_setting(user_email, category, name, value)

    def get_system_settings(self):
        if self.settings_storage.has_system(MAPEDITOR_SYSTEM_CONFIG):
            return self.settings_storage.get_system(MAPEDITOR_SYSTEM_CONFIG)
        else:
            mapeditor_settings = DEFAULT_SYSTEM_SETTING
            self.settings_storage.set_system(MAPEDITOR_SYSTEM_CONFIG, mapeditor_settings)
            return mapeditor_settings

    def set_system_settings(self, settings):
        self.settings_storage.set_system(MAPEDITOR_SYSTEM_CONFIG, settings)

    def get_system_setting(self, name):
        system_settings = self.get_system_settings()
        if name in system_settings:
            return system_settings[name]
        else:
            return None

    def set_system_setting(self, name, value):
        system_settings = self.get_system_settings()
        system_settings[name] = value
        self.set_system_settings(system_settings)

    def add_missing_settings(self, settings, def_settings):
        if isinstance(def_settings, dict):
            for k in def_settings:
                if k in settings:
                    if isinstance(settings[k], dict):
                        self.add_missing_settings(settings[k], def_settings[k])
                else:
                    settings[k] = def_settings[k]

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, MAPEDITOR_USER_CONFIG):
            settings = self.settings_storage.get_user(user, MAPEDITOR_USER_CONFIG)
            # Add missing settings that have been added to defaults since last deployment/login
            self.add_missing_settings(settings, DEFAULT_USER_SETTING)
            return settings
        else:
            user_settings = DEFAULT_USER_SETTING
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, MAPEDITOR_USER_CONFIG, settings)

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

    def get_user_ui_setting(self, user, category, name):
        user_ui_setting = self.get_user_setting(user, MAPEDITOR_UI_SETTINGS)

        result = False
        if category in user_ui_setting:
            if name in user_ui_setting[category]:
                result = user_ui_setting[category][name]
        return result

    def set_user_ui_setting(self, user, category, name, value):
        user_ui_setting = self.get_user_setting(user, MAPEDITOR_UI_SETTINGS)
        if category not in user_ui_setting:
            user_ui_setting[category] = dict()

        user_ui_setting[category][name] = value
        self.set_user_setting(user, MAPEDITOR_UI_SETTINGS, user_ui_setting)
