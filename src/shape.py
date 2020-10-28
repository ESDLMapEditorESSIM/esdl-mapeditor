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

import geojson
import json
from shapely import wkt, wkb
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, GeometryCollection, shape
from shapely.ops import transform
from shapely_geojson import Feature, dumps
import esdl
import pyproj

class Shape:
    def __init__(self):
        self.shape = None

    @staticmethod
    def create(shape_input):
        if isinstance(shape_input, esdl.Point) or (isinstance(shape_input, dict) and "lat" in shape_input):
            return ShapePoint(shape_input)
        if isinstance(shape_input, esdl.Line) or (isinstance(shape_input, list) and "lat" in shape_input[0]):
            return ShapeLine(shape_input)
        if isinstance(shape_input, esdl.Polygon):
            return ShapePolygon(shape_input)
        if isinstance(shape_input, esdl.MultiPolygon):
            return ShapeMultiPolygon(shape_input)

        if isinstance(shape_input, esdl.WKT):
            return Shape.parse_esdl_wkt(shape_input)
        if isinstance(shape_input, esdl.WKB):
            return Shape.parse_esdl_wkb(shape_input)

        if isinstance(shape_input, Point):
            return ShapePoint(shape_input)
        if isinstance(shape_input, LineString):
            return ShapeLine(shape_input)
        if isinstance(shape_input, Polygon):
            return ShapePolygon(shape_input)
        if isinstance(shape_input, MultiPolygon):
            return ShapeMultiPolygon(shape_input)

        if isinstance(shape_input, list) and all(isinstance(elem, list) and "lat" in elem[0] for elem in shape_input):
            return ShapePolygon(shape_input)
        else:
            # TODO: Better check for coordinates structure
            return ShapeMultiPolygon(shape_input)

    @staticmethod
    def parse_esdl(esdl_geometry):
        pass

    @staticmethod
    def parse_leaflet(leaflet_coords):
        pass

    @staticmethod
    def parse_geojson_geometry(geojson_geometry):
        tmp_shp = shape(geojson.loads(json.dumps(geojson_geometry)))
        if isinstance(tmp_shp, Point):
            return ShapePoint(tmp_shp)
        elif isinstance(tmp_shp, LineString):
            return ShapeLine(tmp_shp)
        elif isinstance(tmp_shp, Polygon):
            return ShapePolygon(tmp_shp)
        elif isinstance(tmp_shp, MultiPolygon):
            return ShapeMultiPolygon(tmp_shp)
        else:
            raise Exception("Parsing geojson resulted in unsupported type")

    @staticmethod
    def parse_wkt(wkt_geometry, crs="EPSG:4326"):
        tmp_shp = Shape.transform_crs(wkt.loads(wkt_geometry), crs)

        if isinstance(tmp_shp, Point):
            return ShapePoint(tmp_shp)
        elif isinstance(tmp_shp, LineString):
            return ShapeLine(tmp_shp)
        elif isinstance(tmp_shp, Polygon):
            return ShapePolygon(tmp_shp)
        elif isinstance(tmp_shp, MultiPolygon):
            return ShapeMultiPolygon(tmp_shp)
        elif isinstance(tmp_shp, GeometryCollection):
            return ShapeGeometryCollection(tmp_shp)
        else:
            raise Exception("Parsing WKT resulted in unsupported type")

    @staticmethod
    def parse_wkb(wkb_geometry, crs="EPSG:4326"):
        tmp_shp = Shape.transform_crs(wkb.loads(wkb_geometry), crs)

        if isinstance(tmp_shp, Point):
            return ShapePoint(tmp_shp)
        elif isinstance(tmp_shp, LineString):
            return ShapeLine(tmp_shp)
        elif isinstance(tmp_shp, Polygon):
            return ShapePolygon(tmp_shp)
        elif isinstance(tmp_shp, MultiPolygon):
            return ShapeMultiPolygon(tmp_shp)
        else:
            raise Exception("Parsing WKB resulted in unsupported type")

    @staticmethod
    def parse_esdl_wkt(esdl_wkt):
        if isinstance(esdl_wkt, esdl.WKT):
            return Shape.parse_wkt(esdl_wkt.value, esdl_wkt.CRS)
        else:
            raise Exception("Calling parse_esdl_WKT without an esdl.WKT parameter")

    @staticmethod
    def parse_esdl_wkb(esdl_wkb):
        if isinstance(esdl_wkb, esdl.WKB):
            return Shape.parse_wkb(esdl_wkb.value, esdl_wkb.CRS)
        else:
            raise Exception("Calling parse_esdl_WKB without an esdl.WKB parameter")

    def get_esdl(self):
        pass

    def get_wkt(self):
        return self.shape.wkt

    def get_geojson_feature(self, properties={}):
        feature = Feature(self.shape, properties=properties)
        return json.loads(dumps(feature))

    @staticmethod
    def transform_crs(shp, from_crs):
        if from_crs == "WGS84" or from_crs == "":
            from_crs = "EPSG:4326"

        if from_crs != "EPSG:4326":
            wgs84 = pyproj.CRS("EPSG:4326")
            original_crs = pyproj.CRS(from_crs)

            project = pyproj.Transformer.from_crs(original_crs, wgs84, always_xy=True).transform
            return transform(project, shp)
        else:
            return shp


class ShapePoint(Shape):
    def __init__(self, shape_input):
        if isinstance(shape_input, esdl.Point):
            self.shape = self.parse_esdl(shape_input)
        elif isinstance(shape_input, dict) and "lat" in shape_input:
            self.shape = self.parse_leaflet(shape_input)
        elif isinstance(shape_input, Point):
            self.shape = shape_input
        else:
            raise Exception("ShapePoint constructor called with unsupported type")

    @staticmethod
    def parse_esdl(esdl_geometry):
        if isinstance(esdl_geometry, esdl.Point):
            return Shape.transform_crs(Point(esdl_geometry.lon, esdl_geometry.lat), esdl_geometry.CRS)
        else:
            raise Exception("Cannot instantiate a Shapely Point with an ESDL geometry other than esdl.Point")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        if isinstance(leaflet_coords, dict) and "lat" in leaflet_coords:
            return Point(leaflet_coords["lng"], leaflet_coords["lat"])
        else:
            raise Exception("Incorrect instantiation of a Shapely Point with leaflet coordinates")

    def get_esdl(self):
        return esdl.Point(lon=self.shape.coords[0][0], lat=self.shape.coords[0][1])


class ShapeLine(Shape):
    def __init__(self, shape_input):
        if isinstance(shape_input, esdl.Line):
            self.shape = self.parse_esdl(shape_input)
        elif isinstance(shape_input, list) and all(isinstance(elem, dict) for elem in shape_input):
            self.shape = self.parse_leaflet(shape_input)
        elif isinstance(shape_input, LineString):
            self.shape = shape_input
        else:
            raise Exception("ShapeLine constructor called with unsupported type")

    @staticmethod
    def parse_esdl(esdl_geometry):
        if isinstance(esdl_geometry, esdl.Line):
            linestring = list()
            for p in esdl_geometry.point:
                linestring.append((p.lon, p.lat))
            return Shape.transform_crs(LineString(linestring), esdl_geometry.CRS)
        else:
            raise Exception("Cannot instantiate a Shapely LineString with an ESDL geometry other than esdl.Line")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        if isinstance(leaflet_coords, list) and all(isinstance(elem, dict) for elem in leaflet_coords):
            linestring = list()
            for elem in leaflet_coords:
                linestring.append((elem["lng"], elem["lat"]))
            return LineString(linestring)
        else:
            raise Exception("Incorrect instantiation of a Shapely LineString with leaflet coordinates")

    def get_esdl(self):
        line = esdl.Line()
        for p in self.shape.coords:
            point = esdl.Point(lon=p[0], lat=p[1])
            line.point.append(point)
        return line


class ShapePolygon(Shape):
    def __init__(self, shape_input):
        if isinstance(shape_input, esdl.Polygon):
            self.shape = self.parse_esdl(shape_input)
        elif isinstance(shape_input, list) and all(isinstance(elem, list) for elem in shape_input):
            self.shape = self.parse_leaflet(shape_input)
        elif isinstance(shape_input, Polygon):
            self.shape = shape_input
        else:
            raise Exception("ShapePolygon constructor called with unsupported type")

    @staticmethod
    def parse_esdl(esdl_geometry):
        if isinstance(esdl_geometry, esdl.Polygon):
            exterior = list()
            interiors = list()
            for p in esdl_geometry.exterior.point:
                exterior.append([p.lon, p.lat])
            for pol in esdl_geometry.interior:
                interior = list()
                for p in pol.point:
                    interior.append([p.lon, p.lat])
                interiors.append(interior)
            return Shape.transform_crs(Polygon(exterior, interiors), esdl_geometry.CRS)
        else:
            raise Exception("Cannot instantiate a Shapely Polygon with an ESDL geometry other than esdl.Polygon")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        if isinstance(leaflet_coords, list) and all(isinstance(elem, list) for elem in leaflet_coords):
            exterior = list()
            interiors = list()
            lc_exterior = leaflet_coords.pop(0)
            for p in lc_exterior:
                exterior.append([p["lng"], p["lat"]])
            for pol in leaflet_coords:
                interior = list()
                for p in pol:
                    interior.append([p["lng"], p["lat"]])
                interiors.append(interior)
            return Polygon(exterior, interiors)
        else:
            raise Exception("Incorrect instantiation of a Shapely Polygon with leaflet coordinates")

    def get_esdl(self):
        pol = esdl.Polygon()
        exterior = esdl.SubPolygon()
        for p in self.shape.exterior.coords:
            exterior.point.append(esdl.Point(lon=p[0], lat=p[1]))
        pol.exterior = exterior
        for ip in self.shape.interiors:
            interior = esdl.SubPolygon()
            for p in ip.coords:
                interior.point.append(esdl.Point(lon=p[0], lat=p[1]))
            pol.interior.append(interior)
        return pol


class ShapeMultiPolygon(Shape):
    def __init__(self, shape_input):
        if isinstance(shape_input, esdl.MultiPolygon):
            self.shape = self.parse_esdl(shape_input)
        elif isinstance(shape_input, list) and all(isinstance(elem, list) for elem in shape_input):
            self.shape = self.parse_leaflet(shape_input)
        elif isinstance(shape_input, MultiPolygon):
            self.shape = shape_input
        else:
            raise Exception("ShapeMultiPolygon constructor called with unsupported type")

    @staticmethod
    def parse_esdl(esdl_geometry):
        if isinstance(esdl_geometry, esdl.MultiPolygon):
            plist = list()
            for p in esdl_geometry.polygon:
                plist.append(ShapePolygon.parse_esdl(p))
            return Shape.transform_crs(MultiPolygon(plist), esdl_geometry.CRS)
        else:
            raise Exception(
                "Cannot instantiate a Shapely MultiPolygon with an ESDL geometry other than esdl.MultiPolygon")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        if isinstance(leaflet_coords, list) and all(isinstance(elem, list) for elem in leaflet_coords):
            plist = list()
            for p in leaflet_coords:
                plist.append(ShapePolygon.parse_leaflet(p))
            return MultiPolygon(plist)
        else:
            raise Exception(
                "Incorrect instantiation of a Shapely MultiPolygon with leaflet coordinates")

    def get_esdl(self):
        raise Exception("Not implemented yet, MultiPolygon is not a frequent ESDL geometry")


class ShapeGeometryCollection(Shape):
    def __init__(self, shape_input):
        if isinstance(shape_input, GeometryCollection):
            self.shape = shape_input
        else:
            raise Exception("ShapeMultiPolygon constructor called with unsupported type")

    def get_esdl(self):
        raise Exception("Not implemented yet, GeometryCollection is not a frequent ESDL geometry")