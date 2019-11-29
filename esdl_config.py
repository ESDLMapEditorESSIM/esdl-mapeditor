esdl_config = {
    "profile_database": {
        "host": "http://10.30.2.1",
        "port": "8086",
        "database": "energy_profiles",
        "filters": ""
    },
    "influxdb_profile_data": [
        {
            "profile_uiname": "Solar",
            "multiplier": 1,
            "measurement": "solar_relative_2011-2016",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity households (E1A)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E1A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity shops, office, education (E3A)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity prison (E3B)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3B",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity hotel, hospital (E3C)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3C",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Electricity greenhouses (E3D)",
            "multiplier": 1,
            "measurement": "nedu_elektriciteit_2015-2018",
            "field": "E3D",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating households (G1A)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G1A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating ... (G2A)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2A",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Heating ... (G2C)",
            "multiplier": 1,
            "measurement": "nedu_aardgas_2015-2018",
            "field": "G2C",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Constant",
            "multiplier": 1,
            "measurement": "constant",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Wind op land",
            "multiplier": 1,
            "measurement": "wind-2015",
            "field": "Wind-op-land",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Wind op zee",
            "multiplier": 1,
            "measurement": "wind-2015",
            "field": "Wind-op-zee",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Biomassa",
            "multiplier": 1,
            "measurement": "biomassa-2015",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Elektriciteit Curacao",
            "multiplier": 1,
            "measurement": "elektr-curacao-2015",
            "field": "elektr",
            "profileType": "ENERGY_IN_TJ"
        },
        {
            "profile_uiname": "Wind Curacao",
            "multiplier": 1,
            "measurement": "wind-curacao-2015",
            "field": "value",
            "profileType": "ENERGY_IN_TJ"
        }
    ],
    "energy_carriers": [
    ],
    "control_strategies": [
        {
            "name": "DrivenByDemand",
            "applies_to": "Conversion",
            "connect_to": "OutPort"
        },
        {
            "name": "DrivenBySupply",
            "applies_to": "Conversion",
            "connect_to": "InPort"
        },
        {
            "name": "StorageStrategy",
            "applies_to": "Storage",
            "parameters": [
                {
                    "name": "marginalChargeCosts",
                    "type": "SingleValue"
                },
                {
                    "name": "marginalDischargeCosts",
                    "type": "SingleValue"
                }
            ]
        },
    ],
    "predefined_quantity_and_units": [
        {
            "id": "eb07bccb-203f-407e-af98-e687656a221d",
            "description": "Energy in GJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "GIGA",
            "unit": "JOULE"
        },
        {
            "id": "cc224fa0-4c45-46c0-9c6c-2dba44aaaacc",
            "description": "Energy in TJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "TERRA",
            "unit": "JOULE"
        },
        {
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1c",
            "description": "Power in VA",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE"
        },
        {
            "id": "6279c72a-228b-4c2c-8924-6b794c81778c",
            "description": "Reactive power in VAR",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE_REACTIVE"
        }
    ],
    "predefined_esdl_services": [
        {
            "id": "18d106cf-2af1-407d-8697-0dae23a0ac3e",
            "name": "Get PICO wind potential",
            "explanation": "This queries the Geodan wind potential service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/windturbinegebied",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "geo_query",
            "result": [
                {
                    "code": 200,
                    "action": "esdl"
                }
            ],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"}
                ]
            },
            "query_parameters": [
                {
                    "name": "Distance to buildings",
                    "description": "Minimum distance to the built environment (in meters)",
                    "parameter_name": "bebouwingsafstand",
                    "type": "integer"
                },
                {
                    "name": "Restriction",
                    "description": "",
                    "parameter_name": "restrictie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Preference",
                    "description": "",
                    "parameter_name": "preferentie",
                    "type": "multi-selection",
                    "possible_values": ["natuur", "vliegveld", "infrastructuur", "agrarisch", "turbines"]
                },
                {
                    "name": "Include geometry in ESDL",
                    "description": "",
                    "parameter_name": "geometrie",
                    "type": "boolean"
                }
            ]
        },
        {
            "id": "7f8722a9-669c-499d-8d75-4a1960e0429f",
            "name": "Create ETM scenario",
            "explanation": "This service sends the ESDL information to the ETM and tries to generate an ETM scenario out of it.",
            "url": "http://10.30.2.1:7001/api/v1/EnergySystem/",
            # "url": "http://localhost:5000/api/v1/EnergySystem/",
            "http_method": "post",
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            "type": "send_esdl",
            "body": "url_encoded",
            "query_parameters": [],
            "result": [
                {
                    "code": 200,
                    "action": "print"
                }
            ]
        },
        {
            "id": "3e3f3d4d-5600-4f1b-875d-4b630f2f8d01",
            "required_role": "geis",
            "name": "Query Energy Information Base service",
            "explanation": "This service queries multiple (open) energy data sources for a certain area",
            "url": "http://10.30.2.1:2000/api/EnergySystemBuilder/<area_scope>/<area_id>",
            "http_method": "get",
            "headers": {
                "Accept": "test/xml",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "geo_query",
            "result": [
                {
                    "code": 200,
                    "action": "esdl"
                }
            ],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                # "url_area_subscope": "<area_subscope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "district"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"}
                ],
                "area_subscopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "districts"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"}
                ]
            },
            "query_parameters": []
        },
        {
            "id": "193182ba-6805-4555-9f63-a0b2d5bb3d48",
            "required_role": "loadflow",
            "name": "Loadflow Calculation",
            "explanation": "This service runs a specific kind of loadflow calculation on the energysystem (DC loadflow, DC optimal loadflow, AC loadflow, AC optimal loadflow)",
            "url": "http://10.30.2.1:7002/api/v1/PandapowerLoadflow/<method>",
            "http_method": "post",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "ESDL Mapeditor/0.1"
            },
            "type": "simulation",
            "body": "url_encoded",
            "query_parameters": [
                {
                    "name": "Method",
                    "location": "url",
                    "description": "",
                    "parameter_name": "method",
                    "type": "selection",
                    "possible_values": ["dclf", "dcopf", "lf", "opf"]
                }
            ],
            "result": [
                {
                    "code": 200,
                    "action": "print"
                }
            ]
        }
    ]
}

"""
    "ESSIM": {
        "ESSIM_host": "http://geis.hesi.energy:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://geis.hesi.energy:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim",
        "start_datetime": "2015-01-01T00:00:00+0100",
        "end_datetime": "2016-01-01T00:00:00+0100"
    }
}
"""
