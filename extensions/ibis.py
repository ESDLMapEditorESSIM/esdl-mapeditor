from flask import Flask, session
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, get_session_for_esid
import settings
import requests
import json


class IBISBedrijventerreinen:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering IBIS bedrijventerreinen extension')

        @self.socketio.on('ibis_bedrijventerreinen', namespace='/esdl')
        def get_ibis_contours(info):
            with self.flask_app.app_context():
                print("getting ibis request")
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                initialize_ES = info["initialize_ES"]
                add_boundary_to_ESDL = info["add_boundary_to_ESDL"]
                rin_list = info["rin_list"]

                es_edit = esh.get_energy_system(es_id=active_es_id)
                instance = es_edit.instance
                area = instance[0].area

                try:
                    url = 'http://' + settings.ibis_config["host"] + ':' + settings.ibis_config["port"] + \
                           settings.ibis_config["path_contour"] + rin_list
                    print(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        area_list = json.loads(r.text)
                except Exception as e:
                    print('ERROR in accessing IBIS boundary service for {}'.format(rin_list))
                    return None

                self.emit_geometries_to_client(esh, active_es_id, area_list)

        @self.flask_app.route('/bedrijventerreinen_list')
        def get_ibis_list():
            try:
                url = 'http://' + settings.ibis_config["host"] + ':' + settings.ibis_config["port"] + \
                      settings.ibis_config["path_list"]
                print(url)
                r = requests.get(url)
                if len(r.text) > 0:
                    bedrijventerreinen_list = json.loads(r.text)
            except Exception as e:
                print('ERROR in accessing IBIS service')
                return None

            return { "bedrijventerreinen": bedrijventerreinen_list }

    def emit_geometries_to_client(self, esh, es_id, area_list):
        with self.flask_app.app_context():
            # print(area_list)

            emit_area_list = []
            for area in area_list:
                emit_area_list.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": area['geom']['coordinates']
                    },
                    "properties": {
                        "id": area['code'],
                        "name": area['name'],
                        "KPIs": []
                    }
                })

            # print(emit_area_list)
            # emit('geojson', {"layer": "area_layer", "geojson": emit_area_list})
            self.socketio.emit('geojson', {"layer": "area_layer", "geojson": emit_area_list}, namespace='/esdl')