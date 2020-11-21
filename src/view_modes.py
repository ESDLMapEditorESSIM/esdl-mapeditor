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

from extensions.session_manager import get_session, set_session
from extensions.settings_storage import SettingsStorage
from esdl import esdl
from copy import deepcopy
import src.log as log

logger = log.get_logger(__name__)

view_modes_config = {
    "standard": {
        "Basic": {
            "EnergyAsset": [
                "name",
                "state",
            ],
            "Consumer": [
                "power"
            ],
            "Producer": [
                "power",
                "prodType"
            ],
            "Storage": [
                "capacity"
            ],
            "Transport": [
                "capacity"
            ],
            "Conversion": [
                "power",
                "efficiency"
            ],
            "HeatPump": [
                "COP"
            ]
        },
        "Aggregation": {
            "EnergyAsset": [
                "aggregated",
                "aggregationCount",
            ],
        }
    },
    "ESSIM": {
        "Basic": {
            "EnergyAsset": [
                "name",
                "state",
            ]
        },
        "ESSIM": {
            "Producer": [
                "power"
            ],
            "Conversion": [
                "efficiency",
                "power"
            ],
            "HeatPump": [
                "COP"
            ]
        },
    },
    "CHESS": {
        "Basic": {

        },
    }
}

VIEW_MODES_USER_CONFIG = "VIEW_MODES_USER_CONFIG"
view_modes = None

class ViewModes:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        global view_modes
        if view_modes:
            logger.error("ERROR: Only one ViewModes object can be instantiated")
        else:
            view_modes = self

    @staticmethod
    def get_instance():
        global view_modes
        return view_modes

    def register(self):
        logger.info("Registering ViewModes")

        @self.socketio.on('view_modes_initialize', namespace='/esdl')
        def view_modes_initialize():
            user = get_session('user-email')
            settings = self.get_user_settings(user)
            set_session('mapeditor_view_mode', settings['mode'])
            logger.debug('User has MapEditor view mode: {}'.format(settings['mode']))

        @self.socketio.on('view_modes_set_mode', namespace='/esdl')
        def view_modes_set_mode(mode):
            pass

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, VIEW_MODES_USER_CONFIG):
            return self.settings_storage.get_user(user, VIEW_MODES_USER_CONFIG)
        else:
            user_settings = {
                'mode': 'standard'
            }
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, VIEW_MODES_USER_CONFIG, settings)

    def categorize_object_attributes(self, object, attributes):
        attr_dict = {attr['name']: attr for attr in attributes}
        view_mode = get_session('mapeditor_view_mode')

        this_view_mode_config = view_modes_config[view_mode]

        categorized_attributes_list = dict()
        for key in this_view_mode_config:
            categorized_attributes_list[key] = list()

            for objtype in this_view_mode_config[key]:
                if isinstance(object, esdl.getEClassifier(objtype)):
                    for attr in this_view_mode_config[key][objtype]:
                        attr_info = deepcopy(attr_dict[attr])
                        del attr_dict[attr]
                        categorized_attributes_list[key].append(attr_info)

        categorized_attributes_list['Advanced'] = list()
        for attr in attr_dict:
            attr_info = deepcopy(attr_dict[attr])
            categorized_attributes_list['Advanced'].append(attr_info)

        return categorized_attributes_list


