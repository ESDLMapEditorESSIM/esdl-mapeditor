# Workflow steps

A workflow is defined as a list of steps. Each step has a type. The type determines what the step does.

A fully up-to-date set of workflow steps can be found by looking at Workflow.vue. This basically contains a large
if-else-if statement, where each if-else-if corresponds to a step type. Alternatively, look at the `workflow.js` file,
which contains an enum of all possible steps.

We currently have the following steps (click to view details and configuration options):

- [choice](#choice): user can select from defined options. 
- [select-query](#select-query): user can select from options originating from an api endpoint.
- [multi-select-query](#multi-select-query): user can multiple select from options originating from an API endpoint.
- [table-query](#table-query): show a table from rest or socket call, with row actions.
- [service](#service): call an `esdl_service`, such as an api call with the active esdl as parameters.
- [json-form2](#json-form2): json-forms input, from url, socket or config.
- [download_file](#download_file)
- [upload_file](#upload_file)
- [get_data](#get_data)
- [http_post](#http_post)
- [call_js_function](#call_js_function): call a javascript function.
- [progress](#progress)
- [text](#text): display text, from socket or config.
- [workflow-engine-monitor](#workflow-engine-monitor): follow the progress of a workflow engine sequence.
- [custom](#custom): custom Vue component.


## `choice`

Allows the user to choose between a number of options. The options are defined in the `options` field of the step. The
options are a list of objects, where each object has a `name` and a `next_step` field. The `name` field is the text that
is shown to the user. The `next_step` field is the step that is executed when the user selects this option. The `next_step`
field can be a string, in which case it is the ID of the step to execute. If it is an integer, it is the index of the
step to execute.

An option can also have a `type` field. This is passed along to the button that is shown to the user. This allows for
different types of buttons, for example a primary button or a secondary button. The `type` field is optional, and if
not specified, the default type `primary` is used.

## `select-query`

The `select-query` step performs a request to an API endpoint, and allows the user to select one of the results. The
results are shown in a dropdown, and the user can select one of the options. The selected option is stored in the
workflow state.  

Example config:
```json
{
  "reference": "select_workflow_type", // optional reference, can be used as human readable alternative to index for 'next_step'
  "name": "", // if empty no header will be displayed above the step (used when 'co-viewing' steps)
  "description": "Please select the Omotes workflow type for the calculation.",
  "type": "select-query",
  "multiple": false,
  "source": {
    "url": "http://localhost:9200/workflow/",
    "http_method": "get",
    // "choices_attr": "attribute name", // optional response field containing the choices, if not present the response is assumed to contain the choices directly
    "label_fields": [
      "description"
    ], // response fields used to construct the displayed label separated by ' - '
    "value_field": "id" // response field containing the value
  },
  "target_variable": "chosen_workflow_type", // state variable name where the chosen value will be stored.
  "next_step": "base_steps_with_table",
  "auto_next_step": true
}
```

## `multi-select-query`

The `multi-select-query` step performs a request to an API endpoint, and allows the user to select one or more of the
results. The results are shown in a dropdown, and the user can select one or more of the options. The selected options
are stored in the workflow state. (Not implemented yet)


## `table-query`

This Workflow step shows a table from a REST query and allows you to specify actions (next workflow steps) based on what
the user selects in the action column.

Example config using `from_socket`:
```json
{
  "reference": "runs_table",
  "name": "Results overview",
  "description": "",
  "type": "table-query",
  "show_reload_button": false,
  "source": {
    "from_socket": {
      "event": "get_external_model_runs_for_user",
      "params": {
        "external_model_name": "essim"
      }
    },
    "columns": [ // columns is based on antdv 2.0 column syntax.
      {
        "dataIndex": "run_name", // dataIndex is required, links to the attribute in the REST result json
        "title": "Name", // also required, used as column title
        "ellipsis": true // see AntDV: longer text gets abbreviated with ...
      },
      {
        "dataIndex": "status",
        "title": "Status",
        "align": "center",
        "slots": { // use a specific template to render this column. Two are currently supported: tags and actions (for action column)
          "customRender": "tags"
        }
      },
      {
        "dataIndex": "submitted_to_external_model_at",
        "title": "Submitted",
        "formatter": "formatDate", // special attribute for this component: formatter links to a javascript function in this class
        "defaultSortOrder": "descend" // formatDate also contains sorting of column
      }
    ],
    "actions": [ // Defines the actions that can be done on the row
      {
        "title": "Load result", // title of the action for hoover tip and clickable text if no `icon` is specified
        "icon": "far fa-eye", // clickable icon
        "next_step": "load_run_results", // when button is clicked, the workflow moves to this step (e.g. call ESDL Service)
        "enabled": { // defines rules to enable/disable this action based on another column value
          "dataIndex": "status", // check 'status' dataIndex column for specific values. If status === values[] then enable this action
          "values": [
            "SUCCEEDED"
          ]
        }
      },
      {
        "title": "View details",
        "icon": "fas fa-info-circle",
        "next_step": "view_run_details"
      },
      {
        "title": "Edit",
        "icon": "far fa-edit",
        "next_step": "edit_run"
      },
      {
        "title": "Delete",
        "icon": "far fa-trash-alt",
        "to_socket": {
          "event": "external_models_delete_run",
          "params": {
            "delete_result_url": ""
          },
          "record_params": {
            "run_id": "run_id"
          }
        }
      }
    ],
    "value_field": "run_id", // the uniqe key to identify each row stored in the state (using target_variable): `model_run.run_id`
    "additional_fields": [
      "run_name"
    ] // additional record (row) field added to the state: `model_run.run_name`
  },
  "target_variable": "model_run",
  "with_jwt_token": true
}
```
Example config using `url`:
```json
{
  "name": "Results overview",
  "description": "",
  "type": "table-query",
  "source": {
    "url": "http://localhost:9200/job/",
    "http_method": "get",
    "request_params": {
      "username": "session.email"
    }, // add extra request params. session.* are handled in the backend
    "columns": [ //  columns is based on antdv 2.0 column syntax.
      {
        "dataIndex": "job_name", // dataIndex is required, links to the attribute in the REST result json
        "title": "Name", // also required, used as column title
        "key": "job_name", // give this column a specific key. Not required currently
        "ellipsis": true // see AntDV: longer text gets abbreviated with ...
      },
      {
        "dataIndex": "status",
        "title": "Status",
        "key": "status",
        "slots": { // use a specific template to render this column. Two are currently supported: tags and actions (for action column)
          "customRender": "tags"
        }
      },
      {
        "dataIndex": "stopped_at",
        "title": "Finished at",
        "key": "stopped_at",
        "formatter": "formatDate", // special attribute for this component: formatter links to a javascript function in this class
        "sortOrder": "descend" // formatDate also contains sorting of column
      }
    ],
    "actions": [ // Defines the actions that can be done on the row
      {
        "title": "Load result",  // title of the action
        "next_step": 2, // when button is clicked, the workflow moves to this step (e.g. call ESDL Service).
        "enabled": { // defines rules to enable/disable this action based on another column value
          "dataIndex": "status",  // check 'status' dataIndex column for specific values. If status === values[] then enable this action
          "values": [
            "SUCCEEDED"
          ]
        }
      },
      {
        "title": "Show log",
        "next_step": 3
      }
    ],
    "value_field": "job_id" // the uniqe key to identify each row, and is stored in the state (using target_variable)
  },
  "target_variable": "job",
  "next_step": 1
}
```


## `service`

This step allows the user to call an ESDL Service. The ESDL Service is defined in the `esdl_service` field of the step.
This field is a JSON object, and can contain any ESDL Service that can also be defined outside the Workflow module,
as its own ESDL Service.

If the service returns an ESDL, the ESDL is loaded into the ESDL MapEditor.

Example config for sending active ESDL to api endpoint:
```json
{
  "reference": "start_run",// optional reference, can be used as human readable alternative to index for 'next_step'
  "name": "", // if empty no header will be displayed above the step (used when 'co-viewing' steps)
  "description": "",
  "type": "service",
  "state_params": {
    "run_name": "run_name" // state parameter to use (from previous steps)
  },
  "service": {
    "id": "74c9d1a2-c92a-46ed-a7e4-9931971cdd28",  // must be a unique id
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
        "parameter_name": "run_name", // parameter value picked up from the state (see above)
        "location": "body"
      },
      {
        "name": "user",
        "description": "essim user",
        "value": "essim", // value direct from this config
        "location": "body"
      },
      {
        "name": "startDate",
        "description": "start date",
        "value": "2019-01-01T00:00:00+0100",
        "location": "body"
      },
      {
        "name": "endDate",
        "description": "end date",
        "value": "2020-01-01T00:00:00+0100",
        "location": "body"
      },
      {
        "name": "timeStep",
        "description": "time step",
        "value": "1h",
        "location": "body"
      },
      {
        "name": "influxURL",
        "description": "influx url",
        "value": "http://influxdb:8086",
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
          "parameter": "esdlContents" // send active ESDL base64 encoded as this body parameter
        },
        {
          "type": "esdl_id",
          "parameter": "scenarioID" // send active ESDL ID as this body parameter
        }
      ]
    },
    "result": [ // actions to be done with the result from the api post
      {
        "code": 200,
        "action": "save_model_run", // save external model run to mongodb
        "external_model_name": "essim", // name of the external model to be recorded in mongodb
        "external_model_id_response_param": "id", // model id parameter field in the response
        "run_name_state_param": "run_name" // run name parameter field in the response
      }
    ],
    "with_jwt_token": false,
    "state_params": true
  },
  "workflow_engine_trigger": true, // trigger the workflow engine: this step and following steps will not be performed by Vue but by the backend
  "workflow_engine_run_name": "state_params.run_name", // name of the worflow engine run (sequence)
  "next_step": "retrieve_run_progress_results", // step to display by Vue after starting the workflow engine (workflow-engine-monitor or table-query)
  "workflow_engine_next_step": "retrieve_run_progress_results" // optional next workflow engine calculation step
}
```
Example config for loading an ESDL from an external model run:
```json
{
  "reference": "load_run_results",
  "name": "Load ESDL",
  "description": "Loads the result in the ESDL MapEditor",
  "type": "service",
  "state_params": {
    "run_id": "model_run.run_id",
    "run_name": "model_run.run_name"
  },
  "service": {
    "id": "x1c9d1a2-c92a-46ed-a7e4-9931971cbb33",
    "name": "Load ESDL results",
    "description": "The results should have been loaded in the MapEditor",
    "button_label": "Go back to results",
    "auto": true,
    "type": "",
    "external_model": "essim", // identify that ESDL is to be retrieved from the 'external_model_runs` collection
    "result": [
      {
        "action": "esdl",
        "run_esdl_key": "input_esdl", // parameter in the external model run mongodb doc
        "model_short_name": "essim", // name to be displayed in the `ResultVisualizationsToolbar`
        "animation": { // identify that the ESDL influxdb data for pipes/cables can be animated
          "filter_on_tag": { // optional filter on influxdb query (for essim multiple runs stored in `input ESDL id` collection)
            "tag_name": "simulationRun", // tag to filter on
            "database_key": "model_job_id" // filter value from mongodb key (parameter)
          }
        },
        "external_link": { // optional link in the `ResultVisualizationsToolbar`
          "description": "Open Dashboard",
          "database_key": "model_specific_output.dashboardURL" // mongodb doc key containing the external link
        }
      }
    ],
    "with_jwt_token": true,
    "state_params": true,
    "next_step": "base_steps_with_table"
  }
}
```

## `json-form2`

Allows the user to enter data in a form. The data is stored in the workflow state. The form is defined as a JSON schema.
See https://json-schema.org/ for more information on JSON schemas. The JSON schema is stored in the `schema` field of
the step.

Alternatively, it is possible to retrieve the schema from a URL. This is done by setting the `url` field of the
step. The URL should return a JSON schema. When submitting the step, the data is then send as a POST request to the same
URL.

Example config with schema specified in the config:
```json
{
  "reference": "base_steps_with_table",
  "name": "New Run",
  "type": "json-form2",
  "data": {
    "schema": {
      "type": "object",
      "properties": {
        "run_name": {
          "type": "string",
          "minLength": 3,
          "title": "Name"
        }
      },
      "required": [
        "run_name"
      ]
    }
  },
  "next_step": "base_steps_with_table",
  "auto_next_step": true,
  "co_view_steps": [ // steps that will be displayed simulataneously
    "start_run",
    "runs_table"
  ]
}
```
Example config with schema from socket:
```json
{
  "reference": "edit_run",
  "name": "Edit model run",
  "type": "json-form2",
  "data": {
    "from_socket": { // socket emit to get json-forms config
      "event": "external_models_get_run_jsonforms", // socket emit event
      "state_params": { // state parameters to be send along with the socket emit
        "run_id": "model_run.run_id"
      }
    },
    "to_socket": { // socket emit on click button with data dict from jsonforms
      "event": "external_models_update_run"
    }
  },
  "button": "Save",
  "next_step": "base_steps_with_table"
}
```

## `download_file`

## `upload_file`

## `get_data`

## `http_post`

## `call_js_function`

This step allows the user to call a JavaScript function. The function is defined in the `function` field of the step.

## `progress`

## `text`

A text display component.

Example config:
```json
{
  "reference": "view_run_details",
  "name": "View model run details",
  "type": "text",
  "data": {
    "from_socket": { // socket emit to get text
      "event": "external_models_get_run_text", // socket emit event
      "state_params": { // state parameters to be send along with the socket emit
        "run_id": "model_run.run_id"
      }
    }
  },
  "next_step": "base_steps_with_table"
}
```

## `workflow-engine-monitor`

Workflow component that specifies a workflow engine step, reached by `workflow_engine_next_step`.
It can also be displayed in the frontend by `next_step` to follow the progress of a workflow engine sequence.
The workflow engine will run this step regardless of whether it is displayed.

Example config:
```json
{
  "reference": "retrieve_run_progress_results",
  "monitor_name": "Running Essim Calculation...", // Name to be displayed in the workflow monitor 
  "type": "workflow-engine-monitor",
  "queries": [ // queries to be executed by the workflow engine, other actions to be added.
    {
      "url": "http://localhost:8112/essim/simulation/<MODEL_JOB_ID>",
      "response_mapping": { // mapping to standard 'external_model_run' mongodb doc keys such as `status`, see `extensions/external_models/external_models_storage.py`
        "status": "status.state",
        "progress_fraction": "status.description"
      },
      "model_specific_response_mapping": { // save additional model specific parameters in the `model_specific_input` dict
        "scenarioID": "scenarioID",
        "simRunDate": "simRunDate",
        "dashboardURL": "dashboardURL"
      },
      "esdl_encoding": "base64_encoded",
      "status_mapping": { // mapping to standard 'mapeditor external_models` statusses
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
  // determine whether the query(ies) polling can stop with `success` (continue sequence) or `error` (abort sequence) state
  // can be omitted in which case the query will be run only once
  "completed_statuses": {
    "success": [  // if success the workflow engine will continue with the next step
      "SUCCEEDED"
    ],
    "error": [  // if error the workflow engine sequence will be aborted
      "CANCELLED",
      "ERROR"
    ]
  },
  "retry_interval_seconds": 2, // query polling interval
  "maximum_wait_seconds": 3600 // maximum duration after which the calculation will be aborted
}
```

## `custom`

A custom component can be any Vue component that is hooked up to the Workflow module. This is done by adding the
component to the `WorkflowCustomComponent.vue` file. This file contains a `components` object, which is a mapping from
component name to component. The component name is the name that is used in the `type` field of the step. The component
is the Vue component that is used to render the step.
