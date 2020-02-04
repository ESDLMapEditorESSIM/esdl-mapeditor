from esdl import esdl
from utils.RDWGSConverter import RDWGSConverter
   
   
# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
def convert_coordinates_into_subpolygon(coord_list):
    # print(coord_list)
    # [[x1,y1], [x2,y2], ...]

    # coord_list contains coordinates in [lon, lat] order!

    subpolygon = esdl.SubPolygon()
    for coord_pairs in coord_list:
        point = esdl.Point()
        point.lat = coord_pairs[1]
        point.lon = coord_pairs[0]
        subpolygon.point.append(point)

    return subpolygon


def convert_pcoordinates_into_polygon(coord_list):
    polygon = esdl.Polygon()

    coord_exterior = coord_list[0]
    exterior = convert_coordinates_into_subpolygon(coord_exterior)
    polygon.exterior = exterior

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


def create_geojson(id, name, KPIs, boundary_wgs):
    return {
        "type": "Feature",
        "geometry": boundary_wgs,
        "properties": {
            "id": id,
            "name": name,
            "KPIs": KPIs
        }
    }


def parse_esdl_subpolygon(subpol, close=True):
    ar = []
    points = subpol.point
    firstlat = points[0].lat
    firstlon = points[0].lon
    for point in points:
        lat = point.lat
        lon = point.lon
        ar.append([lon, lat])
    if close:
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


def exchange_coordinates(coords):

    for i in range(0, len(coords)):
        point = coords[i]
        coords[i] = [point[1], point[0]]

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


def calculate_polygon_center(polygon):
    min_lat = float('inf')
    min_lon = float('inf')
    max_lat = 0
    max_lon = 0

    exterior = polygon.exterior
    points = exterior.point
    for p in points:
        if p.lat < min_lat: min_lat = p.lat
        if p.lon < min_lon: min_lon = p.lon
        if p.lat > max_lat: max_lat = p.lat
        if p.lon > max_lon: max_lon = p.lon

    return ((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)


def remove_latlng_annotation_in_array(coords):
    for i in range(0, len(coords)):
        c = coords[i]
        c_new = [c['lat'], c['lng']]
        coords[i] = c_new

    return coords


def remove_latlng_annotation_in_array_of_arrays(coords):
    for i in range(0, len(coords)):
        coords[i] = remove_latlng_annotation_in_array(coords[i])

    return coords


def remove_duplicates_in_polyline(array_of_points):
    coords = []
    i = 0
    prev_lat = 0
    prev_lng = 0
    while i < len(array_of_points):
        coord = array_of_points[i]

        # Don't understand why, but sometimes coordinates come in twice
        if prev_lat != coord['lat'] or prev_lng != coord['lng']:
            coords.append({'lat': coord['lat'], 'lng': coord['lng']})

            prev_lat = coord['lat']
            prev_lng = coord['lng']
        i += 1

    return coords


def remove_duplicates_in_polygon(array_of_array_of_points):
    for i in range(0, len(array_of_array_of_points)):
        array_of_array_of_points[i] = remove_duplicates_in_polyline(array_of_array_of_points[i])

    return array_of_array_of_points


def create_ESDL_geometry(shape):

    if shape['type'] == 'point':
        geometry = esdl.Point(lon=shape['lng'], lat=shape['lat'])

    elif shape['type'] == 'polyline':
        polyline_data = shape['coordinates']
        geometry = esdl.Line()

        i = 0
        prev_lat = 0
        prev_lng = 0
        while i < len(polyline_data):
            coord = polyline_data[i]

            # Don't understand why, but sometimes coordinates come in twice
            if prev_lat != coord['lat'] or prev_lng != coord['lng']:
                point = esdl.Point(lat=coord['lat'], lon=coord['lng'])
                geometry.point.append(point)
                prev_lat = coord['lat']
                prev_lng = coord['lng']
            i += 1

    elif shape['type'] == 'polygon' or shape['type'] == 'rectangle':
        polygon_data = shape['coordinates']  # [lat, lon]
        print(polygon_data)
        polygon_data = remove_duplicates_in_polygon(polygon_data)
        polygon_data = remove_latlng_annotation_in_array_of_arrays(polygon_data)
        polygon_data = exchange_polygon_coordinates(polygon_data)  # --> [lon, lat]

        geometry = convert_pcoordinates_into_polygon(polygon_data)  # expects [lon, lat]

    # elif shape['type'] == 'rectangle':
    #     rect_data = shape['coordinates']
    #     print(rect_data)
    #     #polygon_data = [[rect_data[0], [rect_data[0][0],rect_data[1][1]], rect_data[1], [rect_data[1][0],rect_data[0][1]]]]
    #
    #     geometry = ESDLGeometry.convert_pcoordinates_into_polygon(rect_data)  # expects [lon, lat]


    return geometry
