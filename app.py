#!/usr/bin/env python
from flask import Flask, render_template, session, request, send_from_directory
from flask_socketio import SocketIO, emit
import requests
from model import esdl_sup as esdl

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None


xml_namespace = ("xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'\nxmlns:esdl='http://www.tno.nl/esdl'\nxsi:schemaLocation='http://www.tno.nl/esdl ../esdl/model/esdl.ecore'\n")
ESDL_STORE_HOSTNAME = "http://10.30.2.1"
ESDL_STORE_PORT = "3003"
# ES_ID = "5df98542-430a-44b0-933c-e1c663a48c70"   # Ameland met coordinaten
ES_ID = "86179000-de3a-4173-a4d5-9a2dda2fe7c7"  # Ameland met coords en ids
es_edit = esdl.EnergySystem()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@app.route('/images/<path:path>')
def send_image(path):
    return send_from_directory('images', path)


@socketio.on('update-coord', namespace='/esdl')
def update_coordinates(message):
    print ('received: ' + str(message['id']) + ':' + str(message['lat']) + ',' + str(message['lng']))
    ass_id = message['id']

    instance = es_edit.get_instance()
    area = instance[0].get_area()
    for ar in area.get_area():
        for asset in ar.get_asset():
            if asset.get_id() == ass_id:
                point = esdl.Point()
                point.set_lon(message['lng'])
                point.set_lat(message['lat'])
                asset.set_geometry_with_type(point)
            if isinstance(asset, esdl.AggregatedBuilding):
                for basset in asset.get_asset():
                    if asset.get_id() == ass_id:
                        point = esdl.Point()
                        point.set_lon(message['lng'])
                        point.set_lat(message['lat'])
                        asset.set_geometry_with_type(point)


@socketio.on('command', namespace='/esdl')
def process_command(message):
    print ('received: ' + message['cmd'])
    if message['cmd'] == 'store_esdl':
        write_energysystem_to_file('changed_EnergySystem.esdl', es_edit)
    if message['cmd'] == 'add_asset':
        assettype = message['asset']
        if assettype == 'WindTurbine': asset = esdl.WindTurbine()
        if assettype == 'PVParc': asset = esdl.PVParc()

        point = esdl.Point()
        point.set_lon(message['lng'])
        point.set_lat(message['lat'])
        asset.set_geometry_with_type(point)

        es_edit.get_instance()[0].get_area().add_asset_with_type(asset)


@socketio.on('connect', namespace='/esdl')
def test_connect():
    emit('my_response', {'data': 'Connected', 'count': 0})
    print('Connected')

    list = []

    instance = es_edit.get_instance()
    area = instance[0].get_area()
    for ar in area.get_area():
        for asset in ar.get_asset():
            if isinstance(asset, esdl.AggregatedBuilding):
                for basset in asset.get_asset():
                    geom = basset.get_geometry()
                    if geom:
                        if isinstance(geom, esdl.Point):
                            lat = geom.get_lat()
                            lon = geom.get_lon()

                            list.append([lat, lon, basset.get_name(), basset.get_id(), type(basset).__name__])
            else:
                geom = asset.get_geometry()
                if geom:
                    if isinstance(geom, esdl.Point):
                        lat = geom.get_lat()
                        lon = geom.get_lon()

                        list.append([lat, lon, asset.get_name(), asset.get_id(), type(asset).__name__])

    emit('loadesdl', list)


@socketio.on('disconnect', namespace='/esdl')
def test_disconnect():
    print('Client disconnected', request.sid)


def write_energysystem_to_file(filename, es):
    f = open(filename, 'w+', encoding='UTF-8')
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    es.export(f, 0, namespaceprefix_='esdl:', name_='esdl:EnergySystem', namespacedef_=xml_namespace, pretty_print=True)
    f.close()


def load_ESDL_EnergySystem(id):
    url = ESDL_STORE_HOSTNAME + ':' + ESDL_STORE_PORT + "/store/esdl/" + id + "?format=xml"
    r = requests.get(url)
    esdlstr = r.text
    esdlstr = esdlstr.encode()
    return esdl.parseString(esdlstr)


if __name__ == '__main__':
    es_edit = load_ESDL_EnergySystem(ES_ID)
    socketio.run(app, debug=True)