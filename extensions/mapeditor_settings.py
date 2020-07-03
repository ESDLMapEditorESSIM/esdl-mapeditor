from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_session
from extensions.user_settings import UserSettings


MAPEDITOR_SYSTEM_CONFIG = "MAPEDITOR_SYSTEM_CONFIG"
MAPEDITOR_USER_CONFIG = "MAPEDITOR_USER_CONFIG"

DEFAULT_SYSTEM_SETTING = {
    'ui_settings': {
        'carrier_colors': []
    }
}

DEFAULT_USER_SETTING = {

}

class MapEditorSettings:
    def __init__(self, flask_app: Flask, socket: SocketIO, user_settings: UserSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings = user_settings

        self.register()

    def register(self):
        print("Registering MapEditor Settings extension")

        # Assumes the system setting is a list
        @self.socketio.on('mapeditor_system_settings_append_list', namespace='/esdl')
        def mapeditor_system_settings_append_list(info):
            print('mapeditor_system_settings_get:')
            print(info)
            setting_category = info['category']
            setting_name = info['name']
            setting_value = info['value']

            # TODO: figure out a way to replace settings
            sys_set = self.get_system_settings()
            cat = sys_set[setting_category]
            name_list = cat[setting_name]
            name_list.append(setting_value)
            self.set_system_settings(sys_set)
            print(sys_set)

        @self.socketio.on('mapeditor_system_settings_get', namespace='/esdl')
        def mapeditor_system_settings_get(info):
            print('mapeditor_system_settings_get:')
            print(info)
            setting_category = info['category']
            setting_name = info['name']

            sys_set = self.get_system_settings()
            cat = sys_set[setting_category]
            print(cat[setting_name])
            return cat[setting_name]

    def get_system_settings(self):
        if self.settings.has_system(MAPEDITOR_SYSTEM_CONFIG):
            return self.settings.get_system(MAPEDITOR_SYSTEM_CONFIG)
        else:
            mapeditor_settings = DEFAULT_SYSTEM_SETTING
            self.settings.set_system(MAPEDITOR_SYSTEM_CONFIG, mapeditor_settings)
            return mapeditor_settings

    def set_system_settings(self, settings):
        self.settings.set_system(MAPEDITOR_SYSTEM_CONFIG, settings)

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

    def get_user_settings(self, user):
        if self.settings.has_user(user, MAPEDITOR_USER_CONFIG):
            return self.settings.get_user(user, MAPEDITOR_USER_CONFIG)
        else:
            user_settings = DEFAULT_USER_SETTING
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings.set_user(user, MAPEDITOR_USER_CONFIG, settings)

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