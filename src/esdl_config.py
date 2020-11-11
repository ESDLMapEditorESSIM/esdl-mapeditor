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

esdl_config = {
    "control_strategies": [
        {"name": "DrivenByDemand", "applies_to": "Conversion", "connect_to": "OutPort"},
        {"name": "DrivenBySupply", "applies_to": "Conversion", "connect_to": "InPort"},
        {
            "name": "StorageStrategy",
            "applies_to": "Storage",
            "parameters": [
                {"name": "marginalChargeCosts", "type": "SingleValue"},
                {"name": "marginalDischargeCosts", "type": "SingleValue"},
            ],
        },
    ],
    "predefined_quantity_and_units": [
        {
            "id": "eb07bccb-203f-407e-af98-e687656a221d",
            "description": "Energy in GJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "GIGA",
            "unit": "JOULE",
        },
        {
            "id": "cc224fa0-4c45-46c0-9c6c-2dba44aaaacc",
            "description": "Energy in TJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "TERRA",
            "unit": "JOULE",
        },
        {
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1b",
            "description": "Power in MW",
            "physicalQuantity": "POWER",
            "multiplier": "MEGA",
            "unit": "WATT"
        },
        {
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1c",
            "description": "Power in VA",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE",
        },
        {
            "id": "6279c72a-228b-4c2c-8924-6b794c81778c",
            "description": "Reactive power in VAR",
            "physicalQuantity": "POWER",
            "unit": "VOLT_AMPERE_REACTIVE",
        },
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
                "User-Agent": "ESDL Mapeditor/0.1",
            },
            "type": "geo_query",
            "result": [{"code": 200, "action": "esdl"}],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"},
                ],
            },
            "query_parameters": [
                {
                    "name": "Distance to buildings",
                    "description": "Minimum distance to the built environment (in meters)",
                    "parameter_name": "bebouwingsafstand",
                    "type": "integer",
                },
                {
                    "name": "Restriction",
                    "description": "",
                    "parameter_name": "restrictie",
                    "type": "multi-selection",
                    "possible_values": [
                        "natuur",
                        "vliegveld",
                        "infrastructuur",
                        "agrarisch",
                        "turbines",
                    ],
                },
                {
                    "name": "Preference",
                    "description": "",
                    "parameter_name": "preferentie",
                    "type": "multi-selection",
                    "possible_values": [
                        "natuur",
                        "vliegveld",
                        "infrastructuur",
                        "agrarisch",
                        "turbines",
                    ],
                },
                {
                    "name": "Include geometry in ESDL",
                    "description": "",
                    "parameter_name": "geometrie",
                    "type": "boolean",
                },
            ],
        },
        {
            "id": "50fa716f-f3b0-464c-bf9f-1acffb24f76a",
            "name": "Get PICO solar field potential",
            "explanation": "This queries the Geodan solar field potential service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/zonneveldgebied",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1",
            },
            "type": "geo_query",
            "result": [{"code": 200, "action": "esdl"}],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"},
                ],
            },
            "query_parameters": [
                {
                    "name": "Distance to buildings (m)",
                    "description": "Minimum distance to the built environment (in meters)",
                    "parameter_name": "bebouwingsafstand",
                    "type": "integer",
                },
                {
                    "name": "Restriction",
                    "description": "",
                    "parameter_name": "restrictie",
                    "type": "multi-selection",
                    "possible_values": [
                        "natuur",
                        "vliegveld",
                        "infrastructuur",
                        "agrarisch",
                        "turbines",
                    ],
                },
                {
                    "name": "Preference",
                    "description": "",
                    "parameter_name": "preferentie",
                    "type": "multi-selection",
                    "possible_values": [
                        "natuur",
                        "vliegveld",
                        "infrastructuur",
                        "agrarisch",
                        "turbines",
                    ],
                },
                {
                    "name": "Include geometry in ESDL",
                    "description": "",
                    "parameter_name": "geometrie",
                    "type": "boolean",
                },
            ],
        },
        {
            "id": "c1c209e9-67ff-4201-81f6-0dd7a185ff06",
            "name": "Get PICO rooftop solar potential",
            "explanation": "This queries the Geodan rooftop solar potential service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/zonopdak?geometrie=false",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1",
            },
            "type": "geo_query",
            "result": [{"code": 200, "action": "esdl"}],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "provincies"},
                    {"scope": "REGION", "url_value": "resgebieden"},
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"},
                ],
            },
            "query_parameters": []
        },
        {
            "id": "42c584b1-43c1-4369-9001-c89ba80d8370",
            "name": "Get PICO Startanalyse results",
            "explanation": "This queries the Geodan start analyse service for a certain area",
            "url": "https://pico.geodan.nl/pico/api/v1/<area_scope>/<area_id>/startanalyse",
            "http_method": "get",
            "headers": {
                "Accept": "application/esdl+xml",
                "User-Agent": "ESDL Mapeditor/0.1",
            },
            "type": "geo_query",
            "result": [{"code": 200, "action": "esdl"}],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "MUNICIPALITY", "url_value": "gemeenten"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "buurt"},
                ],
            },
            "query_parameters": [
                {
                    "name": "Strategie",
                    "description": "",
                    "parameter_name": "strategie",
                    "type": "selection",
                    "possible_values": [
                        "S1a",
                        "S1b",
                        "S2a",
                        "S2b",
                        "S2c",
                        "S2d",
                        "S3a",
                        "S3b",
                        "S3c",
                        "S3d",
                        "S4a",
                        "S5a",
                    ],
                }
            ],
        },
        {
            "id": "7f8722a9-669c-499d-8d75-4a1960e0429f",
            "name": "Create ETM scenario",
            "explanation": "This service sends the ESDL information to the ETM and tries to generate an ETM scenario out of it.",
            "url": "http://beta-esdl.energytransitionmodel.com/api/v1/EnergySystem/",
            # "url": "http://localhost:5000/api/v1/EnergySystem/",
            "http_method": "post",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "type": "send_esdl",
            "body": "url_encoded",
            "send_email_in_post_body_parameter": "account",
            "query_parameters": [
                {
                    "name": "Environment",
                    "description": "",
                    "parameter_name": "environment",
                    "location": "body",
                    "type": "selection",
                    "possible_values": [
                        "pro",
                        "beta"
                    ],
                }
            ],
            "result": [{"code": 200, "action": "print"}],
        }
    ]
}
