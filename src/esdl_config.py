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
FLEX_BACKEND_HOST = os.getenv("FLEX_BACKEND_HOST", "http://flexscan:7200")
FLEX_FRONTEND_HOST = os.getenv("FLEX_FRONTEND_HOST", "http://localhost:7201")

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
        # NOTE: To support NWN profile constraint requirement.
        # TODO: Remove these two implementations below after the refinement.
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
        "id": "base_steps_with_table",
        "type": "composite",
        "config": {
          "step_ids": [
            "select_name_and_time_step",
            "select_simulation_period",
            "select_custom_period",
            "select_kpis",
            "start_run",
            "runs_table"
          ]
        },
        "next_step": "base_steps_with_table"
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
        "next_step": "base_steps_with_table",
        "next_step_trigger": "input_change"
      },
      {
        "id": "select_simulation_period",
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
              "id": "year2015",
              "description": "Year 2015",
              "formData": {
                "start_time": "2015-01-01T00:00:00+0100",
                "end_time": "2016-01-01T00:00:00+0100"
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
          "output_wrapper_variable": "selected_simulation_period"
        },
        "next_step": "base_steps_with_table",
        "next_step_trigger": "input_change"
      },
      {
        "id": "select_custom_period",
        "name": "",
        "type": "json-form2",
        "config": {
          "data_from_variable": "selected_simulation_period"
        },
        "data": {
          "from_state": {
            "selected_simulation_period": "selected_simulation_period"
          },
          "to_state": {}
        },
        "next_step": "base_steps_with_table",
        "next_step_trigger": "input_change"
      },
      {
        "id": "select_kpis",
        "name": "",
        "description": "Please select the KPIs that you want to be calculated after the simulation:",
        "type": "select",
        "config": {
          "placeholder": "Select KPI modules",
          "multiple": True,
          "label_fields": [
            "description"
          ],
          "value_field": "id"
        },
        "data": {
          "from_url": {
            "url": "http://essim-engine:8112/essim/simulation/kpiModules/"
          },
          "to_state": {},
          "output_wrapper_variable": "selected_kpis"
        },
        "next_step": "base_steps_with_table",
        "next_step_trigger": "input_change"
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
            "time_step": "time_step"
          },
          "datetimes_convert_Z": True
        },
        "service": {
          "id": "74c9d1a2-c92a-46ed-a7e4-9931971cdd28",
          "description": "",
          "name": "",
          "button_label": "Run Essim Calculation",
          "headers": {
            "User-Agent": "ESDL Mapeditor/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
          },
          "url": "http://essim-engine:8112/essim/simulation",
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
        "next_step": "retrieve_run_progress_results",
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
                "url": "http://essim-engine:8112/essim/simulation/<MODEL_JOB_ID>",
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
        "id": "runs_table",
        "name": "Results overview",
        "description": "",
        "type": "table-external-model",
        "config": {
          "external_model": "essim",
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
      }
    ]
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
        "config": {
          "step_ids": [
            "select_schema",
            "validate_esdl"
          ]
        },
        "next_step": "schema_and_validate"
      },
      {
        "id": "select_schema",
        "name": "Select schema",
        "description": "",
        "type": "select",
        "config": {
          "multiple": False,
          "label_fields": [
            "name"
          ],
          "value_field": "id"
        },
        "data": {
          "from_url": {
            "url": "http://esdl-validator:5000/schema"
          },
          "to_state": {},
          "output_wrapper_variable": "schema"
        },
        "next_step": "schema_and_validate",
        "next_step_trigger": "input_change"
      },
      {
        "id": "validate_esdl",
        "name": "",
        "type": "esdl-service",
        "config": {
          "state_params": {
            "schemas": "schema.id"
          }
        },
        "service": {
          "id": "64c9d1a2-c92a-46ed-a7e4-9931971cbb20",
          "name": "Validate ESDL against schema",
          "description": "",
          "headers": {
            "User-Agent": "ESDL Mapeditor/0.1",
            "Content-Type": "application/xml;charset=UTF-8"
          },
          "url": "http://esdl-validator:5000/validationToMessages/",
          "http_method": "post",
          "type": "send_esdl",
          "query_parameters": [
            {
              "name": "Schemas",
              "description": "ID of the schema to validate this ESDL against",
              "parameter_name": "schemas"
            }
          ],
          "body": "",
          "result": [
            {
              "code": 200,
              "action": "asset_feedback"
            }
          ],
          "with_jwt_token": False,
          "state_params": True
        },
        "button_text": "Validate",
        "previous_step": "select_schema"
      }
    ],
    "show_on_toolbar": True,
    "icon": {
      "filename": "Validator.png",
      "type": "filename"
    }
  }

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
                        # 0
                        "name": "Begin",
                        "description": "How would you like to proceed?",
                        "type": "choice",
                        "options": [
                            # EPS PROJECT
                            {
                                "name": "EPS project",
                                "type": "header",
                            },
                            {
                                "name": "Create a new EPS project",
                                "type": "primary",
                                "next_step": 1,
                                "disable_if_state": "execution.success",
                            },
                            {
                                "name": "Adjust EPS input",
                                "type": "default",
                                "next_step": 13,
                                "disable_if_state": "execution.success",
                            },
                            {
                                "name": "Run EPS", 
                                "type": "primary",
                                "next_step": 4,
                                "disable_if_state": "execution.success",
                            },
                            {
                                "name": "Load EPS",
                                "type": "primary",
                                "next_step": 6,
                                "disable_if_state": "execution.success",
                            },
                            {
                                "name": "Explore EPS results",
                                "type": "default",
                                "enable_if_state": "execution.success",
                                "next_step": 11,
                            },
                            # INFRASTRUCTURE
                            {
                                "name": "Infrastructure",
                                "type": "header",
                            },
                            {
                                "name": "Configure Energy Infrastructure",
                                "type": "default",
                                "enable_if_state":  "execution.success",
                                "next_step": 33,
                            },
                            # ENERGY PROFILES
                            {
                                "name": "Energy profiles",
                                "type": "header",
                            },
                            {
                                "name": "Generate energy profiles template",
                                "type": "default",
                                "enable_if_state": "execution.success",
                                "next_step": 20,
                            },
                            {
                                "name": "Upload energy profiles template",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 21,
                            },
                            # ENERGY SAVING MEASURES
                            {
                                "name": "Energy saving measures",
                                "type": "header",
                            },
                            {
                                "name": "Select EPS measures",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 17,
                            },
                            {
                                "name": "Apply custom energy saving measures",
                                "description": "beta",
                                "type": "default",
                                "enable_if_state": "execution.success",
                                "next_step": 18,
                            },
                            # FLEX SCAN F1
                            {
                                "name": "Flex Scan phase 1 (F1)",
                                "type": "header",
                            },
                            {
                                "name": "Import EPS results into Flex Scan",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "disable_if_state": "flexscanf1.imported",
                                "next_step": 22,
                            },
                            {
                                "name": "Load Flex Scan F1",
                                "type": "primary",
                                "enable_if_state": {
                                    "type": "every",
                                    "conditions": [
                                        "execution.success",
                                        # "flexscanf1.imported"  # TODO: or something like this that is dynamically obtained
                                    ],
                                },
                                "next_step": 24,
                            },
                            {
                                "name": "Explore Flex Scan F1 results",
                                "type": "default",
                                "enable_if_state": "flexscanf1.loaded",
                                "next_step": 26,
                            },
                            # ASSETS
                            {
                                "name": "Assets",
                                "type": "header",
                            },
                            {
                                "name": "Configure your own assets",
                                "type": "default",
                                "enable_if_state": "execution.success",
                                "next_step": 7,
                            },
                            {
                                "name": "Select energy hub assets",
                                "type": "default",
                                "enable_if_state": "flexscanf1.loaded",
                                "next_step": 32,
                            },
                            # EHC
                            {
                                "name": "EHC",
                                "type": "header",
                            },
                            {
                                "name": "Export to EHC",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 27,
                            },
                            {
                                "name": "Load EHC",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 28,
                            },
                            # FLEX SCAN F2
                            {
                                "name": "Flex Scan phase 2 (F2)",
                                "type": "header",
                            },
                            {
                                "name": "Export to Flex Scan F2",
                                "type": "primary",
                                "enable_if_state": "flexscanf1.loaded",
                                "next_step": 29,
                            },
                            {
                                "name": "Load Flex Scan F2",
                                "type": "primary",
                                "enable_if_state": "flexscanf2.loaded",
                                "next_step": 30,
                            },
                            # ESSIM
                            {
                                "name": "ESSIM",
                                "type": "header",
                            },
                            {
                                "name": "Aggregate ESDL buildings for ESSIM",
                                "type": "dashed",
                                "enable_if_state": "execution.success",
                                "next_step": 12,
                            },
                            {
                                "name": "Run ESSIM",
                                "type": "primary",
                                "enable_if_state": "execution.success",
                                "next_step": 31,
                            },
                            {
                                "name": "Export results",
                                "type": "primary",
                                "enable_if_state": "essim.success",
                                "next_step": 19,
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
                        "target_variable": "project",
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
                        "success_text": "The newly uploaded file can be used to start a new EPS run.",
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
                                    "message": "EPS started successfully! It can take up to 45 minutes for the EPS to complete. When it is complete, the results can be found under 'Resultaten' in the EPS Web environment."
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
                        "name": "Select EPS execution",
                        "description": "",
                        "label": "Choose the EPS execution from which to load the results.",
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
                        "next_step": 10,
                    },
                    {
                        # 7
                        "name": "Configure your own assets",
                        "description": "",
                        "type": "text",
                        "text": "At this point of the workflow you can safely add any assets and connections, to model your energy system. Please make sure that you have selected the EPS measures you are interested in, and that you have applied any custom measures if applicable. Selecting different EPS measures will result in a new ESDL being generated, such that your previous changes will not be preserved.",
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
                        "name": "Load EPS",
                        "description": "Please wait a moment while we load the EPS output as ESDL. This ESDL contains the energy system with no measures applied. When the EPS is loaded, please continue.",
                        "type": "service",
                        "state_params": {"execution_id": "execution.id"},
                        "service": {
                            "id": "9bd2f969-f240-4b26-ace5-2e03fbc04b12",
                            "name": "Visualize EPS",
                            "headers": {
                                "Accept": "application/esdl+xml",
                                "User-Agent": "ESDL Mapeditor/0.1",
                            },
                            "url": f"{EPS_WEB_HOST}/api/eps/<execution_id>/esdl/variant",
                            "auto": True,
                            "clearLayers": True,
                            "http_method": "post",
                            "type": "json",
                            "result": [{"code": 200, "action": "esdl"}],
                            "query_parameters": [
                                {
                                    "name": "File Name",
                                    "location": "url",
                                    "parameter_name": "execution_id",
                                }
                            ],
                            "with_jwt_token": True,
                        }
                    },
                    {
                        # 11
                        "name": "Explore EPS results",
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
                        "target_variable": "file",
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
                                "file_name": "file.id",
                            },
                        },
                    },
                    {
                        # 17
                        "name": "Select EPS measures",
                        "description": "",
                        "type": "custom",
                        "component": "eps-select-measures",
                        "state_params": {"execution_id": "execution.id"},
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
                        }
                    },
                    {
                        # 18
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
                        }
                    },
                    {
                        # 19
                        "name": "Export ESSIM results",
                        "description": "",
                        "type": "custom",
                        "component": "dice-export-essim",
                    },
                    {
                        # 20
                        "name": "Generate profile template",
                        "description": "",
                        "type": "custom",
                        "component": "dice-generate-profile-template",
                    },
                    {
                        # 21
                        "name": "Upload profiles",
                        "type": "custom",
                        "component": "dice-upload-profiles",
                    },
                    # {
                    #     # TODO: for future reference, if we ever want to start / run flex scan f1 from mapeditor
                    #     # 22
                    #     "name": "Run Flex Scan F1",
                    #     "description": "Please wait a moment while we run the Flex Scan phase 1",
                    #     "type": "service",
                    #     "state_params": {"execution_id": "execution.id"},
                    #     "service": {
                    #         "id": "f25dfd1a-525d-42db-92d6-6d358bbdfca0",
                    #         "name": "Run Flex Scan phase 1",
                    #         "headers": {
                    #             "Accept": "application/json",
                    #             "User-Agent": "ESDL Mapeditor/0.1",
                    #         },
                    #         "url": f"{FLEX_BACKEND_HOST}/eps/<execution_id>/import",
                    #         "auto": True,
                    #         "clearLayers": False,
                    #         "http_method": "post",
                    #         "type": "json",
                    #         "result": [
                    #             {
                    #                 "code": 200, 
                    #                 "action": "show_message",
                    #                 "message": "Flex Scan Phase 1 started",
                    #             },
                    #         ],
                    #         "query_parameters": [
                    #             {
                    #                 "name": "Execution ID",
                    #                 "parameter_name": "execution_id",
                    #                 "location": "url",
                    #             },
                    #         ],
                    #         "with_jwt_token": True,
                    #     },
                    #     "next_step": 23
                    # },
                    {
                        # 22
                        "name": "Import EPS data into Flex Scan",
                        "description": "",
                        "type": "custom",
                        "component": "flexscan-import-eps",
                        "custom_data": {
                            "flex_frontend_host": FLEX_FRONTEND_HOST,
                        },
                    },
                    {
                        # 23
                        # TODO: placeholder for when we might allow multiple flex scan runs for a single EPS based on scenario (e.g. EPS measures)
                        "name": "Load Flex Scan F1 results",
                        "description": "Load Flex Scan phase 1 results. If no results are shown, you must first import the EPS data and/or accept the phase 1 results (see previous step).",
                        "label": "Choose Flex Scan F1 run",
                        "type": "select-query",
                        "multiple": False,
                        "source": {
                            "url": f"{FLEX_BACKEND_HOST}/executions/",
                            "http_method": "get",
                            "choices_attr": "",
                            "label_fields": ["project_name", "phase1_completed_on"],
                            "value_field": "id",
                            "with_jwt_token": True
                        },
                        "target_variable": "flexscan",
                        "next_step": 24
                    },
                    {
                        # 24
                        "name": "Select Flex Scan F1 year",
                        "description": "Choose the year for which you want to load the Flex Scan Phase 1 results. N.B. make sure to select the correct ESDL layer you wish to use as base for the Flex Scan F1 results.",
                        "type": "choice",
                        "options": [
                            {
                                "name": "2020",
                                "description": "",
                                "next_step": 25,
                                "target_variable_value": {
                                    "year": 2020
                                }
                            },
                            {
                                "name": "2025",
                                "description": "",
                                "next_step": 25,
                                "target_variable_value": {
                                    "year": 2025
                                }
                            },
                            {
                                "name": "2030",
                                "description": "",
                                "next_step": 25,
                                "target_variable_value": {
                                    "year": 2030
                                }
                            },
                        ],
                        "target_variable": "flexscanf1",
                    },
                    {
                        # 25
                        "name": "Load Flex Scan F1",
                        "type": "service",
                        "state_params": {
                            "execution_id": "execution.id",
                            "year": "flexscanf1.year"
                        },
                        "service": {
                            "id": "f25dfd1a-525d-42db-92d6-6d358bbdfca1",
                            "name": "Load Flex Scan phase 1 results",
                            "headers": {
                                "Accept": "application/json",
                                "User-Agent": "ESDL Mapeditor/0.1",
                                "Content-Type": "application/json",
                            },
                            "url": f"{FLEX_BACKEND_HOST}/executions/<execution_id>/phase1/esdl/<year>",
                            "auto": True,
                            "clearLayers": False,
                            "http_method": "post",
                            "type": "send_esdl_json",
                            "body": "base64_encoded",
                            "result": [{"code": 200, "action": "esdl"}],
                            "query_parameters": [
                                {
                                    "name": "Execution ID",
                                    "parameter_name": "execution_id",
                                    "location": "url",
                                },
                                {
                                    "name": "Flex Scan F1 year",
                                    "parameter_name": "year",
                                    "location": "url",
                                }
                            ],
                            "with_jwt_token": True,
                        },
                        # "target_variable": "flexscanf1.year",  # when wanting to set loaded per year
                        "target_variable": "flexscanf1",
                        "target_variable_value": {
                            "loaded": True
                        },
                    },
                    {
                        # 26
                        # TODO: for now link to Flex Scan dashboard F1 results table, optionally later this table could be displayed in the map-editor or KPI layers could be added like for EPS
                        "name": "Explore Flex Scan F1 results",
                        "description": "",
                        "type": "custom",
                        "component": "flexscan-inspect-phase1",
                        "custom_data": {
                            "flex_frontend_host": FLEX_FRONTEND_HOST,
                        },
                    },
                    {
                        # 27
                        # TODO: choose correct type and implement
                        "name": "Export to EHC",
                        "description": "",
                        "type": "text",
                        "text": "The currently active ESDL is being exported to the EHC...",
                    },
                    {
                        # 28
                        # TODO: choose correct type and implement
                        "name": "Load EHC",
                        "description": "",
                        "type": "text",
                        "text": "Work in progress...",
                    },
                    {
                        # 29
                        # TODO: choose correct type and implement
                        "name": "Run/export for Flex Scan F2",
                        "description": "",
                        "type": "text",
                        "text": "Work in progress...",
                    },
                    {
                        # 30
                        # TODO: choose correct type and implement
                        "name": "Load Flex Scan F2",
                        "description": "",
                        "type": "text",
                        "text": "Work in progress...",
                    },
                    {
                        # 31
                        # TODO: choose correct type and implement
                        "name": "Run ESSIM",
                        "description": "",
                        "type": "text",
                        "text": "An ESSIM run can be started via the ESSIM button on the left side of the ESDL Map Editor",
                    },
                    {
                        # 32
                        # TODO: choose correct type and implement
                        "name": "Select energy hub assets",
                        "description": "",
                        "type": "text",
                        "text": "Work in progress...",
                    },
                    {
                        # 33
                        # TODO: choose correct type and implement
                        "name": "",
                        "description": "",
                        "type": "text",
                        "text": """
                            A basic theoretical configuration of the electricity and gas infrastructure has been generated by the EPS. 
                            In this step, this configuration can be adjusted to reflect the actual situation, and the infrastructure attributes can be set. 
                            This can be done using the ESDL Map Editor functionalities.
                        """,
                    },
                ],
            },
        ],
    },
}
