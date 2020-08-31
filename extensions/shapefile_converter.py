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
from flask_executor import Executor
from extensions.session_manager import get_handler, get_session, set_session
import esdl.esdl as esdl
import os
import zipfile
import tempfile
import glob
from uuid import uuid4
from esdl.processing.ESDLGeometry import distance
from pyproj import Proj, Transformer
from pyecore.ecore import EClass
import shapefile
import importlib
from src.process_es_area_bld import process_energy_system
import src.log as log

logger = log.get_logger(__name__)


inner_diameter_keys = ('inner diam', 'diameter', 'inner diameter', 'innerdiameter')
outer_diameter_keys = ('outer diam', 'diameter', 'outer diameter', 'outerdiameter')
name_keys = ('name', 'naam', 'layer')

#FIXME: the row-indexed array won't work if multiple people are uploading zipfiles
#FIXME: the tempdir is never cleaned
#FIXME: use a unique id to have a common link to a zipfile and store the tempdir

class ShapefileConverter:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()
        self.shapefile_list = []
        self.zipfiles = {}
        self.executor = executor

    def register(self):
        logger.info('Registering Shapefile converter extension')

        @self.socketio.on('shpcvrt_receive_files', namespace='/esdl')
        def receive_files(message):
            with self.flask_app.app_context():
                print("Received shpcvrt_receive_files")
                file_content = message['file_content']
                zipfile_name = message['filename']
                zipfile_row = message['zipfile_row']
                self.zipfiles[zipfile_row] = zipfile_name

                # cwd = os.getcwd()
                # cwd_parts = cwd.split(os.path.sep)

                # client_id = session['client_id']
                # directory = os.path.join(cwd_parts[0], os.path.sep, TEMPDIR, client_id + '_' + zipfile_name)

                directory = tempfile.mkdtemp(prefix='shapefile')
                print("Saving file to: {}".format(directory))

                f = open(directory + os.path.sep + zipfile_name, 'wb')
                f.write(file_content)
                f.close()

                with zipfile.ZipFile(directory + os.path.sep + zipfile_name, 'r') as zip_ref:
                    zip_ref.extractall(directory)

                found_shape_files = []
                row = 0
                for shapefile_name in glob.glob(directory + os.path.sep + "/**/*.shp", recursive=True):
                    found_shape_files.append(shapefile_name)
                    self.shapefile_list.append({
                        'zipfile_row': zipfile_row,
                        'row': row,
                        'shapefile_name': shapefile_name
                    })
                    row = row + 1

                print(found_shape_files)
                # set_session('shapefile_dir' + zipfile_row, directory)
                emit('shpcvrt_files_in_zip', {"zipfile_row": zipfile_row, "files": found_shape_files}, namespace='/esdl')

        @self.socketio.on('shpcvrt_receive_energyasset_info', namespace='/esdl')
        def receive_energyasset_info(shapefile_energyasset_list):
            with self.flask_app.app_context():
                print("Received shpcvrt_receive_energyasset_info")

                esh = get_handler()
                active_es_id = get_session('active_es_id')
                es = esh.get_energy_system(active_es_id)
                area = es.instance[0].area

                for shapefile_energyasset in shapefile_energyasset_list:
                    energy_asset = shapefile_energyasset['energy_asset']
                    shapefile_name = shapefile_energyasset['shapefile_name']
                    zipfile_row = shapefile_energyasset['zipfile_row']
                    # zipfile_name = self.zipfiles[int(zipfile_row)]

                    # directory = get_session('shapefile_dir' + zipfile_row)
                    shapefile_name_base = os.path.splitext(shapefile_name)[0]

                    print(shapefile_name_base + ' --> ' + energy_asset)
                    if energy_asset != 'ignore':
                        basename = os.path.basename(shapefile_name_base)
                        subarea = esdl.Area(id=str(uuid4()), name=basename)
                        area.area.append(subarea)
                        self.process_shapefile(subarea, shapefile_name_base, energy_asset)
                # update uuid_dict recursively for the main area (could take long?)
                esh.add_object_to_dict(es_id=active_es_id, esdl_object=area, recursive=True)
                self.executor.submit(process_energy_system, esh=esh, filename='test', force_update_es_id=active_es_id)

    def get_coordinate_transformer(self, wkt=None, epsg_in="epsg:28992", epsg_out="epsg:4326"):
        # wkt = 'PROJCS["RD_New",GEOGCS["GCS_Amersfoort",DATUM["D_Amersfoort",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Double_Stereographic"],PARAMETER["False_Easting",155000.0],PARAMETER["False_Northing",463000.0],PARAMETER["Central_Meridian",5.38763888888889],PARAMETER["Scale_Factor",0.9999079],PARAMETER["Latitude_Of_Origin",52.15616055555555],UNIT["Meter",1.0]]'
        # projection = Proj(projparams=wkt)
        projection_in = None
        if wkt is not None:
            projection_in = Proj(projparams=wkt)
        else:
            # default input projection
            projection_in = Proj(init=epsg_in)
        projection_out = Proj(init=epsg_out)
        transformer = Transformer.from_proj(proj_from=projection_in, proj_to=projection_out)
        return transformer

    def process_shapefile(self, area, filename, energy_asset):
        sf = shapefile.Reader(filename)
        with open(filename + '.prj', 'r') as project_file:
            data = project_file.read()
            transformer = self.get_coordinate_transformer(wkt=data)

        print("File: ", filename)
        print("- Shapefile: ", sf)
        print("- Fields: ", sf.fields)
        print("- Shaperecords: ", sf.shapeRecords())

        self.to_esdl(area, sf, transformer, energy_asset)

    def to_esdl(self, area, sf, transformer, energy_asset):
        i = 0
        for shapeRecord in sf.shapeRecords():
            i += 1
            if shapeRecord.shape.shapeType == shapefile.POLYLINE:
                print('{} {} = {}'.format(shapeRecord.shape.shapeTypeName, shapeRecord.record[0],
                                          shapeRecord.shape.points))
                pipe = esdl.Pipe(name=area.name + '-Pipe' + str(i), id=str(uuid4()))
                line = esdl.Line()
                d = 0.0
                prevlat, prevlon = None, None
                for point in shapeRecord.shape.points:
                    lon, lat = transformer.transform(point[0], point[1])
                    p = esdl.Point(lat=lat, lon=lon)
                    line.point.append(p)
                    if prevlat is not None:
                        d = d + distance((prevlat, prevlon), (lat, lon))
                    prevlat, prevlon = lat, lon
                pipe.length = d * 1000  # in m instead of km

                # diameter was put in mm!
                pipe.innerDiameter = float(self.get_recordproperty(shapeRecord.record, inner_diameter_keys, 0.0)) / 1000
                pipe.outerDiameter = float(self.get_recordproperty(shapeRecord.record, outer_diameter_keys, 0.0)) / 1000

                pipe.geometry = line
                inport = esdl.InPort(id=str(uuid4()), name='InPort')
                outport = esdl.OutPort(id=str(uuid4()), name='OutPort')
                pipe.port.extend((inport, outport))
                area.asset.append(pipe)

            if shapeRecord.shape.shapeType == shapefile.POINT:
                # probably an asset

                if energy_asset == "type_record":
                    esdl_type = self.get_type(shapeRecord.record)
                    esdl_object = esdl_type(name=self.get_name(shapeRecord.record), id=str(uuid4()))
                else:
                    module = importlib.import_module('esdl.esdl')
                    class_ = getattr(module, energy_asset)
                    esdl_object = class_()
                    esdl_object.id = str(uuid4())
                    esdl_object.name = self.get_name(shapeRecord.record)

                # instance = esdl.GenericProducer(name=get_name(shapeRecord.record), id=str(uuid4()))
                point = shapeRecord.shape.points[0]
                lon, lat = transformer.transform(point[0], point[1])
                p = esdl.Point(lat=lat, lon=lon)
                esdl_object.geometry = p
                area.asset.append(esdl_object)
                inport = esdl.InPort(id=str(uuid4()), name='InPort')
                outport = esdl.OutPort(id=str(uuid4()), name='OutPort')
                esdl_object.port.extend((inport, outport))

            if shapeRecord.shape.shapeType == shapefile.POLYGON \
                    or shapeRecord.shape.shapeType == shapefile.POLYGONM \
                    or shapeRecord.shape.shapeType == shapefile.POLYGONZ:

                # If it's a polygon, polygonm or polygonz, we ignore measures and z-coordinates for now
                # we also ignore holes and multipolygons

                if energy_asset == "type_record":
                    esdl_type = self.get_type(shapeRecord.record)
                    esdl_object = esdl_type(name=self.get_name(shapeRecord.record), id=str(uuid4()))
                elif energy_asset == "esdl_area":
                    esdl_object = esdl.Area(id=str(uuid4()), name=self.get_name(shapeRecord.record))
                else:
                    module = importlib.import_module('esdl.esdl')
                    class_ = getattr(module, energy_asset)
                    esdl_object = class_()
                    esdl_object.id = str(uuid4())
                    esdl_object.name = self.get_name(shapeRecord.record)

                # This function only supports polygons without holes (so far).
                parts_len = len(shapeRecord.shape.parts)
                print(parts_len)
                if parts_len > 1:
                    multi_polygon = esdl.MultiPolygon()
                point_idx = 0
                for pol in range(0, parts_len):
                    if parts_len == 1:
                        # If only one polygon,
                        length_of_this_polygon = len(shapeRecord.shape.points)
                    else:
                        if pol == parts_len-1:
                            length_of_this_polygon = len(shapeRecord.shape.points) - shapeRecord.shape.parts[pol]
                        else:
                            length_of_this_polygon = shapeRecord.shape.parts[pol+1]

                    print('- {}'.format(length_of_this_polygon))
                    exterior = esdl.SubPolygon()
                    polygon = esdl.Polygon(exterior=exterior)
    
                    for pi in range(0, length_of_this_polygon):
                        point = shapeRecord.shape.points[point_idx]
                        lon, lat = transformer.transform(point[0], point[1])
                        p = esdl.Point(lat=lat, lon=lon)
                        exterior.point.append(p)
                        point_idx += 1

                    if parts_len > 1:
                        multi_polygon.polygon.append(polygon)

                if parts_len > 1:
                    esdl_object.geometry = multi_polygon
                else:
                    esdl_object.geometry = polygon

                if energy_asset == "esdl_area":
                    area.area.append(esdl_object)
                else:
                    area.asset.append(esdl_object)
                    inport = esdl.InPort(id=str(uuid4()), name='InPort')
                    outport = esdl.OutPort(id=str(uuid4()), name='OutPort')
                    esdl_object.port.extend((inport, outport))

    """
    if the shape record contains the type field, use that to find the appropriate ESDL class
    """
    def get_type(self, record: shapefile._Record):
        record_dict = record.as_dict()
        for key, value in record_dict.items():
            if 'type' == key.lower():
                for esdl_type in esdl.eClassifiers:
                    t: EClass = esdl.getEClassifier(esdl_type).eClass
                    if esdl.EnergyAsset.eClass in t.eAllSuperTypes():
                        # print('checking', esdl_type)
                        if value.lower() in esdl_type.lower():
                            print('Using {} as type for this shape'.format(esdl_type))
                            return esdl.getEClassifier(esdl_type)
        return esdl.GenericProducer

    def get_name(self, record: shapefile._Record):
        record_dict = record.as_dict()

        for key, value in record_dict.items():
            if key.lower() in name_keys:
                return value
        return "unnamed"

    def get_recordproperty(self, record: shapefile._Record, possible_names: list, default_value=None):
        record_dict = record.as_dict()
        for key, value in record_dict.items():
            if key.lower() in possible_names:
                return value
        return default_value
