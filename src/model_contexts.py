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

from extensions.session_manager import get_session, set_session
from extensions.settings_storage import SettingsStorage
from esdl import esdl
from copy import deepcopy
import src.log as log

logger = log.get_logger(__name__)

model_contexts_config = {
    "standard": {
        "Basic": {
            "EnergyAsset": [
                "name",
                "state"
            ],
            "Potential": [
                "name",
            ],
            "ExposedPortsAsset": [
                "name",
                "state"
            ],
            # ===========================
            #  The 5 ESDL capabilities
            # ===========================
            "Consumer": [
                "power"
            ],
            "Producer": [
                "power",
                "prodType"
            ],
            "Storage": [
                "capacity",
                "maxChargeRate",
                "maxDischargeRate",
            ],
            "Transport": [
                "capacity"
            ],
            "Conversion": [
                "power",
                "efficiency"
            ],
            # ===========================
            #  Transport assets
            # ===========================

            # ===========================
            #  Conversion assets
            # ===========================
            "HeatPump": [
                "COP"
            ],
            # ===========================
            #  Building assets
            # ===========================
            "AbstractBuilding": [
                "name"
            ],
            "Building": [
                "type",
                "buildingYear",
                "surfaceArea",
                "floorArea",
                "energyLabel"
            ],
            "AggregatedBuilding": [
                "surfaceArea",
                "numberOfBuildings",
                "floorArea"
            ],
            # ===========================
            #  Potentials
            # ===========================
            "SolarPotential": [
                "area",
                "description",
                "orientation",
                "solarPotentialType",
                "value"
            ],
        },
        "Aggregation": {
            "EnergyAsset": [
                "aggregated",
                "aggregationCount"
            ],
            "Potential": [
                "aggregated",
                "aggregationCount"
            ],
            "Building": [
                "aggregated",
                "aggregationCount"
            ]
        }
    },
    "ESSIM": {
        "Basic": {
            "EnergyAsset": [
                "name",
                "state",
            ],
            "ExposedPortsAsset": [
                "name",
                "state"
            ],
        },
        "ESSIM": {
            # ===========================
            #  The 5 ESDL capabilities
            # ===========================
            "Producer": [
                "power"
            ],
            "Consumer": [
                "power"
            ],
            "Conversion": [
                "efficiency",
                "power"
            ],
            "Storage": [
                "capacity",
                "fillLevel",
                "maxChargeRate",
                "maxDischargeRate",
                "selfDischargeRate"
            ],
            "Transport": [
                "capacity"
            ],
            # ===========================
            #  Conversion assets
            # ===========================
            "HeatPump": [
                "COP",
                "stages"
            ],
            "CHP": [
                "electricalEfficiency",
                "heatEfficiency"
            ]
        },
    },
    "CHESS": {
        "Basic": {
            "EnergyAsset": [
                "name",
                "state",
                "technicalLifetime"
            ],
            "ExposedPortsAsset": [
                "name",
                "state"
            ],
            "Potential": [
                "name",
            ],
            # ===========================
            #  The 5 ESDL capabilities
            # ===========================
            "Consumer": [
                "power"
            ],
            "Producer": [
                "power",
                "prodType"
            ],
            "Storage": [
                "capacity",
                "maxChargeRate",
                "maxDischargeRate",
            ],
#            "Transport": [  # no capacity required for CHESS/Wanda
#                "capacity"
#            ],
            "Conversion": [
                "power",
                "efficiency"
            ],
            # ===========================
            #  Transport assets
            # ===========================
            "Pump": [
                "pumpCurveTable",
                "controlStrategy",
                "pumpCapacity",
                "pumpEfficiency",
                "ratedSpeed"
            ],
            "Pipe": [
                "diameter",
                "innerDiameter",
                "outerDiameter",
                "length",
                "material"
            ],
            "CheckValve": [
                "flowCoefficient",
                "innerDiameter",
                "reopenDeltaP"
            ],
            "Valve": [
                "type",
                "flowCoefficient",
                "innerDiameter",
                "position"
            ],
            "Sensor": [
                "quantityAndUnit"
            ],
            "HeatExchange": [
                "heatTransferCoefficient",
                "diameterPrimarySide",
                "diameterSecundarySide",
                "lengthPrimarySide",
                "lengthSecundarySide",
                "roughnessPrimarySide",
                "roughnessSecundarySide"
            ],
            "HeatStorage": [
                "fillLevel",
                "maxStorageTemperature",
                "minStorageTemperature"
            ],
            # ===========================
            #  Conversion assets
            # ===========================
            "HeatPump": [
                "COP"
            ],
            # ===========================
            #  Building assets
            # ===========================
            "AbstractBuilding": [
                "name"
            ],
            "Building": [
                "type",
                "buildingYear",
                "surfaceArea",
                "floorArea",
                "energyLabel"
            ],
            "AggregatedBuilding": [
                "surfaceArea",
                "numberOfBuildings",
                "floorArea"
            ],
            # ===========================
            #  Potentials
            # ===========================
        }
    }
}
asset_list = {
    "standard": {
        "Producer": [
            "GeothermalSource",
            "Import",
            "PVInstallation",
            "WindTurbine",
        ],
        "Consumer": [
            "ElectricityDemand",
            "Export",
            "HeatingDemand",
        ],
        "Conversion": [
            "CHP",
            "GasHeater",
            "HeatPump",
            "PowerPlant",
            "Electrolyzer",
        ],
        "Storage": [
            "Battery",
            "GasStorage",
            "HeatStorage",
        ],
        "Transport": [
            "Transformer",
        ]
    },
    "ESSIM": {
        "Producer": [
            "GeothermalSource",
            "Import",
            "PVInstallation",
            "WindTurbine"
        ],
        "Consumer": [
            "ElectricityDemand",
            "Export",
            "HeatingDemand",
        ],
        "Conversion": [
            "CHP",
            "Electrolyzer",
            "GasHeater",
            "HeatPump",
            "PowerPlant",
        ],
        "Storage": [
            "Battery",
            "GasStorage",
            "HeatStorage",
        ],
        "Transport": [
            "Transformer",
            "Bus",
        ]
    },
    "CHESS": {
        "Producer": [
            "GenericProducer",
            "GeothermalSource",
            "ResidualHeatSource",
        ],
        "Consumer": [
            "GenericConsumer",
            "HeatingDemand",
        ],
        "Storage": [
            "HeatStorage",
        ],
        "Conversion": [
            "GasHeater",
            "HeatPump",
        ],
        "Transport": [
            "Pipe",
            "Pump",
            "Valve",
            "CheckValve",
            "HeatExchange"
        ]
    }
}


MODEL_CONTEXT_USER_CONFIG = "MODEL_CONTEXTS_USER_CONFIG"
model_contexts = None


class ModelContexts:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        global model_contexts
        if model_contexts:
            logger.error("ERROR: Only one ModelContexts object can be instantiated")
        else:
            model_contexts = self

    @staticmethod
    def get_instance():
        global model_contexts
        return model_contexts

    def initialize_user(self, user):
        settings = self.get_user_settings(user)
        set_session('mapeditor_model_context', settings['mode'])
        logger.debug('User has MapEditor view mode: {}'.format(settings['mode']))
        return settings['mode']

    def register(self):
        logger.info("Registering ModelContexts")

        @self.socketio.on('model_contexts_get_mode_info', namespace='/esdl')
        def model_contexts_get_mode_info():
            return self.model_contexts_get_mode_info()

        @self.socketio.on('model_contexts_set_mode', namespace='/esdl')
        def model_contexts_set_mode(mode):
            user = get_session('user-email')
            settings = self.get_user_settings(user)
            settings['mode'] = mode['mode']
            self.set_user_settings(user, settings)
            set_session('mapeditor_model_context', settings['mode'])
            logger.debug('User has MapEditor view mode: {}'.format(settings['mode']))

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, MODEL_CONTEXT_USER_CONFIG):
            return self.settings_storage.get_user(user, MODEL_CONTEXT_USER_CONFIG)
        else:
            user_settings = {
                'mode': 'standard'
            }
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, MODEL_CONTEXT_USER_CONFIG, settings)

    def model_contexts_get_mode_info(self):
        user = get_session('user-email')
        settings = self.get_user_settings(user)
        return {
            'current_mode': settings['mode'],
            'possible_modes': list(model_contexts_config.keys())
        }

    def categorize_object_attributes(self, object, attributes):
        attr_dict = {attr['name']: attr for attr in attributes}
        model_context = get_session('mapeditor_model_context')

        this_model_context_config = model_contexts_config[model_context]

        categorized_attributes_list = dict()
        for key in this_model_context_config:
            categorized_attributes_list[key] = list()

            for objtype in this_model_context_config[key]:
                if isinstance(object, esdl.getEClassifier(objtype)):
                    for attr in this_model_context_config[key][objtype]:
                        attr_info = deepcopy(attr_dict[attr])
                        del attr_dict[attr]
                        categorized_attributes_list[key].append(attr_info)

        categorized_attributes_list['Advanced'] = list()
        for attr in attr_dict:
            attr_info = deepcopy(attr_dict[attr])
            categorized_attributes_list['Advanced'].append(attr_info)

        return categorized_attributes_list

    def categorize_object_attributes_and_references(self, object, attributes, references):
        attr_dict = {attr['name']: attr for attr in attributes}
        ref_dict = {ref['name']: ref for ref in references}
        model_context = get_session('mapeditor_model_context')

        this_model_context_config = model_contexts_config[model_context]

        categorized_list = dict()
        for key in this_model_context_config:
            categorized_list[key] = list()

            for objtype in this_model_context_config[key]:
                if isinstance(object, esdl.getEClassifier(objtype)):
                    for feature in this_model_context_config[key][objtype]:
                        if feature in attr_dict:
                            attr_info = deepcopy(attr_dict[feature])
                            del attr_dict[feature]
                            categorized_list[key].append(attr_info)
                        elif feature in ref_dict:
                            ref_info = deepcopy(ref_dict[feature])
                            del ref_dict[feature]
                            categorized_list[key].append(ref_info)

        categorized_list['Advanced'] = list()
        for feature in attr_dict:
            attr_info = deepcopy(attr_dict[feature])
            categorized_list['Advanced'].append(attr_info)
        for feature in ref_dict:
            attr_info = deepcopy(ref_dict[feature])
            categorized_list['Advanced'].append(attr_info)

        return categorized_list

    def get_asset_list(self):
        model_context = get_session('mapeditor_model_context')
        if not model_context:
            user = get_session('user-email')
            model_context = self.initialize_user(user)

        return asset_list[model_context]

    def get_asset_list_for_model_context(self, model_context):
        return asset_list[model_context]
