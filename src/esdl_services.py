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

import copy
import json
import urllib.parse
import base64
import uuid

import requests

import src.esdl_config as esdl_config
import src.log as log
from esdl import esdl
from esdl.processing import ESDLAsset
from src.esdl_helper import energy_asset_to_ui
from extensions.session_manager import get_handler, get_session, set_session
from extensions.settings_storage import SettingsStorage
from flask import Flask
from flask_socketio import SocketIO, emit
from src.esdl_helper import energy_asset_to_ui

logger = log.get_logger(__name__)

ESDL_SERVICES_CONFIG = "ESDL_SERVICES_CONFIG"


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

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, ESDL_SERVICES_CONFIG):
            esdl_services_settings = self.settings_storage.get_user(user, ESDL_SERVICES_CONFIG)
        else:
            esdl_services_settings = esdl_config.esdl_config["predefined_esdl_services"]
            self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, esdl_services_settings)
        return esdl_services_settings

    def restore_settings(self, user):
        esdl_services_settings = esdl_config.esdl_config["predefined_esdl_services"]
        self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, esdl_services_settings)
        return esdl_services_settings

    def set_user_settings(self, user, settings):
        self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, settings)

    def get_user_services_list(self, user, roles=[]):
        srvs_list = self.get_user_settings(user)
        # store the user services list in session for later use
        set_session('services_list', srvs_list)

        my_list = copy.deepcopy(srvs_list)
        for s in list(my_list):
            if "required_role" in s and s["required_role"] not in roles:
                my_list.remove(s)

        return my_list

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
        services_list = get_session('services_list')
        for config_service in services_list:
            if config_service["id"] == service_params["service_id"]:
                service = config_service
                break
            # If it's a workflow, look in its steps.
            if config_service["type"] in ("workflow", "vueworkflow"):
                for step in config_service["workflow"]:
                    if (
                        step["type"] in ("service", "custom")
                        and step["service"]["id"] == service_params["service_id"]
                    ):
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
        elif service["type"] == "send_esdl":
            esdlstr = esh.to_string(active_es_id)

            if service["body"] == "url_encoded":
                body["energysystem"] = urllib.parse.quote(esdlstr)
                # print(body)
            elif service["body"] == "base64_encoded":
                esdlstr_bytes = esdlstr.encode('ascii')
                esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                body["energysystem"] = esdlstr_base64_bytes.decode('ascii')
            else:
                body = esdlstr
        elif service["type"] == "simulation":
            esdlstr = esh.to_string(active_es_id)

            if service["body"] == "url_encoded":
                body["energysystem"] = urllib.parse.quote(esdlstr)
            elif service["body"] == "base64_encoded":
                esdlstr_bytes = esdlstr.encode('ascii')
                esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                body["energysystem"] = esdlstr_base64_bytes.decode('ascii')
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
                    esdlstr_bytes = esdlstr.encode('ascii')
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body = esdlstr_base64_bytes.decode('ascii')
            if service["body_config"]["type"] == "json":
                body = {}
                for param in service["body_config"]['parameters']:
                    if param["type"] == "esdl":
                        esdlstr = esh.to_string(active_es_id)
                        if param["encoding"] == "none":
                            body[param["parameter"]] = esdlstr
                        if param["encoding"] == "url_encoded":
                            body[param["parameter"]] = urllib.parse.quote(esdlstr)
                        if param["encoding"] == "base64_encoded":
                            esdlstr_bytes = esdlstr.encode('ascii')
                            esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                            body[param["parameter"]] = esdlstr_base64_bytes.decode('ascii')
                    if param["type"] == "json_string":
                        body_params = service_params["body_config"]
                        for bp in body_params:
                            if param["parameter"] == bp:
                                body[param["parameter"]] = body_params[bp]

        query_params = service_params["query_parameters"]
        config_service_params = service["query_parameters"]
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
                                    body[
                                        cfg_service_param["parameter_name"]
                                    ] = query_params[key]
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
            elif service["http_method"] == "post":
                if service["type"] == "json":
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
                    es, parse_info = esh.add_from_string(service["name"], r.text)
                    # TODO deal with parse_info?
                    return True, None
                elif service["result"][0]["action"] == "print":
                    return True, json.loads(r.text)
                elif service["result"][0]["action"] == "add_assets":
                    es_edit = esh.get_energy_system(es_id=active_es_id)
                    instance = es_edit.instance
                    area = instance[0].area
                    asset_str_list = json.loads(r.text)

                    try:
                        for asset_str in asset_str_list["add_assets"]:
                            asset = ESDLAsset.load_asset_from_string(asset_str)
                            esh.add_object_to_dict(active_es_id, asset)
                            ESDLAsset.add_asset_to_area(es_edit, asset, area.id)
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
                elif service["result"][0]["action"] == "show_message":
                    return True, {"message": service["result"][0]["message"]}
            else:
                logger.warning(
                    "Error running ESDL service - response "
                    + str(r.status_code)
                    + " with reason: "
                    + str(r.reason)
                )
                logger.warning(r)
                logger.warning(r.content)
                return False, None
        except Exception as e:
            logger.warning("Error accessing external ESDL service: " + str(e))
            return False, None

        return False, None
