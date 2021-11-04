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
from esdl.processing.ESDLDataLayer import ESDLDataLayer
from esdl.processing.EcoreDocumentation import EcoreDocumentation

from extensions.session_manager import get_session, set_session
from extensions.settings_storage import SettingsStorage
import src.log as log
from utils.utils import camelCaseToWords

logger = log.get_logger(__name__)


class TableEditor:
    def __init__(self, flask_app: Flask, socket: SocketIO, esdl_doc: EcoreDocumentation, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.datalayer = ESDLDataLayer(esdl_doc)
        self.register()

    def register(self):
        logger.info("Registering TableEditor")

        @self.flask_app.route('/table_editor/asset_data/<asset_type>')
        def table_editor_get_asset_types(asset_type):
            logger.info(asset_type)
            asset_attr_list = self.datalayer.get_object_parameters_by_asset_type(asset_type)
            table_editor_info = dict()
            table_editor_info['column_info'] = self._get_column_info(asset_attr_list)
            table_editor_info['row_info'] = self._get_row_info(asset_attr_list)
            return table_editor_info

    def _get_column_info(self, asset_attr_list):
        """
        :param asset_attr_list: list with all attribute information of all assets for the given asset type
        :return: column information in a format that revolist datagrid likes
        """
        column_info = list()
        if asset_attr_list:
            basic_attrs = asset_attr_list[0]['Basic']
            for attr_info in basic_attrs:
                column = dict()
                column['name'] = camelCaseToWords(attr_info['name'])
                column['prop'] = attr_info['name']
                column['autosize'] = True

                if attr_info['type'] == 'EEnum':
                    options = list()
                    for option in attr_info['options']:
                        options.append({'label': option, 'value': option})
                    column['options'] = options

                column_info.append(column)

        return column_info

    def _get_row_info(self, asset_attr_list):
        """
        :param asset_attr_list: list with all attribute information of all assets for the given asset type
        :return: row information in a format that revolist datagrid likes
        """
        row_info = list()

        for asset_attr_info in asset_attr_list:
            basic_attrs = asset_attr_info['Basic']
            row = dict()
            for attr_info in basic_attrs:
                row[attr_info['name']] = attr_info['value']
            row_info.append(row)

        return row_info
