from flask import Flask
from flask_socketio import SocketIO, emit
import settings
import requests
import json


class Boundaries:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering Boundaries extension')

        @self.flask_app.route('/boundaries_names/<scope_type>')
        def get_boundaries_names(scope_type):
            with self.flask_app.app_context():
                print("getting boundaries names information")

                try:
                    url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                           settings.boundaries_config["path_names"] + '/' + scope_type
                    print(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        reply = json.loads(r.text)
                        return { "boundaries_names": reply }

                except Exception as e:
                    print('ERROR in accessing Boundaries service: '+str(e))
                    return 'ERROR in accessing Boundaries service: '+str(e), 404

        @self.flask_app.route('/boundaries_names/<select_scope_type>/<select_scope_id>/<scope_type>')
        def get_subboundaries_names(select_scope_type, select_scope_id, scope_type):
            with self.flask_app.app_context():
                print("getting boundaries names information")

                try:
                    url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                           settings.boundaries_config["path_names"] + '/' + select_scope_type + '/' + select_scope_id + '/' + scope_type
                    print(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        reply = json.loads(r.text)
                        return json.dumps(reply)

                except Exception as e:
                    print('ERROR in accessing Boundaries service: '+str(e))
                    return 'ERROR in accessing Boundaries service: '+str(e), 404

    # def emit_geometries_to_client(self, esh, es_id, building_list):
    #     with self.flask_app.app_context():
    #         # print(area_list)
    #
    #         emit_bld_list = []
    #         for bld in building_list:
    #             emit_bld_list.append({
    #                 "type": "Feature",
    #                 "geometry": {
    #                     "type": "Polygon",
    #                     "coordinates": bld['geom']['coordinates']
    #                 },
    #                 "properties": {
    #                     "id": bld['code'],
    #                     "name": bld['name'],
    #                 }
    #             })
    #
    #         # print(emit_area_list)
    #         # emit('geojson', {"layer": "area_layer", "geojson": emit_area_list})
    #         emit('geojson', {"layer": "building_layer", "geojson": emit_bld_list}, namespace='/esdl')
