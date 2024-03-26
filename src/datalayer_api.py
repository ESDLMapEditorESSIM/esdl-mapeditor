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

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl.processing.ESDLEcore import instantiate_type
from esdl.processing.ESDLDataLayer import ESDLDataLayer
from extensions.session_manager import get_session
from extensions.vue_backend.control_strategy import get_control_strategy_info, set_control_strategy
from extensions.vue_backend.cost_information import set_cost_information
from dataclasses import asdict
from extensions.vue_backend.messages.DLA_table_data_message import DLA_table_data_request, DLA_table_data_response, \
    DLA_set_table_data_request
from extensions.vue_backend.messages.DLA_delete_ref_message import DeleteRefMessage
from src.asset_draw_toolbar import AssetDrawToolbar
import src.log as log
import esdl

logger = log.get_logger(__name__)


class DataLayerAPI:
    def __init__(self, flask_app: Flask, socket: SocketIO, esdl_doc: EcoreDocumentation):
        self.flask_app = flask_app
        self.socketio = socket
        self.datalayer = ESDLDataLayer(esdl_doc)
        self.register()

    def register(self):
        logger.info("Registering DataLayerAPI")

        # Implementation that could be used for the ESDL Browser
        @self.socketio.on('DLA_get_object_info', namespace='/esdl')
        def DLA_get_object_info(identifier):
            return self.datalayer.get_object_info_by_identifier(identifier)

        # Implementation that is used for the Sidebar
        @self.socketio.on('DLA_get_object_properties', namespace='/esdl')
        def DLA_get_object_properties(identifier):
            return self.datalayer.get_object_parameters_by_identifier(identifier)

        # @self.socketio.on('DLA_set_object_properties', namespace='/esdl')
        # def DLA_set_object_properties(identifier, properties):
        #     return self.datalayer.set_object_parameters_by_identifier(identifier, properties)       

        @self.socketio.on('DLA_set_cost_information', namespace='/esdl')
        def DLA_set_cost_information(identifier, cost_information):
            if isinstance(identifier['id'], list):
                esdl_objects = list()
                for obj_id in identifier['id']:
                    esdl_objects.append(self.datalayer.get_object_from_identifier({'id': obj_id}))
            else:
                esdl_objects = [self.datalayer.get_object_from_identifier(identifier)]

            for obj in esdl_objects:
                set_cost_information(obj, cost_information)

        @self.socketio.on('DLA_get_marg_costs', namespace='/esdl')
        def DLA_get_marg_costs(identifier):
            esdl_object = self.datalayer.get_object_from_identifier(identifier)

            mc = None
            if esdl_object.costInformation:
                if esdl_object.costInformation.marginalCosts:
                   mc = esdl_object.costInformation.marginalCosts.value

            return {'marg_costs': mc}


        @self.socketio.on('DLA_get_cs_info', namespace='/esdl')
        def DLA_get_cs_info(identifier):
            """
            Gets information about the control strategy attached to an EnergyAsset

            :param str identifier: identifier (ID or fragment) of the EnergyAsset 
            """
            result = dict()

            object = self.datalayer.get_object_from_identifier(identifier)
            if isinstance(object, esdl.EnergyAsset):
                # information about the attached control_strategy (if any)
                result['controlStrategy'] = get_control_strategy_info(object)

                eref = object.eClass.findEStructuralFeature('controlStrategy')
                result['controlStrategyTypes'] = self.datalayer.get_filtered_type(object, eref)

                # list of ports
                oi = self.datalayer.get_object_info_by_identifier(identifier)
                for ref in oi['references']:
                    if ref['name'] == 'port':
                        result['ports'] = ref['value']

                # list of sensors
                result['sensor_list'] = self.datalayer.get_area_object_list_of_type(esdl.Sensor)

                # list of standard profiles
                result['profile_list'] = self.datalayer.get_standard_profiles_list()

            return result

        @self.socketio.on('DLA_set_cs', namespace='/esdl')
        def DLA_set_cs(identifier, cs_info):
            """
            Sets or changes the control strategy for an EnergyAsset. 

            :param str identifier: identifier (ID or fragment) of the EnergyAsset of which the control strategy must be set
            """
            object = self.datalayer.get_object_from_identifier(identifier)
            set_control_strategy(object, cs_info)

        @self.socketio.on('DLA_remove_cs', namespace='/esdl')
        def DLA_remove_cs(identifier):
            """
            Removes a control strategy from an EnergyAsset. Also removes the control strategy from the list of Services. 

            :param str identifier: identifier (ID or fragment) of the EnergyAsset of which the control strategy must be removed
            """
            object = self.datalayer.get_object_from_identifier(identifier)

            if isinstance(object, esdl.EnergyAsset):
                self.datalayer.remove_control_strategy(object)

        @self.socketio.on('DLA_get_table_data', namespace='/esdl')
        def DLA_get_table_data(message):
            table_data_request = DLA_table_data_request(**message)
            print('DLA_get_table_data_request', table_data_request)
            response: DLA_table_data_response = self.datalayer.get_table(table_data_request)
            # return the dataclass as dict
            return asdict(response)

        @self.socketio.on('DLA_set_table_data', namespace='/esdl')
        def DLA_set_table_data(message):
            new_table_data = DLA_set_table_data_request(**message)
            print('DLA_set_table_data_request', new_table_data)
            self.datalayer.set_table(new_table_data)

        @self.socketio.on('DLA_delete_ref', namespace='/esdl')
        def DLA_delete_ref(message):
            delete_ref_message = DeleteRefMessage(**message)
            return self.datalayer.delete_ref(delete_ref_message)

        @self.flask_app.route('/DLA_get_asset_toolbar_info')
        def DLA_get_asset_toolbar_info():
            """
            Retrieves a list of assets that can be rendered in the AssetDrawToolbox. Elements in the list change when
            view_mode changes.

            :return: a dictionary with per ESDL capability a list of assets
            """
            with self.flask_app.app_context():
                adt = AssetDrawToolbar.get_instance()
                assets_per_cap_dict = self.datalayer.get_asset_list()
                edr_assets_on_toolbar = adt.load_asset_draw_toolbar_edr_assets()
                recently_used_edr_assets = self.datalayer.get_recently_used_edr_assets()
                return {
                    "assets_per_cap_dict": assets_per_cap_dict,
                    "edr_assets": edr_assets_on_toolbar,
                    "recent_edr_assets": recently_used_edr_assets
                }

        @self.socketio.on('DLA_get_profile_names_list', namespace='/esdl')
        def DLA_get_profile_names_list(message):
            """
            :return: a dictionary returning the list of profile names in the
            current ESDL, and the list of uploaded profile names.
            """
            esdl_profile_names = self.datalayer.get_profile_names_list()

            return {"esdl_profile_names": esdl_profile_names}

        @self.socketio.on('DLA_get_environmental_profiles_info', namespace='/esdl')
        def DLA_get_environmental_profiles_info():
            """
            Gets information about the Environmental profiles configured in the ESDL. Also includes information on
            the currently available standard profiles

            :return: dictionary with environmental profile information
            """
            result = dict()
            result['env_profiles'] = self.datalayer.get_environmental_profiles()

            # list of standard profiles
            result['standard_profiles_list'] = self.datalayer.get_standard_profiles_list()

            return result

        @self.socketio.on('DLA_update_environmental_profiles_info', namespace='/esdl')
        def DLA_update_environmental_profiles_info(info):
            """
            Updates information about the Environmental profiles configured in the ESDL.
            """
            action = info["action"]
            profile_info = info["profile_info"]

            self.datalayer.update_environmental_profiles(action, profile_info)

        @self.socketio.on('DLA_get_carrier_info', namespace='/esdl')
        def DLA_get_carrier_info(message):
            """
            Gets information about a carrier configured in the ESDL.

            :return: dictionary with carrier information
            """
            return asdict(self.datalayer.get_carrier(message['id']))

        @self.socketio.on('DLA_update_carrier_info', namespace='/esdl')
        def DLA_update_carrier_info(message):
            """
            Updates information about a carrier configured in the ESDL.
            """
            return self.datalayer.update_carrier(message['id'], message['carr_info'])

        @self.socketio.on('DLA_add_EDR_carriers', namespace='/esdl')
        def DLA_add_EDR_carriers(message):
            """
            Add carriers information from an EDR dataset.
            """
            return self.datalayer.add_EDR_carriers(message['id'])

        @self.socketio.on('DLA_get_sector_info', namespace='/esdl')
        def DLA_get_sector_info(message):
            """
            Gets information about a carrier configured in the ESDL.

            :return: dictionary with carrier information
            """
            return asdict(self.datalayer.get_sector(message['id']))

        @self.socketio.on('DLA_update_sector_info', namespace='/esdl')
        def DLA_update_sector_info(message):
            """
            Updates information about a carrier configured in the ESDL.
            """
            return self.datalayer.update_sector(message['id'], message['sector_info'])

        @self.socketio.on('DLA_add_EDR_sectors', namespace='/esdl')
        def DLA_add_EDR_sectors(message):
            """
            Add sectors information from an EDR dataset.
            """
            return self.datalayer.add_EDR_sectors(message['id'])
