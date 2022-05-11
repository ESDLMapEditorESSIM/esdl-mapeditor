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
import glob

from flask import Flask, send_from_directory, abort, make_response

import os
import io
import shapefile
import shutil
import tempfile
import zipfile
import time

from esdl import esdl
from extensions.session_manager import set_session, get_session, get_handler
from pyecore.ecore import EAttribute
import src.log as log

logger = log.get_logger(__name__)

# Shape types:
# POINT = 1
# POLYLINE = 3
# POLYGON = 5

# Field type: the type of data at this column index. Types can be:
# "C": Characters, text.
# "N": Numbers, with or without decimals.
# "F": Floats (same as "N").
# "L": Logical, for boolean True/False values.
# "D": Dates.
# "M": Memo, has no meaning within a GIS and is part of the xbase spec instead.


WGS84_WKT_CRS = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'


ESDL_GEOMETRY_SHAPETYPE_MAPPING = {
    "Point": shapefile.POINT,
    "Line": shapefile.POLYLINE,
    "Polygon": shapefile.POLYGON
}

ETYPE_TO_GEOMETRY_TYPE_MAPPING = {
    "EString": "C",
    "EEnum": "C",
    "EBoolean": "L",
    "EDate": "D",
    "EInt": "N",
    "EDouble": "F"
}

# Mapping for attributes of assets where first 10 characters are not unique
ATTR_NAME_MAPPING = {
    "heatpumpCoolingPower": "hpCoolPwr",
    "heatpumpCoolingCOP": "hpCoolCOP",
    "temperatureMax": "tempMax",
    "temperatureMin": "tempMin",
}


class ESDL2Shapefile:

    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info('Registering ESDL2Shapefile extension')

        @self.flask_app.route('/esdl2shapefile')
        def export_to_shapefile():
            active_es_id = get_session('active_es_id')
            esh = get_handler()
            es = esh.get_energy_system(active_es_id)
            es_name = get_session('es_filename')
            if not es_name:
                es_name = es.name if es.name else "Untitled EnergySystem"

            file_obj = ESDL2Shapefile.convert_esdl_to_shapefiles_zipfile(es)
            response = make_response(file_obj.read())
            response.headers.set('Content-Type', 'zip')
            response.headers.set('Content-Disposition', 'attachment', filename='%s.zip' % es_name)
            return response

    @staticmethod
    def convert_esdl_to_shapefiles_zipfile(es: esdl.EnergySystem):
        assets_with_geometry = dict()
        for obj in es.eAllContents():
            if isinstance(obj, esdl.Asset):
                if obj.geometry and not obj.geometry.CRS == 'Simple':
                    if obj.eClass.name in assets_with_geometry:
                        assets_with_geometry[obj.eClass.name]['objects'].append(obj)
                    else:
                        assets_with_geometry[obj.eClass.name] = {'objects': [obj], 'attr_types': []}

        # collect attribute types
        for asset_type, assets in assets_with_geometry.items():
            asset_set_attr_dict = dict()
            for asset in assets['objects']:
                ESDL2Shapefile.add_asset_basic_set_attributes(asset, asset_set_attr_dict)
                assets_with_geometry[asset_type]['attr_types'] = asset_set_attr_dict

        shapefiles_collection_dir = tempfile.mkdtemp(prefix="ESDL2Shapefile-")
        for asset_type, assets in assets_with_geometry.items():
            # assume uniform geometries
            geom_type = assets['objects'][0].geometry.eClass.name

            w = shapefile.Writer(os.path.join(shapefiles_collection_dir, asset_type),
                                 shapeType=ESDL_GEOMETRY_SHAPETYPE_MAPPING[geom_type])
            ESDL2Shapefile.add_shapefile_fields(w, assets['attr_types'])

            for asset in assets['objects']:
                ESDL2Shapefile.esdl_geometry_to_shapefile(w, asset.geometry)
                ESDL2Shapefile.add_shapefile_field_values(w, asset, assets['attr_types'])

            w.close()

            prj_filename = asset_type + '.prj'
            with open(os.path.join(shapefiles_collection_dir, prj_filename), 'w') as prj_file:
                prj_file.write(WGS84_WKT_CRS)

        # Create zip file in memory and add all shapefile info
        file_obj = io.BytesIO()
        with zipfile.ZipFile(file_obj, 'w') as zip_file:
            for filename in glob.glob(os.path.join(shapefiles_collection_dir, '*')):
                zip_file.write(filename, os.path.basename(filename))
        file_obj.seek(0)

        # Clean up created files
        shutil.rmtree(shapefiles_collection_dir)

        return file_obj

    @staticmethod
    def esdl_geometry_to_shapefile(w, geometry):
        if isinstance(geometry, esdl.Point):
            w.point(geometry.lon, geometry.lat)
        if isinstance(geometry, esdl.Line):
            line_points = list()
            for p in geometry.point:
                line_points.append([p.lon, p.lat])
            w.line([line_points])
        # For now, only exterior coordinates are exported
        if isinstance(geometry, esdl.Polygon):
            ext_pol_points = list()
            for p in geometry.exterior.point:
                ext_pol_points.append([p.lon, p.lat])
            ext_pol_points.append(ext_pol_points[0])
            w.poly([ext_pol_points])

    @staticmethod
    def add_asset_basic_set_attributes(asset, asset_set_attr_dict):
        for x in asset.eClass.eAllStructuralFeatures():
            if isinstance(x, EAttribute):
                if asset.eIsSet(x.name):
                    if x.name not in asset_set_attr_dict:
                        e_type = x.eType.eClass.name
                        if e_type == 'EDataType':
                            e_type = x.eType.name
                        # print(f"{asset.eClass.name} - {x.name}: {e_type}")
                        attr_type = ETYPE_TO_GEOMETRY_TYPE_MAPPING[e_type]
                        asset_set_attr_dict[x.name] = ({'name': x.name, 'type': attr_type})

    @staticmethod
    def add_shapefile_fields(w, attr_types):
        for attr in attr_types.values():
            attr_name = attr['name']
            if attr_name in ATTR_NAME_MAPPING:
                attr_name = ATTR_NAME_MAPPING[attr_name]
            w.field(attr_name, attr['type'])

    @staticmethod
    def add_shapefile_field_values(w, asset, attr_types):
        values_list = list()
        for attr in attr_types.values():
            if asset.eIsSet(attr['name']):
                values_list.append(asset.eGet(attr['name']))
            else:
                values_list.append(None)

        w.record(*values_list)

