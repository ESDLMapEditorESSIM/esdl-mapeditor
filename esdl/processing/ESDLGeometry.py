from esdl import esdl
from utils.RDWGSConverter import RDWGSConverter
   
# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
    
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


def convert_pcoordinates_into_polygon(coord_list):
    polygon = esdl.Polygon()

    coord_exterior = coord_list[0]
    exterior  = convert_coordinates_into_subpolygon(coord_exterior)
    polygon.exterior.append(exterior)

    if len(coord_list) > 1:
        coord_list.pop(0)  # remove exterior polygon
        for coord_interior in coord_list:  # iterate over remaining interiors
            interior = convert_coordinates_into_subpolygon(coord_interior)
            polygon.interior.append(interior)

    return polygon


def convert_mpcoordinates_into_multipolygon(coord_list):
    mp = esdl.MultiPolygon()
    for coord_polygon in coord_list:
        polygon = convert_pcoordinates_into_polygon(coord_polygon)
        mp.polygon.append(polygon)

    return mp


def create_boundary_from_geometry(geometry):
    if isinstance(geometry, esdl.Polygon):
        exterior = geometry.exterior
        interiors = geometry.interior

        ar = []
        ar.append(parse_esdl_subpolygon(exterior))
        for interior in interiors:
            ar.append(parse_esdl_subpolygon(interior))

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
            ar.append(parse_esdl_subpolygon(exterior))
            for interior in interiors:
                ar.append(parse_esdl_subpolygon(interior))

            mp.append(ar)

        geom = {
            'type': 'MultiPolygon',
            'coordinates': mp
        }

    return geom


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


def create_boundary_from_contour(contour):
    exterior = contour.exterior
    interiors = contour.interior

    ar = []
    ar.append(parse_esdl_subpolygon(exterior))
    for interior in interiors:
        ar.append(parse_esdl_subpolygon(interior))

    geom = {
        'type': 'Polygon',
        'coordinates': ar
    }
    # print(geom)

    return geom


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
        return convert_mpcoordinates_into_multipolygon(coordinates)
    if type == 'Polygon':
        return convert_pcoordinates_into_polygon(coordinates)

    return None

def convert_mp_rd_to_wgs(coords):
    RDWGS = RDWGSConverter()

    for i in range(0, len(coords)):
        for j in range(0, len(coords[i])):
            for k in range(0, len(coords[i][j])):
                point = coords[i][j][k]
                coords[i][j][k] = RDWGS.fromRdToWgs(point)

    return coords


def exchange_polygon_coordinates(coords):

    for i in range(0, len(coords)):
        for j in range(0, len(coords[i])):
            point = coords[i][j]
            coords[i][j] = [point[1], point[0]]

    return coords


def exchange_multipolygon_coordinates(coords):

    for i in range(0, len(coords)):
        for j in range(0, len(coords[i])):
            for k in range(0, len(coords[i][j])):
                point = coords[i][j][k]
                coords[i][j][k] = [point[1], point[0]]

    return coords
