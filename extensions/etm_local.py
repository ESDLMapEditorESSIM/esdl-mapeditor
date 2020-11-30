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
import requests
import csv
import codecs
import json

from extensions.settings_storage import SettingsStorage
import src.settings as settings
import src.log as log
from src.process_es_area_bld import get_area_id_from_mapeditor_id


logger = log.get_logger(__name__)

ETMLOCAL_SYSTEM_CONFIG = 'ETMLOCAL_SYSTEM_CONFIG'
ETMLOCAL_DEFAULT_SYSTEM_CONFIG = {
    'etmlocal_api': 'https://beta-local.energytransitionmodel.com/api/v1/exports/<ID>',
    'CBS_ETM_ID_mapping': 'data/CBS-ETM-mapping.csv'
}

# ETLocal interface implementation
# --------------------------------
# Github site: https://github.com/quintel/etlocal
# List of IDs: https://github.com/quintel/etlocal/wiki/Overview:-datasets-and-dataset-IDs
# Example API call: https://beta-local.energytransitionmodel.com/api/v1/exports/14597


class ETMLocal:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.cbs_etm_id_mapping = dict()

        self.plugin_settings = self.get_settings()
        self.register()

        self.read_cbs_etm_id_mapping()

    def register(self):
        logger.info('Registering ETMLocal extension')

        @self.socketio.on('etmlocal_get_info', namespace='/esdl')
        def get_info(cbs_id):
            if cbs_id in self.cbs_etm_id_mapping:
                etm_id = self.cbs_etm_id_mapping[cbs_id]
                return self.call_etmlocal_api(etm_id)
            else:
                return 'ID does not exist'

    def get_settings(self):
        if self.settings_storage.has_system(ETMLOCAL_SYSTEM_CONFIG):
            etmlocal_plugin_settings = self.settings_storage.get_system(ETMLOCAL_SYSTEM_CONFIG)
        else:
            etmlocal_plugin_settings = ETMLOCAL_DEFAULT_SYSTEM_CONFIG
            self.settings_storage.set_system(ETMLOCAL_SYSTEM_CONFIG, etmlocal_plugin_settings)
        return etmlocal_plugin_settings

    def read_cbs_etm_id_mapping(self):
        mapping_csv_file = self.plugin_settings['CBS_ETM_ID_mapping']

        with codecs.open(mapping_csv_file, encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file, delimiter=';')
            next(reader)    # skip header
            for row in reader:
                self.cbs_etm_id_mapping[row[0].split('_')[0]] = row[1]

        logger.debug("Nummber of records: {}".format(len(self.cbs_etm_id_mapping)))

    def call_etmlocal_api(self, id):
        id = get_area_id_from_mapeditor_id(id)
        url = self.plugin_settings['etmlocal_api'].replace('<ID>', id)
        result = None

        try:
            logger.info("Querying URL "+url)
            r = requests.get(url)
            if r.status_code == 200:
                result = json.loads(r.text)
            else:
                logger.debug("ETMLocal API returned status code: {}".format(r.status_code))
        except Exception as e:
            logger.debug("Error accessing ETMLocal API: " + str(e))

        return result



