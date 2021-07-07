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

import src.log as log
from src.view_modes import ViewModes
from esdl.processing.ESDLAsset import get_asset_capability_type
from extensions.session_manager import get_session
from extensions.settings_storage import SettingsStorage
from flask import Flask
from flask_socketio import SocketIO, emit

logger = log.get_logger(__name__)
asset_draw_toolbar = None

ASSET_DRAW_TOOLBAR_CONFIG = "ASSET_DRAW_TOOLBAR_CONFIG"
STANDARD_ASSETS = "STANDARD_ASSETS"
EDR_ASSETS = "EDR_ASSETS"


class AssetDrawToolbar:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.view_modes = ViewModes.get_instance()

        self.register()

        global asset_draw_toolbar
        if asset_draw_toolbar:
            logger.error("ERROR: Only one AssetDrawToolbar object can be instantiated")
        else:
            asset_draw_toolbar = self

    def register(self):
        logger.info('Registering AssetDrawToolbar extension')

        @self.socketio.on('load_asset_draw_toolbar_edr_assets', namespace='/esdl')
        def load_asset_draw_toolbar_edr_assets():
            return self.load_asset_draw_toolbar_edr_assets()

        @self.socketio.on('save_asset_draw_toolbar_edr_assets', namespace='/esdl')
        def save_asset_draw_toolbar_edr_assets(edr_asset_list):
            self.save_asset_draw_toolbar_edr_assets(edr_asset_list)
            emit('edr_assets_on_toolbar', self.add_capability_info(edr_asset_list))

        @self.socketio.on('load_asset_draw_toolbar_standard_assets_info', namespace='/esdl')
        def load_asset_draw_toolbar_standard_assets_info():
            return self.load_asset_draw_toolbar_standard_assets_info()

        @self.socketio.on('save_asset_draw_toolbar_standard_assets', namespace='/esdl')
        def save_asset_draw_toolbar_standard_assets(standard_asset_list):
            self.save_asset_draw_toolbar_standard_assets(standard_asset_list)
            view_mode_info = self.view_modes.view_modes_get_mode_info()
            emit('standard_assets_on_toolbar', standard_asset_list[view_mode_info['current_mode']])

    @staticmethod
    def get_instance():
        global asset_draw_toolbar
        return asset_draw_toolbar

    def load_asset_draw_toolbar_standard_assets_info(self):
        user = get_session('user-email')
        adt_settings = self.get_user_settings(user)
        view_mode_info = self.view_modes.view_modes_get_mode_info()

        standard_assets_info = {
            'standard_assets': adt_settings[STANDARD_ASSETS],
            'current_mode': view_mode_info['current_mode'],
            'possible_modes': view_mode_info['possible_modes']
        }

        return standard_assets_info

    def save_asset_draw_toolbar_standard_assets(self, standard_asset_list):
        user = get_session('user-email')
        adt_settings = self.get_user_settings(user)
        adt_settings[STANDARD_ASSETS] = standard_asset_list
        self.set_user_settings(user, adt_settings)

    def add_capability_info(self, edr_asset_list):
        module = importlib.import_module('esdl.esdl')
        for asset_info in edr_asset_list:
            class_ = getattr(module, asset_info['edr_asset_type'])
            asset = class_()
            asset_info['edr_asset_cap'] = get_asset_capability_type(asset)
        return edr_asset_list

    def load_asset_draw_toolbar_edr_assets(self):
        user = get_session('user-email')
        adt_settings = self.get_user_settings(user)
        return self.add_capability_info(adt_settings[EDR_ASSETS])

    def save_asset_draw_toolbar_edr_assets(self, edr_asset_list):
        user = get_session('user-email')
        adt_settings = self.get_user_settings(user)
        adt_settings[EDR_ASSETS] = edr_asset_list
        self.set_user_settings(user, adt_settings)

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, ASSET_DRAW_TOOLBAR_CONFIG):
            asset_draw_toolbar_settings = self.settings_storage.get_user(user, ASSET_DRAW_TOOLBAR_CONFIG)
        else:
            asset_draw_toolbar_settings = self.create_default_settings()
            self.settings_storage.set_user(user, ASSET_DRAW_TOOLBAR_CONFIG, asset_draw_toolbar_settings)
        return asset_draw_toolbar_settings

    def restore_settings(self, user):
        asset_draw_toolbar_settings = self.create_default_settings()
        self.settings_storage.set_user(user, ASSET_DRAW_TOOLBAR_CONFIG, asset_draw_toolbar_settings)
        return asset_draw_toolbar_settings

    def create_default_settings(self):
        asset_draw_toolbar_settings = {
            STANDARD_ASSETS: {},
            EDR_ASSETS: [],
        }

        view_mode_info = self.view_modes.view_modes_get_mode_info()
        for view_mode in view_mode_info['possible_modes']:
            asset_draw_toolbar_settings[STANDARD_ASSETS][view_mode] = self.get_view_mode_asset_list(view_mode)

        return asset_draw_toolbar_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, ASSET_DRAW_TOOLBAR_CONFIG, settings)

    def get_view_mode_asset_list(self, view_mode):
        return self.view_modes.get_asset_list_for_view_mode(view_mode)

