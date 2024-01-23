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
from esdl.esdl_handler import StringURI
from esdl.processing import ESDLAsset, ESDLGeometry
from extensions.session_manager import get_handler, get_session, set_session
from extensions.settings_storage import SettingsStorage
from src.esdl_helper import energy_asset_to_ui

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
            user = get_session('user-email')
            return self.get_user_settings(user)

        @self.socketio.on('store_esdl_services_list', namespace='/esdl')
        def store_esdl_services_list(settings):
            user = get_session('user-email')
            # TODO: check settings format before storing
            self.set_user_settings(user, settings)

            # Emit the new list to the browser such that the UI is updated
            emit('esdl_services', settings)

        @self.socketio.on('restore_esdl_services_settings', namespace='/esdl')
        def restore_esdl_services_settings():
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
            esh = get_handler()
            active_es_id = get_session('active_es_id')

            obj = esh.get_by_id(active_es_id, object_id)
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

    def get_user_services_list(self, user: str, roles: List[str] = []) -> List[Dict[str, Any]]:
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
            return ar

    def call_esdl_service(self, service_params):
        """Actually call an ESDL service."""

        esh = get_handler()
        active_es_id = get_session("active_es_id")

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
            if config_service["type"] in ("workflow", "vueworkflow"):
                for step in config_service["workflow"]:
                    if (
                        step["type"] in ("service", "custom")
                    ):
                        if "service" in step and step["service"]["id"] == service_params["service_id"]:
                            service = step["service"]
                            break

        if service is None:
            return False, None

        url = service["url"]
        headers = service["headers"]
        if service.get("with_jwt_token", False):
            jwt_token = get_session("jwt-token")
            headers["Authorization"] = f"Bearer {jwt_token}"

        body = {}

        if "send_email_in_post_body_parameter" in service:
            body[service["send_email_in_post_body_parameter"]] = get_session("user-email")

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
            esdlstr = esh.to_string(active_es_id)

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
            esdlstr = esh.to_string(active_es_id)

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
                esdlstr = esh.to_string(active_es_id)
                if service["body_config"]["encoding"] == "none":
                    body = esdlstr
                if service["body_config"]["encoding"] == "url_encoded":
                    body = urllib.parse.quote(esdlstr)
                if service["body_config"]["encoding"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode('utf-8')
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body = esdlstr_base64_bytes.decode('utf-8')
            if service["body_config"]["type"] == "json":
                #body = {}
                for param in service["body_config"]['parameters']:
                    if param["type"] == "esdl":
                        del body['energysystem'] # added earlier
                        esdlstr = esh.to_string(active_es_id)
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

        query_params = service_params["query_parameters"]
        config_service_params = service.get("query_parameters", {})
        if query_params:
            first_qp = True
            for key in query_params:
                if query_params[
                    key
                ]:  # to filter empty lists for multi-selection parameters
                    for cfg_service_param in config_service_params:
                        if cfg_service_param["parameter_name"] == key:
                            if "location" in cfg_service_param:
                                if cfg_service_param["location"] == "url":
                                    url = url.replace(
                                        "<" + cfg_service_param["parameter_name"] + ">",
                                        str(query_params[key]),
                                    )
                                elif cfg_service_param["location"] == "body" and isinstance(body, dict):
                                    if "encoding" in cfg_service_param and cfg_service_param["encoding"] == "base64":
                                        param_value = (base64.b64encode(query_params[key].encode('utf-8'))).decode('utf-8')
                                    else:
                                        param_value = query_params[key]
                                    body[
                                        cfg_service_param["name"]
                                    ] = param_value
                            else:
                                if first_qp:
                                    url = url + "?"
                                else:
                                    url = url + "&"
                                url = (
                                    url + key + "=" + self.array2list(query_params[key])
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
                return False, None

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

                    es, parse_info = esh.add_from_string(service["name"], esdl_response)
                    # TODO deal with parse_info?
                    return True, None
                elif service["result"][0]["action"] == "print":
                    return True, json.loads(r.text)
                elif service["result"][0]["action"] == "add_assets":
                    es_edit = esh.get_energy_system(es_id=active_es_id)
                    instance = es_edit.instance
                    area = instance[0].area
                    asset_str_list = json.loads(r.text)

                    # Fix for services that return an ESDL string that represents one asset
                    if isinstance(asset_str_list, str):
                        asset_str_list = {
                            "add_assets": [asset_str_list]
                        }

                    try:
                        for asset_str in asset_str_list["add_assets"]:
                            asset = ESDLAsset.load_asset_from_string(asset_str)
                            esh.add_object_to_dict(active_es_id, asset, recursive=True)
                            ESDLAsset.add_object_to_area(es_edit, asset, area.id)
                            asset_ui, conn_list = energy_asset_to_ui(esh, active_es_id, asset)
                            emit(
                                "add_esdl_objects",
                                {
                                    "es_id": active_es_id,
                                    "asset_pot_list": [asset_ui],
                                    "zoom": True,
                                },
                            )
                            emit(
                                "add_connections",
                                {"es_id": active_es_id, "conn_list": conn_list},
                            )
                    except Exception as e:
                        logger.warning("Exception occurred: " + str(e))
                        return False, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}
                elif service["result"][0]["action"] == "add_potentials":
                    es_edit = esh.get_energy_system(es_id=active_es_id)
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
                            esh.add_object_to_dict(active_es_id, potential, recursive=True)
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
                        return False, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}
                elif service["result"][0]["action"] == "add_profile":
                    rset = ResourceSet()

                    profile_str = r.text
                    uri = StringURI('profile.esdl', profile_str)
                    resource = rset.create_resource(uri)
                    resource.load()
                    profile = resource.contents[0]

                    if isinstance(profile, esdl.GenericProfile):
                        # hack for now, how to find the asset for which the service was called
                        b64_esdl = body["b64_esdl"]
                        ascii_esdl_str = base64.b64decode(b64_esdl.encode("utf-8")).decode("utf-8")
                        uri = StringURI('asset.esdl', ascii_esdl_str)
                        resource = rset.create_resource(uri)
                        resource.load()
                        asset = resource.contents[0]
                        asset_id = asset.id
                        asset_in_es = esh.get_by_id(es_id=active_es_id, object_id=asset_id)

                        found_first_outport = False
                        for p in asset_in_es.port:
                            if isinstance(p, esdl.OutPort):
                                found_first_outport = True
                                break

                        if not found_first_outport:
                            p = esdl.OutPort(id=str(uuid.uuid4()), name="OutPort")
                            asset_in_es.port.append(p)

                        p.profile.append(profile)
                        return True, {"send_message_to_UI_but_do_nothing": {}}
                    else:
                        logger.error("Service was expected to give back a profile")
                        return False, None
                elif service["result"][0]["action"] == "add_notes":
                    es_edit = esh.get_energy_system(es_id=active_es_id)
                    esi = es_edit.energySystemInformation
                    if not esi:
                        esi = es_edit.energySystemInformation = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
                        esh.add_object_to_dict(active_es_id, esi)
                    notes = esi.notes
                    if not notes:
                        notes = esi.notes = esdl.Notes(id=str(uuid.uuid4()))
                        esh.add_object_to_dict(active_es_id, notes)

                    notes_from_service = ESDLAsset.load_asset_from_string(esdl_string=r.text)
                    if isinstance(notes_from_service, esdl.Notes):
                        notes_list = []
                        for note in list(notes_from_service.note):
                            notes.note.append(note)
                            esh.add_object_to_dict(active_es_id, note)
                            map_location = note.mapLocation
                            if map_location:
                                coords = {'lng': map_location.lon, 'lat': map_location.lat}
                                notes_list.append({'id': note.id, 'location': coords, 'title': note.title,
                                                   'text': note.text, 'author': note.author})  # , 'date': n.date})
                        emit('add_notes', {'es_id': active_es_id, 'notes_list': notes_list})
                    else:
                        logger.error("Service with id "+service_params["service_id"]+" did not return a esdl.Notes object")
                        return False, None

                    return True, {"send_message_to_UI_but_do_nothing": {}}
                elif service["result"][0]["action"] == "asset_feedback":
                    service_results = json.loads(r.text)

                    asset_results_dict = dict()
                    for sr in service_results:
                        asset_results_dict[sr['assetID']] = sr['messages']
                    return True, {
                        "asset_feedback": asset_results_dict
                    }
                elif service["result"][0]["action"] == "show_message":
                    message = service["result"][0]["message"]
                    if 'json_field' in service["result"][0]:
                        message = r.json()[service["result"][0]['json_field']]
                        import html  # escape html entities in log file of NWN
                        message = html.escape(message)
                        message = message.replace("\n", "<br/>")
                    return True, {"message": message}
            else:
                logger.warning(
                    "Error running ESDL service - response "
                    + str(r.status_code)
                    + " with reason: "
                    + str(r.reason)
                )
                logger.warning(r)
                logger.warning(r.content)
                return False, str(r.content)
        except Exception as e:
            logger.exception("Error accessing external ESDL service: " + str(e))
            return False, None

        return False, None
