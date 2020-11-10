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
from flask_socketio import SocketIO, emit
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl.processing.ESDLEcore import instantiate_type
from esdl.processing.ESDLDataLayer import ESDLDataLayer
from extensions.vue_backend.control_strategy import get_control_strategy_info, set_control_strategy
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

        @self.socketio.on('DLA_get_object_info', namespace='/esdl')
        def DLA_get_object_info(identifier):
            return self.datalayer.get_object_info_by_identifier(identifier)
        
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

            print(result)
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
