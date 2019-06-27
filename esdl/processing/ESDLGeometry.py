from esdl import esdl;

class ESDLGeometry:

    def __init__(self):
        pass

# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def convert_coordinates_into_subpolygon(coord_list):
        # print(coord_list)
        # [[x1,y1], [x2,y2], ...]

        subpolygon = esdl.SubPolygon()
        for coord_pairs in coord_list:
            point = esdl.Point()
            point.lat = coord_pairs[0]
            point.lon = coord_pairs[1]
            subpolygon.point.append(point)

        return subpolygon

    @staticmethod
    def convert_pcoordinates_into_polygon(coord_list):
        polygon = esdl.Polygon()

        coord_exterior = coord_list[0]
        exterior  = ESDLGeometry.convert_coordinates_into_subpolygon(coord_exterior)
        polygon.exterior.append(exterior)

        if len(coord_list) > 1:
            coord_list.pop(0)  # remove exterior polygon
            for coord_interior in coord_list:  # iterate over remaining interiors
                interior = ESDLGeometry.convert_coordinates_into_subpolygon(coord_interior)
                polygon.interior.append(interior)

        return polygon

    @staticmethod
    def convert_mpcoordinates_into_multipolygon(coord_list):
        mp = esdl.MultiPolygon()
        for coord_polygon in coord_list:
            polygon = ESDLGeometry.convert_pcoordinates_into_polygon(coord_polygon)
            mp.polygon.append(polygon)

        return mp

    @staticmethod
    def create_boundary_from_geometry(geometry):
        if isinstance(geometry, esdl.Polygon):
            exterior = geometry.exterior
            interiors = geometry.interior

            ar = []
            ar.append(ESDLGeometry.parse_esdl_subpolygon(exterior))
            for interior in interiors:
                ar.append(ESDLGeometry.parse_esdl_subpolygon(interior))

            geom = {
                'type': 'Polygon',  # TODO: was POLYGON
                'coordinates': ar
            }
            # print(geom)

        if isinstance(geometry, esdl.MultiPolygon):
            polygons = geometry.polygon
            mp = []
            for polygon in polygons:
                exterior = polygon.exterior
                interiors = polygon.interior

                ar = []
                ar.append(ESDLGeometry.parse_esdl_subpolygon(exterior))
                for interior in interiors:
                    ar.append(ESDLGeometry.parse_esdl_subpolygon(interior))

                mp.append(ar)

            geom = {
                'type': 'MultiPolygon',
                'coordinates': mp
            }

        return geom

    @staticmethod
    def parse_esdl_subpolygon(subpol):
        ar = []
        points = subpol.point
        firstlat = points[0].lat
        firstlon = points[0].lon
        for point in points:
            lat = point.lat
            lon = point.lon
            ar.append([lon, lat])
        ar.append([firstlon, firstlat])  # close the polygon: TODO: check if necessary??
        return ar

    @staticmethod
    def create_boundary_from_contour(contour):
        exterior = contour.exterior
        interiors = contour.interior

        ar = []
        ar.append(ESDLGeometry.parse_esdl_subpolygon(exterior))
        for interior in interiors:
            ar.append(ESDLGeometry.parse_esdl_subpolygon(interior))

        geom = {
            'type': 'Polygon',
            'coordinates': ar
        }
        # print(geom)

        return geom

    @staticmethod
    def create_geometry_from_geom(geom):
        """
        :param geom: geometry information
        :return: esdl.MultiPolygon or esdl.Polygon
        """
        # paramter geom has following structure:
        # 'geom': {
        #    "type":"MultiPolygon",
        #    "bbox":[...],
        #    "coordinates":[[[[6.583651,53.209594], [6.58477,...,53.208816],[6.583651,53.209594]]]]
        # }

        type = geom['type']
        coordinates = geom['coordinates']

        if type == 'MultiPolygon':
            return ESDLGeometry.convert_mpcoordinates_into_multipolygon(coordinates)
        if type == 'Polygon':
            return ESDLGeometry.convert_pcoordinates_into_polygon(coordinates)

        return None



