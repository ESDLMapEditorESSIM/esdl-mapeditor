from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, set_session
import settings
import requests
import urllib
import json


# ---------------------------------------------------------------------------------------------------------------------
#  Get energy system statistics information
# ---------------------------------------------------------------------------------------------------------------------
class ESStatisticsService:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering ESStatistics extension')

        @self.socketio.on('get_es_statistics', namespace='/esdl')
        def get_es_statistics():
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                esdl_str = esh.to_string(active_es_id)
                return self.call_es_statistics_service(esdl_str)

    def call_es_statistics_service(self, esdl_str):
        url = 'http://' + settings.statistics_settings_config['host'] + ':' + settings.statistics_settings_config['port']\
              + settings.statistics_settings_config['path']

        body = {"energysystem": urllib.parse.quote(esdl_str)}

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ESDL Mapeditor/0.1"
        }

        reply = dict()
        try:
            r = requests.post(url, headers=headers, data=json.dumps(body))

            if len(r.text) > 0:
                reply = json.loads(r.text)
            else:
                print("WARNING: Empty response for energy system statistics service")

        except Exception as e:
            print('ERROR in accessing energy system statistics service: {}'.format(e))

        return reply
