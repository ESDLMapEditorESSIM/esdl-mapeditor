# Workflow steps

A workflow is defined as a list of steps. Each step has a type. The type determines what the step does.

A fully up to date set of workflow steps can be found by looking at Workflow.vue. This basically contains a large
if-else-if statement, where each if-else-if corresponds to a step type. Alternatively, look at the `workflow.js` file,
which contains an enum of all possible steps.

We currently have the following steps.


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

## `multi-select-query`

The `multi-select-query` step performs a request to an API endpoint, and allows the user to select one or more of the
results. The results are shown in a dropdown, and the user can select one or more of the options. The selected options
are stored in the workflow state.

## `service`

This step allows the user to call an ESDL Service. The ESDL Service is defined in the `esdl_service` field of the step.
This field is a JSON object, and can contain any ESDL Service that can also be defined outside the Workflow module,
as its own ESDL Service.

If the service returns an ESDL, the ESDL is loaded into the ESDL MapEditor.

## `json_form`

Allows the user to enter data in a form. The data is stored in the workflow state. The form is defined as a JSON schema.
See https://json-schema.org/ for more information on JSON schemas. The JSON schema is stored in the `schema` field of the
step.

Alternatively, it is possible to retrieve the schema from a URL. This is done by setting the `url` field of the
step. The URL should return a JSON schema. When submitting the step, the data is then send as a POST request to the same
URL.

## `download_file`

## `upload_file`

## `get_data`

## `http_post`

## `call_js_function`

This step allows the user to call a JavaScript function. The function is defined in the `function` field of the step.

## `progress`

## `text`

A text component. The text is defined in the `text` field of the step.

## `custom`

A custom component can be any Vue component that is hooked up to the Workflow module. This is done by adding the
component to the `WorkflowCustomComponent.vue` file. This file contains a `components` object, which is a mapping from
component name to component. The component name is the name that is used in the `type` field of the step. The component
is the Vue component that is used to render the step.
