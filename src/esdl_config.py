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

ESDL_AGGREGATOR_HOST = os.getenv("ESDL_AGGREGATOR_HOST", "http://esdl-aggregator:3490")
ESDL_UPLOAD_PROFILES_HOST = os.getenv("ESDL_UPLOAD_PROFILES_HOST", "http://mapeditor-upload-profiles:4003")
ESDL_COST_SERVICE_HOST = os.getenv("ESDL_COST_SERVICE_HOST", "http://mapeditor-cost-service:4004")
ESDL_VALIDATOR_URL = os.getenv("ESDL_VALIDATOR_URL", "http://esdl-validator:5000")
ESSIM_URL = os.getenv("ESSIM_URL", "http://essim-engine:8112")

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
            "id": "3186b787-624c-4b23-b5a6-d17ba4c271b1",
            "description": "Energy in PJ",
            "physicalQuantity": "ENERGY",
            "multiplier": "PETA",
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
            "id": "57174dc5-4f95-43dc-af15-311d29c8b207",
            "description": "Coefficient in %",
            "physicalQuantity": "COEFFICIENT",
            "unit": "PERCENT",
        },
        {
            "id": "18bdeeee-a98c-48eb-bfba-803a3a658c5d",
            "description": "Coefficient",
            "physicalQuantity": "COEFFICIENT",
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
                    "id": "essim_base_steps_with_table",
                    "type": "composite",
                    "config": {
                        "step_ids": [
                            "essim_select_name_and_time_step",
                            "essim_select_simulation_period",
                            "essim_select_custom_period",
                            "essim_select_kpis",
                            "essim_start_run",
                            "essim_runs_table",
                        ]
                    },
                    "next_step": "essim_base_steps_with_table",
                },
                {
                    "id": "essim_select_name_and_time_step",
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
                    "next_step": "essim_base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "essim_select_simulation_period",
                    "name": "",
                    "description": "Select the simulation period:",
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
                    "next_step": "essim_base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "essim_select_custom_period",
                    "name": "",
                    "type": "json-form2",
                    "config": {"data_from_variable": "selected_simulation_period"},
                    "data": {
                        "from_state": {"selected_simulation_period": "selected_simulation_period"},
                        "to_state": {},
                    },
                    "next_step": "essim_base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "essim_select_kpis",
                    "name": "",
                    "description": "Select the KPIs that you want to be calculated after the simulation:",
                    "type": "select",
                    "config": {
                        "placeholder": "Select KPI modules",
                        "multiple": True,
                        "label_fields": ["description"],
                        "value_field": "id",
                    },
                    "data": {
                        "from_url": {"url": "http://essim-engine:8112/essim/simulation/kpiModules/"},
                        "to_state": {},
                        "output_wrapper_variable": "selected_kpis",
                    },
                    "next_step": "essim_base_steps_with_table",
                    "next_step_trigger": "input_change",
                },
                {
                    "id": "essim_start_run",
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
                        "headers": {
                            "User-Agent": "ESDL Mapeditor/1.0",
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                        "url": f"{ESSIM_URL}/essim/simulation",
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
                    "next_step": "essim_retrieve_run_progress_status",
                    "workflow_engine": {
                        "run_name": "state_params.run_name",
                        "workflow_engine_next_step": "essim_retrieve_run_progress_status",
                    },
                },
                {
                    "id": "essim_retrieve_run_progress_status",
                    "monitor_name": "Running Essim Calculation...",
                    "type": "workflow-engine-monitor",
                    "config": {
                        "model_run_result_polling": {
                            "query_list": [
                                {
                                    "url": f"{ESSIM_URL}/essim/simulation/<MODEL_JOB_ID>",
                                    "response_mapping": {
                                        "status": "status.state",
                                        "progress_fraction": "status.description",
                                    },
                                    "model_specific_response_mapping": {
                                        "scenarioID": "scenarioID",
                                        "simRunDate": "simRunDate",
                                        "dashboardURL": "dashboardURL",
                                    },
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
                            "maximum_wait_seconds": 86400,
                        }
                    },
                    "workflow_engine": {"workflow_engine_next_step": "essim_retrieve_run_results"},
                },
                {
                    "id": "essim_retrieve_run_results",
                    "monitor_name": "Getting Essim Results...",
                    "type": "workflow-engine-monitor",
                    "config": {
                        "model_run_result_polling": {
                            "query_list": [
                                {
                                    "url": f"{ESSIM_URL}/essim/simulation/<MODEL_JOB_ID>/ESDLWithProfiles",
                                    "response_mapping": {"output_esdl": "esdl"},
                                    "esdl_encoding": "base64_encoded",
                                    "stop_query_on": {
                                        "key": "output_esdl",
                                        "condition": "not_equal",
                                        "value": None,
                                        "new_status": "SUCCEEDED",
                                    },
                                }
                            ],
                            "retry_interval_seconds": 2,
                            "maximum_wait_seconds": 600,
                        }
                    },
                    "workflow_engine": {"workflow_engine_next_step": "essim_show_run_results"},
                },
                {
                    "id": "essim_show_run_results",
                    "monitor_name": "Essim Result",
                    "type": "workflow-engine-monitor",
                    "config": {
                        "model_run_show_results": [
                            {"description": "run name", "value_database_key": "run_name"},
                            {"value_database_key": "model_specific_output.dashboardURL", "link_text": "Open dashboard"},
                        ]
                    },
                },
                {
                    "id": "essim_runs_table",
                    "name": "Results overview",
                    "description": "",
                    "type": "table-external-model",
                    "config": {
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
                        "load_input_esdl": True,
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
                        "from_url": {"url": f"{ESDL_VALIDATOR_URL}/schema"},
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
                        "url": f"{ESDL_VALIDATOR_URL}/validationToMessages",
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
}
