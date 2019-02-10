# ESDL-WebEditor

## Introduction

Very simple web-based ESDL editor, reads ESDL EnergySystem from GEIS ESDL store and saves changes in ESDL-file on filesystem 

Currently supports:
- moving existing assets
- adding PVParc and WindTurbine (only to top-level area

## Working principle

Run `app.py` and open browser on `http:\\localhost:5000`. The application serves as a simple webserver and serves index.html and the images.
There is a websocket connection between the python application and webbrowser for bi-directional communication.

## Dependencies

- Leaflet
- Leaflet Draw
- JQuery
- Socket.io


