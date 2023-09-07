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
import os

from src.settings import heatnetwork_dispatcher_config

EPS_WEB_HOST = os.getenv("EPS_WEB_HOST", "http://epsweb:3401")
ESDL_AGGREGATOR_HOST = os.getenv("ESDL_AGGREGATOR_HOST", "http://esdl-aggregator:3490")
HEATNETWORK_DISPATCHER_URL = heatnetwork_dispatcher_config["host"] + ":" + str(heatnetwork_dispatcher_config["port"])

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
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1a",
            "description": "Power in kW",
            "physicalQuantity": "POWER",
            "multiplier": "KILO",
            "unit": "WATT",
        },
        {
            "id": "e9405fc8-5e57-4df5-8584-4babee7cdf1b",
            "description": "Power in MW",
            "physicalQuantity": "POWER",
            "multiplier": "MEGA",
            "unit": "WATT",
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
            "query_parameters": [],
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
                    "possible_values": ["pro", "beta"],
                }
            ],
            "result": [{"code": 200, "action": "print"}],
        },
        {
            "id": "912c4a2b-8eee-46f7-a225-87c5f85e645f",
            "name": "ESDL Validator",
            "explanation": "This service allows you validate an ESDL against a certain schema",
            "type": "vueworkflow",
            "workflow": [
                {
                    "name": "Select schema",
                    "description": "",
                    "type": "select-query",
                    "multiple": False,
                    "source": {
                        "url": "http://10.30.2.1:3011/schema",
                        "http_method": "get",
                        "label_fields": ["name"],
                        "value_field": "id",
                    },
                    "target_variable": "schema",
                    "next_step": 1,
                },
                {
                    "name": "Schema validation",
                    "description": "",
                    "type": "service",
                    "state_params": {"schemas": "schema.id"},
                    "service": {
                        "id": "64c9d1a2-c92a-46ed-a7e4-9931971cbb27",
                        "name": "Validate ESDL against scehema",
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/0.1",
                            "Content-Type": "application/xml",
                        },
                        "url": "http://10.30.2.1:3011/validationToMessages/",
                        "http_method": "post",
                        "type": "send_esdl",
                        "query_parameters": [
                            {
                                "name": "Schemas",
                                "description": "ID of the schema to validate this ESDL against",
                                "parameter_name": "schemas",
                            }
                        ],
                        "body": "",
                        "result": [{"code": 200, "action": "asset_feedback"}],
                        "with_jwt_token": False,
                        "state_params": True,
                    },
                },
            ],
        },
        {
                "id": "123451a2-c92a-46ed-a7e4-993197712345",
                "name": "Start Heat Network calculation",
                "description": "Submit a heat network to the calculation service",
                "headers": {
                    "User-Agent": "ESDL Mapeditor/1.0",
                    "Content-Type": "application/json"
                },
                "url": f"{HEATNETWORK_DISPATCHER_URL}/job/",
                "http_method": "post",
                "type": "send_esdl",
                "send_email_in_post_body_parameter": "user_name",
                "show_query_params": True,
                "query_parameters": [
                    {
                        "type": "string",
                        "name": "Scenario name",
                        "description": "Give this scenario a unique name",
                        "parameter_name": "job_name",
                        "location": "body"
                    },
                    {
                        "type": "selection",
                        "name": "Workflow type",
                        "description": "Select the calculation type to execute",
                        "parameter_name": "work_flow_type",
                        "location": "body",
                        "possible_values": [
                            "GROWTH_OPTIMIZER"
                        ]
                    }
                ],
                "body_config": {
                    "type": "json",
                    "parameters": [
                        {
                            "type": "esdl",
                            "encoding": "base64_encoded",
                            "parameter": "input_esdl"
                        }
                    ]
                },
                "body": "base64_encoded",
                "result": [
                    {
                        "code": 200,
                        "action": "show_message",
                        "message": "Calculation successfully submitted."
                    },
                    {
                        "code": 404,
                        "action": "show_message",
                        "message": "Error in submitting calculation."
                    }
                ],
                "with_jwt_token": True,
                "state_params": False
            },
        {
            "id": "x12c4a2b-8eee-46f7-a225-87c5f85e645f",
            "name": "Heat Network calculation results",
            "explanation": "This service allows you to view results from heat network simulations and optimizations",
            "type": "vueworkflow",
            "workflow": [
                {
                    "name": "Results overview",
                    "description": "",
                    "type": "table-query",
                    "source": {
                        "url": HEATNETWORK_DISPATCHER_URL + "/job/user/{username}",
                        "http_method": "get",
                        "request_params": {"username": "session.email"},
                        "columns": [
                            {
                                "dataIndex": "job_name",
                                "title": "Name",
                                "ellipsis": True
                            },
                            {
                                "dataIndex": "status",
                                "title": "Status",
                                "align": "center",
                                "slots": {
                                    "customRender": "tags"
                                }
                            },
                            {
                                "dataIndex": "stopped_at",
                                "title": "Finished at",
                                "formatter": "formatDate",
                                "defaultSortOrder": "descend"
                            }
                        ],
                        "actions": [
                            {
                                "title": "Load result",
                                "next_step": 2
                            },
                            {
                                "title": "Show log",
                                "next_step": 3
                            },
                            {
                                "title": "Delete",
                                "next_step": 4
                            }
                        ],
                        "value_field": "job_id"
                    },
                    "target_variable": "job",
                    "with_jwt_token": True,
                    "next_step": 0
                },
                {
                    "name": "Result selected",
                    "state_params": {
                        "job_id": "job.job_id"
                    },
                    "description": "How would you like to proceed?",
                    "type": "choice",
                    "options": [
                        {
                            "name": "Load ESDL result",
                            "description": "Load the results as ESDL on the map.",
                            "type": "primary",
                            "next_step": 2
                        },
                        {
                            "name": "View log output",
                            "description": "View the log output of this execution.",
                            "type": "default",
                            "next_step": 3
                        }
                    ]
                },
                {
                    "name": "Load ESDL",
                    "description": "Loads the result in the ESDL MapEditor",
                    "type": "service",
                    "state_params": {
                        "job_id": "job.job_id"
                    },
                    "service": {
                        "id": "x1c9d1a2-c92a-46ed-a7e4-9931971cbb27",
                        "name": "Load ESDL results",
                        "description": "The results should have been loaded in the MapEditor",
                        "button_label": "Go back to results",
                        "auto": True,
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/0.1",
                            "Content-Type": "application/xml"
                        },
                        "url": HEATNETWORK_DISPATCHER_URL + "/job/<job_id>/result",
                        "http_method": "get",
                        "type": "",
                        "query_parameters": [
                            {
                                "name": "Job id",
                                "description": "Job id",
                                "parameter_name": "job_id",
                                "location": "url"
                            }
                        ],
                        "body": "",
                        "result": [
                            {
                                "code": 200,
                                "action": "esdl",
                                "encoding": "base64_encoded",
                                "json_field": "output_esdl"
                            }
                        ],
                        "with_jwt_token": True,
                        "state_params": True,
                        "next_step": 0
                    }
                },
                {
                    "name": "Show log file",
                    "type": "service",
                    "state_params": {
                        "job_id": "job.job_id"
                    },
                    "service": {
                        "id": "x5c9d1a2-c92a-46ed-a7e4-9931971cbb27",
                        "name": "Request the log file",
                        "description": "The logfile is shown below:",
                        "button_label": "Go back",
                        "auto": True,
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/0.1",
                            "Content-Type": "application/xml"
                        },
                        "url": HEATNETWORK_DISPATCHER_URL + "/job/<job_id>/logs",
                        "http_method": "get",
                        "type": "",
                        "query_parameters": [
                            {
                                "name": "Job id",
                                "description": "Job id",
                                "parameter_name": "job_id",
                                "location": "url"
                            }
                        ],
                        "body": "",
                        "result": [
                            {
                                "code": 200,
                                "action": "show_message",
                                "message": "Show log",
                                "json_field": "logs"
                            }
                        ],
                        "with_jwt_token": True,
                        "state_params": True,
                        "next_step": 0
                    }
                },
                {
                    "name": "Delete result",
                    "description": "Delete the selected result",
                    "type": "service",
                    "state_params": {
                        "job_id": "job.job_id"
                    },
                    "service": {
                        "id": "x9c9d1a2-c92a-46ed-a7e4-9931971cbb2e",
                        "name": "Delete the result",
                        "description": "Press the button below to delete the result",
                        "button_label": "Delete result",
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/1.0",
                            "Content-Type": "application/json"
                        },
                        "url": HEATNETWORK_DISPATCHER_URL + "/job/<job_id>",
                        "http_method": "delete",
                        "type": "",
                        "query_parameters": [
                            {
                                "name": "Job id",
                                "description": "Job id",
                                "parameter_name": "job_id",
                                "location": "url"
                            }
                        ],
                        "body": "",
                        "result": [
                            {
                                "code": 200,
                                "action": "show_message",
                                "message": "Result succesfully removed"
                            }
                        ],
                        "with_jwt_token": True,
                        "state_params": True,
                        "next_step": 0
                    }
                }
            ]
        }

    ],
    "role_based_esdl_services": {
        "eps": [
            {
                "id": "9951c271-f9b6-4c4e-873f-b309dff19e03",
                "name": "Energy Potential Scan",
                "explanation": "This workflow allows you to run the EPS web service and view the EPS results.",
                "type": "vueworkflow",
                "workflow": [
                    {
                        # 0
                        "name": "Begin",
                        "description": "How would you like to proceed?",
                        "type": "choice",
                        "options": [
                            {
                                "name": "Create a new EPS project",
                                "next_step": 1,
                                "type": "primary",
                            },
                            {
                                "name": "Adjust EPS input",
                                "next_step": 13,
                                "type": "default",
                            },
                            {"name": "Run EPS", "next_step": 4, "type": "primary"},
                            {
                                "name": "Inspect EPS results",
                                "next_step": 6,
                                "type": "primary",
                            },
                            {
                                "name": "Aggregate ESDL buildings for ESSIM",
                                "next_step": 12,
                                "type": "default",
                            },
                        ],
                    },
                    {
                        # 1
                        "name": "Create Project",
                        "description": "",
                        "type": "custom",
                        "component": "eps-create-project",
                        "url": f"{EPS_WEB_HOST}/api/projects/",
                        "next_step": 0,
                    },
                    {
                        # 2
                        "name": "Select existing project",
                        "description": "Please select the project for which you would like to upload a project file.",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": f"{EPS_WEB_HOST}/api/projects/",
                            "http_method": "get",
                            "choices_attr": "projects",
                            "label_fields": ["name"],
                            "value_field": "id",
                        },
                        "target_variable": "project_id",
                        "next_step": 3,
                    },
                    {
                        # 3
                        "name": "Upload project file",
                        "description": "Note: When uploading a project file with the same name as a previous project "
                        "file, the previous file will be overwritten!",
                        "type": "upload_file",
                        "target": {
                            "url": f"{EPS_WEB_HOST}/api/uploads/",
                            "request_params": {"project_id": "project.id"},
                            "response_params": {"name": "file_name"},
                        },
                        "next_step": 0,
                    },
                    {
                        # 4
                        "name": "Select existing project",
                        "description": "",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": f"{EPS_WEB_HOST}/api/projects/",
                            "http_method": "get",
                            "choices_attr": "projects",
                            "label_fields": ["name"],
                            "value_field": "id",
                        },
                        "target_variable": "project",
                        "next_step": 5,
                    },
                    {
                        # 5
                        "name": "Run the EPS",
                        "description": "",
                        "type": "custom",
                        "component": "eps-service",
                        "url": f"{EPS_WEB_HOST}/api/eps/",
                        "target": {
                            "request_params": {"project_id": "project.id"},
                            "user_response_spec": {
                                "0": {"message": "Failed starting the EPS."},
                                "200": {
                                    "message": "EPS started successfully! It can take up to 45 minutes for the EPS to complete. When it is complete, the results can be found under 'Inspect results'."
                                },
                                "429": {
                                    "message": "It is currently busy on the server. We cannot start an EPS execution "
                                    "at this time. Please try again at a later time. "
                                },
                            },
                        },
                    },
                    {
                        # 6
                        "name": "EPS execution",
                        "description": "",
                        "label": "Select EPS execution to inspect:",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": f"{EPS_WEB_HOST}/api/eps/",
                            "http_method": "get",
                            "choices_attr": "executions",
                            "label_fields": ["project", "id", "success"],
                            "value_field": "id",
                        },
                        "target_variable": "execution",
                        "next_step": 7,
                    },
                    {
                        # 7
                        "name": "Execution selected",
                        "description": "How would you like to proceed?",
                        "type": "choice",
                        "options": [
                            {
                                "name": "Load EPS result",
                                "description": "Load the results as ESDL on the map. Your current layers will be overwritten!",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 10,
                            },
                            {
                                "name": "Inspect EPS results",
                                "type": "default",
                                "enable_if_state": "execution.success",
                                "next_step": 11,
                            },
                            {
                                "name": "Download project file",
                                "type": "default",
                                "next_step": 9,
                            },
                            # {
                            #     "name": "View progress",
                            #     "type": "default",
                            #     "disable_if_state": "execution.finished_on",
                            #     "next_step": 8,
                            # },
                        ],
                    },
                    {
                        # 8
                        "name": "EPS execution progress",
                        "description": "",
                        "type": "progress",
                        "refresh": 30,
                        "source": {
                            "url": f"{EPS_WEB_HOST}/api/eps/progress",
                            "request_params": {"execution_id": "execution.id"},
                            "progress_field": "latest_progress",
                            "message_field": "latest_message",
                        },
                    },
                    {
                        # 9
                        "name": "Download project file",
                        "description": "The project file that was used as input to perform this EPS analysis can be "
                        "downloaded here.",
                        "type": "download_file",
                        "source": {
                            "url": EPS_WEB_HOST + "/api/eps/{execution_id}/input",
                            "request_params": {"execution_id": "execution.id"},
                        },
                    },
                    {
                        # 10
                        "name": "Load EPS results",
                        "description": "Please wait a moment while we load an ESDL with the EPS results. When the EPS "
                        "is loaded, please continue.",
                        "type": "service",
                        "state_params": {"execution_id": "execution.id"},
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b12",
                            "name": "Visualize EPS",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/eps/<execution_id>/esdl",
                            "auto": True,
                            "clearLayers": True,
                            "http_method": "get",
                            "type": "",
                            "result": [{"code": 200, "action": "esdl"}],
                            "query_parameters": [
                                {
                                    "name": "File Name",
                                    "location": "url",
                                    "parameter_name": "execution_id",
                                }
                            ],
                            "with_jwt_token": True,
                            "state_params": True,
                        }
                    },
                    {
                        # 11
                        "name": "Inspect EPS results",
                        "description": "",
                        "type": "custom",
                        "component": "eps-inspect-result",
                        "custom_data": {
                            "url": EPS_WEB_HOST
                            + "/api/eps/{execution_id}/pand/{pand_bagid}"
                        },
                    },
                    {
                        # 12
                        "name": "Aggregate ESDL buildings for ESSIM",
                        "description": "The ESDL generated by the EPS contains every building individually. This "
                        "causes unnecessarily long processing time if buildings have the same "
                        "profiles. With this service, similar buildings are combined into aggregated "
                        "buildings, which will make it faster to run ESSIM and easier to interpret "
                        "results. Note: This will create a new ESDL layer.",
                        "type": "service",
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b13",
                            "name": "Aggregate ESDL buildings for ESSIM",
                            "headers": {
                                "Content-Type": "application/json",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "type": "send_esdl_json",
                            "body": "base64_encoded",
                            "url": f"{ESDL_AGGREGATOR_HOST}/aggregate",
                            "http_method": "post",
                            "result": [{"code": 200, "action": "esdl"}],
                            "with_jwt_token": True,
                        },
                        "next_step": 0,
                    },
                    {
                        # 13
                        "name": "Adjust EPS input",
                        "description": "",
                        "type": "choice",
                        "options": [
                            {
                                "name": "Download project file",
                                "description": "If you want to inspect the KvK data or modify input data, you can download a project file.",
                                "next_step": 14,
                                "type": "primary",
                            },
                            {
                                "name": "Upload project file",
                                "description": "A project file can be uploaded to serve as input for a new EPS run.",
                                "next_step": 2,
                                "type": "primary",
                            },
                        ],
                    },
                    {
                        # 14
                        "name": "Select existing project",
                        "description": "Please select the project for which you would like to download a project file.",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": f"{EPS_WEB_HOST}/api/projects/",
                            "http_method": "get",
                            "choices_attr": "projects",
                            "label_fields": ["name"],
                            "value_field": "id",
                        },
                        "target_variable": "project",
                        "next_step": 15,
                    },
                    {
                        # 15
                        "name": "Select project file",
                        "description": "Please select the project file you would like to download.",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": EPS_WEB_HOST + "/api/projects/{project_id}/files",
                            "request_params": {"project_id": "project.id"},
                            "http_method": "get",
                            "choices_attr": "file_names",
                            "label_fields": ["name"],
                            "value_field": "id",
                        },
                        "target_variable": "file_name",
                        "next_step": 16,
                    },
                    {
                        # 16
                        "name": "Download project file",
                        "description": "By clicking the button below you can download the selected project file.",
                        "type": "download_file",
                        "source": {
                            "url": EPS_WEB_HOST
                            + "/api/projects/{project_id}/files/{file_name}",
                            "request_params": {
                                "project_id": "project.id",
                                "file_name": "file_name.id",
                            },
                        },
                        "next_step": 0,
                    },
                ],
            }
        ]
    },
}
