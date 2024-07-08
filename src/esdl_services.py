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

import base64
import copy
import json
import urllib.parse
import uuid
from typing import Any, Dict, List

import requests
from flask import Flask
from flask_socketio import SocketIO, emit
from pyecore.resources import ResourceSet

import src.esdl_config as esdl_config
import src.log as log
from esdl import esdl
from esdl.processing.string_uri import StringURI
from esdl.undo_wrapper import undo_record_changes
from extensions.session_manager import get_project_manager, get_session, set_session
from esdl.processing import ESDLAsset, ESDLGeometry
from extensions.settings_storage import SettingsStorage
from src.esdl_helper import energy_asset_to_ui
from src.process_es_area_bld import calc_possible_locations_in_area, choose_location
from src.tno.undoredo.types import serialize_command_stack
from utils.datetime_utils import parse_date

logger = log.get_logger(__name__)

ESDL_SERVICES_CONFIG = "ESDL_SERVICES_CONFIG"
"""The key the ESDL Services are stored with in the settings."""


class ESDLServices:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info('Registering ESDLServices extension')

        @self.socketio.on('get_esdl_services_list', namespace='/esdl')
        def get_esdl_services_list():
            """
            Get the list of ESDL services for the current user.
            :return:
            """
            user = get_session('user-email')
            return self.get_user_settings(user)

        @self.socketio.on('refresh_esdl_services_list', namespace='/esdl')
        def refresh_esdl_services_list():
            """
            Refresh the list of ESDL services for the current user by sending the list to the browser.
            """
            user = get_session('user-email')
            role = get_session('user-role')
            emit('esdl_services', self.get_user_services_list(user, role))

        @self.socketio.on('store_esdl_services_list', namespace='/esdl')
        def store_esdl_services_list(settings):
            """
            Store the ESDL services list for the current user.
            :param settings: The new settings to store.
            :return:
            """
            user = get_session('user-email')
            # TODO: check settings format before storing
            self.set_user_settings(user, settings)

            # Emit the new list to the browser such that the UI is updated
            emit('esdl_services', settings)

        @self.socketio.on('restore_esdl_services_settings', namespace='/esdl')
        def restore_esdl_services_settings():
            """
            Restore ESDL services to how they were before user modifications.
            :return:
            """
            user = get_session('user-email')
            settings = self.restore_settings(user)

            # Emit the new list to the browser such that the UI is updated
            emit('esdl_services', settings)

            return settings

        @self.flask_app.route('/get_toolbar_services')
        def get_toolbar_services():
            services_list = list()

            user = get_session('user-email')
            services = self.get_user_settings(user)

            for service in services:
                if 'show_on_toolbar' in service:
                    if service['show_on_toolbar']:
                        svc = dict()
                        svc['id'] = service['id']
                        svc['name'] = service['name']
                        svc['icon_url'] = '/icons/service.png'
                        if service['icon']:
                            if service['icon']['type'] == 'filename':
                                svc['icon_url'] = '/icons/' + service['icon']['filename']
                        services_list.append(svc);
            return {'services_list': services_list}

        @self.flask_app.route('/get_object_esdl/<object_id>')
        def get_object_esdl(object_id):
            pm = get_project_manager()
            active_es_id = get_session('active_es_id')

            obj = pm.get_by_id(active_es_id, object_id)
            if obj:
                uri = StringURI('obj.esdl')
                rset = ResourceSet()
                resource = rset.create_resource(uri)
                resource.append(obj.deepcopy())
                resource.save()
                obj_esdl_string =  uri.getvalue()
                return {"esdl": obj_esdl_string}

            return None

    def get_user_settings(self, user: str) -> List[Dict[str, Any]]:
        """Get the user services from the settings storage. """
        if self.settings_storage.has_user(user, ESDL_SERVICES_CONFIG):
            esdl_services_settings = self.settings_storage.get_user(user, ESDL_SERVICES_CONFIG)
        else:
            esdl_services_settings = esdl_config.esdl_config["predefined_esdl_services"]
            self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, esdl_services_settings)
        return esdl_services_settings

    def get_role_based_services(self, roles: List[str]) -> List[Dict[str, Any]]:
        """Get the services available for this user role from the config. """
        role_based_esdl_services: Dict[str, Any] = esdl_config.esdl_config["role_based_esdl_services"]
        selected_services = list()
        for role in roles:
            role_services = role_based_esdl_services.get(role, [])
            selected_services.extend(role_services)
        return selected_services

    def restore_settings(self, user: str):
        esdl_services_settings = esdl_config.esdl_config["predefined_esdl_services"]
        self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, esdl_services_settings)
        return esdl_services_settings

    def set_user_settings(self, user: str, settings):
        self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, settings)

    def get_user_services_list(self, user: str, roles: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get the full list of services for this user with the given roles. Both user and roles come from Keycloak.
        """
        srvs_list = self.get_user_settings(user)
        # store the user services list in session for later use
        set_session('services_list', srvs_list)

        # Start with user services, remove those services that the user does not have the role for.
        final_services_list = copy.deepcopy(srvs_list)
        for service in list(final_services_list):
            if "required_role" in service and service["required_role"] not in roles:
                final_services_list.remove(service)

        service_ids: List[str] = [service["id"] for service in final_services_list]
        # Get role based services and add them, unless a service with matching ID exists.
        role_based_services = self.get_role_based_services(roles)
        for role_based_service in role_based_services:
            if role_based_service["id"] not in service_ids:
                final_services_list.append(role_based_service)

        return final_services_list

    def array2list(self, ar):
        if isinstance(ar, list):
            return ",".join(ar)
        else:
            return str(ar)

    @undo_record_changes("External service call")
    def call_esdl_service(self, service_params):
        """Actually call an ESDL service."""

        pm = get_project_manager()
        active_es_id = get_session("active_es_id")
        es = pm.get_active_energy_system()

        # {'service_id': '18d106cf-2af1-407d-8697-0dae23a0ac3e', 'area_scope': 'provincies', 'area_id': '12',
        #  'query_parameters': {'bebouwingsafstand': '32432', 'restrictie': 'vliegveld', 'preferentie': 'infrastructuur', 'geometrie': 'true'}}

        # Find the currently active service.
        service = None
        # services_list = get_session('services_list')
        user_email = get_session('user-email')
        role = get_session('user-role')
        services_list = self.get_user_services_list(user_email, role)
        for config_service in services_list:
            if config_service["id"] == service_params["service_id"]:
                service = config_service
                break
            # If it's a workflow, look in its steps.
            if "type" in config_service and config_service["type"] in ("workflow", "vueworkflow"):
                for step in config_service["workflow"]:
                    if (
                        step["type"] in ("service", "custom")
                    ):
                        if "service" in step and step["service"]["id"] == service_params["service_id"]:
                            service = step["service"]
                            break

        if service is None:
            return False, None, None

        url = service["url"]
        headers = service["headers"]
        if service.get("with_jwt_token", False):
            jwt_token = get_session("jwt-token")
            headers["Authorization"] = f"Bearer {jwt_token}"

        body = {}

        if "send_email_in_post_body_parameter" in service:
            body[service["send_email_in_post_body_parameter"]] = get_session("user-email")

        if "type" in service:
            if service["type"] == "geo_query":
                area_scope_tag = service["geographical_scope"]["url_area_scope"]
                area_id_tag = service["geographical_scope"]["url_area_id"]

                area_scope = service_params["area_scope"]
                url = url.replace(area_scope_tag, area_scope)
                ares_id = service_params["area_id"]
                url = url.replace(area_id_tag, ares_id)
                if "url_area_subscope" in service["geographical_scope"]:
                    area_subscope_tag = service["geographical_scope"]["url_area_subscope"]
                    area_subscope = service_params["area_subscope"]
                    url = url.replace(area_subscope_tag, area_subscope)
            elif service["type"].startswith("send_esdl"):
                esdlstr = pm.active_energy_system_to_string()

                if service["body"] == "url_encoded":
                    body["energysystem"] = urllib.parse.quote(esdlstr)
                    # print(body)
                elif service["body"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode('utf-8')
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body["energysystem"] = esdlstr_base64_bytes.decode('utf-8')
                else:
                    body = esdlstr
            elif service["type"] == "simulation":
                esdlstr = pm.active_energy_system_to_string()

                if service["body"] == "url_encoded":
                    body["energysystem"] = urllib.parse.quote(esdlstr)
                elif service["body"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode('utf-8')
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body["energysystem"] = esdlstr_base64_bytes.decode('utf-8')
                else:
                    body = esdlstr

        if "body_config" in service:
            if service["body_config"]["type"] == "text":
                esdlstr = pm.active_energy_system_to_string()
                if service["body_config"]["encoding"] == "none":
                    body = esdlstr
                if service["body_config"]["encoding"] == "url_encoded":
                    body = urllib.parse.quote(esdlstr)
                if service["body_config"]["encoding"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode('utf-8')
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body = esdlstr_base64_bytes.decode('utf-8')
            if service["body_config"]["type"] == "json":
                body = {}
                for param in service["body_config"]['parameters']:
                    if param["type"] == "esdl":
                        if "energysystem" in body:
                            del body["energysystem"]  # added earlier
                        esdlstr = pm.active_energy_system_to_string()
                        if param["encoding"] == "none":
                            body[param["parameter"]] = esdlstr
                        if param["encoding"] == "url_encoded":
                            body[param["parameter"]] = urllib.parse.quote(esdlstr)
                        if param["encoding"] == "base64_encoded":
                            esdlstr_bytes = esdlstr.encode('utf-8')
                            esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                            body[param["parameter"]] = esdlstr_base64_bytes.decode('utf-8')
                    if param["type"] == "value":
                        body[param["parameter"]] = param["value"]
                    if param["type"] == "json_string":
                        body_params = service_params["body_config"]
                        for bp in body_params:
                            if param["parameter"] == bp:
                                body[param["parameter"]] = body_params[bp]

        # The parameter values that were communicated by the frontend
        query_params = service_params["query_parameters"]
        # The parameter definition from the service config
        config_service_params = service.get("query_parameters", {})
        if query_params:
            first_qp = True
            for cfg_service_param in config_service_params:
                param = None

                if "type" in cfg_service_param and cfg_service_param["type"] == "constant":
                    param = cfg_service_param["value"]
                    key = cfg_service_param["parameter_name"]
                elif "parameter" in cfg_service_param:
                    for key in query_params:
                        if query_params[key] and cfg_service_param["parameter"] == key:
                            param = query_params[key]
                            break
                elif "parameter_name" in cfg_service_param:
                    # If "parameter" is not specified in service config, use "parameter_name" if available
                    for key in query_params:
                        if query_params[key] and cfg_service_param["parameter_name"] == key:
                            param = query_params[key]
                            break

                if param:
                    # Is there any parameter formatting required...
                    if "formatter" in cfg_service_param:
                        if "type" in cfg_service_param["formatter"] and \
                                cfg_service_param["formatter"]["type"] == "datetime_formatter":
                            parsed_datetime = parse_date(param)
                            param = parsed_datetime.strftime(cfg_service_param["formatter"]["format"])

                    # Find out what to do with this parameter
                    if "location" in cfg_service_param:
                        if cfg_service_param["location"] == "url":
                            # Parameter is part of the URL path: e.g. /query/area/<area_id>/sub_area/...
                            url = url.replace(
                                "<" + cfg_service_param["parameter_name"] + ">",
                                str(param),
                            )
                        elif cfg_service_param["location"] == "body" and isinstance(body, dict):
                            # Parameter is part of the body json
                            if "encoding" in cfg_service_param and cfg_service_param["encoding"] == "base64":
                                param_value = (base64.b64encode(param.encode('utf-8'))).decode('utf-8')
                            else:
                                param_value = param
                            body[
                                cfg_service_param["parameter_name"]
                            ] = param_value
                    else:
                        # Parameter is a "real" URL parameter: ?key1=value1&key2=value2&...
                        if first_qp:
                            url = url + "?"
                        else:
                            url = url + "&"
                        url = (
                            url + key + "=" + self.array2list(param)
                        )
                        first_qp = False

        try:
            if service["http_method"] == "get":
                r = requests.get(url, headers=headers)
            elif service["http_method"] == "delete":
                r = requests.delete(url, headers=headers)
            elif service["http_method"] == "post":
                if service["type"].endswith("json") or ("body_config" in service and service["body_config"]["type"] == "json"):
                    kwargs = {"json": body}
                else:
                    kwargs = {"data": body}
                r = requests.post(url, headers=headers, **kwargs)
            else:
                # Should not happen, there should always be a method.
                return False, None, None

            if r.status_code == 200 or r.status_code == 201:
                # print(r.text)

                if service["result"][0]["action"] == "esdl":
                    if "encoding" in service["result"][0]:
                        if service["result"][0]["encoding"] == "url_encoded":
                            esdl_response = urllib.parse.quote(r.text)
                        elif service["result"][0]["encoding"] == "base64_encoded":
                            response_with_esdl = r.text
                            if "json_field" in service['result'][0]:  # use specific json field in result
                                response_with_esdl = r.json()[service['result'][0]['json_field']]
                            esdlstr_bytes = response_with_esdl.encode('utf-8')
                            esdlstr_base64_bytes = base64.b64decode(esdlstr_bytes)
                            esdl_response = esdlstr_base64_bytes.decode('utf-8')
                        else:
                            esdl_response = r.text
                    else:
                        esdl_response = r.text

                    variant, parse_info = pm.add_energy_system(StringURI(service["name"], esdl_response))
                    # TODO deal with parse_info?

                    # TODO: Check if this is correct?!
                    return True, {}, pm.get_energy_system(variant)
                elif service["result"][0]["action"] == "print":
                    return True, json.loads(r.text), es
                elif service["result"][0]["action"] == "add_assets":
                    es_edit = pm.get_active_energy_system()
                    instance = es_edit.instance
                    area = instance[0].area
                    add_assets_service_result = json.loads(r.text)
                    add_assets_to_area = dict()

                    if isinstance(add_assets_service_result, dict):
                        if not "add_assets" in add_assets_service_result:
                            # Service returns a dictionary with area id as key, and ESDL object string list as value
                            add_assets_to_area = add_assets_service_result
                        else:
                            add_assets = add_assets_service_result["add_assets"]
                            if isinstance(add_assets, list):
                                add_assets_to_area[area.id] = add_assets
                            elif isinstance(add_assets, str):
                                add_assets_to_area[area.id] = [add_assets]
                            else:
                                logger.error("add_assets service config not handled properly yet!")
                                return False, "add_assets service config not handled properly yet!", None

                    # If service returns an ESDL string that represents one asset, add it to the main area
                    if isinstance(add_assets_service_result, str):
                        add_assets_to_area = {
                            area.id: [add_assets_service_result]
                        }
                    # If service returns a list of ESDL strings, add them to main area
                    if isinstance(add_assets_service_result, list):
                        add_assets_to_area = {
                            area.id: add_assets_service_result
                        }
                    try:
                        # with undo_record_changes(service.get("name")):
                        for area_id, asset_str_list in add_assets_to_area.items():
                            area_to_be_added_to = pm.get_by_id(active_es_id, area_id)
                            if not area_to_be_added_to:
                                # If service returns an Area ID that cannot be found, add asset to main Area
                                area_to_be_added_to = area

                            area_shape = None
                            if "mode" in service["result"][0] and service["result"][0]["mode"] == "give_coordinates":
                                # The assets that will be added must be placed on a grid within the area boundary
                                shape_dictionary = get_session('shape_dictionary')
                                if area_to_be_added_to.id in shape_dictionary:
                                    area_shape = shape_dictionary[area_to_be_added_to.id]
                                    # Calculate "enough" possible locations for assets inside the area
                                    possible_locations = calc_possible_locations_in_area(area_shape, len(asset_str_list))

                            for asset_str in asset_str_list:
                                asset = ESDLAsset.load_asset_from_string(asset_str)
                                # Only assign a new location if the asset didn't already have a location
                                if not asset.geometry and area_shape:
                                    # The asset gets a random location from the list of possible locations
                                    asset.geometry = choose_location(possible_locations).get_esdl()

                                # Assign a sector to the asset when configured in the service configuration
                                if "sector_id" in service["result"][0]:
                                    sector_id = service["result"][0]["sector_id"]
                                    if sector_id:
                                        sector = pm.get_by_id(active_es_id, sector_id)
                                        if sector:
                                            asset.sector = sector

                                pm.add_object_to_dict(active_es_id, asset, recursive=True)
                                ESDLAsset.add_object_to_area(es_edit, asset, area_to_be_added_to.id)
                                asset_ui, conn_list = energy_asset_to_ui(pm, active_es_id, asset)
                                if asset_ui:
                                    emit(
                                        "add_esdl_objects",
                                        {
                                            "es_id": active_es_id,
                                            "asset_pot_list": [asset_ui],
                                            "zoom": True,
                                        },
                                    )
                                if conn_list:
                                    emit(
                                        "add_connections",
                                        {"es_id": active_es_id, "conn_list": conn_list},
                                    )
                        if "feedback" in service["result"][0] and service["result"][0]["feedback"] is not None:
                            emit("toast_message", service["result"][0]["feedback"])
                    except Exception as e:
                        logger.warning("Exception occurred: " + str(e))
                        return False, None, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}, es
                elif service["result"][0]["action"] == "add_potentials":
                    es_edit = pm.get_active_energy_system()
                    instance = es_edit.instance
                    area = instance[0].area
                    potential_str_list = json.loads(r.text)

                    # Fix for services that return an ESDL string that represents one asset
                    if isinstance(potential_str_list, str):
                        potential_str_list = [potential_str_list]

                    try:
                        potentials_to_be_added = list()
                        for potential_str in potential_str_list:
                            potential = ESDLAsset.load_asset_from_string(potential_str)
                            pm.add_object_to_dict(active_es_id, potential, recursive=True)
                            ESDLAsset.add_object_to_area(es_edit, potential, area.id)
                            # asset_ui, conn_list = energy_asset_to_ui(esh, active_es_id, potential)

                            coords = ESDLGeometry.parse_esdl_subpolygon(potential.geometry.exterior,
                                                                        False)  # [lon, lat]
                            coords = ESDLGeometry.exchange_coordinates(coords)
                            potentials_to_be_added.append(['polygon', 'potential', potential.name, potential.id,
                                                           type(potential).__name__, coords])

                        emit(
                            "add_esdl_objects",
                            {
                                "es_id": active_es_id,
                                "asset_pot_list": potentials_to_be_added,
                                "zoom": False,
                            },
                        )
                    except Exception as e:
                        logger.warning("Exception occurred: " + str(e))
                        return False, None, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}, es
                elif service["result"][0]["action"] == "add_profile":
                    rset = ResourceSet()

                    profile_str = r.text
                    uri = StringURI('profile.esdl', profile_str)
                    resource = rset.create_resource(uri)
                    resource.load()
                    profile = resource.contents[0]

                    if isinstance(profile, esdl.GenericProfile):
                        # hack for now, how to find the asset for which the service was called
                        b64_esdl = body["esdl"]
                        ascii_esdl_str = base64.b64decode(b64_esdl.encode("utf-8")).decode("utf-8")
                        uri = StringURI('asset.esdl', ascii_esdl_str)
                        resource = rset.create_resource(uri)
                        resource.load()
                        asset = resource.contents[0]
                        asset_id = asset.id
                        asset_in_es = pm.get_by_id(es_id=active_es_id, object_id=asset_id)

                        first_outport = None
                        for p in asset_in_es.port:
                            if isinstance(p, esdl.OutPort):
                                first_outport = p
                                break

                        if not first_outport:
                            first_outport = esdl.OutPort(id=str(uuid.uuid4()), name="OutPort")
                            asset_in_es.port.append(first_outport)

                        first_outport.profile.append(profile)
                        pm.add_object_to_dict(active_es_id, profile, recursive=True)
                        return True, {"send_message_to_UI_but_do_nothing": {}}, es
                    else:
                        logger.error("Service was expected to give back a profile")
                        return False, None, None
                elif service["result"][0]["action"] == "add_notes":
                    es_edit = pm.get_active_energy_system()
                    esi = es_edit.energySystemInformation
                    if not esi:
                        esi = es_edit.energySystemInformation = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
                        pm.add_object_to_dict(active_es_id, esi)
                    notes = esi.notes
                    if not notes:
                        notes = esi.notes = esdl.Notes(id=str(uuid.uuid4()))
                        pm.add_object_to_dict(active_es_id, notes)

                    notes_from_service = ESDLAsset.load_asset_from_string(esdl_string=r.text)
                    if isinstance(notes_from_service, esdl.Notes):
                        notes_list = []
                        for note in list(notes_from_service.note):
                            notes.note.append(note)
                            pm.add_object_to_dict(active_es_id, note)
                            map_location = note.mapLocation
                            if map_location:
                                coords = {'lng': map_location.lon, 'lat': map_location.lat}
                                notes_list.append({'id': note.id, 'location': coords, 'title': note.title,
                                                   'text': note.text, 'author': note.author})  # , 'date': n.date})
                        emit('add_notes', {'es_id': active_es_id, 'notes_list': notes_list})
                    else:
                        logger.error("Service with id "+service_params["service_id"]+" did not return a esdl.Notes object")
                        return False, None, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}, es
                elif service["result"][0]["action"] == "asset_feedback":
                    service_results = json.loads(r.text)

                    asset_results_dict = dict()
                    for sr in service_results:
                        asset_results_dict[sr['assetID']] = sr['messages']
                    return True, {
                        "asset_feedback": asset_results_dict
                    }, es
                elif service["result"][0]["action"] == "show_message":
                    message = service["result"][0]["message"]
                    if 'json_field' in service["result"][0]:
                        message = r.json()[service["result"][0]['json_field']]
                        import html  # escape html entities in log file of NWN
                        message = html.escape(message)
                        message = message.replace("\n", "<br/>")
                    return True, {"message": message}, es
            else:
                logger.warning(
                    "Error running ESDL service - response "
                    + str(r.status_code)
                    + " with reason: "
                    + str(r.reason)
                )
                logger.warning(r)
                logger.warning(r.content)
                return False, str(r.content), None
        except Exception as e:
            logger.exception("Error accessing external ESDL service: " + str(e))
            return False, None, None

        return False, None, None
