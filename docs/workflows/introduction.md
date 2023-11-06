# Intro

The workflow module allows a developer to specify a workflow for a user to follow. It is built to be generic and
extensible, allowing for a wide variety of workflows to be created. Workflows can function as very short-lived
operations of a few consecutive steps, or they can be full-fledged sub-applications within the larger application,
that can support pausing and resuming at any point in the workflow.


## Conditional next steps

Normally, a step has a single next_step field, that indicates the id of the step to go to next. However, it is also
possible to specify a list of next steps, each with a condition. For the condition we use a DSL, for which the schema
can be found in `workflowSchemes.js`. See `demo_workflow.json` for an example of this in action.
