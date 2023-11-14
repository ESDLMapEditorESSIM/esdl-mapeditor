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
edrclient_instance = None


class EDRClient:

    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.EDR_config = settings.edr_config
        self.ESDLDrive_config = settings.esdl_drive_config

        global edrclient_instance
        if edrclient_instance:
            logger.error("ERROR: Only one EDRClient object can be instantiated")
        else:
            edrclient_instance = self

        self.register()

    @staticmethod
    def get_instance():
        global edrclient_instance
        return edrclient_instance

    def register(self):
        logger.info("Registering EDR extension")

        @self.flask_app.route('/edr_assets')
        def get_edr_assets():
            try:
                res_code, res_list = self.get_EDR_list("EnergyAsset")

                if res_code == 200:
                    return jsonify(res_list), 200
                else:
                    logger.error('code: ', res_code)
                    send_alert('Error in getting the EDR assets (code: '+res_code+')')
                    abort(500, 'Error in getting the EDR assets (code: '+res_code+')')
            except Exception as e:
                logger.error('Exception: ')
                logger.error(e)
                send_alert('Error accessing EDR API')
                abort(500, 'Error accessing EDR API')\

        @self.flask_app.route('/edr_carriers')
        def get_edr_carriers():
            try:
                res_code, res_list = self.get_EDR_list("Carriers")

                if res_code == 200:
                    return jsonify(res_list), 200
                else:
                    logger.error('code: ', res_code)
                    send_alert('Error in getting the EDR carriers (code: '+res_code+')')
                    abort(500, 'Error in getting the EDR carriers (code: '+res_code+')')
            except Exception as e:
                logger.error('Exception: ')
                logger.error(e)
                send_alert('Error accessing EDR API')
                abort(500, 'Error accessing EDR API')

        @self.flask_app.route('/edr_sectors')
        def get_edr_sectors():
            try:
                res_code, res_list = self.get_EDR_list("Sectors")

                if res_code == 200:
                    return jsonify(res_list), 200
                else:
                    logger.error('code: ', res_code)
                    send_alert('Error in getting the EDR sectors (code: '+res_code+')')
                    abort(500, 'Error in getting the EDR sectors (code: '+res_code+')')
            except Exception as e:
                logger.error('Exception: ')
                logger.error(e)
                send_alert('Error accessing EDR API')
                abort(500, 'Error accessing EDR API')

    def get_object_from_EDR(self, edr_object_id):
        url = self.EDR_config['host'] + "/store/edr/query?addESDL=true&path=" + \
              urllib.parse.quote(edr_object_id, safe='')
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
                return esdl_str
            else:
                send_alert('Error getting EDR object - response ' + str(r.status_code) + ' with reason: ' + str(
                    r.reason))
                print(r)
                print(r.content)
                return 0
        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return 0

    def get_EDR_profiles_list(self, field_map=None, include_esdl=False):
        res_code, res_list = self.get_EDR_list("GenericProfile", field_map=field_map, include_esdl=include_esdl)
        return res_code, res_list

    def get_EDR_profile(self, profile_id):
        pass

    def get_EDR_list(self, esdl_type, field_map=None, include_esdl=False):
        """
        Retrieves a list of items from the EDR. Can be used for assets (type="EnergyAsset"), profiles
        (type="GenericProfile"), carrier lists (type="Carriers"),
        """
        if not field_map:
            field_map = {
                'value': 'id',
                'label': 'title',
                'description': 'description'
            }
        add_esdl = 'true' if include_esdl else 'false'
        edr_url = self.EDR_config['host'] + \
                  "/store/edr/query?addESDL="+add_esdl+"&addImageData=false&esdlType="+esdl_type+"&maxResults=-1"
        # logger.debug('accessing URL: '+edr_url)

        r = requests.get(edr_url)
        if r.status_code == 200:
            result = json.loads(r.text)
            item_list = []
            item_type_list = []
            for a in result:
                item_type = a['esdlType']
                if not item_type in item_type_list:
                    item_type_list.append(item_type)

                item = {'item_type': item_type}
                for f in field_map:
                    item[f] = a[field_map[f]] if field_map[f] in a and a[field_map[f]] is not None else ''

                item_list.append(item)

            item_type_list.sort()
            item_list.sort(key=lambda x: x["label"])

            result = {'item_list': item_list, 'item_type_list': item_type_list}
            return r.status_code, result
        else:
            return r.status_code, None
