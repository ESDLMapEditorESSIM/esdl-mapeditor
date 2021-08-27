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
import base64

from flask import Flask
from flask_socketio import SocketIO
from extensions.session_manager import get_handler, get_session
import src.settings as settings
import requests
import urllib
import json
import src.log as log

logger = log.get_logger(__name__)

# ---------------------------------------------------------------------------------------------------------------------
#  Get energy system statistics information
# ---------------------------------------------------------------------------------------------------------------------
class ESStatisticsService:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering ESStatistics extension')

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

        esdlstr_bytes = esdl_str.encode('ascii')
        esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
        body = {"energysystem": esdlstr_base64_bytes.decode('ascii')}

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
