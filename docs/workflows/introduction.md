# Intro

The workflow module allows a developer to specify a workflow for a user to follow. It is built to be generic and
extensible, allowing for a wide variety of workflows to be created. Workflows can function as very short-lived
operations of a few consecutive steps, or they can be full-fledged sub-applications within the larger application,
that can support pausing and resuming at any point in the workflow.


## State

The workflow can track a state, which is a simple key-value store. Various steps store data in this state by default.
For example the `json_form` step stores the data entered by the user in the state. The state can be used by other steps
to make decisions, or to display information to the user.


## Conditional next steps

Normally, a step has a single next_step field, that indicates the id of the step to go to next. However, it is also
possible to specify a list of next steps, each with a condition. For the condition we use a DSL, for which the schema
can be found in `workflowSchemes.js`. See `demo_workflow.json` for an example of this in action.

All conditions operate only on the state of the workflow.
