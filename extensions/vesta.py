from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from extensions.user_settings import SettingType, UserSettings
from extensions.session_manager import get_handler, get_session, set_session, del_session
from esdl.processing import ESDLAsset
import requests
import json


VESTA_SYSTEM_CONFIG = 'VESTA_CONFIG'


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class Vesta:
    def __init__(self, flask_app: Flask, socket: SocketIO, user_settings: UserSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.user_settings = user_settings
        self.vesta_plugin_settings = self.get_config()

        self.register()

    def get_config(self):
        if self.user_settings.has_system(VESTA_SYSTEM_CONFIG):
            vesta_plugin_settings = self.user_settings.get_system(VESTA_SYSTEM_CONFIG)
        else:
            vesta_plugin_settings = {
                "edr_url": "https://edr.hesi.energy",
                "edr_measures_tags": "measures,vesta"
            }
            self.user_settings.set_system(VESTA_SYSTEM_CONFIG, vesta_plugin_settings)
        return vesta_plugin_settings

    def register(self):
        print("Registering VESTA extension")

        @self.socketio.on('vesta_area_restrictions', namespace='/esdl')
        def set_area_restrictions(area_id):
            with self.flask_app.app_context():
                esh = get_handler()
                print(area_id)

                # TODO: get restrictions

                emit('vesta_restrictions_data', {"area_id": area_id})

        @self.flask_app.route('/vesta_restrictions')
        def get_vesta_restrictions():
            result = self.get_edr_vesta_measures_list()
            if result is None:
                return jsonify([]), 200
            else:
                return jsonify(result), 200

        @self.flask_app.route('/vesta_restriction/<id>')
        def get_vesta_restriction(id):
            result = self.get_edr_vesta_measures(id)
            if result is None:
                return jsonify([]), 200
            else:
                return jsonify(result), 200

    def get_edr_vesta_measures_list(self):
        url = self.vesta_plugin_settings["edr_url"] + "/store/tagged?tag=" + self.vesta_plugin_settings["edr_measures_tags"]

        try:
            r = requests.get(url)
            if r.status_code == 200:
                result = json.loads(r.text)
                return result
            else:
                print('EDR returned unexpected result. Check Vesta plugin settings')
                send_alert('EDR returned unexpected result. Check Vesta plugin settings')
                return None

        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return None

    def get_edr_vesta_measures(self, measures_id):
        url = self.vesta_plugin_settings["edr_url"] + "/store/esdl/" + measures_id + "?format=xml"

        try:
            r = requests.get(url)
            if r.status_code == 200:
                result = []
                measures = ESDLAsset.load_asset_from_string(r.text)
                for m in measures.measure:
                    result.append({
                        "id": m.id,
                        "name": m.name
                    })
                return result
            else:
                print('EDR returned unexpected result. Check Vesta plugin settings')
                send_alert('EDR returned unexpected result. Check Vesta plugin settings')
                return None

        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return None
