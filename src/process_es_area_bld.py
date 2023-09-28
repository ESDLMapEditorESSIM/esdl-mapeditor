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
import random

from sys import getsizeof
from flask import session
from flask_socketio import emit

from esdl import esdl
from esdl.processing import ESDLGeometry, ESDLAsset, ESDLEnergySystem, ESDLQuantityAndUnits
from esdl.processing.ESDLEnergySystem import get_notes_list
from extensions.boundary_service import BoundaryService, is_valid_boundary_id
from extensions.session_manager import set_handler, get_handler, get_session, set_session_for_esid, set_session, \
    get_session_for_esid
from src.esdl_helper import generate_profile_info, get_asset_and_coord_from_port_id, asset_state_to_ui, \
    get_tooltip_asset_attrs, add_spatial_attributes
from src.shape import Shape, ShapePoint
from src.assets_to_be_added import AssetsToBeAdded
from utils.RDWGSConverter import RDWGSConverter
import shapely
import math
import re


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


def get_area_id_from_mapeditor_id(id):
    """
    Mapeditor frontend uses e.g. 'BUxxxxxxxx (1 of 4)' in case of MulitPolygons
    :param id: id from the frontend
    :return: clean id (without ' (1 of 4)')
    """
    if re.match(r".* ([0-9]+ of [0-9]+)", id):
        return id.split()[0]
    else:
        return id


# ---------------------------------------------------------------------------------------------------------------------
#   Update asset geometries
# ---------------------------------------------------------------------------------------------------------------------
def calc_random_location_around_center(center, delta_x, delta_y, convert_RD_to_WGS):
    geom = esdl.Point()
    x = center[0] + ((-0.5 + random.random()) * delta_x / 2)
    y = center[1] + ((-0.5 + random.random()) * delta_y / 2)
    if convert_RD_to_WGS and (x > 180 or y > 180):  # Assume RD
        rdwgs = RDWGSConverter()
        wgs = rdwgs.fromRdToWgs([x, y])
        geom.lat = wgs[0]
        geom.lon = wgs[1]
    else:
        geom.lat = y
        geom.lon = x
    return geom


def calc_building_assets_location(building, force_repositioning=False):
    """
    Calculate the locations of assets in buildings when they are not given
    The building editor uses a 500x500 pixel canvas
    Rules:
    - Assets of type AbstractConnection are placed in the left-most column
    - Other transport assets in the second column
    - Then production
    - Then conversion and storage
    - Then demand
    - And finally potentials
    """
    num_conns = 0
    num_transp = 0
    num_prod = 0
    num_conv_stor = 0
    num_cons = 0
    num_potentials = 0
    for basset in building.asset:
        if isinstance(basset, esdl.AbstractConnection):
            num_conns = num_conns + 1
        elif isinstance(basset, esdl.Transport):
            num_transp = num_transp + 1
        if isinstance(basset, esdl.Producer):
            num_prod = num_prod + 1
        if isinstance(basset, esdl.Conversion) or isinstance(basset, esdl.Storage):
            num_conv_stor = num_conv_stor + 1
        if isinstance(basset, esdl.Consumer):
            num_cons = num_cons + 1
    for bpotential in building.potential:
        num_potentials = num_potentials + 1

    num_cols = 0
    if num_conns > 0: num_cols = num_cols + 1
    if num_transp > 0: num_cols = num_cols + 1
    if num_prod > 0: num_cols = num_cols + 1
    if num_conv_stor > 0: num_cols = num_cols + 1
    if num_cons > 0: num_cols = num_cols + 1
    if num_potentials > 0: num_cols = num_cols + 1

    if num_cols > 0:
        column_width = 500 / (num_cols + 1)
        column_idx = 1
        column_conns_x = int(num_conns > 0) * column_idx * column_width
        column_idx += (num_conns > 0)
        column_transp_x = int(num_transp> 0) * column_idx * column_width
        column_idx += (num_transp > 0)
        column_prod_x = int(num_prod > 0) * column_idx * column_width
        column_idx += (num_prod > 0)
        column_cs_x = int(num_conv_stor > 0) * column_idx * column_width
        column_idx += (num_conv_stor > 0)
        column_cons_x = int(num_cons > 0) * column_idx * column_width
        column_idx += (num_cons > 0)
        column_pots_x = int(num_potentials > 0) * column_idx * column_width
        column_idx += (num_potentials > 0)

        row_conns_height = 500 / (num_conns + 1)
        row_transp_height = 500 / (num_transp + 1)
        row_prod_height = 500 / (num_prod + 1)
        row_cs_height = 500 / (num_conv_stor + 1)
        row_cons_height = 500 / (num_cons + 1)
        row_pots_height = 500 / (num_potentials + 1)

        row_conns_idx = 1
        row_transp_idx = 1
        row_prod_idx = 1
        row_cs_idx = 1
        row_cons_idx = 1
        row_pots_idx = 1

        for basset in building.asset:
            if not basset.geometry or force_repositioning:
                if isinstance(basset, esdl.AbstractConnection):
                    basset.geometry = esdl.Point(lon=column_conns_x, lat=row_conns_idx * row_conns_height, CRS="Simple")
                    row_conns_idx = row_conns_idx + 1
                elif isinstance(basset, esdl.Transport):
                    basset.geometry = esdl.Point(lon=column_transp_x, lat=row_transp_idx * row_transp_height, CRS="Simple")
                    row_transp_idx = row_transp_idx + 1
                if isinstance(basset, esdl.Producer):
                    basset.geometry = esdl.Point(lon=column_prod_x, lat=row_prod_idx * row_prod_height, CRS="Simple")
                    row_prod_idx = row_prod_idx + 1
                if isinstance(basset, esdl.Conversion) or isinstance(basset, esdl.Storage):
                    basset.geometry = esdl.Point(lon=column_cs_x, lat=row_cs_idx * row_cs_height, CRS="Simple")
                    row_cs_idx = row_cs_idx + 1
                if isinstance(basset, esdl.Consumer):
                    basset.geometry = esdl.Point(lon=column_cons_x, lat=row_cons_idx * row_cons_height, CRS="Simple")
                    row_cons_idx = row_cons_idx + 1

        for bpotential in building.potential:
            if not bpotential.geometry or force_repositioning:
                bpotential.geometry = esdl.Point(lon=column_pots_x, lat=row_pots_idx * row_pots_height, CRS="Simple")
                row_pots_idx = row_pots_idx + 1


def calc_possible_locations_in_area(shape, num_assets_in_area):
    """ Generate a list of locations in the area (represented by its shape)
    Find nx and ny such that:
    nx * ny = num_points and nx/ny = bbox_width / bbox_height

    --> nx = bbox_width * ny / bbox_height
    --> ny = sqrt(num_points * bbox_height / bbox_width)

    :param shape: the shape object belonging to the area
    :param num_assets_in_area: number of assets that need to be positioned within the area
    :return: list of Shapely Points that lie within the (multi)polygon shape
    """

    bbox = shape.shape.bounds   # returns (minx, miny, maxx, maxy)
    rect_pol = shapely.geometry.box(bbox[0], bbox[1], bbox[2], bbox[3])
    shape_area = shape.shape.area
    bbox_area = rect_pol.area
    # Use 2 as a scaling factor (for the fact that the polygon will not align with the chosen grid
    bbox_num_points = 2 * round(num_assets_in_area * bbox_area / shape_area)

    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]

    ny = round(math.sqrt(bbox_num_points * bbox_height / bbox_width))
    if ny == 0:     # This occurred for a very 'thin' neighbourhood (BU03631007), with one asset
        ny = 1
    nx = round(bbox_num_points / ny)
    delta_y = bbox_height / (ny + 1)
    delta_x = bbox_width / (nx + 1)

    possible_locations = list()

    # generate raster based on bbox and add points from raster that are within shape to possible_locations list
    for x_iter in range(nx):
        for y_iter in range(ny):
            p = shapely.geometry.Point(bbox[0] + (x_iter+1)*delta_x, bbox[1] + (y_iter+1)*delta_y)
            if p.within(shape.shape):
                possible_locations.append(ShapePoint(p))

    return possible_locations


def choose_location(possible_locations):
    idx = random.randrange(0, len(possible_locations))
    location = possible_locations.pop(idx)
    return location


def update_asset_geometries_shape(area, shape):

    possible_locations = None
    if shape:
        num_assets_in_area = len(area.asset)
        if num_assets_in_area > 0:
            possible_locations = calc_possible_locations_in_area(shape, num_assets_in_area)

    # TODO: An area with a building, with buildingunits (!) with assets is not supported yet
    for asset in area.asset:
        geom = asset.geometry
        if not geom and possible_locations:
            loc = choose_location(possible_locations).get_esdl()
            asset.geometry = loc
            # print("assigning location lng:{} lat:{} to asset".format(loc.lon, loc.lat))

        if isinstance(asset, esdl.AbstractBuilding):
            calc_building_assets_location(asset)


# ---------------------------------------------------------------------------------------------------------------------
#  Boundary information processing
# ---------------------------------------------------------------------------------------------------------------------
def create_building_KPIs(building):
    KPIs = {}

    try:
        largest_bunit_floorArea = 0
        largest_bunit_type = None

        for basset in building.asset:
            if isinstance(basset, esdl.BuildingUnit):
                if basset.floorArea > largest_bunit_floorArea:
                    largest_bunit_floorArea = basset.floorArea
                    btypes = []
                    for gd in basset.type:
                        btypes.append(gd.name)
                    largest_bunit_type = ", ".join(btypes)

        if largest_bunit_type:
            KPIs["buildingType"] = largest_bunit_type
    except:
        pass

    try:
        if building.buildingYear > 0:
            KPIs["buildingYear"] = building.buildingYear
    except:
        pass

    try:
        if building.floorArea > 0:
            KPIs["floorArea"] = building.floorArea
    except:
        pass

    if building.KPIs:
        for kpi in building.KPIs.kpi:
            KPIs[kpi.name] = kpi.value

    return KPIs


def find_area_info_geojson(area_list, pot_list, this_area, shape_dictionary):
    area_id = this_area.id
    area_name = this_area.name
    if not area_name: area_name = ""
    area_scope = this_area.scope
    area_geometry = this_area.geometry

    user = get_session('user-email')
    user_settings = BoundaryService.get_instance().get_user_settings(user)
    boundaries_year = user_settings['boundaries_year']

    geojson_KPIs = {}
    geojson_dist_kpis = {}
    area_KPIs = this_area.KPIs
    if area_KPIs:
        for kpi in area_KPIs.kpi:
            if not isinstance(kpi, esdl.DistributionKPI):
                kpi_qau = kpi.quantityAndUnit
                if kpi_qau:
                    if isinstance(kpi_qau, esdl.QuantityAndUnitReference):
                        kpi_qau = kpi_qau.reference

                    if not kpi_qau:     # Reference field in the ESDL could be "" (but should never be)
                        unit = ''
                    else:
                        unit = ESDLQuantityAndUnits.unit_to_string(kpi_qau)
                else:
                    unit = ''
                geojson_KPIs[kpi.name] = {
                    'value': kpi.value,
                    'unit': unit
                }
            else:
                geojson_dist_kpis[kpi.name] = {"type": "distributionKPI",
                                               "value": []}
                for str_val in kpi.distribution.stringItem:
                    geojson_dist_kpis[kpi.name]["value"].append({"name": str_val.label,
                                              "value": str_val.value})

                if area_geometry:
                    shape = Shape.create(area_geometry)
                    geojson_dist_kpis[kpi.name]["location"] = [shape.shape.centroid.coords.xy[1][0], shape.shape.centroid.coords.xy[0][0]]
                else:
                    geojson_dist_kpis[kpi.name]["location"] = None

    area_shape = None

    if area_geometry:
        if isinstance(area_geometry, esdl.Polygon):
            shape_polygon = Shape.create(area_geometry)
            area_list.append(shape_polygon.get_geojson_feature({
                "id": area_id,
                "name": area_name,
                "KPIs": geojson_KPIs,
                "dist_KPIs": geojson_dist_kpis
            }))
            area_shape = shape_polygon
        if isinstance(area_geometry, esdl.MultiPolygon):
            boundary_wgs = ESDLGeometry.create_boundary_from_geometry(area_geometry)
            shape_multipolygon = Shape.parse_geojson_geometry(boundary_wgs)
            num_sub_polygons = len(shape_multipolygon.shape.geoms)
            for i, pol in enumerate(shape_multipolygon.shape.geoms):
                if num_sub_polygons > 1:
                    area_id_number = " ({} of {})".format(i + 1, num_sub_polygons)
                else:
                    area_id_number = ""
                shape_polygon = Shape.create(pol)
                area_list.append(shape_polygon.get_geojson_feature({
                    "id": area_id + area_id_number,
                    "name": area_name,
                    "KPIs": geojson_KPIs,
                    "dist_KPIs": geojson_dist_kpis
                }))
            area_shape = shape_multipolygon
        if isinstance(area_geometry, esdl.WKT):
            shape_wkt = Shape.create(area_geometry)
            area_list.append(shape_wkt.get_geojson_feature({
                "id": area_id,
                "name": area_name,
                "KPIs": geojson_KPIs
            }))
            area_shape = shape_wkt
    else:
        if area_id and area_scope.name != 'UNDEFINED':
            if is_valid_boundary_id(area_id):
                # print('Retrieve boundary from boundary service')
                boundary_wgs = BoundaryService.get_instance().get_boundary_from_service(boundaries_year, area_scope, str.upper(area_id))
                if boundary_wgs:
                    sh = Shape.parse_geojson_geometry(boundary_wgs['geom'])
                    num_sub_polygons = len(sh.shape.geoms)
                    for i, pol in enumerate(sh.shape.geoms):
                        if num_sub_polygons > 1:
                            area_id_number = " ({} of {})".format(i + 1, num_sub_polygons)
                        else:
                            area_id_number = ""
                        shape_polygon = Shape.create(pol)
                        # We still need to add the center of the area for the distribution KPI.
                        if area_KPIs:
                            for kpi in area_KPIs.kpi:
                                if isinstance(kpi, esdl.DistributionKPI):
                                    shape = sh
                                    geojson_dist_kpis[kpi.name]["location"] = [shape.shape.centroid.coords.xy[1][0],
                                                                               shape.shape.centroid.coords.xy[0][0]]

                        area_list.append(shape_polygon.get_geojson_feature({
                            "id": area_id + area_id_number,
                            "name": boundary_wgs['name'],
                            "KPIs": geojson_KPIs,
                            "dist_KPIs": geojson_dist_kpis
                        }))

                    area_shape = sh

    # assign random coordinates if boundary is given and area contains assets without coordinates
    # and gives assets within buildings a proper coordinate
    if area_shape:
        shape_dictionary[area_id] = area_shape
    # call this function even with area_shape == None, to position building assets inside a building
    update_asset_geometries_shape(this_area, area_shape)

    potentials = this_area.potential
    for potential in potentials:
        potential_geometry = potential.geometry
        potential_name = potential.name
        if not potential_name:
            potential_name = ""
        if potential_geometry:
            if isinstance(potential_geometry, esdl.WKT):
                shape = Shape.create(potential_geometry)
                pot_list.append(shape.get_geojson_feature({
                    "id": potential.id,
                    "name": potential_name,
                }))
                shape_dictionary[potential.id] = shape

    for area in this_area.area:
        find_area_info_geojson(area_list, pot_list, area, shape_dictionary)


def create_area_info_geojson(area):
    area_list = []
    pot_list = []

    shape_dictionary = get_session('shape_dictionary')
    if not shape_dictionary:
        shape_dictionary = {}

    print("- Finding ESDL boundaries...")
    BoundaryService.get_instance().preload_area_subboundaries_in_cache(area)
    find_area_info_geojson(area_list, pot_list, area, shape_dictionary)
    print("- Done")

    set_session('shape_dictionary', shape_dictionary)
    return area_list, pot_list


def find_boundaries_in_ESDL(top_area):
    print("Finding area and potential boundaries in ESDL")
    area_list, pot_list = create_area_info_geojson(top_area)

    # Sending an empty list triggers removing the legend at client side
    print('- Sending area information to client, size={}'.format(getsizeof(area_list)))
    emit('geojson', {"layer": "area_layer", "geojson": area_list})
    # Buildings are now taken care of in process_building
    # print('- Sending building information to client, size={}'.format(getsizeof(building_list)))
    # emit('geojson', {"layer": "bld_layer", "geojson": building_list})
    print('- Sending potential information to client, size={}'.format(getsizeof(pot_list)))
    emit('geojson', {"layer": "pot_layer", "geojson": pot_list})


def add_missing_coordinates(area):
    min_lat = float("inf")
    max_lat = -float("inf")
    min_lon = float("inf")
    max_lon = -float("inf")

    for child in area.eAllContents():
        point = None
        if isinstance(child, esdl.Polygon):
            if child.CRS != "Simple": point = child.exterior.point[0]     # take first coordinate of exterior of polygon
        if isinstance(child, esdl.Point):
            if child.CRS != "Simple": point = child
        if point:
            if point.lat < min_lat: min_lat = point.lat
            if point.lat > max_lat: max_lat = point.lat
            if point.lon < min_lon: min_lon = point.lon
            if point.lon > max_lon: max_lon = point.lon
            point = None

    delta_x = max_lon - min_lon
    delta_y = max_lat - min_lat
    center = [(min_lon + max_lon)/2, (min_lat + max_lat)/2]
    RD_coords = (max_lat > 180 and max_lon > 180)               # boolean indicating if RD CRS is used

    for child in area.eAllContents():
        if (isinstance(child, esdl.EnergyAsset) and not isinstance(child.eContainer(), esdl.AbstractBuilding)) or \
                isinstance(child, esdl.AggregatedBuilding) or isinstance(child, esdl.Building):
            if not child.geometry:
                print("add missing coordinates for asset {}".format(child.name))
                child.geometry = calc_random_location_around_center(center, delta_x / 4, delta_y / 4, RD_coords)


def add_asset_to_asset_list(asset_list, asset):
    port_list = []
    ports = asset.port
    for p in ports:
        conn_to_ids = [cp.id for cp in p.connectedTo]
        profile = p.profile
        profile_info_list = []
        p_carr_id = None
        if p.carrier:
            p_carr_id = p.carrier.id
        if profile:
            profile_info_list = []  # generate_profile_info(profile)
        port_list.append(
            {'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to_ids, 'profile': profile_info_list,
             'carrier': p_carr_id})

    # Collect extra attributes that might be required to draw specific icons, ...
    extra_attributes = dict()
    extra_attributes['assetType'] = asset.assetType

    state = asset_state_to_ui(asset)
    geom = asset.geometry
    if geom:
        if isinstance(geom, esdl.Point):
            lat = geom.lat
            lon = geom.lon

            capability_type = ESDLAsset.get_asset_capability_type(asset)
            attrs = get_tooltip_asset_attrs(asset, 'marker')
            add_spatial_attributes(asset, attrs)
            asset_list.append(['point', 'asset', asset.name, asset.id, type(asset).__name__, [lat, lon],
                               attrs, state, port_list, capability_type, extra_attributes])
        if isinstance(geom, esdl.Line):
            coords = []
            for point in geom.point:
                coords.append([point.lat, point.lon])
            attrs = get_tooltip_asset_attrs(asset, 'line')
            add_spatial_attributes(asset, attrs)
            asset_list.append(['line', 'asset', asset.name, asset.id, type(asset).__name__, coords,
                               attrs, state, port_list])
        if isinstance(geom, esdl.Polygon):
            coords = ESDLGeometry.parse_esdl_subpolygon(geom.exterior, False)  # [lon, lat]
            coords = ESDLGeometry.exchange_coordinates(coords)  # --> [lat, lon]
            capability_type = ESDLAsset.get_asset_capability_type(asset)
            attrs = get_tooltip_asset_attrs(asset, 'polygon')
            add_spatial_attributes(asset, attrs)
            asset_list.append(
                ['polygon', 'asset', asset.name, asset.id, type(asset).__name__, coords, attrs, state,
                 port_list, capability_type, extra_attributes])


# ---------------------------------------------------------------------------------------------------------------------
#  Process building and process area
# ---------------------------------------------------------------------------------------------------------------------
def process_building(esh, es_id, asset_list, building_list, area_bld_list, conn_list, building, bld_editor, level):
    # Add building to list that is shown in a dropdown at the top
    area_bld_list.append(['Building', building.id, building.name, level])

    # Determine if building has assets
    building_has_assets = False
    if building.asset:
        for basset in building.asset:
            if isinstance(basset, esdl.EnergyAsset):
                building_has_assets = True
                break

    # Generate information for drawing building (as a point or a polygon)
    if isinstance(building, esdl.Building) or isinstance(building, esdl.AggregatedBuilding):
        geometry = building.geometry
        bld_KPIs = create_building_KPIs(building)

        # Collect extra attributes that might be required to draw specific icons, ...
        extra_attributes = dict()
        extra_attributes['assetType'] = building.assetType

        if geometry:
            if isinstance(geometry, esdl.Point):
                building_list.append(
                    ['point', building.name, building.id, type(building).__name__, [geometry.lat, geometry.lon],
                     building_has_assets, bld_KPIs, extra_attributes])
                bld_coord = (geometry.lat, geometry.lon)
            elif isinstance(geometry, esdl.Polygon):
                coords = ESDLGeometry.parse_esdl_subpolygon(building.geometry.exterior, False)  # [lon, lat]
                coords = ESDLGeometry.exchange_coordinates(coords)  # --> [lat, lon]
                # building_list.append(['polygon', building.name, building.id, type(building).__name__, coords, building_has_assets])
                boundary = ESDLGeometry.create_boundary_from_geometry(geometry)
                building_list.append(['polygon', building.name, building.id, type(building).__name__,
                                      boundary['coordinates'], building_has_assets, bld_KPIs, extra_attributes])
                # bld_coord = coords
                bld_coord = ESDLGeometry.calculate_polygon_center(geometry)
    elif building.containingBuilding:       # BuildingUnit
        bld_geom = building.containingBuilding.geometry
        if bld_geom:
            if isinstance(bld_geom, esdl.Point):
                bld_coord = (bld_geom.lat, bld_geom.lon)
            elif isinstance(bld_geom, esdl.Polygon):
                bld_coord = ESDLGeometry.calculate_polygon_center(bld_geom)

    # Iterate over all assets in building to gather all required information
    for basset in building.asset:
        if isinstance(basset, esdl.AbstractBuilding):
            process_building(esh, es_id, asset_list, building_list, area_bld_list, conn_list, basset, bld_editor, level + 1)
        else:
            # Create a list of ports for this asset
            port_list = []
            ports = basset.port
            for p in ports:
                conn_to = p.connectedTo
                conn_to_id_list = [ct.id for ct in conn_to]
                carrier_id = p.carrier.id if p.carrier else None
                # TODO: add profile_info
                port_list.append({'name': p.name, 'id': p.id, 'type': type(p).__name__, 'conn_to': conn_to_id_list, 'carrier': carrier_id})

            geom = basset.geometry
            coord = ()
            if geom:    # Individual asset in Building has its own geometry information
                if isinstance(geom, esdl.Point):
                    lat = geom.lat
                    lon = geom.lon
                    coord = (lat, lon)

                    capability_type = ESDLAsset.get_asset_capability_type(basset)
                    state = asset_state_to_ui(basset)
                    if bld_editor:
                        tooltip_asset_attrs = get_tooltip_asset_attrs(basset, 'marker')
                        extra_attributes = dict()
                        extra_attributes['assetType'] = basset.assetType
                        asset_list.append(['point', 'asset', basset.name, basset.id, type(basset).__name__, [lat, lon],
                                           tooltip_asset_attrs, state, port_list, capability_type, extra_attributes])
                else:
                    send_alert("Assets within buildings with geometry other than esdl.Point are not supported")

            # Inherit geometry from containing building
            # if level > 0:
            #     coord = bld_coord

            ports = basset.port
            for p in ports:
                p_carr_id = None
                if p.carrier:
                    p_carr_id = p.carrier.id
                conn_to = p.connectedTo
                if conn_to:
                    for pc in conn_to:
                        in_different_buildings = False
                        pc_asset = get_asset_and_coord_from_port_id(esh, es_id, pc.id)

                        # If the asset the current asset connects to, is in a building...
                        if pc_asset['asset'].containingBuilding:
                            bld_pc_asset = pc_asset['asset'].containingBuilding
                            bld_basset = basset.containingBuilding
                            # If the asset is in a different building ...
                            if not bld_pc_asset == bld_basset:
                                in_different_buildings = True
                                if bld_pc_asset.geometry:
                                    if bld_editor:
                                        # ... connect to the left border
                                        pc_asset_coord = (coord[0], 0)
                                    else:
                                        # ... use the building coordinate instead of the asset coordinate
                                        if isinstance(bld_pc_asset.geometry, esdl.Point):
                                            pc_asset_coord = (bld_pc_asset.geometry.lat, bld_pc_asset.geometry.lon)
                                        elif isinstance(bld_pc_asset.geometry, esdl.Polygon):
                                            pc_asset_coord = ESDLGeometry.calculate_polygon_center(bld_pc_asset.geometry)

                                    # If connecting to a building outside of the current, replace current asset
                                    # coordinates with building coordinates too
                                    if not bld_editor:
                                        coord = bld_coord
                            else:
                                # asset is in the same building, use asset's own coordinates
                                pc_asset_coord = pc_asset['coord']
                        else:
                            # other asset is not in a building
                            if bld_editor:
                                # ... connect to the left border
                                pc_asset_coord = (coord[0], 0)
                            else:
                                # ... just use asset's location
                                pc_asset_coord = pc_asset['coord']

                        pc_carr_id = None
                        if pc.carrier:
                            pc_carr_id = pc.carrier.id
                        # Add connections if we're editing a building or if the connection is between two different buildings
                        # ( The case of an asset in an area that is connected with an asset in a building is handled
                        #   in process_area (now all connections are added twice, from both sides) )
                        if bld_editor or in_different_buildings:
                            conn_list.append({'from-port-id': p.id, 'from-port-carrier': p_carr_id,
                                              'from-asset-id': basset.id, 'from-asset-coord': coord,
                                              'to-port-id': pc.id, 'to-port-carrier': pc_carr_id,
                                              'to-asset-id': pc_asset['asset'].id, 'to-asset-coord': pc_asset_coord})

    if bld_editor:
        for potential in building.potential:
            geom = potential.geometry
            if geom:
                if isinstance(geom, esdl.Point):
                    lat = geom.lat
                    lon = geom.lon

                    asset_list.append(
                        ['point', 'potential', potential.name, potential.id, type(potential).__name__, [lat, lon]])


def process_area(esh, es_id, asset_list, building_list, area_bld_list, conn_list, area, level):
    area_bld_list.append(['Area', area.id, area.name, level])

    # process subareas
    for ar in area.area:
        process_area(esh, es_id, asset_list, building_list, area_bld_list, conn_list, ar, level+1)

    # process assets in area
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            process_building(esh, es_id, asset_list, building_list, area_bld_list, conn_list, asset, False, level+1)
        if isinstance(asset, esdl.EnergyAsset):
            add_asset_to_asset_list(asset_list, asset)

            for p in asset.port:
                p_asset = get_asset_and_coord_from_port_id(esh, es_id, p.id)
                p_asset_coord = p_asset['coord']        # get proper coordinate if asset is line
                conn_to_ids = [cp.id for cp in p.connectedTo]
                p_carr_id = None
                if p.carrier:
                    p_carr_id = p.carrier.id
                if conn_to_ids:
                    for pc in p.connectedTo:
                        pc_asset = get_asset_and_coord_from_port_id(esh, es_id, pc.id)
                        pc_asset_coord = None
                        if pc_asset['asset'].containingBuilding:
                            bld_pc_asset = pc_asset['asset'].containingBuilding
                            if bld_pc_asset.geometry:
                                if isinstance(bld_pc_asset.geometry, esdl.Point):
                                    pc_asset_coord = (bld_pc_asset.geometry.lat, bld_pc_asset.geometry.lon)
                                elif isinstance(bld_pc_asset.geometry, esdl.Polygon):
                                    pc_asset_coord = ESDLGeometry.calculate_polygon_center(bld_pc_asset.geometry)
                        else:
                            pc_asset_coord = pc_asset['coord']

                        pc_carr_id = None
                        if pc.carrier:
                            pc_carr_id = pc.carrier.id
                        conn_list.append({'from-port-id': p.id, 'from-port-carrier': p_carr_id,
                                          'from-asset-id': p_asset['asset'].id, 'from-asset-coord': p_asset_coord,
                                          'to-port-id': pc.id, 'to-port-carrier': pc_carr_id,
                                          'to-asset-id': pc_asset['asset'].id, 'to-asset-coord': pc_asset_coord})

    for potential in area.potential:
        geom = potential.geometry
        if geom:
            if isinstance(geom, esdl.Point):
                lat = geom.lat
                lon = geom.lon

                asset_list.append(
                    ['point', 'potential', potential.name, potential.id, type(potential).__name__, [lat, lon]])
            if isinstance(geom, esdl.Polygon):
                coords = []

                for point in geom.exterior.point:
                    coords.append([point.lat, point.lon])
                asset_list.append(['polygon', 'potential', potential.name, potential.id, type(potential).__name__, coords])


# ---------------------------------------------------------------------------------------------------------------------
#  Recalcultate area and building list
# ---------------------------------------------------------------------------------------------------------------------
def recalculate_area_bld_list(area):
    area_bld_list = []
    recalculate_area_bld_list_area(area, area_bld_list, 1)
    return area_bld_list

def recalculate_area_bld_list_area(area, area_bld_list, level):
    area_bld_list.append(['Area', area.id, area.name, level])

    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            area_bld_list.append(['Building', asset.id, asset.name, level])

    for subarea in area.area:
        recalculate_area_bld_list_area(subarea, area_bld_list, level+1)


def find_area_location_based(esh, active_es_id, geometry):
    shape_dictionary = get_session('shape_dictionary')

    obj_geometry_shape = Shape.create(geometry)
    areas_that_contain_obj = list()

    for key in shape_dictionary.keys():
        area_shp = shape_dictionary[key]
        if area_shp.shape.contains(obj_geometry_shape.shape):
            areas_that_contain_obj.append(key)

    if len(areas_that_contain_obj) == 0:
        es = esh.get_energy_system(es_id=active_es_id)
        return es.instance[0].area.id   # If no area is found, return the id of the top level area
    elif len(areas_that_contain_obj) == 1:
        return areas_that_contain_obj[0]
    else:
        # Find area that is 'lowest' in the area hierarchy
        lowest_level = 0
        lowest_area_id = None
        for ar_id in areas_that_contain_obj:
            area = esh.get_by_id(active_es_id, ar_id)
            area_level = 1
            while isinstance(area.eContainer(), esdl.Area):
                area_level += 1
                area = area.eContainer()
            if area_level > lowest_level:
                lowest_level = area_level
                lowest_area_id = ar_id

        return lowest_area_id


# ---------------------------------------------------------------------------------------------------------------------
#  Get building information
# ---------------------------------------------------------------------------------------------------------------------
def get_building_information(building):
    asset_list = []
    building_list = []
    bld_list = []
    conn_list = []

    active_es_id = get_session('active_es_id')
    esh = get_handler()

    process_building(esh, active_es_id, asset_list, building_list, bld_list, conn_list, building, True, 0)
    return {
        "id": building.id,
        "asset_list": asset_list,
        "building_list": building_list,
        "area_bld_list": bld_list,
        "conn_list": conn_list
    }


# ---------------------------------------------------------------------------------------------------------------------
#  Get information about building connections (required for deleting the connections to/from a building)
# ---------------------------------------------------------------------------------------------------------------------
def get_building_connections(building):
    active_es_id = get_session('active_es_id')
    esh = get_handler()

    conn_list = []

    for basset in building.asset:
        if isinstance(basset, esdl.EnergyAsset):
            for p in basset.port:
                conn_to = p.connectedTo
                if conn_to:
                    for pc in conn_to:
                        pc_asset = get_asset_and_coord_from_port_id(esh, active_es_id, pc.id)

                        # If the asset the current asset connects to, is in a building...
                        if pc_asset['asset'].containingBuilding:
                            bld_pc_asset = pc_asset['asset'].containingBuilding
                            bld_basset = basset.containingBuilding
                            # If the asset is in a different building ...
                            if not bld_pc_asset == bld_basset:
                                conn_list.append({"from_id": p.id, "to_id": pc.id})
                        else:
                            # other asset is not in a building
                            conn_list.append({"from_id": p.id, "to_id": pc.id})

    return conn_list


# ---------------------------------------------------------------------------------------------------------------------
#  Initialization after new or load energy system
#  If this function is run through process_energy_system.submit(filename, es_title) it is executed
#  in a separate thread.
# ---------------------------------------------------------------------------------------------------------------------
def process_energy_system(esh, filename=None, es_title=None, app_context=None, force_update_es_id=None, zoom=True):
    # emit('clear_ui')
    print("Processing energysystems in esh")
    print("active_es_id at start: {}".format(get_session('active_es_id')))

    # 4 June 2020 - Edwin: uncommented following line, we need to check if this is now handled properly
    # set_session('active_es_id', main_es.id)     # TODO: check if required here?
    es_list = esh.get_energy_systems()
    es_info_list = get_session("es_info_list")

    if force_update_es_id == "all":
        emit('clear_esdl_layer_list')

    for es in es_list:
        asset_list = []
        building_list = []
        area_bld_list = []
        conn_list = []

        if not isinstance(es, esdl.EnergySystem):
            print("- Detected ESDL without an EnergySystem, is of type {}. Ignoring.".format(es.eClass.name))
            continue

        if es.id is None:
            es.id = str(uuid.uuid4())

        if es.id not in es_info_list or es.id == force_update_es_id or force_update_es_id == "all":
            print("- Processing energysystem with id {}".format(es.id))
            name = es.name
            if not name:
                title = 'Untitled Energysystem'
            else:
                title = name

            emit('create_new_esdl_layer', {'es_id': es.id, 'title': title}) # removes old layer if exists
            emit('set_active_layer_id', es.id)

            area = es.instance[0].area
            find_boundaries_in_ESDL(area)       # also adds coordinates to assets if possible
            carrier_list = ESDLEnergySystem.get_carrier_list(es)
            emit('carrier_list', {'es_id': es.id, 'carrier_list': carrier_list})
            sector_list = ESDLEnergySystem.get_sector_list(es)
            if sector_list:
                emit('sector_list', {'es_id': es.id, 'sector_list': sector_list})

            # KPIs that are connected to top-level area are visualized in a KPI dialog
            print('- Processing KPIs')
            area_kpis = ESDLEnergySystem.process_area_KPIs(area)
            area_name = area.name
            if not area_name:
                area_name = title
            if area_kpis['kpi_list']:   # Only emit KPI info when there are KPIs available
                emit('kpis', {'es_id': es.id, 'scope': area_name, 'kpi_info': area_kpis})
                emit('kpis_present', True)

            # measures can contain assets that still need to be added to the energysystem
            assets_to_be_added = AssetsToBeAdded.get_assets_from_measures(es)
            if assets_to_be_added:
                emit('ATBA_assets_to_be_added', {'ed_id': es.id, 'assets_to_be_added': assets_to_be_added})

            # Probably the following call is not required anymore, everything is handled by find_boundaries_in_ESDL
            add_missing_coordinates(area)
            print('- Processing area')
            process_area(esh, es.id, asset_list, building_list, area_bld_list, conn_list, area, 0)
            notes_list = get_notes_list(es)

            emit('add_building_objects', {'es_id': es.id, 'building_list': building_list, 'zoom': zoom})
            emit('add_esdl_objects', {'es_id': es.id, 'asset_pot_list': asset_list, 'zoom': zoom})
            emit('area_bld_list', {'es_id': es.id,  'area_bld_list': area_bld_list})
            emit('add_connections', {'es_id': es.id, 'add_to_building': False, 'conn_list': conn_list})
            emit('add_notes', {'es_id': es.id,  'notes_list': notes_list})

            set_session_for_esid(es.id, 'conn_list', conn_list)
            set_session_for_esid(es.id, 'asset_list', asset_list)
            set_session_for_esid(es.id, 'area_bld_list', area_bld_list)

            # TODO: update asset_list???
            es_info_list[es.id] = {
                "processed": True
            }

            # If one energysystem is added (by calling an external service or via the API) the active_es_id (backend) and
            # active_layer_id (frontend) are not synchronized. As a temporary fix the following lines are added.
            # Be aware: process_energy_system is called in a seperate thread, active_es_id is also changed in the functions
            # calling process_energy_system!
            if get_session('active_es_id') != es.id:
                set_session('active_es_id', es.id)
        else:
            print("- Energysystem with id {} already processed".format(es.id))

    set_handler(esh)
    # emit('set_active_layer_id', main_es.id)

    print("active_es_id at end: {}".format(get_session('active_es_id')))

    #session.modified = True
    print('session variables set', session)
    # print('es_id: ', get_session('es_id'))



