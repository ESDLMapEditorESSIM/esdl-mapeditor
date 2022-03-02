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
from uuid import uuid4

from flask import Flask
from flask_socketio import SocketIO

from esdl import Asset
import esdl
from esdl.processing.ESDLDataLayer import ESDLDataLayer
from esdl.processing.EcoreDocumentation import EcoreDocumentation

from extensions.session_manager import get_session, set_session, get_handler
from extensions.settings_storage import SettingsStorage
import src.log as log
from extensions.vue_backend.cost_information import _change_cost_unit
from utils.utils import camelCaseToWords, str2float

logger = log.get_logger(__name__)

cost_information_unit_list = [
  {'value': '', 'label': "Please select a unit..."},
  {'value': 'EUR', 'label': "EUR"},
  {'value': 'EUR/yr', 'label': "EUR/yr"},
  {'value': 'EUR/kW', 'label': "EUR/kW"},
  {'value': 'EUR/MW', 'label': "EUR/MW"},
  {'value': 'EUR/kWh', 'label': "EUR/kWh"},
  {'value': 'EUR/MWh', 'label': "EUR/MWh"},
  {'value': 'EUR/kWh/yr', 'label': "EUR/kWh/yr"},
  {'value': 'EUR/MWh/yr', 'label': "EUR/MWh/yr"},
  {'value': 'EUR/m', 'label': "EUR/m"},
  {'value': 'EUR/km', 'label': "EUR/km"},
  {'value': 'EUR/m2', 'label': "EUR/m2"},
  {'value': 'EUR/m3', 'label': "EUR/m3"},
  {'value': '%', 'label': "% of CAPEX"},
]


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
            logger.info(f"Retreiving information for table editor for assets with type {asset_type}")
            asset_info_list = self.datalayer.get_object_parameters_by_asset_type(asset_type)
            self.filter_cost_information(asset_info_list)
            table_editor_info = dict()
            table_editor_info['column_info'] = self._get_column_info(asset_info_list)
            table_editor_info['row_info'] = self._get_row_info(asset_info_list)
            return table_editor_info

        @self.socketio.on('change_cost_attr', namespace='/esdl')
        def change_cost_attr(info):
            id = info['id']
            attr = info['attr']
            value = info['value']

            esh = get_handler()
            active_es_id = get_session('active_es_id')
            asset = esh.get_by_id(active_es_id, id)

            self.set_cost_attr(asset, attr, value)

    def filter_cost_information(self, asset_info_list):
        set_ci = set()
        for asset in asset_info_list:
            cost_information = asset['cost_information']
            for ci in cost_information:
                if ci['value']:
                    set_ci.add(ci['name'])

        for asset in asset_info_list:
            new_cost_information = list()
            cost_information = asset['cost_information']
            for ci in cost_information:
                if ci['name'] in set_ci:
                    new_cost_information.append(ci)
            asset['cost_information'] = new_cost_information

    def set_cost_attr(self, asset: Asset, attr_name, value):
        print(f"Setting {attr_name} to {value} for asset ID {asset.id}")
        ci = asset.costInformation
        if not ci:
            ci = asset.costInformation = esdl.CostInformation(id=str(uuid4()))

        try:
            attr = ci.eGet(attr_name)
            if attr:
                # Singlevalue was found and value must be set
                attr.value = str2float(value)
            else:
                # Singlevalue was NOT found and value must be set
                ci.eSet(attr_name, esdl.SingleValue(id=str(uuid4()), value=str2float(value)))
        except AttributeError:
            if attr_name.endswith('_unit'):
                attr = ci.eGet(attr_name[:-5])
                if attr:
                    # Singlevalue was found and unit must be set
                    qau = attr.profileQuantityAndUnit
                    if not qau:
                        qau = attr.profileQuantityAndUnit = esdl.QuantityAndUnitType(
                            id=str(uuid4()),
                            physicalQuantity=esdl.PhysicalQuantityEnum.COST
                        )
                    _change_cost_unit(qau, value)
                else:
                    # Singlevalue was NOT found and unit must be set
                    sv = esdl.SingleValue(id=str(uuid4()))
                    sv.profileQuantityAndUnit = esdl.QuantityAndUnitType(
                        id=str(uuid4()),
                        physicalQuantity=esdl.PhysicalQuantityEnum.COST
                    )
                    _change_cost_unit(sv.profileQuantityAndUnit, value)
                    ci.eSet(attr_name, sv)
            else:
                raise Exception('Unknown attribute for setting costInformation via the TableEditor')

    def _get_column_info(self, asset_info_list):
        """
        :param asset_info_list: list with all attribute information of all assets for the given asset type
        :return: column information in a format that revolist datagrid likes
        """
        column_info = list()
        if asset_info_list:
            basic_attrs = asset_info_list[0]['attributes']['Basic']
            for attr_info in basic_attrs:
                column = dict()
                column['name'] = camelCaseToWords(attr_info['name'])
                column['prop'] = attr_info['name']
                column['autoSize'] = True

                if attr_info['type'] == 'EEnum':
                    options = list()
                    for option in attr_info['options']:
                        options.append({'label': option, 'value': option})
                    column['options'] = options

                column_info.append(column)

            cost_info = asset_info_list[0]['cost_information']
            for ci in cost_info:
                column = dict()
                column['name'] = ci['uiname']
                column['prop'] = ci['name']
                column['autoSize'] = True
                column['ref'] = 'costInformation.' + ci['name']
                column_info.append(column)

                column = dict()
                column['name'] = ci['uiname'] + ' unit'
                column['prop'] = ci['name'] + '_unit'
                column['autoSize'] = True
                column['options'] = cost_information_unit_list
                column['ref'] = 'costInformation.' + ci['name'] + '_unit'
                column_info.append(column)

        return column_info

    def _find_id_in_attr_info(self, asset_attr_info):
        """
        As the asset ID attribute can be in Basic/Advanced/... category (depends on a user setting), we need to
        search for it
        :param asset_attr_info: dict[category] with attribute lists
        :return: value of ID
        """
        for cat in asset_attr_info:
            attr_list = asset_attr_info[cat]
            for attr in attr_list:
                if attr['name'] == 'id':
                    return attr['value']
        return None

    def _get_row_info(self, asset_info_list):
        """
        :param asset_info_list: list with all information of all assets for the given asset type
        :return: row information in a format that revolist datagrid likes
        """
        row_info = list()

        for asset_attr_info in asset_info_list:
            basic_attrs = asset_attr_info['attributes']['Basic']
            row = dict()
            row['id'] = self._find_id_in_attr_info(asset_attr_info['attributes'])
            for attr_info in basic_attrs:
                row[attr_info['name']] = attr_info['value']

            cost_attrs = asset_attr_info['cost_information']
            for ca in cost_attrs:
                if ca['value']:
                    row[ca['name']] = ca['value']
                    row[ca['name'] + '_unit'] = ca['unit']
                else:
                    row[ca['name']] = ''
                    row[ca['name'] + '_unit'] = ''
            row_info.append(row)

        return row_info
