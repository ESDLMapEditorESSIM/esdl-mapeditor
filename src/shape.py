#  This work is based on original code developed and copyrighted by TNO 2022.
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
from shapely import wkt, wkb, to_geojson
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, GeometryCollection, shape
from shapely.ops import transform
from shapely.validation import explain_validity
import esdl
import pyproj


class Shape:
    """
    Represents a shape, like a point, line, polygon or multi polgygon. Provides functionality to convert to and from
    ESDL geometries, Shapely geometries, WKT/WKB, Leaflet (used in the ESDL MapEditor), GeoJSON. Uses a Shapely shape
    internally and provides different methods to convert to and from different other formats.
    """
    def __init__(self):
        """
        Constructor of the Shape class.
        """
        self.shape = None

    @staticmethod
    def create(shape_input):
        """
        Function to create an instance of the right subclass of Shape based on any input. Tries to guess the input
        format and returns an instance of the right class.

        :param shape_input: input that represents information about the shape. Can be a list with coordinates, a
                            dictionary with "lat" and "lng" fields, an ESDL geometry object or a Shapely geometry object.
        :return: an instance of the right Shape subclass
        """
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

        if isinstance(shape_input, list) and all(
                isinstance(elem, list) and all(isinstance(sub_elem, list) and "lat" in sub_elem[0] for sub_elem in elem)
                for elem in shape_input):
            return ShapeMultiPolygon(shape_input)
        else:
            if isinstance(shape_input, list) and all(isinstance(elem, list) and "lat" in elem[0] for elem in shape_input):
                return ShapePolygon(shape_input)

    @staticmethod
    def parse_esdl(esdl_geometry):
        """
        Function that parses an ESDL geometry object. Must be overridden by the subclass.
        """
        pass

    @staticmethod
    def parse_leaflet(leaflet_coords):
        """
        Function that parses an list of leaflet coordinates. Must be overridden by the subclass.
        """
        pass

    @staticmethod
    def parse_geojson_geometry(geojson_geometry):
        """
        Function that parses a GeoJSON string and creates an instance of the right Shape subclass

        :param geojson_geometry: GeoJSON string
        :return: an instance of the right Shape subclass with the parsed geometry information from the GeoJSON string
        """
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
        """
        Function that parses a WKT string and creates an instance of the right Shape subclass

        :param wkt_geometry: a WKT (Well Known Text) string
        :return: an instance of the right Shape subclass with the parsed geometry information from the WKT string
        """
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
        """
        Function that parses a WKB string and creates an instance of the right Shape subclass

        :param wkb_geometry: a WKB (Well Known Binary) byte string
        :return: an instance of the right Shape subclass with the parsed geometry information from the WKB string
        """
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
        """
        Function that parses an esdl.WKT string and creates an instance of the right Shape subclass

        :param esdl_wkt: an instance of esdl.WKT
        :return: an instance of the right Shape subclass with the parsed geometry information from the esdl.WKT
        """
        if isinstance(esdl_wkt, esdl.WKT):
            return Shape.parse_wkt(esdl_wkt.value, esdl_wkt.CRS)
        else:
            raise Exception("Calling parse_esdl_WKT without an esdl.WKT parameter")

    @staticmethod
    def parse_esdl_wkb(esdl_wkb):
        """
        Function that parses an esdl.WKB string and creates an instance of the right Shape subclass

        :param esdl_wkb: an instance of esdl.WKB
        :return: an instance of the right Shape subclass with the parsed geometry information from the esdl.WKB
        """
        if isinstance(esdl_wkb, esdl.WKB):
            return Shape.parse_wkb(esdl_wkb.value, esdl_wkb.CRS)
        else:
            raise Exception("Calling parse_esdl_WKB without an esdl.WKB parameter")

    def get_shape(self):
        """
        Function that returns the Shapely geometry representation of the loaded geometry
        """
        return self.shape

    def get_esdl(self):
        """
        Function that returns an ESDL geometry. Must be overridden by the subclass.
        """
        pass

    def get_wkt(self):
        """
        Function that generates a WKT string from the loaded geometry

        :return: a WKT string representing the loaded geometry information
        """
        return self.shape.wkt

    def is_valid(self):
        """
        Returns whether the loaded shape is a valid geometry (per the OGC Simple Features rules), e.g. no
        self-intersections and holes properly contained within the exterior.
        """
        return self.shape.is_valid

    def explain_validity(self):
        """
        Returns a human-readable reason why the loaded shape is invalid, or "Valid Geometry" if it is valid.
        """
        return explain_validity(self.shape)

    def get_geojson_feature(self, properties={}):
        """
        Function that generates a GeoJSON feature from the loaded geometry, with the properties given as an input

        :param properties: the properties that must be added to the GeoJSON FFeature
        :return: a GeoJSON Feature representing the loaded geometry information, with the given properties
        """
        geojson_geometry_str = to_geojson(self.shape)
        geojson_geometry = json.loads(geojson_geometry_str)
        geojson_feature = {
            "type": "Feature",
            "geometry": geojson_geometry,
            "properties": properties
        }

        return geojson_feature

    @staticmethod
    def transform_crs(shp, from_crs):
        """
        Function that transforms the CRS (Coordinate Reference System) of the Shapely shape to WGS84 (EPSG:4326)

        :shp: input Shapely shape in any CRS that is supported by pyproj
        :from_crs: the CRS used for the Shapely shape
        :return: Shapely shape transformed to WGS84
        """
        if from_crs == "WGS84" or from_crs == "" or from_crs is None:
            from_crs = "EPSG:4326"

        if from_crs != "EPSG:4326":
            wgs84 = pyproj.CRS("EPSG:4326")
            original_crs = pyproj.CRS(from_crs)

            project = pyproj.Transformer.from_crs(original_crs, wgs84, always_xy=True).transform
            return transform(project, shp)
        else:
            return shp


class ShapePoint(Shape):
    """
    Represents a point. Provides functionality to convert to and from esdl.Point, Shapely Point, WKT/WKB,
    Leaflet (used in the ESDL MapEditor), GeoJSON. Uses a Shapely Point internally and provides different methods
    to convert to and from different other formats.
    """

    def __init__(self, shape_input):
        """
        Constructor of the ShapePoint class. Can be called with an esdl.Point, a dictionary with "lat" and "lng" keys,
        or a Shapely Point instance

        :param shape_input: the input shape, can be an esdl.Point, a dictionary with "lat" and "lng" keys,
                            or a Shapely Point instance
        """
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
        """
        Function that uses an esdl.Point instance as an input to generate a Shapely Point (using WGS84 as CRS)

        :param esdl_geometry: an esdl.Point instance
        :return: a Shapely shape (using WGS84 as CRS)
        """
        if isinstance(esdl_geometry, esdl.Point):
            return Shape.transform_crs(Point(esdl_geometry.lon, esdl_geometry.lat), esdl_geometry.CRS)
        else:
            raise Exception("Cannot instantiate a Shapely Point with an ESDL geometry other than esdl.Point")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        """
        Function that uses a dictionary with "lat" and "lng" keys as an input to generate a Shapely Point (using
        WGS84 as CRS)

        :param esdl_geometry: a dictionary with "lat" and "lng" keys
        :return: a Shapely Point (using WGS84 as CRS)
        """
        if isinstance(leaflet_coords, dict) and "lat" in leaflet_coords:
            return Point(leaflet_coords["lng"], leaflet_coords["lat"])
        else:
            raise Exception("Incorrect instantiation of a Shapely Point with leaflet coordinates")

    def get_esdl(self):
        """
        Function that generates an esdl.Point instance based on the loaded shape.

        :return: an esdl.Point instance based on the loaded shape
        """
        return esdl.Point(lon=self.shape.coords[0][0], lat=self.shape.coords[0][1])


class ShapeLine(Shape):
    """
    Represents a line. Provides functionality to convert to and from esdl.Line, Shapely LineString, WKT/WKB,
    Leaflet (used in the ESDL MapEditor), GeoJSON. Uses a Shapely LineString internally and provides different methods
    to convert to and from different other formats.
    """

    def __init__(self, shape_input):
        """
        Constructor of the ShapeLine class. Can be called with an esdl.Line, a list of dictionaries with "lat" and
        "lng" keys, or a Shapely LineString instance

        :param shape_input: the input shape, can be an esdl.Line, a list of dictionaries with "lat" and
                            "lng" keys, or a Shapely LineString instance
        """
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
        """
        Function that uses an esdl.Line instance as an input to generate a Shapely LineString (using WGS84 as CRS)

        :param esdl_geometry: an esdl.Line instance
        :return: a Shapely LineString (using WGS84 as CRS)
        """
        if isinstance(esdl_geometry, esdl.Line):
            linestring = list()
            for p in esdl_geometry.point:
                linestring.append((p.lon, p.lat))
            return Shape.transform_crs(LineString(linestring), esdl_geometry.CRS)
        else:
            raise Exception("Cannot instantiate a Shapely LineString with an ESDL geometry other than esdl.Line")

    @staticmethod
    def parse_leaflet(leaflet_coords):
        """
        Function that uses a list of dictionaries with "lat" and "lng" keys as an input to generate a Shapely
        LineString (using WGS84 as CRS)

        :param esdl_geometry: a list of dictionaries with "lat" and "lng" keys
        :return: a Shapely LineString (using WGS84 as CRS)
        """
        if isinstance(leaflet_coords, list) and all(isinstance(elem, dict) for elem in leaflet_coords):
            linestring = list()
            for elem in leaflet_coords:
                linestring.append((elem["lng"], elem["lat"]))
            return LineString(linestring)
        else:
            raise Exception("Incorrect instantiation of a Shapely LineString with leaflet coordinates")

    def get_esdl(self):
        """
        Function that generates an esdl.Line instance based on the loaded shape.

        :return: an esdl.Line instance based on the loaded shape
        """
        line = esdl.Line()
        for p in self.shape.coords:
            point = esdl.Point(lon=p[0], lat=p[1])
            line.point.append(point)
        return line


class ShapePolygon(Shape):
    """
    Represents a polygon. Provides functionality to convert to and from esdl.Polygon, Shapely Polygon, WKT/WKB,
    Leaflet (used in the ESDL MapEditor), GeoJSON. Uses a Shapely Polygon internally and provides different methods
    to convert to and from different other formats.
    """

    def __init__(self, shape_input):
        """
        Constructor of the ShapePolygon class. Can be called with an esdl.Polygon, a list of lists of dictionaries
        with "lat" and "lng" keys, or a Shapely Polygon instance

        :param shape_input: the input shape, can be an esdl.Polygon, a list of lists of dictionaries
                            with "lat" and "lng" keys, or a Shapely Polygon instance
        """
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
        """
        Function that uses an esdl.Polygon instance as an input to generate a Shapely Polygon (using WGS84 as CRS)

        :param esdl_geometry: an esdl.Polygon instance
        :return: a Shapely Polygon (using WGS84 as CRS)
        """
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
        """
        Function that uses a list of lists of dictionaries with "lat" and "lng" keys as an input to generate a Shapely
        Polygon (using WGS84 as CRS). The first element in the list represents the exterior of the polygon, the other
        elements represent zero, one or more interiors (holes in the polygon)

        :param esdl_geometry: a list of lists of dictionaries with "lat" and "lng" keys
        :return: a Shapely Polygon (using WGS84 as CRS)
        """
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
        """
        Function that generates an esdl.Polygon instance based on the loaded shape.

        :return: an esdl.Polygon instance based on the loaded shape
        """
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

    def get_leaflet_rings(self):
        """
        Returns this polygon's rings as [lat, lon] point lists (unclosed, i.e. without a last point
        repeating the first), the coordinate format used by Leaflet.
        Ring 0 is the exterior, the rest (if any) are interior holes.
        """
        rings = [list(self.shape.exterior.coords)[:-1]]
        for interior in self.shape.interiors:
            rings.append(list(interior.coords)[:-1])
        return [[[lat, lon] for lon, lat in ring] for ring in rings]


class ShapeMultiPolygon(Shape):
    """
    Represents a multipolygon. Provides functionality to convert to and from esdl.MultiPolygon, Shapely MultiPolygon,
    WKT/WKB, Leaflet (used in the ESDL MapEditor), GeoJSON. Uses a Shapely MultiPolygon internally and provides
    different methods to convert to and from different other formats.
    """

    def __init__(self, shape_input):
        """
        Constructor of the ShapeMultiPolygon class. Can be called with an esdl.MultiPolygon, a list of lists of lists
        of dictionaries with "lat" and "lng" key, or a Shapely Polygon instance

        :param shape_input: the input shape, can be an esdl.MultiPolygon, a list of lists of lists of dictionaries
                            with "lat" and "lng" key, or a Shapely MultyPolygon instance
        """
        if isinstance(shape_input, esdl.MultiPolygon):
            self.shape = self.parse_esdl(shape_input)
        elif (isinstance(shape_input, list) and
              all(isinstance(elem, list) and
                  (all(isinstance(sub_elem, list) for sub_elem in elem)) for elem in shape_input)):
            self.shape = self.parse_leaflet(shape_input)
        elif isinstance(shape_input, MultiPolygon):
            self.shape = shape_input
        else:
            raise Exception("ShapeMultiPolygon constructor called with unsupported type")

    @staticmethod
    def parse_esdl(esdl_geometry):
        """
        Function that uses an esdl.MultiPolygon instance as an input to generate a Shapely MultiPolygon (using WGS84
        as CRS)

        :param esdl_geometry: an esdl.MultiPolygon instance
        :return: a Shapely MultiPolygon (using WGS84 as CRS)
        """
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
        """
        Function that uses a list of lists of lists of dictionaries with "lat" and "lng" keys as an input to generate
        a Shapely MultiPolygon (using WGS84 as CRS). Iterates over the outer list and calls ShapePolygon.parse_leaflet
        for each element

        :param esdl_geometry: a list of lists of lists of dictionaries with "lat" and "lng" keys
        :return: a Shapely MultiPolygon (using WGS84 as CRS)
        """
        if isinstance(leaflet_coords, list) and all(isinstance(elem, list) and (all(isinstance(sub_elem, list) for sub_elem in elem)) for elem in leaflet_coords):
            plist = list()
            for p in leaflet_coords:
                plist.append(ShapePolygon.parse_leaflet(p))
            return MultiPolygon(plist)
        else:
            raise Exception(
                "Incorrect instantiation of a Shapely MultiPolygon with leaflet coordinates")

    def get_esdl(self):
        mp = esdl.MultiPolygon()
        for p in self.shape.geoms:
            mp.polygon.append(ShapePolygon(p).get_esdl())
        return mp

    def get_leaflet_coords(self):
        """
        Returns a list of sub-polygons, each a list of rings ([lat, lon] point lists; ring 0 is the
        exterior, the rest are holes), the coordinate format used by Leaflet.
        """
        return [ShapePolygon(p).get_leaflet_rings() for p in self.shape.geoms]

    def get_polygon_list_esdl(self):
        """
        Returns a list of esdl.Polygon, one per sub-polygon of the loaded MultiPolygon shape.
        """
        return [ShapePolygon(p).get_esdl() for p in self.shape.geoms]


class ShapeGeometryCollection(Shape):
    """
    Represents a geometry collection. Provides functionality to convert to and from Shapely GeometryCollection,
    WKT/WKB and GeoJSON. Uses a Shapely GeometryCollection internally and provides different methods
    to convert to and from different other formats.
    """

    def __init__(self, shape_input):
        """
        Constructor of the ShapeGeometryCollection class. Can be called with a Shapely GeometryCollection instance

        :param shape_input: the input shape, can be a Shapely GeometryCollection instance
        """
        if isinstance(shape_input, GeometryCollection):
            self.shape = shape_input
        else:
            raise Exception("ShapeMultiPolygon constructor called with unsupported type")

    def get_esdl(self):
        """
        This get_esdl function is not yet implemented for the ShapeGeometryCollection class, as GeometryCollection
        is not a frequent ESDL geometry
        """
        raise Exception("Not implemented yet, GeometryCollection is not a frequent ESDL geometry")
