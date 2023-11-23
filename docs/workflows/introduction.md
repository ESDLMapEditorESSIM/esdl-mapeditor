# Workflow module

## Introduction

The workflow module allows a developer to specify a workflow for a user to follow. It is built to be generic and
extensible, allowing for a wide variety of workflows to be created. Workflows can function as very short-lived
operations of a few consecutive steps, or they can be full-fledged sub-applications within the larger application,
that can support pausing and resuming at any point in the workflow.


## How is a Workflow defined / relation with ESDL Services

The workflow module is built on top of the ESDL Services module of the ESDL MapEditor. This ESDL Services module
allowed users to call external ESDL Services, which as input could take an ESDL, and return a modified ESDL. These
ESDL Services were defined through a JSON spec. Every user can have their own set of ESDL Services defined, and the
MapEditor contains a number of default ESDL Services.

To define a workflow, all we have to do is define an ESDL service with as type "workflow". See `demo_workflow.json` for
an example workflow. You can copy paste this demo workflow into your ESDL Services definition. Within the ESDL
MapEditor, you can access this through the Settings > ESDL Services Management plugin. This gives you a large input
area, containing JSON.


## Principles

A Workflow is like an application within the ESDL MapEditor. It has its own state, and its own set of steps, and it
may or may not interact with the map at all. The workflow module is built to be generic, allowing for a wide variety of
workflows to be created easily through the definition of predefined workflow steps.

It also allows custom functionality to be added through custom workflow steps. These are Vue components that can be
defined by the developer, and that can be used in the workflow definition. However, if this is done it should be
considered whether this functionality should be added to the core workflow module, or whether it should be added as a
separate plugin.


## State

The workflow can track a state, which is a simple key-value store. Various steps store data in this state by default.
For example the `json_form` step stores the data entered by the user in the state. The state can be used by other steps
to make decisions, or to display information to the user.


## Conditional next steps

Normally, a step has a single next_step field, that indicates the id of the step to go to next. However, it is also
possible to specify a list of next steps, each with a condition. For the condition we use a DSL, for which the schema
can be found in `workflowSchemes.js`. See `demo_workflow.json` for an example of this in action.

All conditions operate only on the state of the workflow.


## Layout and rendering

The Workflow module is developed in Vue.js. We use AntDV as CSS framework. Any Workflow settings that are passed to
a layout component will go to an AntDV component.

For the `json_form` component, we use a JSON Form rendering engine. We use the `@jsonforms` package for this. See
https://jsonforms.io/ for more information on JSON Forms.
