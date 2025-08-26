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

EPS_WEB_HOST = os.getenv("EPS_WEB_HOST", "http://epsweb:3401")
ESDL_AGGREGATOR_HOST = os.getenv("ESDL_AGGREGATOR_HOST", "http://esdl-aggregator:3490")
ESDL_UPLOAD_PROFILES_HOST = os.getenv("ESDL_UPLOAD_PROFILES_HOST", "http://mapeditor-upload-profiles:4003")
ESDL_COST_SERVICE_HOST = os.getenv("ESDL_COST_SERVICE_HOST", "http://mapeditor-cost-service:4004")
FLEX_BACKEND_HOST = os.getenv("FLEX_BACKEND_HOST", "http://localhost:7200")
FLEX_FRONTEND_HOST = os.getenv("FLEX_FRONTEND_HOST", "http://localhost:7201")
ESSIM_BACKEND_HOST = os.getenv("ESSIM_BACKEND_HOST", "http://essim-engine:8112")

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
            "id": "12c481c0-f81e-49b6-9767-90457684d24a",
            "description": "Energy in kWh",
            "physicalQuantity": "ENERGY",
            "multiplier": "KILO",
            "unit": "WATTHOUR",
        },
        {
            "id": "93aa23ea-4c5d-4969-97d4-2a4b2720e523",
            "description": "Energy in MWh",
            "physicalQuantity": "ENERGY",
            "multiplier": "MEGA",
            "unit": "WATTHOUR",
        },
        {
            "id": "6fcd2303-b504-4939-8312-8cba25749265",
            "description": "Energy in GWh",
            "physicalQuantity": "ENERGY",
            "multiplier": "GIGA",
            "unit": "WATTHOUR",
        },
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
            "id": "x12c4a2b-8eee-46f7-a225-87c5f85e666a",
            "name": "Essim",
            "explanation": "Run, view and manage Essim calculations",
            "type": "vueworkflow",
            "hide_step_history": True,
            "workflow": [
                {
                    "id": "base_steps_with_table",
                    "type": "composite",
                    "config": {
                        "step_ids": [
                            "select_name_and_time_step",
                            "select_simulation_period",
                            "select_custom_period",
                            "select_kpis",
                            "start_run",
                            "runs_table",
                        ]
                    },
                    "next_step": "base_steps_with_table",
                },
                {
                    "id": "select_name_and_time_step",
                    "name": "New Run",
                    "type": "json-form2",
                    "data": {
                        "from_config": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "run_name": {"type": "string", "minLength": 3, "title": "Name"},
                                    "time_step": {
                                        "type": "string",
                                        "oneOf": [
                                            {"const": "1h", "title": "1 hour"},
                                            {"const": "15m", "title": "15 minutes"},
                                        ],
                                    },
                                },
                                "required": ["run_name", "time_step"],
                            },
                            "uischema": {
                                "elements": [
                                    {"scope": "#/properties/run_name", "type": "Control"},
                                    {"scope": "#/properties/time_step", "type": "Control"},
                                ],
                                "type": "VerticalLayout",
                            },
                            "formData": {"time_step": "1h"},
                        },
                        "to_state": {},
                    },
                    "next_step": "base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "select_simulation_period",
                    "name": "",
                    "description": "Please select the simulation period:",
                    "type": "select",
                    "config": {
                        "placeholder": "Select simulation period",
                        "multiple": False,
                        "label_fields": ["description"],
                        "value_field": "id",
                    },
                    "data": {
                        "from_config": [
                            {
                                "id": "year2015",
                                "description": "Year 2015",
                                "formData": {
                                    "start_time": "2015-01-01T00:00:00+0100",
                                    "end_time": "2016-01-01T00:00:00+0100",
                                },
                                "schema": {
                                    "properties": {
                                        "start_time": {"format": "date-time", "type": "string"},
                                        "end_time": {"format": "date-time", "type": "string"},
                                    },
                                    "required": ["start_time", "end_time"],
                                    "type": "object",
                                },
                                "uischema": {
                                    "elements": [
                                        {
                                            "scope": "#/properties/start_time",
                                            "type": "Control",
                                            "options": {"readonly": True},
                                        },
                                        {
                                            "scope": "#/properties/end_time",
                                            "type": "Control",
                                            "options": {"readonly": True},
                                        },
                                    ],
                                    "type": "VerticalLayout",
                                },
                            },
                            {
                                "id": "year2019",
                                "description": "Year 2019",
                                "formData": {
                                    "start_time": "2019-01-01T00:00:00+0100",
                                    "end_time": "2020-01-01T00:00:00+0100",
                                },
                                "schema": {
                                    "properties": {
                                        "start_time": {"format": "date-time", "type": "string"},
                                        "end_time": {"format": "date-time", "type": "string"},
                                    },
                                    "required": ["start_time", "end_time"],
                                    "type": "object",
                                },
                                "uischema": {
                                    "elements": [
                                        {
                                            "scope": "#/properties/start_time",
                                            "type": "Control",
                                            "options": {"readonly": True},
                                        },
                                        {
                                            "scope": "#/properties/end_time",
                                            "type": "Control",
                                            "options": {"readonly": True},
                                        },
                                    ],
                                    "type": "VerticalLayout",
                                },
                            },
                            {
                                "id": "custom",
                                "description": "custom period",
                                "formData": {},
                                "schema": {
                                    "properties": {
                                        "start_time": {"format": "date-time", "type": "string"},
                                        "end_time": {"format": "date-time", "type": "string"},
                                    },
                                    "required": ["start_time", "end_time"],
                                    "type": "object",
                                },
                                "uischema": {
                                    "elements": [
                                        {"scope": "#/properties/start_time", "type": "Control"},
                                        {"scope": "#/properties/end_time", "type": "Control"},
                                    ],
                                    "type": "VerticalLayout",
                                },
                            },
                        ],
                        "to_state": {},
                        "output_wrapper_variable": "selected_simulation_period",
                    },
                    "next_step": "base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "select_custom_period",
                    "name": "",
                    "type": "json-form2",
                    "config": {"data_from_variable": "selected_simulation_period"},
                    "data": {
                        "from_state": {"selected_simulation_period": "selected_simulation_period"},
                        "to_state": {},
                    },
                    "next_step": "base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "select_kpis",
                    "name": "",
                    "description": "Please select the KPIs that you want to be calculated after the simulation:",
                    "type": "select",
                    "config": {
                        "placeholder": "Select KPI modules",
                        "multiple": True,
                        "label_fields": ["description"],
                        "value_field": "id",
                    },
                    "data": {
                        "from_url": {"url": f"{ESSIM_BACKEND_HOST}/essim/simulation/kpiModules/"},
                        "to_state": {},
                        "output_wrapper_variable": "selected_kpis",
                    },
                    "next_step": "base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "start_run",
                    "name": "",
                    "description": "",
                    "type": "esdl-service",
                    "config": {
                        "state_params": {
                            "run_name": "run_name",
                            "start_time": "start_time",
                            "end_time": "end_time",
                            "time_step": "time_step",
                        },
                        "datetimes_convert_Z": True,
                    },
                    "service": {
                        "id": "74c9d1a2-c92a-46ed-a7e4-9931971cdd28",
                        "description": "",
                        "name": "",
                        "button_label": "Run Essim Calculation",
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/1.0",
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                        "url": f"{ESSIM_BACKEND_HOST}/essim/simulation",
                        "http_method": "post",
                        "type": "send_esdl",
                        "send_email_in_post_body_parameter": "user_name",
                        "query_parameters": [
                            {
                                "name": "simulationDescription",
                                "description": "Simulation name",
                                "parameter_name": "run_name",
                                "location": "body",
                            },
                            {
                                "name": "startDate",
                                "description": "start date",
                                "parameter_name": "start_time",
                                "location": "body",
                            },
                            {
                                "name": "endDate",
                                "description": "end date",
                                "parameter_name": "end_time",
                                "location": "body",
                            },
                            {
                                "name": "timeStep",
                                "description": "time step",
                                "parameter_name": "time_step",
                                "location": "body",
                            },
                            {
                                "name": "influxURL",
                                "description": "influx url",
                                "value": "http://influxdb:8086",
                                "location": "body",
                            },
                            {"name": "user", "description": "Essim user", "value": "mapeditor", "location": "body"},
                        ],
                        "body": "json_text",
                        "body_config": {
                            "type": "json",
                            "parameters": [
                                {"type": "esdl", "encoding": "base64_encoded", "parameter": "esdlContents"},
                                {"type": "esdl_id", "parameter": "scenarioID"},
                            ],
                        },
                        "result": [
                            {
                                "code": 200,
                                "action": "save_model_run",
                                "external_model_name": "essim",
                                "external_model_id_response_param": "id",
                                "run_name_state_param": "run_name",
                            }
                        ],
                        "with_jwt_token": False,
                        "state_params": True,
                    },
                    "button_text": "Start model run",
                    "next_step": "retrieve_run_progress_results",
                    "workflow_engine": {
                        "run_name": "state_params.run_name",
                        "workflow_engine_next_step": "retrieve_run_progress_results",
                    },
                },
                {
                    "id": "retrieve_run_progress_results",
                    "monitor_name": "Running Essim Calculation...",
                    "type": "workflow-engine-monitor",
                    "config": {
                        "model_run_result_polling": {
                            "query_list": [
                                {
                                    "url": f"{ESSIM_BACKEND_HOST}/essim/simulation/<MODEL_JOB_ID>",
                                    "response_mapping": {
                                        "status": "status.state",
                                        "progress_fraction": "status.description",
                                    },
                                    "model_specific_response_mapping": {
                                        "scenarioID": "scenarioID",
                                        "simRunDate": "simRunDate",
                                        "dashboardURL": "dashboardURL",
                                    },
                                    "esdl_encoding": "base64_encoded",
                                    "status_mapping": {
                                        "SUBMITTED": ["CREATED"],
                                        "RUNNING": ["RUNNING"],
                                        "SUCCEEDED": ["COMPLETE"],
                                        "CANCELLED": ["CANCELLED"],
                                        "ERROR": ["TIMEOUT", "ERROR"],
                                    },
                                }
                            ],
                            "retry_interval_seconds": 2,
                            "maximum_wait_seconds": 3600,
                        }
                    },
                },
                {
                    "id": "runs_table",
                    "name": "Results overview",
                    "description": "",
                    "type": "table-external-model",
                    "config": {
                        "external_model": "essim",
                        "model_short_name": "essim",
                        "has_feedback_messages": False,
                        "result_animation": {
                            "filter_on_tag": {"tag_name": "simulationRun", "value_database_key": "model_job_id"}
                        },
                        "result_external_link": {
                            "description": "Open Dashboard",
                            "value_database_key": "model_specific_output.dashboardURL",
                        },
                        "delete_result_url": "",
                        "time_series_xlsx_download": {
                            "filter_on_tag": {"tag_name": "simulationRun", "value_database_key": "model_job_id"},
                            "esdl_object_name_field": "assetName",
                            "excel_sheets_per_table": [
                                {
                                    "name_postfix": "PinW",
                                    "field_name_recorded_per_esdl_object": "allocationPower",
                                    "field_names_unrelated_to_esdl_objects": ["imbalancePower"],
                                    "exclude_values": {"field_name": "capability", "values_to_exclude": ["Transport"]},
                                },
                                {
                                    "name_postfix": "EinJ",
                                    "field_name_recorded_per_esdl_object": "allocationEnergy",
                                    "field_names_unrelated_to_esdl_objects": ["imbalanceEnergy"],
                                    "exclude_values": {"field_name": "capability", "values_to_exclude": ["Transport"]},
                                },
                            ],
                        },
                    },
                    "data": {
                        "from_socket": {
                            "event": "get_external_model_runs_for_user",
                            "params": {"external_model_name": "essim"},
                        }
                    },
                    "with_jwt_token": True,
                },
            ],
        },
        {
            "id": "912c4a2b-8eee-46f7-a225-87c5f85e645f",
            "name": "ESDL Validator",
            "explanation": "This service allows you validate an ESDL against a certain schema",
            "type": "vueworkflow",
            "workflow": [
                {
                    "id": "schema_and_validate",
                    "type": "composite",
                    "config": {"step_ids": ["select_schema", "validate_esdl"]},
                    "next_step": "schema_and_validate",
                },
                {
                    "id": "select_schema",
                    "name": "Select schema",
                    "description": "",
                    "type": "select",
                    "config": {"multiple": False, "label_fields": ["name"], "value_field": "id"},
                    "data": {
                        "from_url": {"url": "http://esdl-validator:5000/schema"},
                        "to_state": {},
                        "output_wrapper_variable": "schema",
                    },
                    "next_step": "schema_and_validate",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "validate_esdl",
                    "name": "",
                    "type": "esdl-service",
                    "config": {"state_params": {"schemas": "schema.id"}},
                    "service": {
                        "id": "64c9d1a2-c92a-46ed-a7e4-9931971cbb20",
                        "name": "Validate ESDL against schema",
                        "description": "",
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/0.1",
                            "Content-Type": "application/xml;charset=UTF-8",
                        },
                        "url": "http://esdl-validator:5000/validationToMessages/",
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
                    "button_text": "Validate",
                    "previous_step": "select_schema",
                },
            ],
            "show_on_toolbar": True,
            "icon": {"filename": "Validator.png", "type": "filename"},
        },
    ],
    "role_based_esdl_services": {
        "eps": [
            {
                "id": "9951c271-f9b6-4c4e-873f-b309dff19e03",
                "name": "EIGEN Plan & Design Workflow",
                "explanation": "This workflow allows you to run the ICE workflow for business parks.",
                "type": "vueworkflow",
                "resumable": True,
                "workflow": [
                    {
                        "id": "home",
                        "name": "Begin",
                        "description": "How would you like to proceed?",
                        "type": "choice",
                        "options": [
                            # CREATE BASELINE ENERGY SYSTEM
                            {
                                "name": "Create baseline energy system",
                                "type": "header",
                            },
                            {
                                "name": "Create a new Energy Potential Scan project",
                                "type": "primary",
                                "next_step": "create-project",
                            },
                            {
                                "name": "Adjust EPS input",
                                "type": "primary",
                                "next_step": "adjust-eps-input",
                            },
                            {
                                "name": "Run EPS",
                                "type": "primary",
                                "next_step": "select-existing-project-for-run-eps",
                            },
                            {
                                "name": "Load EPS results",
                                "type": "primary",
                                "next_step": "select-eps-execution",
                            },
                            {
                                "name": "Explore EPS results",
                                "type": "primary",
                                "next_step": "explore-eps-results",
                                "enable_if_state": "execution.success",
                            },
                            {
                                "name": "Apply EPS measures",
                                "type": "primary",
                                "next_step": "apply-eps-measures",
                                "enable_if_state": "execution.success",
                            },
                            # ESTIMATE FLEX ASSETS
                            # {
                            #     "name": "Estimate flex assets",
                            #     "type": "header",
                            # },
                            # {
                            #     "name": "Start Flex Scan phase 1",
                            #     "type": "primary",
                            #     "next_step": "start-flex-scan-phase-1",
                            #     "enable_if_state": "execution.success",
                            # },
                            # {
                            #     "name": "Load FS phase 1 results",
                            #     "type": "primary",
                            #     "next_step": "select-flex-scan-f1-year",
                            #     "enable_if_state": "execution.success",
                            # },
                            # CONFIGURE ENERGY INFRASTRUCTURE
                            {
                                "name": "Configure energy infrastructure",
                                "type": "header",
                            },
                            {
                                "name": "Configure energy infrastructure",
                                "type": "primary",
                                "next_step": "configure-energy-infrastructure",
                            },
                            # ADD SMART METER PROFILES
                            {
                                "name": "Add smart meter profiles",
                                "type": "header",
                            },
                            {
                                "name": "Generate energy profiles template",
                                "type": "primary",
                                "next_step": "generate-profile-template",
                            },
                            {
                                "name": "Upload energy profiles template",
                                "type": "primary",
                                "next_step": "upload-profiles",
                            },
                            # CONFIGURE SCENARIOS
                            {
                                "name": "Configure scenarios",
                                "type": "header",
                            },
                            {
                                "name": "Apply energy saving measures",
                                "type": "primary",
                                "next_step": "custom-energy-saving-measures",
                            },
                            {
                                "name": "Configure new assets",
                                "type": "primary",
                                "next_step": "configure-new-assets",
                            },
                            {
                                "name": "Configure energy hub",
                                "type": "primary",
                                "next_step": "energy-hub",
                            },
                            # OPTIMISE ENERGY HUB
                            {
                                "name": "Optimise energy hub",
                                "type": "header",
                            },
                            {
                                "name": "Add asset costs",
                                "type": "subheader",
                            },
                            {
                                "name": "Generate cost information template",
                                "type": "primary",
                                "next_step": "generate-cost-information-template",
                            },
                            {
                                "name": "Upload cost information template",
                                "type": "primary",
                                "next_step": "upload-cost-information-template",
                            },
                            {
                                "name": "Optimise asset dimensions",
                                "type": "subheader",
                            },
                            {
                                "name": "Run Energy Hub Configurator",
                                "type": "primary",
                                "next_step": "run-energy-hub-configurator",
                            },
                            {
                                "name": "Load EHC results",
                                "type": "primary",
                                "next_step": "load-ehc-results",
                            },
                            {
                                "name": "Optimise flexibility (in development)",
                                "type": "subheader",
                            },
                            {
                                "name": "Flex Scan phase 2",
                                "type": "primary",
                                "disabled": False,
                                "next_step": "flex-scan-phase-2",
                            },
                            {
                                "name": "Calculate business case (in development)",
                                "type": "subheader",
                            },
                            {
                                "name": "Run Energy Hub Configurator",
                                "type": "primary",
                                "disabled": True,
                                "next_step": "run-ehc-business-case-module",
                            },
                            {
                                "name": "Load EHC results",
                                "type": "primary",
                                "disabled": True,
                                "next_step": "load-ehc-business-case-results",
                            },
                            # SIMULATE TOTAL ENERGY SYSTEM
                            {
                                "name": "Simulate total energy system",
                                "type": "header",
                            },
                            {
                                "name": "Run Essim",
                                "type": "primary",
                                "next_step": "essim",
                            },
                        ],
                    },
                    {
                        "id": "create-project",
                        "name": "Create Project",
                        "description": "",
                        "type": "custom",
                        "component": "eps-create-project",
                        "url": f"{EPS_WEB_HOST}/api/projects/",
                        "next_step": "home",
                    },
                    {
                        "id": "adjust-eps-input",
                        "name": "Adjust EPS input",
                        "description": "",
                        "type": "choice",
                        "options": [
                            {
                                "name": "Download project file",
                                "description": "If you want to inspect the KvK data or modify input data, you can download a project file.",
                                "next_step": "select-existing-project-for-download",
                                "type": "primary",
                            },
                            {
                                "name": "Upload project file",
                                "description": "An adjusted project file can be uploaded to serve as input for a new EPS run. This file can then be selected in the next step: Run EPS.",
                                "next_step": "select-existing-project-for-upload",
                                "type": "primary",
                            },
                        ],
                    },
                    {
                        "id": "select-existing-project-for-download",
                        "name": "Select existing project",
                        "description": "Please select the project for which you would like to download a project file.",
                        "type": "select",
                        "config": {
                            "multiple": False,
                            "label_fields": ["name"],
                            "value_field": "id",
                            "choices_attr": "projects",
                        },
                        "data": {
                            "from_url": {
                                "url": f"{EPS_WEB_HOST}/api/projects/",
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                            },
                            "to_state": {},
                            "output_wrapper_variable": "project",
                        },
                        "next_step": "select-project-file-for-download",
                    },
                    {
                        "id": "select-project-file-for-download",
                        "name": "Select project file",
                        "description": "Please select the project file you would like to download.",
                        "type": "select",
                        "config": {
                            "multiple": False,
                            "label_fields": ["name"],
                            "value_field": "id",
                            "choices_attr": "file_names",
                        },
                        "data": {
                            "from_url": {
                                "url": f"{EPS_WEB_HOST}/api/projects/{{project_id}}/files",
                                "request_params": [{"name": "project_id", "parameter_name": "project.id"}],
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                            },
                            "to_state": {},
                            "output_wrapper_variable": "file",
                        },
                        "next_step": "download-project-file",
                    },
                    {
                        "id": "download-project-file",
                        "name": "Download project file",
                        "description": "By clicking the button below you can download the selected project file.",
                        "type": "download_file",
                        "source": {
                            "url": EPS_WEB_HOST + "/api/projects/{project_id}/files/{file_name}",
                            "request_params": {
                                "project_id": "project.id",
                                "file_name": "file.id",
                            },
                        },
                    },
                    {
                        "id": "select-existing-project-for-upload",
                        "name": "Select existing project",
                        "description": "Please select the project for which you would like to upload a project file.",
                        "type": "select",
                        "config": {
                            "multiple": False,
                            "label_fields": ["name"],
                            "value_field": "id",
                            "choices_attr": "projects",
                        },
                        "data": {
                            "from_url": {
                                "url": f"{EPS_WEB_HOST}/api/projects/",
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                            },
                            "to_state": {},
                            "output_wrapper_variable": "project",
                        },
                        "next_step": "upload-project-file",
                    },
                    {
                        "id": "upload-project-file",
                        "name": "Upload project file",
                        "description": "Note: When uploading a project file with the same name as a previous project file, the previous file will be overwritten!",
                        "type": "upload_file",
                        "target": {
                            "url": f"{EPS_WEB_HOST}/api/uploads/",
                            "request_params": {"project_id": "project.id"},
                            "response_params": {"name": "file_name"},
                        },
                        "success_text": "The newly uploaded file can be used to start a new EPS run.",
                    },
                    {
                        "id": "select-existing-project-for-run-eps",
                        "name": "Select existing project",
                        "description": "",
                        "type": "select",
                        "multiple": False,
                        "target_variable": "project",

                        "config": {
                            "multiple": False,
                            "choices_attr": "projects",
                            "label_fields": [
                                "id",
                                "name"
                            ],
                            "value_field": "id",
                        },
                        "data": {
                            "from_url": {
                                "url": f"{EPS_WEB_HOST}/api/projects/",
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                            },
                            "to_state": {},
                            "output_wrapper_variable": "project",
                        },
                        "next_step": "run-the-eps",
                    },
                    {
                        "id": "run-the-eps",
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
                                    "message": "EPS started successfully! It can take up to 45 minutes for the EPS to complete. When it is complete, the results can be found under 'Resultaten' in the EPS Web environment."
                                },
                                "429": {
                                    "message": "It is currently busy on the server. We cannot start an EPS execution at this time. Please try again at a later time."
                                },
                            },
                        },
                    },
                    {
                        "id": "select-eps-execution",
                        "name": "Select EPS execution",
                        "description": "",
                        "label": "Choose the EPS execution from which to load the results as a baseline energy system ESDL in the Map Editor.",
                        "type": "select",
                        "config": {
                            "multiple": False,
                            "choices_attr": "executions",
                            "label_fields": [
                                "project.name",
                                "id",
                                {
                                    "label": "complete",
                                    "map": {True: "Complete", False: "Failed"},
                                    "default": "Processing",
                                },
                            ],
                            "value_field": "id",
                        },
                        "data": {
                            "from_url": {
                                "url": f"{EPS_WEB_HOST}/api/eps/",
                                "method": "GET",
                                "headers": {"Accept": "application/json"},
                            },
                            "to_state": {},
                            "output_wrapper_variable": "execution",
                        },
                        "button_text": "Load EPS results",
                        "next_step": "load-eps",
                    },
                    {
                        "id": "load-eps",
                        "name": "Load EPS",
                        "description": "Please wait a moment while we load the EPS output as ESDL. This ESDL contains the energy system with no measures applied. When the EPS is loaded, please continue.",
                        "type": "esdl-service",
                        "config": {
                            "state_params": {"execution_id": "execution.id"},
                        },
                        "button_text": "Confirm EPS loaded",
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b12",
                            "name": "Visualize EPS",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/eps/<execution_id>/esdl/variant",
                            "auto": True,
                            "http_method": "post",
                            "type": "json",
                            "result": [{"code": 200, "action": "esdl"}],
                            "query_parameters": [
                                {
                                    "location": "url",
                                    "parameter_name": "execution_id",
                                }
                            ],
                            "with_jwt_token": True,
                        },
                    },
                    {
                        "id": "explore-eps-results",
                        "name": "Explore EPS results",
                        "description": "",
                        "type": "custom",
                        "component": "eps-inspect-result",
                        "custom_data": {"url": EPS_WEB_HOST + "/api/eps/{execution_id}/pand/{pand_bagid}"},
                    },
                    {
                        "id": "apply-eps-measures",
                        "name": "Apply EPS measures",
                        "description": "",
                        "type": "custom",
                        "component": "eps-select-measures",
                        "config": {
                            "state_params": {"execution_id": "execution.id"},
                        },
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b14",
                            "name": "Select EPS measures",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/eps/<execution_id>/esdl/variant",
                            "http_method": "post",
                            "type": "json",
                            "query_parameters": [
                                {
                                    "name": "Execution ID",
                                    "parameter_name": "execution_id",
                                    "location": "url",
                                },
                                {
                                    "parameter_name": "isolation_roof",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "isolation_facade",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "isolation_glass",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "wtw",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "led",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "heat_pump",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "pv",
                                    "location": "body",
                                },
                            ],
                            "result": [{"code": 200, "action": "esdl"}],
                            "with_jwt_token": True,
                        },
                    },
                    # {
                    #     "id": "start-flex-scan-phase-1",
                    #     "name": "Start Flex Scan phase 1",
                    #     "description": "",
                    #     "type": "custom",
                    #     "component": "flexscan-import-eps",
                    #     "custom_data": {
                    #         "flex_frontend_host": FLEX_FRONTEND_HOST,
                    #     },
                    # },
                    # {
                    #     "id": "select-flex-scan-f1-year",
                    #     "name": "Select Flex Scan F1 year",
                    #     "description": "Choose the year for which you want to load the Flex Scan phase 1 results. NB. Make sure to select the ESDL layer you wish to use as a baseline for the Flex Scan F1 results.",
                    #     "type": "choice",
                    #     "options": [
                    #         {
                    #             "name": "2020",
                    #             "description": "",
                    #             "next_step": "load-flex-scan-f1",
                    #             "target_variable_value": {"year": 2020},
                    #         },
                    #         {
                    #             "name": "2025",
                    #             "description": "",
                    #             "next_step": "load-flex-scan-f1",
                    #             "target_variable_value": {"year": 2025},
                    #         },
                    #         {
                    #             "name": "2030",
                    #             "description": "",
                    #             "next_step": "load-flex-scan-f1",
                    #             "target_variable_value": {"year": 2030},
                    #         },
                    #     ],
                    #     "target_variable": "flexscanf1",
                    # },
                    # {
                    #     "id": "load-flex-scan-f1",
                    #     "name": "Load Flex Scan F1",
                    #     "type": "esdl-service",
                    #     "config": {
                    #         "state_params": {"execution_id": "execution.id", "year": "flexscanf1.year"},
                    #     },
                    #     "service": {
                    #         "id": "f25dfd1a-525d-42db-92d6-6d358bbdfca1",
                    #         "name": "Load Flex Scan phase 1 results",
                    #         "headers": {
                    #             "Accept": "application/json",
                    #             "User-Agent": "ESDL Mapeditor/0.1",
                    #             "Content-Type": "application/json",
                    #         },
                    #         "url": f"{FLEX_BACKEND_HOST}/executions/<execution_id>/phase1/esdl/<year>",
                    #         "auto": True,
                    #         "http_method": "post",
                    #         "type": "send_esdl_json",
                    #         "body": "base64_encoded",
                    #         "result": [{"code": 200, "action": "esdl"}],
                    #         "query_parameters": [
                    #             {
                    #                 "name": "Execution ID",
                    #                 "parameter_name": "execution_id",
                    #                 "location": "url",
                    #             },
                    #             {
                    #                 "name": "Flex Scan F1 year",
                    #                 "parameter_name": "year",
                    #                 "location": "url",
                    #             },
                    #         ],
                    #         "with_jwt_token": True,
                    #     },
                    #     "target_variable": "flexscanf1",
                    #     "target_variable_value": {"loaded": True},
                    # },
                    {
                        "id": "configure-energy-infrastructure",
                        "name": "",
                        "description": "",
                        "type": "text",
                        "data": {
                            "from_config": {
                                "text": """
                                A basic theoretical configuration of the electricity and gas infrastructure has been generated by the EPS, connecting all electricity connections to one substation and all gas connections to one gas network. In this step, this infrastructure configuration can be adjusted to reflect the actual situation, and the infrastructure attributes can be set.
                                This can be done using the standard ESDL Map Editor functionalities.
                            """,
                            },
                        },
                    },
                    {
                        "id": "generate-profile-template",
                        "name": "Generate profile template",
                        "description": "",
                        "type": "custom",
                        "component": "pdtoolsuite-generate-profile-template",
                    },
                    {
                        "id": "upload-profiles",
                        "name": "Upload profiles",
                        "type": "custom",
                        "component": "pdtoolsuite-upload-profiles",
                    },
                    {
                        "id": "custom-energy-saving-measures",
                        "name": "Custom energy saving measures",
                        "description": "",
                        "type": "custom",
                        "component": "eps-custom-measures",
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b15",
                            "name": "Custom EPS measures",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/custom_measures/",
                            "http_method": "post",
                            "type": "send_esdl_json",
                            "body": "base64_encoded",
                            "query_parameters": [
                                {
                                    "parameter_name": "measures_to_apply",
                                    "location": "body",
                                },
                                {
                                    "parameter_name": "building_ids",
                                    "location": "body",
                                },
                            ],
                            "result": [{"code": 200, "action": "esdl"}],
                            "with_jwt_token": True,
                        },
                    },
                    {
                        "id": "configure-new-assets",
                        "name": "Configure new assets",
                        "description": "",
                        "type": "text",
                        "data": {
                            "from_config": {
                                "text": "At this point of the workflow you can add any assets and connections, to model your energy system scenario. Please make sure that you have selected the EPS measures you are interested in beforehand, and that you have applied any custom measures if applicable. These cannot be adjusted in a later stage.",
                            },
                        },
                    },
                    {
                        "id": "energy-hub",
                        "name": "Energy Hub",
                        "description": "",
                        "type": "custom",
                        "component": "pdtoolsuite-init-energy-hub",
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b16",
                            "name": "EPS Energy Hub",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/energy_hubs/",
                            "http_method": "post",
                            "type": "send_esdl_json",
                            "body": "base64_encoded",
                            "query_parameters": [
                                {
                                    "parameter_name": "building_ids",
                                    "location": "body",
                                },
                            ],
                            "result": [{"code": 200, "action": "esdl"}],
                            "with_jwt_token": True,
                        },
                    },
                    {
                        "id": "generate-cost-information-template",
                        "name": "Generate cost information template",
                        "description": "",
                        "type": "custom",
                        "component": "cost-information-generate-template",
                    },
                    {
                        "id": "upload-cost-information-template",
                        "name": "Upload cost information template",
                        "description": "",
                        "type": "custom",
                        "component": "cost-information-upload-template",
                    },
                    {
                        "id": "run-energy-hub-configurator",
                        "name": "Run Energy Hub Configurator",
                        "description": "For the energy hub configured in an ESDL layer, the economical optimal collective battery specifications can be calculated with the EHC, together with the corresponding business case. As result of this step, a new ESDL layer will be created with the EHC results, and a business case Excel will be downloaded to your browser automatically.",
                        "type": "service",
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b13",
                            "name": "Run Energy Hub Configurator",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            # "url": "https://ehc.bicore.nl/auth-test",
                            "url": "https://ehc.bicore.nl/process",
                            # "url": "http://localhost:8111/dice_workflow/mock",
                            "http_method": "post",
                            "type": "",
                            "body_config": {
                                "type": "json",
                                "profiles": "inline",
                                "parameters": [
                                    {
                                        "type": "esdl",
                                        "parameter": "esdl",
                                        "encoding": "base64_encoded",
                                    },
                                    {
                                        "type": "value",
                                        "parameter": "email",
                                        "value": "lars@xithing.io",
                                    }
                                ],
                            },
                            "result": [
                                {
                                    "action": "download_file",
                                    "encoding": "base64_encoded",
                                    "json_field": "esdl",
                                    "filename": "ehc_result.esdl",
                                    "content_type": "application/xml",
                                },
                                {
                                    "action": "download_file",
                                    "encoding": "base64_encoded",
                                    "json_field": "business_case_excel",
                                    "filename": "ehc_business_case.csv",
                                    "content_type": "text/csv",
                                },
                            ],
                            "with_jwt_token": True,
                        }
                    },
                    {
                        "id": "load-ehc-results",
                        "name": "Load Energy Hub Configurator results",
                        "description": "",
                        "type": "text",
                        "data": {
                            "from_config": {
                                "text": "The ESDL file from the EHC results can be imported into the Map Editor by selecting the 'Import ESDL with in-line profiles' option from the 'File' menu in the top-left corner of the screen. The ESDL file can be selected from the file dialog that appears and will be automatically added to your ESDL layers.",
                            },
                        },
                    },
                    {
                        "id": "flex-scan-phase-2",
                        "name": "Flex Scan phase 2",
                        "type": "composite",
                        "config": {
                            "step_ids": [
                                "select-name-and-goal-flex-scan",
                                "select-hub-flex-scan",
                                "start-flex-scan-phase-2",
                                "table-flex-scan-phase-2-runs",
                            ]
                        },
                        "next_step": "flex-scan-phase-2",
                    },
                    {
                        "id": "select-name-and-goal-flex-scan",
                        "type": "json-form2",
                        "data": {
                            "from_config": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "run_name": {"type": "string", "minLength": 3, "title": "Name"},
                                        "optimization_goal": {
                                            "type": "string",
                                            "oneOf": [
                                                {"const": "infra", "title": "infra"},
                                                {"const": "duurzaamheid", "title": "sustainability"},
                                                {"const": "kosten", "title": "costs"},
                                            ],
                                        },
                                        "start_date": {"format": "date", "type": "string"},
                                        "end_date": {
                                            "format": "date",
                                            "type": "string",
                                            "title": "End Date (including this day)",
                                        },
                                    },
                                    "required": ["run_name", "optimization_goal", "start_date", "end_date"],
                                }
                            },
                            "to_state": {},
                        },
                        "next_step": "flex-scan-phase-2",
                        "next_step_trigger": "input_change",
                    },
                    {
                        "id": "select-hub-flex-scan",
                        "name": "",
                        "description": "Select the Hub (electricity network from active ESDL)",
                        "type": "select",
                        "config": {"multiple": False, "label_fields": ["title"], "value_field": "id"},
                        "data": {
                            "from_socket": {
                                "event": "get_electricity_networks_active_es",
                            },
                            "to_state": {},
                            "output_wrapper_variable": "selected_hub",
                        },
                        "reload_on_esdl_activation": True,
                        "next_step": "flex-scan-phase-2",
                        "next_step_trigger": "input_change",
                    },
                    {
                        "id": "start-flex-scan-phase-2",
                        "name": "",
                        "description": "",
                        "type": "esdl-service",
                        "config": {
                            "state_params": {
                                "run_name": "run_name",
                                "optimization_goal": "optimization_goal",
                                "start_date": "start_date",
                                "end_date": "end_date",
                                "hub_elect_network_id": "selected_hub.id",
                            },
                        },
                        "service": {
                            "id": "74c9d1a2-c92a-46ed-a7e4-9931971ced58",
                            "description": "",
                            "name": "",
                            "headers": {
                                "User-Agent": "ESDL Mapeditor/1.0",
                                "Accept": "application/json",
                                "Content-Type": "application/json",
                            },
                            "url": f"{FLEX_BACKEND_HOST}/flex/start",
                            "http_method": "post",
                            "type": "send_esdl",
                            "send_email_in_post_body_parameter": "user_name",
                            "query_parameters": [
                                {
                                    "name": "run_name",
                                    "description": "Run name",
                                    "parameter_name": "run_name",
                                    "location": "body",
                                },
                                {
                                    "name": "optimization_goal",
                                    "description": "Optimization goal",
                                    "parameter_name": "optimization_goal",
                                    "location": "body",
                                },
                                {
                                    "name": "start_date",
                                    "description": "Start date",
                                    "parameter_name": "start_date",
                                    "location": "body",
                                },
                                {
                                    "name": "end_date",
                                    "description": "End date",
                                    "parameter_name": "end_date",
                                    "location": "body",
                                },
                                {
                                    "name": "hub_elect_network_id",
                                    "description": "Hub electricity network ID",
                                    "parameter_name": "hub_elect_network_id",
                                    "location": "body",
                                },
                            ],
                            "body": "json_text",
                            "body_config": {
                                "type": "json",
                                "parameters": [
                                    {"type": "esdl", "encoding": "base64_encoded", "parameter": "esdl_file_base64_str"},
                                ],
                            },
                            "result": [
                                {
                                    "code": 200,
                                    "action": "save_model_run",
                                    "external_model_name": "flexscan",
                                    "external_model_id_response_param": "phase2_execution_id",
                                    "external_model_logs_response_param": "error",
                                    "run_name_state_param": "run_name",
                                }
                            ],
                            "with_jwt_token": False,
                            "state_params": True,
                        },
                        "button_text": "Start model run",
                        "next_step": "flex-scan-phase-2",
                        "workflow_engine": {
                            "run_name": "state_params.run_name",
                            "workflow_engine_next_step": "retrieve-flex-scan-phase-2-run-progress-results",
                        },
                    },
                    {
                        "id": "retrieve-flex-scan-phase-2-run-progress-results",
                        "monitor_name": "Running Flexscan phase 2 Calculation...",
                        "type": "workflow-engine-monitor",
                        "config": {
                            "model_run_result_polling": {
                                "query_list": [
                                    {
                                        "url": f"{FLEX_BACKEND_HOST}/flex/<MODEL_JOB_ID>/progress",
                                        "response_mapping": {
                                            "status": "status",
                                            "progress_fraction": "progress_fraction",
                                            "logs": "logs",
                                            "output_esdl": "output_esdl_base64",
                                        },
                                        "model_specific_response_mapping": {
                                            "flexscan_results_url": "flexscan_results_url",
                                        },
                                        "esdl_encoding": "base64_encoded",
                                        "status_mapping": {
                                            "SUBMITTED": ["SUBMITTED"],
                                            "RUNNING": ["RUNNING"],
                                            "SUCCEEDED": ["SUCCEEDED"],
                                            "WARNING": ["WARNING"],
                                            "ERROR": ["ERROR"],
                                        },
                                    }
                                ],
                                "retry_interval_seconds": 2,
                                "maximum_wait_seconds": 3600,
                            }
                        },
                    },
                    {
                        "id": "table-flex-scan-phase-2-runs",
                        "name": "Results overview",
                        "description": "",
                        "type": "table-external-model",
                        "config": {
                            "model_short_name": "flexscan",
                            "has_feedback_messages": False,
                            "result_external_link": {
                                "description": "View flexscan dashboard",
                                "value_database_key": "model_specific_output.flexscan_results_url",
                            },
                            "delete_result_url": f"{FLEX_BACKEND_HOST}/flex/<MODEL_JOB_ID>/results",
                            "load_input_esdl": True,
                        },
                        "data": {
                            "from_socket": {
                                "event": "get_external_model_runs_for_user",
                                "params": {"external_model_name": "flexscan"},
                            }
                        },
                        "with_jwt_token": True,
                    },
                    {
                        "id": "run-ehc-business-case-module",
                        "name": "Run EHC Business Case module",
                        "description": "",
                        "type": "text",
                        "data": {
                            "from_config": {
                                "text": "PLACEHOLDER",
                            },
                        },
                    },
                    {
                        "id": "load-ehc-business-case-results",
                        "name": "Load EHC Business Case results",
                        "description": "",
                        "type": "text",
                        "data": {
                            "from_config": {
                                "text": "PLACEHOLDER",
                            },
                        },
                    },
                    {
                        "id": "essim",
                        "name": "Essim",
                        "type": "composite",
                        "config": {
                            "step_ids": [
                                "select_name_and_time_step_essim",
                                "select_simulation_period_essim",
                                "select_custom_period_essim",
                                "start_run_essim",
                                "runs_table_essim"
                            ]
                        },
                        "next_step": "essim"
                    },
                    {
                        "id": "select_name_and_time_step_essim",
                        "type": "json-form2",
                        "data": {
                            "from_config": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "run_name": {
                                            "type": "string",
                                            "minLength": 3,
                                            "title": "Name"
                                        },
                                        "time_step": {
                                            "type": "string",
                                            "oneOf": [
                                                {
                                                    "const": "1h",
                                                    "title": "1 hour"
                                                },
                                                {
                                                    "const": "15m",
                                                    "title": "15 minutes"
                                                }
                                            ]
                                        }
                                    },
                                    "required": [
                                        "run_name",
                                        "time_step"
                                    ]
                                },
                                "uischema": {
                                    "elements": [
                                        {
                                            "scope": "#/properties/run_name",
                                            "type": "Control"
                                        },
                                        {
                                            "scope": "#/properties/time_step",
                                            "type": "Control"
                                        }
                                    ],
                                    "type": "VerticalLayout"
                                },
                                "formData": {
                                    "time_step": "1h"
                                }
                            },
                            "to_state": {}
                        },
                        "next_step": "essim",
                        "next_step_trigger": "input_change"
                    },
                    {
                        "id": "select_simulation_period_essim",
                        "name": "",
                        "description": "Please select the simulation period:",
                        "type": "select",
                        "config": {
                            "placeholder": "Select simulation period",
                            "multiple": False,
                            "label_fields": [
                                "description"
                            ],
                            "value_field": "id"
                        },
                        "data": {
                            "from_config": [
                                {
                                    "id": "year2019",
                                    "description": "Year 2019",
                                    "formData": {
                                        "start_time": "2019-01-01T00:00:00+0100",
                                        "end_time": "2020-01-01T00:00:00+0100"
                                    },
                                    "schema": {
                                        "properties": {
                                            "start_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            },
                                            "end_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            }
                                        },
                                        "required": [
                                            "start_time",
                                            "end_time"
                                        ],
                                        "type": "object"
                                    },
                                    "uischema": {
                                        "elements": [
                                            {
                                                "scope": "#/properties/start_time",
                                                "type": "Control",
                                                "options": {
                                                    "readonly": True
                                                }
                                            },
                                            {
                                                "scope": "#/properties/end_time",
                                                "type": "Control",
                                                "options": {
                                                    "readonly": True
                                                }
                                            }
                                        ],
                                        "type": "VerticalLayout"
                                    }
                                },
                                {
                                    "id": "year2019",
                                    "description": "Year 2023",
                                    "formData": {
                                        "start_time": "2023-01-01T00:00:00+0100",
                                        "end_time": "2024-01-01T00:00:00+0100"
                                    },
                                    "schema": {
                                        "properties": {
                                            "start_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            },
                                            "end_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            }
                                        },
                                        "required": [
                                            "start_time",
                                            "end_time"
                                        ],
                                        "type": "object"
                                    },
                                    "uischema": {
                                        "elements": [
                                            {
                                                "scope": "#/properties/start_time",
                                                "type": "Control",
                                                "options": {
                                                    "readonly": True
                                                }
                                            },
                                            {
                                                "scope": "#/properties/end_time",
                                                "type": "Control",
                                                "options": {
                                                    "readonly": True
                                                }
                                            }
                                        ],
                                        "type": "VerticalLayout"
                                    }
                                },
                                {
                                    "id": "custom",
                                    "description": "custom period",
                                    "formData": {},
                                    "schema": {
                                        "properties": {
                                            "start_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            },
                                            "end_time": {
                                                "format": "date-time",
                                                "type": "string"
                                            }
                                        },
                                        "required": [
                                            "start_time",
                                            "end_time"
                                        ],
                                        "type": "object"
                                    },
                                    "uischema": {
                                        "elements": [
                                            {
                                                "scope": "#/properties/start_time",
                                                "type": "Control"
                                            },
                                            {
                                                "scope": "#/properties/end_time",
                                                "type": "Control"
                                            }
                                        ],
                                        "type": "VerticalLayout"
                                    }
                                }
                            ],
                            "to_state": {},
                            "output_wrapper_variable": "selected_simulation_period_essim"
                        },
                        "next_step": "essim",
                        "next_step_trigger": "input_change"
                    },
                    {
                        "id": "select_custom_period_essim",
                        "name": "",
                        "type": "json-form2",
                        "config": {
                            "data_from_variable": "selected_simulation_period_essim"
                        },
                        "data": {
                            "from_state": {
                                "selected_simulation_period_essim": "selected_simulation_period_essim"
                            },
                            "to_state": {}
                        },
                        "next_step": "essim",
                        "next_step_trigger": "input_change"
                    },
                    {
                        "id": "start_run_essim",
                        "name": "",
                        "description": "",
                        "type": "esdl-service",
                        "config": {
                            "state_params": {
                                "run_name": "run_name",
                                "start_time": "start_time",
                                "end_time": "end_time",
                                "time_step": "time_step"
                            },
                            "datetimes_convert_Z": True
                        },
                        "service": {
                            "id": "74c9d1a2-c92a-46ed-a7e4-9931971cdd28",
                            "description": "",
                            "name": "",
                            "headers": {
                                "User-Agent": "ESDL Mapeditor/1.0",
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            "url": f"{ESSIM_BACKEND_HOST}/essim/simulation",
                            "http_method": "post",
                            "type": "send_esdl",
                            "send_email_in_post_body_parameter": "user_name",
                            "query_parameters": [
                                {
                                    "name": "simulationDescription",
                                    "description": "Simulation name",
                                    "parameter_name": "run_name",
                                    "location": "body"
                                },
                                {
                                    "name": "startDate",
                                    "description": "start date",
                                    "parameter_name": "start_time",
                                    "location": "body"
                                },
                                {
                                    "name": "endDate",
                                    "description": "end date",
                                    "parameter_name": "end_time",
                                    "location": "body"
                                },
                                {
                                    "name": "timeStep",
                                    "description": "time step",
                                    "parameter_name": "time_step",
                                    "location": "body"
                                },
                                {
                                    "name": "influxURL",
                                    "description": "influx url",
                                    "value": "http://influxdb:8086",
                                    "location": "body"
                                },
                                {
                                    "name": "user",
                                    "description": "Essim user",
                                    "value": "mapeditor",
                                    "location": "body"
                                }
                            ],
                            "body": "json_text",
                            "body_config": {
                                "type": "json",
                                "parameters": [
                                    {
                                        "type": "esdl",
                                        "encoding": "base64_encoded",
                                        "parameter": "esdlContents"
                                    },
                                    {
                                        "type": "esdl_id",
                                        "parameter": "scenarioID"
                                    }
                                ]
                            },
                            "result": [
                                {
                                    "code": 200,
                                    "action": "save_model_run",
                                    "external_model_name": "essim",
                                    "external_model_id_response_param": "id",
                                    "run_name_state_param": "run_name"
                                }
                            ],
                            "with_jwt_token": False,
                            "state_params": True
                        },
                        "button_text": "Start model run",
                        "next_step": "essim",
                        "workflow_engine": {
                            "run_name": "state_params.run_name",
                            "workflow_engine_next_step": "retrieve_run_progress_results"
                        }
                    },
                    {
                        "id": "retrieve_run_progress_results",
                        "monitor_name": "Running Essim Calculation...",
                        "type": "workflow-engine-monitor",
                        "config": {
                            "model_run_result_polling": {
                                "query_list": [
                                    {
                                        "url": f"{ESSIM_BACKEND_HOST}/essim/simulation/<MODEL_JOB_ID>",
                                        "response_mapping": {
                                            "status": "status.state",
                                            "progress_fraction": "status.description"
                                        },
                                        "model_specific_response_mapping": {
                                            "scenarioID": "scenarioID",
                                            "simRunDate": "simRunDate",
                                            "dashboardURL": "dashboardURL"
                                        },
                                        "esdl_encoding": "base64_encoded",
                                        "status_mapping": {
                                            "SUBMITTED": [
                                                "CREATED"
                                            ],
                                            "RUNNING": [
                                                "RUNNING"
                                            ],
                                            "SUCCEEDED": [
                                                "COMPLETE"
                                            ],
                                            "CANCELLED": [
                                                "CANCELLED"
                                            ],
                                            "ERROR": [
                                                "TIMEOUT",
                                                "ERROR"
                                            ]
                                        }
                                    }
                                ],
                                "retry_interval_seconds": 2,
                                "maximum_wait_seconds": 3600
                            }
                        }
                    },
                    {
                        "id": "runs_table_essim",
                        "name": "Results overview",
                        "description": "",
                        "type": "table-external-model",
                        "config": {
                          "model_short_name": "essim",
                          "has_feedback_messages": False,
                          "result_animation": {
                            "filter_on_tag": {
                              "tag_name": "simulationRun",
                              "value_database_key": "model_job_id"
                            }
                          },
                          "result_external_link": {
                            "description": "Open Dashboard",
                            "value_database_key": "model_specific_output.dashboardURL"
                          },
                          "delete_result_url": "",
                          "time_series_xlsx_download": {
                            "filter_on_tag": {
                              "tag_name": "simulationRun",
                              "value_database_key": "model_job_id"
                            },
                            "esdl_object_name_field": "assetName",
                            "excel_sheets_per_table": [
                              {
                                "name_postfix": "PinW",
                                "field_name_recorded_per_esdl_object": "allocationPower",
                                "field_names_unrelated_to_esdl_objects": [
                                  "imbalancePower"
                                ],
                                "exclude_values": {
                                  "field_name": "capability",
                                  "values_to_exclude": [
                                    "Transport"
                                  ]
                                }
                              },
                              {
                                "name_postfix": "EinJ",
                                "field_name_recorded_per_esdl_object": "allocationEnergy",
                                "field_names_unrelated_to_esdl_objects": [
                                  "imbalanceEnergy"
                                ],
                                "exclude_values": {
                                  "field_name": "capability",
                                  "values_to_exclude": [
                                    "Transport"
                                  ]
                                }
                              }
                            ]
                          }
                        },
                        "data": {
                          "from_socket": {
                            "event": "get_external_model_runs_for_user",
                            "params": {
                              "external_model_name": "essim"
                            }
                          }
                        },
                        "with_jwt_token": True
                      },
                    # TODO: check if these steps can be safely removed
                    # {
                    #     # 8
                    #     "name": "EPS execution progress",
                    #     "description": "",
                    #     "type": "progress",
                    #     "refresh": 30,
                    #     "source": {
                    #         "url": f"{EPS_WEB_HOST}/api/eps/progress",
                    #         "request_params": {"execution_id": "execution.id"},
                    #         "progress_field": "latest_progress",
                    #         "message_field": "latest_message",
                    #     },
                    # },
                    # {
                    #     # 9
                    #     "name": "Download project file",
                    #     "description": "The project file that was used as input to perform this EPS analysis can be "
                    #     "downloaded here.",
                    #     "type": "download_file",
                    #     "source": {
                    #         "url": EPS_WEB_HOST + "/api/eps/{execution_id}/input",
                    #         "request_params": {"execution_id": "execution.id"},
                    #     },
                    # },
                ],
            },
        ],
    },
}
