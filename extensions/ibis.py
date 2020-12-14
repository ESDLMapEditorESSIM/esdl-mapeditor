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

from flask import Flask, session
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session
import src.settings as settings
import requests
import json
from uuid import uuid4
from esdl import esdl
from esdl.processing import ESDLGeometry
import src.log as log

logger = log.get_logger(__name__)


class IBISBedrijventerreinen:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering IBIS bedrijventerreinen extension')

        @self.socketio.on('ibis_bedrijventerreinen', namespace='/esdl')
        def get_ibis_contours(info):
            with self.flask_app.app_context():
                logger.info("getting ibis request")
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                add_boundary_to_ESDL = info["add_boundary_to_ESDL"]
                rin_list = info["rin_list"]

                es_edit = esh.get_energy_system(es_id=active_es_id)
                instance = es_edit.instance
                area = instance[0].area

                try:
                    url = 'http://' + settings.ibis_config["host"] + ':' + settings.ibis_config["port"] + \
                           settings.ibis_config["path_contour"] + rin_list
                    logger.info(url)
                    r = requests.get(url)
                    if len(r.text) > 0:
                        area_list = json.loads(r.text)
                except Exception as e:
                    logger.info('ERROR in accessing IBIS boundary service for {}'.format(rin_list))
                    return None

                if add_boundary_to_ESDL:
                    self.add_geometries_to_esdl(esh, active_es_id, area_list)
                self.emit_geometries_to_client(esh, active_es_id, area_list)

        @self.flask_app.route('/bedrijventerreinen_list')
        def get_ibis_list():
            try:
                url = 'http://' + settings.ibis_config["host"] + ':' + settings.ibis_config["port"] + \
                      settings.ibis_config["path_list"]
                logger.info(url)
                r = requests.get(url)
                if len(r.text) > 0:
                    bedrijventerreinen_list = json.loads(r.text)
            except Exception as e:
                logger.info('ERROR in accessing IBIS service')
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
            emit('geojson', {"layer": "area_layer", "geojson": emit_area_list}, namespace='/esdl')

    def add_geometries_to_esdl(self, esh, es_id, area_list):
        with self.flask_app.app_context():

            es_edit = esh.get_energy_system(es_id)
            instance = es_edit.instance
            area = instance[0].area

            for ibis_area in area_list:
                new_area = esdl.Area(id=str(uuid4()), name=ibis_area['name'])
                new_area.scope = esdl.AreaScopeEnum.from_string("UNDEFINED")

                boundary = ibis_area

                if boundary:
                    geometry = ESDLGeometry.create_geometry_from_geom(boundary['geom'])
                    new_area.geometry = geometry

                area.area.append(new_area)
                esh.add_object_to_dict(es_id, new_area)