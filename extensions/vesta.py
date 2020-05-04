from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from extensions.user_settings import SettingType, UserSettings
from extensions.session_manager import get_handler, get_session, set_session, del_session
# import requests


class Vesta:
    def __init__(self, flask_app: Flask, socket: SocketIO, user_settings: UserSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings = user_settings

        self.register()

    def register(self):
        print("Registering VESTA extension")

        @self.socketio.on('vesta_area_restrictions', namespace='/esdl')
        def set_area_restrictions(area_id):
            with self.flask_app.app_context():
                esh = get_handler()
                print(area_id)

                # TODO: get restrictions

                emit('vesta_restrictions_data', {"area_id": area_id})

        @self.flask_app.route('/vesta')
        def get_vesta():
            return "ok", 200