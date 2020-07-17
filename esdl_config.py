"""
    "ESSIM": {
        "ESSIM_host": "http://geis.hesi.energy:8112",
        "ESSIM_path": "/essim/simulation",
        "influxURL": "http://geis.hesi.energy:8086",
        "grafanaURL": "http://geis.hesi.energy:3000",
        "user": "essim",
        "start_datetime": "2015-01-01T00:00:00.000000+0100",
        "end_datetime": "2016-01-01T00:00:00.000000+0100"
    }
}
"""

# EPS_API_URL = 'http://localhost:3400'
EPS_API_URL = 'https://eps.hesi.energy'


esdl_config = {
    "profile_database": {
        "host": "http://10.30.2.1",
        "port": "8086",
        "database": "energy_profiles",
        "filters": "",
    },
    "influxdb_profile_data": [
    ],
    "energy_carriers": [
    ],
    "energy_carriers": [],
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
            "url": "http://10.30.2.1:7001/api/v1/EnergySystem/",
            # "url": "http://localhost:5000/api/v1/EnergySystem/",
            "http_method": "post",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "type": "send_esdl",
            "body": "url_encoded",
            "query_parameters": [],
            "result": [{"code": 200, "action": "print"}],
        },
        {
            "id": "3e3f3d4d-5600-4f1b-875d-4b630f2f8d01",
            "required_role": "geis",
            "name": "Query Energy Information Base service",
            "explanation": "This service queries multiple (open) energy data sources for a certain area",
            "url": "http://10.30.2.1:2000/api/EnergySystemBuilder/<area_scope>/<area_id>",
            "http_method": "get",
            "headers": {"Accept": "test/xml", "User-Agent": "ESDL Mapeditor/0.1"},
            "type": "geo_query",
            "result": [{"code": 200, "action": "esdl"}],
            "geographical_scope": {
                "url_area_scope": "<area_scope>",
                # "url_area_subscope": "<area_subscope>",
                "url_area_id": "<area_id>",
                "area_scopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "district"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"},
                ],
                "area_subscopes": [
                    {"scope": "PROVINCE", "url_value": "province"},
                    {"scope": "REGION", "url_value": "region"},
                    {"scope": "MUNICIPALITY", "url_value": "municipality"},
                    {"scope": "DISTRICT", "url_value": "districts"},
                    {"scope": "NEIGHBOURHOOD", "url_value": "neighbourhood"},
                ],
            },
            "query_parameters": [],
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
                "User-Agent": "ESDL Mapeditor/0.1",
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
                    "possible_values": ["dclf", "dcopf", "lf", "opf"],
                }
            ],
            "result": [{"code": 200, "action": "print"}],
        },
        {
            "id": "d2ecfa3a-f0cd-4091-a78e-2675801dfcb1",
            "required_role": "urban-strategy",
            "name": "Urban Strategy Charging Stations",
            "explanation": "This service queries the US database for Charging Station information",
            "url": "http://10.30.2.1:7003/api/v1/ChargingStations",
            #            "url": "http://localhost:5000/api/v1/ChargingStations",
            "http_method": "get",
            "headers": {
                "Accept": "application/json",
                "User-Agent": "ESDL Mapeditor/0.1",
            },
            "type": "",
            "query_parameters": [],
            "result": [{"code": 200, "action": "add_assets"}],
        },
        {
            "id": "d0239a80-5ec5-4940-b6df-4d431f7746e8",
            "required_role": "eps",
            "name": "Energy Potential Scan - Run",
            "explanation": "This service allows you to run the EPS web service.",
            "type": "workflow",
            "workflow": [
                {
                    # 0
                    "name": "Begin",
                    "description": "How would you like to proceed?",
                    "type": "choice",
                    "options": [
                        {"name": "Create a new EPS project", "next_step": 1},
                        {"name": "Upload file for existing project", "next_step": 5},
                        {"name": "Run EPS for uploaded file", "next_step": 7},
                    ],
                },
                {
                    # 1
                    "name": "Create Project",
                    "description": "",
                    "type": "form",
                    "fields": [
                        {
                            "type": "text",
                            "target_variable": "project_name",
                            "description": "Project name",
                        },
                    ],
                    "previous_step": 0,
                    "next_step": 2,
                },
                {
                    # 2
                    "name": "Business Parks",
                    "description": "These business parks come from the dataset 'Landelijke informatie IBIS Bedrijventerreinen'. Please select one or more for which the EPS should be executed.",
                    "type": "select-query",
                    "multiple": True,
                    "source": {
                        "url": f"{EPS_API_URL}/api/business-parks/",
                        "http_method": "get",
                        "choices_attr": "business_parks",
                        "label_fields": ["location", "rin_id", "name"],
                        "value_field": "rin_id",
                    },
                    "target_variable": "selected_parks",
                    "next_step": 3,
                },
                {
                    # 3
                    "name": "Show Business Parks",
                    "description": "Show the selected business parks on the map, or just continue.",
                    "type": "call_js_function",
                    "label": "Show on map",
                    "dom_elements": {
                        "rin_list": "selected_parks",
                    },
                    "js_function": "get_ibis_info",
                    "parameters": [False],
                    "previous_step": 2,
                    "next_step": 4,
                },
                {
                    # 4
                    "name": "Download address list from the KvK",
                    "description": "For downloading this file the KvK API is queried, which could incur additional costs.",
                    "type": "download_file",
                    "url": f"{EPS_API_URL}/api/kvk/download_project_file/",
                    "request_params": {
                        "project_name": "project_name",
                        "rin_ids": "selected_parks",
                    },
                    "previous_step": 3,
                },
                {
                    # 5
                    "name": "Select existing project",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": f"{EPS_API_URL}/api/projects/",
                        "http_method": "get",
                        "choices_attr": "projects",
                        "label_fields": ["name"],
                        "value_field": "id",
                    },
                    "target_variable": "project_id",
                    "previous_step": 0,
                    "next_step": 6,
                },
                {
                    # 6
                    "name": "Upload EPS data input file",
                    "description": "",
                    "type": "upload_file",
                    "url": f"{EPS_API_URL}/api/uploads/",
                    "request_params": {"project_id": "project_id",},
                    "previous_step": 5,
                },
                {
                    # 7
                    "name": "Select existing project",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": f"{EPS_API_URL}/api/projects/",
                        "http_method": "get",
                        "choices_attr": "projects",
                        "label_fields": ["name"],
                        "value_field": "id",
                    },
                    "target_variable": "project_id",
                    "previous_step": 0,
                    "next_step": 8,
                },
                {
                    # 8
                    "name": "Select data file",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": f"{EPS_API_URL}/api/uploads/",
                        "http_method": "get",
                        "choices_attr": "files",
                        "label_fields": ["name"],
                        "value_field": "name",
                    },
                    "request_params": {"project_id": "project_id",},
                    "target_variable": "file_name",
                    "previous_step": 7,
                    "next_step": 9,
                },
                {
                    # 9
                    "name": "Run EPS",
                    "description": "",
                    "type": "service",
                    "state_params": {
                        "project_id": "project_id",
                        "file_name": "file_name",
                    },
                    "service": {
                        "id": "a8e42361-6e61-4393-940f-ec6964557433",
                        "name": "Run the EPS",
                        "type": "json",
                        "url": f"{EPS_API_URL}/api/eps/",
                        "http_method": "post",
                        "headers": {"Content-Type": "application/json"},
                        "with_jwt_token": True,
                        "query_parameters": [
                            {
                                "name": "Project ID",
                                "location": "body",
                                "parameter_name": "project_id",
                            },
                            {
                                "name": "File Name",
                                "location": "body",
                                "parameter_name": "file_name",
                            },
                        ],
                        "state_params": True,
                        "result": [
                            {
                                "code": 200,
                                "action": "show_message",
                                "message": "EPS started successfully!",
                            }
                        ],
                    },
                    "previous_step": 8,
                },
            ],
        },
        {
            "id": "9951c271-f9b6-4c4e-873f-b309dff19e03",
            "required_role": "eps",
            "name": "Energy Potential Scan - Results",
            "explanation": "This service allows you to view the EPS results.",
            "type": "workflow",
            "workflow": [
                {
                    # 0
                    "name": "Begin",
                    "description": "How would you like to proceed?",
                    "type": "choice",
                    "options": [
                        {"name": "View progress of EPS execution", "next_step": 1},
                        {"name": "Visualize EPS result", "next_step": 3},
                    ],
                },
                {
                    # 1
                    "name": "Select EPS execution to inspect",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": f"{EPS_API_URL}/api/eps/",
                        "http_method": "get",
                        "choices_attr": "executions",
                        "label_fields": ["project", "id", "name"],
                        "value_field": "id",
                    },
                    "target_variable": "execution_id",
                    "previous_step": 0,
                    "next_step": 2,
                },
                {
                    # 2
                    "name": "EPS execution progress",
                    "description": "",
                    "type": "get_data",
                    "url": f"{EPS_API_URL}/api/eps/progress",
                    "request_params": {"execution_id": "execution_id",},
                    "refresh": 30,
                    "fields": [
                        {"name": "id"},
                        {"name": "created"},
                        {"name": "finished_on"},
                        {"name": "project"},
                        {"name": "success"},
                        {
                            "name": "logs",
                            "fields": [{"name": "progress"}, {"name": "message"}],
                        },
                    ],
                    "previous_step": 1,
                },
                {
                    # 3
                    "name": "Select EPS execution to visualize",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": f"{EPS_API_URL}/api/eps/?success=true",
                        "http_method": "get",
                        "choices_attr": "executions",
                        "label_fields": ["project", "id", "name"],
                        "value_field": "id",
                    },
                    "target_variable": "execution_id",
                    "previous_step": 0,
                    "next_step": 4,
                },
                {
                    # 8
                    "name": "Visualize EPS",
                    "description": "",
                    "type": "service",
                    "state_params": {"execution_id": "execution_id",},
                    "service": {
                        "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b12",
                        "name": "Visualize EPS",
                        "headers": {
                            "Accept": "application/esdl+xml",
                            "User-Agent": "ESDL Mapeditor/0.1",
                        },
                        "url": f"{EPS_API_URL}/api/eps/<execution_id>/esdl",
                        "http_method": "get",
                        "type": "",
                        "result": [{"code": 200, "action": "esdl"}],
                        "query_parameters": [
                            {
                                "name": "Execution ID",
                                "location": "url",
                                "parameter_name": "execution_id",
                            }
                        ],
                        "with_jwt_token": True,
                        "state_params": True,
                    },
                    "previous_step": 3,
                },
            ],
        },
    ],
}
