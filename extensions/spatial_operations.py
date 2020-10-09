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

import uuid

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_executor import Executor
from shapely.geometry import Polygon, MultiPoint, Point
from shapely.ops import triangulate
from pprint import pprint

from extensions.session_manager import get_handler, get_session, set_session
from extensions.boundary_service import BoundaryService, is_valid_boundary_id
import esdl.esdl as esdl
from src.shape import Shape
from src.esdl_helper import energy_asset_to_ui
import src.log as log


logger = log.get_logger(__name__)


class SpatialOperations:
    def __init__(self, flask_app: Flask, socket: SocketIO):  # , executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.boundary_service_instance = BoundaryService.get_instance()
        self.register()

    def register(self):
        logger.info('Registering Spatial Operations extension')

        @self.socketio.on('spatop_preprocess_areas', namespace='/esdl')
        def spatop_preprocess_subarea():
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                es = esh.get_energy_system(active_es_id)
                area = es.instance[0].area
                return self.preprocess_area(area)

        @self.socketio.on('spatop_joint_middle_subarea', namespace='/esdl')
        def spatop_joint_middle_subarea():
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                es = esh.get_energy_system(active_es_id)
                area = es.instance[0].area

                sub_area_shape_list = get_session('sub_area_shape_list')

                asset_to_ui_list = list()
                for ar in sub_area_shape_list:
                    shape = ar['shape']
                    id = ar['id']
                    if isinstance(shape.shape, Polygon):
                        # Calculate the center of the area
                        centroid = shape.shape.centroid
                        sh_centroid = Shape.create(centroid)
                        ar['shape_centroid'] = sh_centroid
                        ar['shape_centroid_wkt'] = sh_centroid.get_wkt()
                        esdl_centroid = sh_centroid.get_esdl()

                        # Generate a Joint at the center of the area
                        joint = esdl.Joint(id=str(uuid.uuid4()),name="Joint: "+id)
                        joint.geometry = esdl_centroid
                        joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                        joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
                        area.asset.append(joint)
                        esh.add_object_to_dict(active_es_id, joint, recursive=True)
                        # Mapping to ESDL object, such that connecting can be done easily later on
                        ar['esdl_joint'] = joint

                        asset_to_ui, conn_list_to_ui = energy_asset_to_ui(esh, active_es_id, joint)
                        asset_to_ui_list.append(asset_to_ui)

                # Update the UI
                emit("add_esdl_objects", {
                    "es_id": active_es_id,
                    "asset_pot_list": asset_to_ui_list,
                    "zoom": False,
                 })

        @self.socketio.on('spatop_joint_delaunay', namespace='/esdl')
        def spatop_joint_delaunay():
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                es = esh.get_energy_system(active_es_id)
                area = es.instance[0].area

                list_of_shapely_points = list()         # to feed the delaunay triangulation algorithm
                mapping_centroid_wkt_to_joint = dict()  # to find the joints at both sides of all edges

                for obj in area.eAllContents():
                    if isinstance(obj, esdl.Joint):
                        geom = obj.geometry
                        sh_geom = Shape.create(geom)
                        list_of_shapely_points.append(sh_geom.shape)
                        mapping_centroid_wkt_to_joint[sh_geom.get_wkt()] = obj

                if len(list_of_shapely_points):
                    shapely_multipoint = MultiPoint(list_of_shapely_points)
                    edges = triangulate(shapely_multipoint, edges=True)

                    self.create_pipes(edges, None, mapping_centroid_wkt_to_joint)

        @self.socketio.on('spatop_joint_delaunay_subarea', namespace='/esdl')
        def spatop_joint_delaunay():
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                es = esh.get_energy_system(active_es_id)

                sub_area_shape_list = get_session('sub_area_shape_list')
                top_area_shape = get_session('top_area_shape')

                list_of_shapely_points = list()         # to feed the delaunay triangulation algorithm
                mapping_centroid_wkt_to_joint = dict()  # to find the joints at both sides of all edges
                for ar in sub_area_shape_list:
                    list_of_shapely_points.append(ar['shape_centroid'].shape)
                    mapping_centroid_wkt_to_joint[ar['shape_centroid_wkt']] = ar['esdl_joint']

                shapely_multipoint = MultiPoint(list_of_shapely_points)
                edges = triangulate(shapely_multipoint, edges=True)

                self.create_pipes(edges, top_area_shape, mapping_centroid_wkt_to_joint)


    @staticmethod
    def add_boundary_to_shape_list(shape_list, area_id, boundary):
        sh = Shape.parse_geojson_geometry(boundary['geom'])
        num_sub_polygons = len(sh.shape.geoms)
        for i, pol in enumerate(sh.shape.geoms):
            if num_sub_polygons > 1:
                area_id_number = " ({} of {})".format(i + 1, num_sub_polygons)
            else:
                area_id_number = ""
            shape_polygon = Shape.create(pol)
            if shape_polygon.shape.area > 0.0001:
                shape_list.append({
                    'id': area_id + area_id_number,
                    'shape': shape_polygon,
                })

    def preprocess_area(self, area):
        user = get_session('user-email')
        year = self.boundary_service_instance.get_user_setting(user, 'boundaries_year')

        sub_area_shape_list = list()
        top_area_shape = list()
        if year and area.id and area.scope.name != 'UNDEFINED':
            if is_valid_boundary_id(area.id):
                boundary = self.boundary_service_instance.get_boundary_from_service(year, area.scope, str.upper(area.id))
                top_area_shape = Shape.parse_geojson_geometry(boundary['geom'])

                for ar in area.area:
                    if ar.id and ar.scope.name != 'UNDEFINED':
                        if is_valid_boundary_id(ar.id):
                            boundary = self.boundary_service_instance.get_boundary_from_service(year, ar.scope, str.upper(ar.id))
                            self.add_boundary_to_shape_list(sub_area_shape_list, ar.id, boundary)

        set_session('sub_area_shape_list', sub_area_shape_list)
        set_session('top_area_shape', top_area_shape)
        return len(sub_area_shape_list)

    @staticmethod
    def create_pipes(edges, top_area_shape, mapping_centroid_wkt_to_joint):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        es = esh.get_energy_system(active_es_id)
        area = es.instance[0].area

        asset_to_ui_list = list()
        connections_to_ui_list = list()

        for edge in edges:
            if top_area_shape and not edge.within(top_area_shape.shape):
                continue

            edge_point_0 = Point(edge.coords[0])
            edge_point_1 = Point(edge.coords[1])

            # Find the ESDL Joint based on the coordinates of the ends of the edge
            joint_0 = mapping_centroid_wkt_to_joint[edge_point_0.wkt]
            joint_1 = mapping_centroid_wkt_to_joint[edge_point_1.wkt]

            # Locations of both sides of the edge
            point_0 = joint_0.geometry.clone()
            point_1 = joint_1.geometry.clone()

            # Generate a pipe and connect to the joints at both sides
            pipe = esdl.Pipe(id=str(uuid.uuid4()), name="pipe", state=esdl.AssetStateEnum.OPTIONAL)
            line = esdl.Line()
            line.point.append(point_0)
            line.point.append(point_1)
            pipe.geometry = line
            pipe_inport = esdl.InPort(id=str(uuid.uuid4()), name="In")
            pipe_outport = esdl.OutPort(id=str(uuid.uuid4()), name="Out")
            pipe_inport.connectedTo.append(joint_0.port[1])  # Second port of joint is the OutPort
            pipe_outport.connectedTo.append(joint_1.port[0])  # First port of joint is the InPort
            pipe.port.append(pipe_inport)
            pipe.port.append(pipe_outport)

            area.asset.append(pipe)
            esh.add_object_to_dict(active_es_id, pipe, recursive=True)

            # Prepare updating UI
            asset_to_ui, conn_list_to_ui = energy_asset_to_ui(esh, active_es_id, pipe)
            asset_to_ui_list.append(asset_to_ui)
            connections_to_ui_list.extend(conn_list_to_ui)

        # Update the UI
        emit("add_esdl_objects", {
            "es_id": active_es_id,
            "asset_pot_list": asset_to_ui_list,
            "zoom": False,
        })
        emit("add_connections", {"es_id": active_es_id, "conn_list": connections_to_ui_list})
