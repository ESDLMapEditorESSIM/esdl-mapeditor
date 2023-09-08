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

from flask import Flask, request
from flask_socketio import SocketIO

from extensions.mapeditor_settings import MapEditorSettings
from extensions.session_manager import get_session, set_session
from extensions.settings_storage import SettingsStorage
import src.log as log

logger = log.get_logger(__name__)

CUSTOM_ICONS_SETTINGS = "CUSTOM_ICONS"


class CustomIcons:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        self.mapeditor_settings = MapEditorSettings.get_instance()

    def register(self):
        logger.info("Registering CustomIcons")

        @self.flask_app.route('/custom_icons')
        def get_custom_icon_info():
            user = get_session('user-email')
            settings = self.get_user_settings(user)
            icons_list = list()

            for k,v in settings['custom_icons'].items():
                icons_list.append({
                    'key': v['id'],
                    'selector': k,
                    'icon': {
                        'content_type': v['content_type'],
                        'data': v['data']
                    }
                })

            return {'icons_list': icons_list}

        @self.flask_app.route('/custom_icon', methods=['POST'])
        def add_custom_icon():
            custom_icon_info = request.get_json(silent=True)

            user = get_session('user-email')
            self.set_custom_icon(
                user,
                custom_icon_info['id'],
                custom_icon_info['asset_selector'],
                custom_icon_info['image_content_type'],
                custom_icon_info['image_data']
            )

            return 'OK', 200

        @self.flask_app.route('/custom_icon', methods=['DELETE'])
        def delete_custom_icon():
            custom_icon_info = request.get_json(silent=True)

            user = get_session('user-email')
            self.delete_custom_icon(user, custom_icon_info['asset_selector'])

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, CUSTOM_ICONS_SETTINGS):
            return self.settings_storage.get_user(user, CUSTOM_ICONS_SETTINGS)
        else:
            user_settings = {
                'custom_icons': {}
            }
            self.set_user_settings(user, user_settings)
            return user_settings

    def user_has_custom_icons(self):
        user = get_session('user-email')
        user_settings = self.get_user_settings(user)
        has_custom_icons = len(user_settings['custom_icons']) > 0
        return has_custom_icons

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, CUSTOM_ICONS_SETTINGS, settings)

    def set_custom_icon(self, user, id: str, asset_selector: str, image_content_type: str, image_data: str):
        settings = self.get_user_settings(user)
        settings['custom_icons'][asset_selector] = {
            'id': id,
            'content_type': image_content_type,
            'data': image_data
        }
        self.set_user_settings(user, settings)

    def delete_custom_icon(self, user, asset_selector: str):
        settings = self.get_user_settings(user)
        if asset_selector in settings:
            del settings[asset_selector]
            self.set_user_settings(user, settings)
        else:
            logger.error(f"{asset_selector} was not found in the custom icons dictionary")