# How to develop a Workflow

As described in the introduction, a Workflow is a ESDL Service of type "workflow". This means that the workflow is
defined through a JSON spec.

At the time of writing we unfortunately do not have a JSON schema for this spec. However, the `demo_workflow.json`
file contains a good example of how to define a workflow. The workflow is defined as a list of steps. Each step has
a type. The type determines what the step does. For example, the `json_form` step allows the user to enter data in a
form, and stores the data in the workflow state.

