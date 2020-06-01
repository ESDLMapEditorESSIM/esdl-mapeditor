from flask import Flask
from flask_socketio import SocketIO, emit

import time
import requests
import json
import uuid
import re

from esdl import esdl
from esdl.processing import ESDLGeometry
from extensions.session_manager import get_handler, get_session

import settings


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


# ---------------------------------------------------------------------------------------------------------------------
#  GEIS Boundary service access
# ---------------------------------------------------------------------------------------------------------------------
boundary_service_mapping = {
    'ZIPCODE': 'zipcodes',
    'NEIGHBOURHOOD': 'neighbourhoods',
    'DISTRICT': 'districts',
    'MUNICIPALITY': 'municipalities',
    'REGION': 'regions',
    'PROVINCE': 'provinces',
    'COUNTRY': 'countries'
}

#create a cache for the boundary service
boundary_cache = dict()
current_boundaries_year = "2018"


def is_valid_boundary_id(id):
    return re.match('PV[0-9]{2,2}|RES[0-9]{2,2}|GM[0-9]{4,4}|WK[0-9]{6,6}|BU[0-9]{8,8}|[0-9]{2,2}', id.upper())


def get_boundary_from_service(scope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """
    if is_valid_boundary_id(id):
        time.sleep(0.01) # yield a little concurrency when running this in a thread
        if id in boundary_cache:
            # print('Retrieve boundary from cache', id)
            # res_boundary = copy.deepcopy(boundary_cache[id])   # this doesn't solve messing up cache
            # return res_boundary
            return boundary_cache[id]

        try:
            # url = 'http://' + GEIS_CLOUD_IP + ':' + BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[str.upper(scope)] + '/' + id
            # url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[scope.name] + '/' + id
            url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] + \
                  settings.boundaries_config["path_boundaries"] + '/YEAR/' + current_boundaries_year + '/' + boundary_service_mapping[scope.name] + '/' + id
            # print('Retrieve from boundary service', id)
            r = requests.get(url)
            if len(r.text) > 0:
                reply = json.loads(r.text)
                # geom = reply['geom']

            # {'type': 'MultiPolygon', 'coordinates': [[[[253641.50000000006, 594417.8126220703], [253617, .... ,
            # 594477.125], [253641.50000000006, 594417.8126220703]]]]}, 'code': 'BU00030000', 'name': 'Appingedam-Centrum',
            # 'tCode': 'GM0003', 'tName': 'Appingedam'}
                boundary_cache[id] = reply
                return reply
            else:
                print("WARNING: Empty response for GEIS boundary service for {} with id {}".format(scope.name, id))
                return None

        except Exception as e:
            print('ERROR in accessing GEIS boundary service for {} with id {}: {}'.format(scope.name, id, e))
            return None
    else:
        return None


def get_subboundaries_from_service(scope, subscope, id):
    """
    :param scope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param subscope: any of the following: zipcode, neighbourhood, district, municipality, energyregion, province, country
    :param id: the identifier of the 'scope'
    :return: the geomertry of the indicated 'scope'
    """

    if is_valid_boundary_id(id):
        try:
            # url = 'http://' + settings.GEIS_CLOUD_HOSTNAME + ':' + settings.BOUNDARY_SERVICE_PORT + '/boundaries/' + boundary_service_mapping[subscope.name]\
            #       + '/' + boundary_service_mapping[scope.name] + '/' + id
            url = 'http://' + settings.boundaries_config["host"] + ':' + settings.boundaries_config["port"] \
                  + settings.boundaries_config["path_boundaries"] + '/YEAR/' + current_boundaries_year + '/' \
                  + boundary_service_mapping[subscope.name] + '/' \
                  + boundary_service_mapping[scope.name] + '/' + id
            r = requests.get(url)
            reply = json.loads(r.text)
            # print(reply)

            # ARRAY OF:
            # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
            # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

            return reply
        except Exception as e:
            print('ERROR in accessing GEIS boundary service for {} with id {}, subscope {}: {}'.format(scope.name, id, subscope.name, str(e)))
            return {}
    else:
        return {}


def preload_subboundaries_in_cache(top_area_scope, sub_area_scope, top_area_id):
    sub_boundaries = get_subboundaries_from_service(top_area_scope, sub_area_scope, top_area_id)

    for sub_boundary in sub_boundaries:
        code = sub_boundary['code']
        geom = sub_boundary['geom']
        if code and geom:
            boundary_cache[code] = sub_boundary


def preload_area_subboundaries_in_cache(top_area):
    top_area_scope = top_area.scope
    # fix bug in that the top area does not have an id
    if top_area.id is None:
        top_area.id = str(uuid.uuid4())
    top_area_id = top_area.id

    sub_areas = top_area.area
    if sub_areas:
        first_sub_area = sub_areas[0]
        sub_area_scope = first_sub_area.scope

        if top_area_scope and sub_area_scope and is_valid_boundary_id(top_area_id):
            preload_subboundaries_in_cache(top_area_scope, sub_area_scope, top_area_id)


# ---------------------------------------------------------------------------------------------------------------------
#  Get boundary information
# ---------------------------------------------------------------------------------------------------------------------
class BoundaryService:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        print('Registering BoundaryService extension')

        @self.socketio.on('get_boundary_info', namespace='/esdl')
        def get_boundary_info(info):
            print('get_boundary_info:')
            print(info)
            identifier = info["identifier"]
            toparea_name = info["toparea_name"]
            scope = info["scope"]
            subscope_enabled = info["subscope_enabled"]
            subscope = info["subscope"]
            select_subareas = info["select_subareas"]
            selected_subareas = info["selected_subareas"]
            initialize_ES = info["initialize_ES"]
            add_boundary_to_ESDL = info["add_boundary_to_ESDL"]

            if not is_valid_boundary_id(identifier):
                send_alert("Not a valid identifier. Try identifiers like PV27(Noord-Holland) or GM0060 (Ameland)")
                return

            active_es_id = get_session('active_es_id')
            esh = get_handler()
            es_edit = esh.get_energy_system(es_id=active_es_id)
            instance = es_edit.instance
            area = instance[0].area

            area_list = []
            boundary = None
            if subscope_enabled:
                preload_subboundaries_in_cache(esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                               esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                               str.upper(identifier))
            else:
                boundary = get_boundary_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
                if boundary:
                    geom = boundary['geom']
                    # geometry = ESDLGeometry.create_geometry_from_geom()

                    for i in range(0, len(geom['coordinates'])):
                        if len(geom['coordinates']) > 1:
                            area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                        else:
                            area_id_number = ""
                        area_list.append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": geom['coordinates'][i]
                            },
                            "properties": {
                                "id": area.id + area_id_number,
                                "name": area.name,
                                "KPIs": []
                            }
                        })

            if initialize_ES:
                # change ID, name and scope of ES

                if select_subareas:
                    area.id = "part of " + identifier
                else:
                    area.id = identifier

                # Area ID has changed, re-add to dictionairy
                esh.add_object_to_dict(active_es_id, area)

                area.scope = esdl.AreaScopeEnum.from_string(str.upper(scope))
                area.name = toparea_name
                if add_boundary_to_ESDL:
                    # returns boundary: { type: '', boundary: [[[[ ... ]]]] } (multipolygon in RD)
                    if not boundary:    # check if already requested
                        boundary = get_boundary_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)), str.upper(identifier))
                    if boundary:
                        geometry = ESDLGeometry.create_geometry_from_geom(boundary['geom'])
                        area.geometry = geometry

                    # boundary = get_boundary_from_service(area_scope, area_id)
                    # if boundary:
                    #    emit('area_boundary', {'info-type': 'MP-RD', 'crs': 'RD', 'boundary': boundary})

            if subscope_enabled:
                boundaries = get_subboundaries_from_service(esdl.AreaScopeEnum.from_string(str.upper(scope)),
                                                        esdl.AreaScopeEnum.from_string(str.upper(subscope)),
                                                        str.upper(identifier))
                # result (boundaries) is an ARRAY of:
                # {'code': 'BU00140500', 'geom': '{"type":"MultiPolygon","bbox":[...],"coordinates":[[[[6.583651,53.209594],
                # [6.58477,...,53.208816],[6.583651,53.209594]]]]}'}

                if not boundaries:
                    send_alert('Error processing boundary information or no boundary information returned')

                for boundary in boundaries:
                    geom = None
                    try:
                        # geom = json.loads(boundary["geom"])
                        geom = boundary["geom"]
                    except Exception as e:
                        print('Error parsing JSON from GEIS boundary service: '+ str(e))

                    if geom:
                        # print('boundary["geom"]: ')
                        # print(boundary["geom"])
                        # print(boundary)

                        skip_subarea = False
                        if select_subareas and selected_subareas and boundary["code"] not in selected_subareas:
                            skip_subarea = True

                        if not skip_subarea:
                            sub_area_id = boundary["code"]
                            sub_area_name = boundary["name"]

                            if initialize_ES:
                                sub_area = esdl.Area()
                                sub_area.id = sub_area_id
                                sub_area.name = sub_area_name
                                sub_area.scope = esdl.AreaScopeEnum.from_string(str.upper(subscope))

                                if add_boundary_to_ESDL:
                                    geometry = ESDLGeometry.create_geometry_from_geom(geom)
                                    sub_area.geometry = geometry

                                area.area.append(sub_area)
                                esh.add_object_to_dict(active_es_id, sub_area)

                            # print({'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': json.loads(geom)})
                            # boundary = create_boundary_from_contour(area_contour)
                            # emit('area_boundary', {'crs': 'WGS84', 'boundary': boundary})

                            # emit('area_boundary', {'info-type': 'MP-WGS84', 'crs': 'WGS84', 'boundary': geom, 'color': AREA_LINECOLOR, 'fillcolor': AREA_FILLCOLOR})

                            for i in range(0, len(geom['coordinates'])):
                                if len(geom['coordinates']) > 1:
                                    area_id_number = " ({} of {})".format(i + 1, len(geom['coordinates']))
                                else:
                                    area_id_number = ""
                                area_list.append({
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": geom['coordinates'][i]
                                    },
                                    "properties": {
                                        "id": sub_area_id + area_id_number,
                                        "name": sub_area_name,
                                        "KPIs": []
                                    }
                                })

            emit('geojson', {"layer": "area_layer", "geojson": area_list})
            print('Ready processing boundary information')

