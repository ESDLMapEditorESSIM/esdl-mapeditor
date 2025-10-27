# Workflow step types

Below is a list of the available workflow step types following steps (click to view details and configuration options):

- [choice](#choice): user can select one or multiple from defined options.
- [select](#select): user can select from options originating from an api endpoint.
- [table](#table): show a table with row actions.
- [table-external-model](#table-external-model): show a table with runs for an external model with row actions.
- [esdl-service](#esdl-service): call an esdl service, such as an api request with the active esdl as parameter.
- [json-form2](#json-form2): json-forms input, from url, socket or config.
- [download_file](#download_file)
- [upload_file](#upload_file)
- [get-send-data](#get-send-data): allows for retrieving data and sending on, for instance from state to an url.
- [http_post](#http_post)
- [call_js_function](#call_js_function): call a javascript function.
- [progress](#progress)
- [text](#text): display text, from socket or config.
- [workflow-engine-monitor](#workflow-engine-monitor): follow the progress of a workflow engine sequence.
- [composite](#composite): display several step simultaneously.
- [custom](#custom): custom Vue component.

For all types the [data](steps_general.md#data) configuration determines how to get and send data. Each type has
specific formats for the required input data and created output data. These are discussed below.

### `choice`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

Allows the user to choose between a number of options. The options are defined in the `options` field of the step. The
options are a list of objects, where each object has a `name` and a `next_step` field. The `name` field is the text that
is shown to the user. The `next_step` field is the step id that is executed when the user selects this option.

An option can also have a `type` field. This is passed along to the button that is shown to the user. This allows for
different types of buttons, for example a primary button or a secondary button. The `type` field is optional, and if
not specified, the default type `primary` is used.

### `select`

The `select` step lets the user select (a) value(s) from a dropdown.

#### `config` options

- `multiple`: boolean flag to determine single or multiple selection mode.
- `label_fields`: list of key names, the values of these keys in the option object (see input data) will be concatenated
  with a `_` to form the label shown to the user.
- `value_field`: key of a unique field in each option by which to identify the selected option(s).

#### required input data

The required input consists of a list of object with key-value pairs. The values can be dicts as well.

#### output data

The object from the input data list which is selected by the user. In the `multiple` mode the output will be a list of
selected objects (possibly empty).

Example config:

```json
{
  "id": "select_workflow_type",
  "name": "",
  "description": "Please select the Omotes workflow type for the calculation:",
  "type": "select",
  "config": {
    "multiple": false,
    "label_fields": [
      "description"
    ],
    "value_field": "id"
  },
  "data": {
    "from_url": {
      "url": "http://localhost:9200/workflow/"
    },
    "to_state": {},
    "output_wrapper_variable": "selected_workflow_type"
  },
  "next_step": "base_steps_with_table",
  "next_step_trigger": "input_change"
}
```

## `table`

This Workflow step shows a table and allows you to specify actions (next workflow steps) based on what the user selects
in the action column.

#### `config` options

For more details see the json example below.

- `columns`: list of columns to be displayed using which keys (dataIndex).
- `actions`: list of actions with `title`, `icon`, `next_step` and `enabled` options.
- `value_field`: key of a unique field in each row by which to identify.
- `additional_fields`: list of key values that will also be added to the workflow state along with the `value_field`.
- `row_selection`: optional row selection with `type` of `radio` or `checkbox` and `enabled` option with `dataIndex` and
  `condition`.

#### required input data

The required input consists of a list of row objects with key-value pairs. The values can be dicts as well.

#### output data

When an action is clicked for a specific row, the `value_field` and `additional_fields` are added to the state. There is
no real output data from this component.

Example config:

```json
     {
  "id": "choose_geothermal_source",
  "name": "Select one of the aquifers below",
  "description": "Properties from regional nation-wide maps: a local study will give more reliable results.",
  "type": "table",
  "config": {
    "columns": [
      {
        "dataIndex": "name",
        "title": "Name",
        "ellipsis": true
      },
      {
        "dataIndex": "aquiferTemperature",
        "title": "Temperature [\u00B0C]"
      },
      {
        "dataIndex": "flowRate",
        "title": "Flow Rate [kg/s]"
      },
      {
        "dataIndex": "power",
        "title": "Power [W]"
      }
    ],
    "row_selection": {
      "type": "radio",
      "enabled": {
        "dataIndex": "power",
        "condition": {
          "type": "larger_than",
          "value": 0
        }
      }
    },
    "value_field": "name"
  },
  "data": {
    "from_url": {
      "url": "http://localhost:6300/api/query",
      "request_params": [
        {
          "name": "lat",
          "parameter_name": "lat"
        },
        {
          "name": "lng",
          "parameter_name": "lng"
        },
        {
          "name": "service_identifier",
          "value": "geothermal_layer_selection"
        }
      ]
    },
    "to_state": {
    },
    "output_wrapper_variable": "chosen_aquifer_row"
  },
  "next_step_trigger": "input_change"
}
```

## `table-external-model`

This Workflow step shows a table of all runs for an external model with run actions. There is also a filter to only show
run from a specific project or group.
The following run actions are available:

- Load result
- View feedback (if `has_feedback_messages`)
- View details
- Edit
- Download xlsx (if `time_series_xlsx_download`)
- Delete

#### `config` options

For more details see the json example below.

- `external_model`: name of the external model.
- `model_short_name`: a short name to be displayed in the result visualization.
- `has_feedback_messages`: boolean flag for feedback messages from a model run.
- `result_animation`: activates the ESDL animation option with the optional `influxdb_host_override` which can be useful
  for local development when the profiles in the esdl point to another host, the `filter_on_tag` determines how to
  extract data from influxdb.
- `result_external_link`: activates the option of displaying an external link to model run results.
- `delete_result_url`: optional external model endpoint to also delete data from the external model database when
  deleting a run.
- `time_series_xlsx_download`: activates the time series download to xlsx option. There are quite some configuration
  settings, see below for essim format, here is also an optional `influxdb_host_override`.

#### required input data

The required input consists of a list of row objects with key-value pairs. The values can be dicts as well.

#### output data

There is no output data from this component.

Example config:

```json
{
  "id": "runs_table",
  "name": "Results overview",
  "description": "",
  "type": "table-external-model",
  "config": {
    "external_model": "essim",
    "model_short_name": "essim",
    "result_animation": {
      "filter_on_tag": {
        "tag_name": "simulationRun",
        "value_database_key": "model_job_id"
      },
      "influxdb_host_override": "localhost"
    },
    "result_external_link": {
      "description": "Open Dashboard",
      "value_database_key": "model_specific_output.dashboardURL"
    },
    "delete_result_url": "http://localhost:9200/job/<MODEL_JOB_ID>",
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
      ],
      "influxdb_host_override": "localhost"
    }
  },
  "data": {
    "from_socket": {
      "event": "get_external_model_runs_for_user",
      "params": {
        "external_model_name": "omotes"
      }
    },
    "output_wrapper_variable": "model_run"
  },
  "with_jwt_token": true
}
```

## `esdl-service`

**The `source` section is to be updated to match the new setup, see [Workflow steps](steps_general.md)
This will be after the refactor of `esdl_services.py`.**

This step allows the user to call an ESDL Service. The ESDL Service is defined in the `service` field of the step.
This field is a JSON object, and can contain any ESDL Service that can also be defined outside the Workflow module,
as its own ESDL Service.

If the service returns an ESDL, the ESDL is loaded into the ESDL MapEditor and optionally saved into the external models
mongodb database.

More info to come after the update.

Example config for sending an ESDL to an external model:

```json
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
    "datetimes_convert_Z": true
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
    "url": "http://localhost:8112/essim/simulation",
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
    "with_jwt_token": false,
    "state_params": true
  },
  "next_step": "retrieve_run_progress_results",
  "workflow_engine": {
    "run_name": "state_params.run_name",
    "workflow_engine_next_step": "retrieve_run_progress_results"
  }
}
```

Example config for loading an ESDL from an external model run:

```json
{
  "id": "load_run_results",
  "name": "Load ESDL",
  "description": "Loads the result in the ESDL MapEditor",
  "type": "esdl-service",
  "config": {
    "state_params": {
      "run_id": "model_run.run_id",
      "run_name": "model_run.run_name"
    }
  },
  "service": {
    "id": "x1c9d1a2-c92a-46qd-a7e4-9931971cbb33",
    "name": "Load ESDL results",
    "description": "The results should have been loaded in the MapEditor",
    "button_label": "Go back to results",
    "auto": true,
    "type": "",
    "external_model": "essim",
    "result": [
      {
        "action": "esdl",
        "run_esdl_key": "input_esdl",
        "model_short_name": "essim",
        "animation": {
          "filter_on_tag": {
            "tag_name": "simulationRun",
            "value_database_key": "model_job_id"
          }
        },
        "external_link": {
          "description": "Open Dashboard",
          "value_database_key": "model_specific_output.dashboardURL"
        }
      }
    ],
    "with_jwt_token": true,
    "state_params": true
  },
  "next_step": "base_steps_with_table",
  "next_step_trigger": "loading_complete"
}
```

## `json-form2`

Allows the user to enter data in a form defined as a JSON schema. Input validation occurs when rules are provided.
See https://json-schema.org/ for more information on JSON schemas. The JSON schema is stored in the `schema` field of
the step.

#### `config` options

For more details see the json example below.

- `data_from_variable`: name of the key in the input data which holds the input data, if not present the data is
  expected to be in the root of the input data object.

#### required input data

The required input consists three objects of which the first is obligatory: `schema`, `uischema` and `formdata`. More
information on these can be found on https://json-schema.org/, an example can be found below.

#### output data

The `formData` object is updated on user input, this will be sent as output.

Example config with schema specified in the config:

```json
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
}
```

Example config with data from state:

```json
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
}
```

## `download_file`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

## `upload_file`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

## `get-send-data`

Allows for retrieving data and sending on, for instance from state and socket to an url. The sending can be done
automatically after the data is loaded or after a button click, see the `next_step_trigger`
in [General workflow step parameters](steps_general.md#general-workflow-step-parameters).

#### `config` options

For more details see the json example below.

- `text_below_button_variable`: optional input data object variable key to text that will be displayed below the button
  as information.

#### required input data

There is no required input data format other than that it should match the destination where it is sent on to.

#### output data

The input data is sent as output data as is.

Example config to delete a model run via a socket event. An information text about the run is displayed below the
button.

```json
{
  "id": "delete_run",
  "name": "Delete model run",
  "description": "Are you sure you want to delete all run data (see below)?",
  "type": "get-send-data",
  "config": {
    "text_below_button_variable": "model_text"
  },
  "data": {
    "from_config": {
      "delete_result_url": "http://localhost:9200/job/<MODEL_JOB_ID>"
    },
    "from_state": {
      "run_id": "model_run.run_id"
    },
    "from_socket": {
      "event": "external_models_get_run_text",
      "state_params": {
        "run_id": "model_run.run_id"
      },
      "wrapper_variable": "model_text"
    },
    "to_socket": {
      "event": "external_models_delete_run"
    }
  },
  "button_text": "Delete",
  "next_step": "base_steps_with_table"
}
```

## `http_post`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

## `call_js_function`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

This step allows the user to call a JavaScript function. The function is defined in the `function` field of the step.

## `progress`

**To be updated to match the new setup, see [Workflow steps](steps_general.md)**

## `text`

A text display component.
No configuration options (yet) and no output is sent. The input is expected to be text or html.

Example config:

```json
{
  "id": "view_run_details",
  "name": "View model run details",
  "type": "text",
  "data": {
    "from_socket": {
      "event": "external_models_get_run_text",
      "state_params": {
        "run_id": "model_run.run_id"
      }
    }
  },
  "button_text": "Back",
  "next_step": "base_steps_with_table"
}
```

## `workflow-engine-monitor`

A workflow component that specifies a workflow engine step. It contains actions to be done in by the workflow engine.
So far there are twp actions available: `model_run_result_polling` and `model_run_show_results`.
It can also be displayed in the frontend in which case it will only follow the progress of a workflow engine sequence.
The workflow engine will run this step regardless of whether it is displayed. There is no input or output data
involved.  
A possible next action can be invoked upon completion of the step using the `workflow_engine`,
`workflow_engine_next_step` key, see example below.

#### `config` options

The available options:

- `model_run_result_polling`: poll status/result endpoint(s) of an external model to track a model run progress and
  finally obtain the results. Several things are needed for this:
    - `response_mapping`: which response keys hold the status and progress.
    - `model_specific_response_mapping`: which response keys to also save which as model specific.
    - `status_mapping`: how to map the external model statuses to mapeditor statuses.
    - `retry_interval_seconds`: how often to poll.
    - `maximum_wait_seconds`: maximum polling time.
- `model_run_show_results`: show run results: a list of database item keys to show the value of.
  A list of row items is each needed each of which can contain:
    - `value_database_key`: the mongodb key for which to show the value (can be nested with dot)
    - `description`: optional, if present this description will be printed in front of the value
    - `link_text`: optional, this will convert the value into a link with the provided `link_text`.

Example config for two consecutive steps: first follow the progress and on completion show results:

```json
[
  {
    "id": "retrieve_run_progress_results",
    "monitor_name": "Running Essim Calculation...",
    "type": "workflow-engine-monitor",
    "config": {
      "model_run_result_polling": {
        "query_list": [
          {
            "url": "http://localhost:8112/essim/simulation/<MODEL_JOB_ID>",
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
    },
    "workflow_engine": {
      "workflow_engine_next_step": "show_run_results"
    }
  },
  {
    "id": "show_run_results",
    "monitor_name": "Essim Result",
    "type": "workflow-engine-monitor",
    "config": {
      "model_run_show_results": [
        {
          "description": "essim ID",
          "value_database_key": "model_specific_output.scenarioID"
        },
        {
          "value_database_key": "model_specific_output.dashboardURL",
          "link_text": "Open dashboard"
        }
      ]
    }
  }
]
```

## `composite`

A composite workflow step that consists of several child steps that are displayed simultaneously.
Data can be directly relayed between the child steps by using:

```json
{
  "next_step": "id_of_the_composite_step",
  "next_step_trigger": "input_change"
}
```

This will submit the data on UI input and by going to the composite step again (the view does not change) the other
child steps data are updated.

There is no input or output data involved, this is specified in the child steps themselves.

#### `config` options

There is only one mandatory config parameter:

- `step_ids`: a list of child step id's to be displayed simultaneously.

Example config:

```json
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
}
```

## `custom`

A custom component can be any Vue component that is hooked up to the Workflow module. This is done by adding the
component to the `WorkflowCustomComponent.vue` file. This file contains a `components` object, which is a mapping from
component name to component. The component name is the name that is used in the `type` field of the step. The component
is the Vue component that is used to render the step.
