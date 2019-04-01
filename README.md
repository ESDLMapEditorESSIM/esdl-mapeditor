# ESDL-WebEditor

## Introduction

Web-based ESDL editor, allows loading, editing and saving ESDL EnergySystem files

## Installation

1. Clone this repository

2. Install shapely by downloaden the wheel from
[this website](http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely)...

3. ...and then install it using pip (replace filename with your chosen version):
   ```
   pip install Shapely‑1.6.4.post1‑cp37‑cp37m‑win_amd64.whl
   ```

4. install the other dependencies
   ```
   pip install -r requirements.txt
   ```

## Starting the application

Run `app.py` and open browser on `http:\\localhost:5000`. The application serves as a simple webserver and serves index.html and the images.
There is a websocket connection between the python application and webbrowser for bi-directional communication.

## Dependencies

- Leaflet
- Leaflet Draw
- JQuery
- Socket.io


