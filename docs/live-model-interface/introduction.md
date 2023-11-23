# Live model interface

## Introduction

The live model interface is an interface between the ESDL MapEditor and externally running computing models. These
models can be anything, for example a model that calculates the wind potential of a windmill when placed on a certain
location, or a model that performs a load flow calculation. The interface is "live" in the sense that it was developed
so that models can be run in the background, and the results are immediately shown in the MapEditor. This allows for
a very interactive experience, where the user can immediately see the results of his actions.

## Technology

For the live model interface, we use RabbitMQ as message broker. The ESDL MapEditor and the models communicate through
RabbitMQ. The ESDL MapEditor sends messages to the models, and the models send messages back to the ESDL MapEditor. The
messages are JSON message.

## How it works

In the ESDL MapEditor, we define a number of events that might be interesting for external events to react to. For
example, after selecting an asset and moving the mouse to a certain location can already be an event. An external
model can subscribe to such an event, for example an external that can determine whether or not this asset can be
placed on the location the user is moving his mouse to. The external model can then send a message back to the ESDL
MapEditor, indicating whether or not the asset can be placed on the location. The ESDL MapEditor can then show this
information to the user, for example by showing a green or red circle around the mouse cursor.

## Requirements for a live model

A live model is any kind of application that runs in the background, and that communicates with the ESDL MapEditor
through RabbitMQ. The ESDL MapEditor sends messages to RabbitMQ, and the model can choose which messages to subscribe
to. The model can then send messages back to RabbitMQ.

A live model then only needs to be able to interface with RabbitMQ, and can be written in any language. However because
deployment happens in Docker, it is required for a live model to have a Dockerfile. Furthermore, it needs to connect
to the BaseInfrastructure of the docker toolsuite of the ESDL MapEditor, to allow for communication with RabbitMQ.
