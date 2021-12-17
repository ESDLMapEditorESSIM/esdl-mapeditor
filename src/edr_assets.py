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
import urllib

from flask import Flask, jsonify, abort
from flask_socketio import SocketIO
from extensions.settings_storage import SettingsStorage
import src.settings as settings
import src.log as log
import requests
import json

logger = log.get_logger(__name__)

#TODO: find proper way
def send_alert(msg):
    print(msg)

ASSET_TYPE_TAG_PREFIX = "assetType:"


class EDRAssets:

    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.current_asset_string = ''
        self.EDR_config = settings.edr_config
        self.ESDLDrive_config = settings.esdl_drive_config

        self.register()

    def register(self):
        logger.info("Registering EDRAssets extension")

        @self.flask_app.route('/edr_assets')
        def get_edr_assets():
            edr_url = self.ESDLDrive_config['hostname'] + \
                      "/store/edr/query?addESDL=false&addImageData=false&esdlType=EnergyAsset&maxResults=-1"
            # logger.debug('accessing URL: '+edr_url)

            try:
                r = requests.get(edr_url)
                if r.status_code == 200:
                    result = json.loads(r.text)
                    asset_list = []
                    asset_type_list = []
                    for a in result:
                        asset_type = a['esdlType']
                        if not asset_type in asset_type_list:
                            asset_type_list.append(asset_type)

                        asset = {
                            'id': a["id"],
                            'title': a["title"],
                            'asset_type': asset_type,
                            'description': a["description"] if 'description' in a else '',
                        }
                        asset_list.append(asset)

                    asset_type_list.sort()
                    asset_list.sort(key=lambda x: x["title"])

                    return (jsonify({'asset_list': asset_list, 'asset_type_list': asset_type_list})), 200
                else:
                    logger.error('code: ', r.status_code)
                    send_alert('Error in getting the EDR assets')
                    abort(500, 'Error in getting the EDR assets')
            except Exception as e:
                logger.error('Exception: ')
                logger.error(e)
                send_alert('Error accessing EDR API')
                abort(500, 'Error accessing EDR API')

    def get_asset_from_EDR(self, edr_asset_id):
        url = self.ESDLDrive_config['hostname'] + "/store/edr/query?addESDL=true&path=" + \
              urllib.parse.quote(edr_asset_id, safe='')
        print('EDR url: ', url)
        headers = {
            'Accept': "application/json",
            'User-Agent': "ESDL Mapeditor/0.1"
        }

        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                result = json.loads(r.text)
                # print(result)
                esdl_str_b64 = result[0]['esdl']
                esdl_str_b64_bytes = esdl_str_b64.encode('utf-8')
                esdl_str_bytes = base64.b64decode(esdl_str_b64_bytes)
                esdl_str = esdl_str_bytes.decode('utf-8')
                self.current_asset_string = esdl_str
                # self.current_asset = ESDLAsset.load_asset_from_string(result)
                return self.current_asset_string
            else:
                send_alert('Error getting EDR asset - response ' + str(r.status_code) + ' with reason: ' + str(
                    r.reason))
                print(r)
                print(r.content)
                return 0
        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return 0