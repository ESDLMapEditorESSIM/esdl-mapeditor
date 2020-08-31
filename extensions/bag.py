#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session
import src.settings as settings
import requests
from esdl.processing import ESDLAsset, ESDLGeometry, ESDLEnergySystem
import esdl
from geomet import wkt
import src.log as log

logger = log.get_logger(__name__)

class BAG:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering BAG extension')

        @self.socketio.on('get_bag_contours', namespace='/esdl')
        def get_bag_contours(info):
            with self.flask_app.app_context():
                print("getting bag information")
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                area_id = info["id"]
                area_polygon = { 'type': 'polygon', 'coordinates': info["polygon"] }
                geometry = ESDLGeometry.create_ESDL_geometry(area_polygon)
                boundary_wgs = ESDLGeometry.create_boundary_from_geometry(geometry)
                # boundary_geojson = ESDLGeometry.create_geojson(area_id, '', [], boundary_wgs)
                wkt_string = wkt.dumps(boundary_wgs)
                # wkt_string = 'POLYGON ((4.359093904495239 52.012174264626445, 4.357388019561768 52.01154692445308, 4.357978105545044 52.01078750089633, 4.360188245773315 52.01160635705717, 4.362355470657349 52.012478026181434, 4.360767602920532 52.012847820073766, 4.359093904495239 52.012174264626445))'
                # wkt_quoted = urllib.parse.quote(wkt_string)

                es_edit = esh.get_energy_system(es_id=active_es_id)
                instance = es_edit.instance
                top_area = instance[0].area
                target_area = ESDLEnergySystem.find_area(top_area, area_id)
                if target_area:
                    try:
                        # url = 'http://' + settings.bag_config["host"] + ':' + settings.bag_config["port"] + \
                        #        settings.bag_config["path_contour"] + '?wkt=' + wkt_quoted + '&format=xml'
                        # print(url)
                        # r = requests.get(url)
                        url = 'http://' + settings.bag_config["host"] + ':' + settings.bag_config["port"] + \
                               settings.bag_config["path_contour"] + '?format=xml'
                        print(url)
                        r = requests.post(url, json={"wkt": wkt_string})
                        if r.status_code == 201:
                            esdl_string = r.text
                            bag_es = ESDLAsset.load_asset_from_string(esdl_string)
                            if bag_es:
                                bag_inst = bag_es.instance[0]
                                if bag_inst:
                                    bag_area = bag_inst.area
                                    if bag_area:
                                        bld_list = []
                                        for bld in bag_area.asset:
                                            if isinstance(bld, esdl.Building):
                                                target_area.asset.append(bld.deepcopy())
                                                geometry = bld.geometry
                                                boundary_wgs = ESDLGeometry.create_boundary_from_geometry(geometry)
                                                bld_list.append(ESDLGeometry.create_geojson(bld.id, bld.name, [], boundary_wgs))

                                        if bld_list:
                                            emit('geojson', {"layer": "bld_layer", "geojson": bld_list})

                    except Exception as e:
                        print('ERROR in accessing BAG service: '+str(e))
                        return None

                    # @EWOUD: Deze 'mogelijkheid' kunnen we ook gebruiken om geometries te renderen in de frontend
                    # self.emit_geometries_to_client(esh, active_es_id, bld_list)
                else:
                    print("ERROR in finding area in ESDL for BAG service")
                    # self.flask_app.send_alert("ERROR in finding area in ESDL for BAG service")
                    return None

        # @self.flask_app.route('/building_list')
        # def get_building_list():
        #     try:
        #         url = 'http://' + settings.bag_config["host"] + ':' + settings.bag_config["port"] + \
        #               settings.bag_config["path_list"]
        #         print(url)
        #         r = requests.get(url)
        #         if len(r.text) > 0:
        #             building_list = json.loads(r.text)
        #     except Exception as e:
        #         print('ERROR in accessing BAG service')
        #         return None
        #
        #     return { "buildings": building_list }

    def emit_geometries_to_client(self, esh, es_id, building_list):
        with self.flask_app.app_context():
            # print(area_list)

            emit_bld_list = []
            for bld in building_list:
                emit_bld_list.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": bld['geom']['coordinates']
                    },
                    "properties": {
                        "id": bld['code'],
                        "name": bld['name'],
                    }
                })

            # print(emit_area_list)
            # emit('geojson', {"layer": "area_layer", "geojson": emit_area_list})
            emit('geojson', {"layer": "building_layer", "geojson": emit_bld_list}, namespace='/esdl')