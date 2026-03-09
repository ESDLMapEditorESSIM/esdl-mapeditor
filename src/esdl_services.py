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
from typing import Any, Tuple

import requests
from flask import Flask
from flask_socketio import SocketIO, emit
from pyecore.resources import ResourceSet
from requests import Response

import src.esdl_config as esdl_config
import src.log as log
from esdl import esdl, Profiles
from esdl.processing.string_uri import StringURI
from esdl.undo import UndoRedoCommandStack
from esdl.undo_wrapper import undo_record_changes
from esdl.processing import ESDLAsset, ESDLGeometry
from esdlproject.ProjectManager import ProjectManager, load_external_string
from extensions.prompt_manager import PromptManager
from extensions.external_models.external_models_storage import (
    ExternalModelsStorage,
    ESDL_FEEDBACK,
    OUTPUT_ESDL,
    INPUT_ESDL,
    RunStatus,
)
from extensions.projects import update_visualization_options
from extensions.session_manager import get_project_manager, get_session, set_session, del_session
from extensions.settings_storage import SettingsStorage
from src.esdl2inlineprofile import copy_and_convert_esdl_profiles
from src.esdl_helper import energy_asset_to_ui
from src.process_es_area_bld import (
    calc_possible_locations_in_area,
    choose_location,
    find_area_location_based,
    get_area_id_from_mapeditor_id,
    call_process_energy_system,
)
from src.tno.shared.util import get_nested_dict_value
from utils.datetime_utils import parse_date
from src.tno.projects.duplicate_detection import DuplicatePrompt, find_duplicate_variant_collection, generate_renamed_esdl_string

logger = log.get_logger(__name__)

ESDL_SERVICES_CONFIG = "ESDL_SERVICES_CONFIG"
"""The key the ESDL Services are stored with in the settings."""


class ESDLServices:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        settings_storage: SettingsStorage,
        models_storage: ExternalModelsStorage,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.models_storage = models_storage

        self.register()
        PromptManager.register_handler("esdl_duplicate_service_import", self._handle_esdl_duplicate_service_import)

    def register(self):
        logger.info("Registering ESDLServices extension")

        @self.socketio.on("get_esdl_services_list", namespace="/esdl")
        def get_esdl_services_list():
            """
            Get the list of ESDL services for the current user.
            :return:
            """
            user = get_session("user-email")
            return self.get_user_settings(user)

        @self.socketio.on("refresh_esdl_services_list", namespace="/esdl")
        def refresh_esdl_services_list():
            """
            Refresh the list of ESDL services for the current user by sending the list to the browser.
            """
            user = get_session("user-email")
            role = get_session("user-role")
            emit("esdl_services", self.get_user_services_list(user, role))

        @self.socketio.on("store_esdl_services_list", namespace="/esdl")
        def store_esdl_services_list(settings):
            """
            Store the ESDL services list for the current user.
            :param settings: The new settings to store.
            :return:
            """
            user = get_session("user-email")
            # TODO: check settings format before storing
            self.set_user_settings(user, settings)

            # Emit the new list to the browser such that the UI is updated
            emit("esdl_services", settings)

        @self.socketio.on("restore_esdl_services_settings", namespace="/esdl")
        def restore_esdl_services_settings():
            """
            Restore ESDL services to how they were before user modifications.
            :return:
            """
            user = get_session("user-email")
            settings = self.restore_settings(user)

            # Emit the new list to the browser such that the UI is updated
            emit("esdl_services", settings)

            return settings

        @self.flask_app.route("/get_toolbar_services")
        def get_toolbar_services():
            services_list = list()

            user = get_session("user-email")
            services = self.get_user_settings(user)

            for service in services:
                if "show_on_toolbar" in service:
                    if service["show_on_toolbar"]:
                        svc = dict()
                        svc["id"] = service["id"]
                        svc["name"] = service["name"]
                        svc["icon_url"] = "/icons/service.png"
                        if service["icon"]:
                            if service["icon"]["type"] == "filename":
                                svc["icon_url"] = "/icons/" + service["icon"]["filename"]
                        services_list.append(svc)
            return {"services_list": services_list}

        @self.flask_app.route("/get_object_esdl/<object_id>")
        def get_object_esdl(object_id):
            pm = get_project_manager()
            active_es_id = get_session("active_es_id")

            obj = pm.get_by_id(active_es_id, object_id)
            if obj:
                uri = StringURI("obj.esdl")
                rset = ResourceSet()
                resource = rset.create_resource(uri)
                resource.append(obj.deepcopy())
                resource.save()
                obj_esdl_string = uri.getvalue()
                return {"esdl": obj_esdl_string}

            return None

    def get_user_settings(self, user: str) -> list[dict[str, Any]]:
        """Get the user services from the settings storage."""
        if self.settings_storage.has_user(user, ESDL_SERVICES_CONFIG):
            esdl_services_settings = self.settings_storage.get_user(user, ESDL_SERVICES_CONFIG)
        else:
            esdl_services_settings = esdl_config.esdl_config["predefined_esdl_services"]
            self.settings_storage.set_user(user, ESDL_SERVICES_CONFIG, esdl_services_settings)
        return esdl_services_settings

    def get_role_based_services(self, roles: list[str]) -> list[dict[str, Any]]:
        """Get the services available for this user role from the config."""
        role_based_esdl_services: dict[str, Any] = esdl_config.esdl_config["role_based_esdl_services"]
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

    def get_user_services_list(self, user: str, roles: list[str] = None) -> list[dict[str, Any]]:
        """
        Get the full list of services for this user with the given roles. Both user and roles come from Keycloak.
        """
        if roles is None:
            roles = []
        srvs_list = self.get_user_settings(user)
        # store the user services list in session for later use
        set_session("services_list", srvs_list)

        # Start with user services, remove those services that the user does not have the role for.
        final_services_list = copy.deepcopy(srvs_list)
        for service in list(final_services_list):
            if "required_role" in service and service["required_role"] not in roles:
                final_services_list.remove(service)

        service_ids: list[str] = [service["id"] for service in final_services_list]
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
    def call_esdl_service(self, service_params, stack: UndoRedoCommandStack) -> list[Tuple[bool, str | dict | None, dict | None]]:
        """Actually call an ESDL service."""

        pm = get_project_manager()
        active_es_id = pm.get_active_energy_system().id

        # {'service_id': '18d106cf-2af1-407d-8697-0dae23a0ac3e', 'area_scope': 'provincies', 'area_id': '12',
        #  'query_parameters': {'bebouwingsafstand': '32432', 'restrictie': 'vliegveld', 'preferentie': 'infrastructuur', 'geometrie': 'true'}}

        # Find the currently active service.
        service = None
        # services_list = get_session('services_list')
        if "service_config" in service_params:
            service = service_params["service_config"]
        else:
            user_email = get_session("user-email")
            role = get_session("user-role")
            services_list = self.get_user_services_list(user_email, role)
            for config_service in services_list:
                if config_service["id"] == service_params["service_id"]:
                    service = config_service
                    break
                # If it's a workflow, look in its steps.
                if "type" in config_service and config_service["type"] in (
                    "workflow",
                    "vueworkflow",
                ):
                    for step in config_service["workflow"]:
                        if step["type"] in ("esdl-service", "custom"):
                            if "service" in step and step["service"]["id"] == service_params["service_id"]:
                                service = step["service"]
                                break
                # If the service ID was found as a step in a workflow (embedded for loop), also exit this for loop
                if service:
                    break

        if service is None:
            return [(False, None, None)]
        stack.update_label(service["name"])
        url = None
        headers = service.get("headers", {})
        if "url" in service:
            url = service["url"]
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
                area_id = get_area_id_from_mapeditor_id(service_params["area_id"])
                url = url.replace(area_id_tag, area_id)
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
                    esdlstr_bytes = esdlstr.encode("utf-8")
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body["energysystem"] = esdlstr_base64_bytes.decode("utf-8")
                elif service["body"] == "json_text":
                    body["energysystem"] = esdlstr
                else:
                    body = esdlstr
            elif service["type"] == "simulation":
                esdlstr = pm.active_energy_system_to_string()

                if service["body"] == "url_encoded":
                    body["energysystem"] = urllib.parse.quote(esdlstr)
                elif service["body"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode("utf-8")
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body["energysystem"] = esdlstr_base64_bytes.decode("utf-8")
                else:
                    body = esdlstr

        # The parameter values that were communicated by the frontend
        state_params = service_params.get("state_params")
        # The parameter definition from the service config
        config_service_params = service.get("query_parameters", {})

        if "body_config" in service:
            if service["body_config"].get("profiles") == "inline":
                es_converted = copy_and_convert_esdl_profiles(active_es_id)
                uri = StringURI("es_converted.esdl")
                es_converted_resource = ResourceSet().create_resource(uri)
                es_converted_resource.append(es_converted)
                es_converted_resource.save(uri)
                esdlstr = uri.getvalue()
            else:
                esdlstr = pm.active_energy_system_to_string()

            if service["body_config"]["type"] == "text":
                if service["body_config"]["encoding"] == "none":
                    body = esdlstr
                elif service["body_config"]["encoding"] == "url_encoded":
                    body = urllib.parse.quote(esdlstr)
                elif service["body_config"]["encoding"] == "base64_encoded":
                    esdlstr_bytes = esdlstr.encode("utf-8")
                    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                    body = esdlstr_base64_bytes.decode("utf-8")
            elif service["body_config"]["type"] == "json":
                # body = {}
                for param in service["body_config"]["parameters"]:
                    if param["type"] == "esdl":
                        if "energysystem" in body:
                            del body["energysystem"]  # added earlier
                        if param["encoding"] == "none":
                            body[param["parameter"]] = esdlstr
                        elif param["encoding"] == "url_encoded":
                            body[param["parameter"]] = urllib.parse.quote(esdlstr)
                        elif param["encoding"] == "base64_encoded":
                            esdlstr_bytes = esdlstr.encode("utf-8")
                            esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                            body[param["parameter"]] = esdlstr_base64_bytes.decode("utf-8")
                    elif param["type"] == "esdl_store":
                        # Retrieve an ESDL that was a result of an earlier service call
                        if "energysystem" in body:
                            del body["energysystem"]  # added earlier
                        esdlstr = get_session("esdl_store")
                        # Clear the stored ESDL after retrieving it.
                        del_session("esdl_store")
                        if param["encoding"] == "none":
                            body[param["parameter"]] = esdlstr
                        elif param["encoding"] == "url_encoded":
                            body[param["parameter"]] = urllib.parse.quote(esdlstr)
                        elif param["encoding"] == "base64_encoded":
                            esdlstr_bytes = esdlstr.encode("utf-8")
                            esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                            body[param["parameter"]] = esdlstr_base64_bytes.decode("utf-8")
                    elif param["type"] == "esdl_id":
                        body[param["parameter"]] = active_es_id
                    elif param["type"] == "value":
                        body[param["parameter"]] = param["value"]
                    elif param["type"] == "json_string":
                        body_params = service_params["body_config"]
                        for bp in body_params:
                            if param["parameter"] == bp:
                                body[param["parameter"]] = body_params[bp]
                    if param["type"] == "object":
                        obj = dict()
                        # Create and object (dictionary) with key value pairs from specific parameters from the state
                        for p in param["parameters"]:
                            if state_params:
                                for key in state_params:
                                    if state_params[key]:
                                        if p["parameter"] == key:
                                            obj[p["parameter_name"]] = state_params[key]
                        body[param["parameter_name"]] = obj

        first_qp = True
        for cfg_service_param in config_service_params:
            param = None
            if "value" in cfg_service_param:  # get value direct from service json config
                param = cfg_service_param["value"]
            elif state_params:  # find state parameter value
                for key in state_params:
                    if state_params[key]:  # to filter empty lists for multi-selection parameters
                        if cfg_service_param["parameter_name"] == key:
                            param = state_params[key]  # param now contains the communicated value (by the UI)

            if param:
                # Is there any parameter formatting required...
                if "formatter" in cfg_service_param:
                    if (
                        "type" in cfg_service_param["formatter"]
                        and cfg_service_param["formatter"]["type"] == "datetime_formatter"
                    ):
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
                            param_value = (base64.b64encode(param.encode("utf-8"))).decode("utf-8")
                        else:
                            param_value = param
                        # For backwards compatibility support both names. When using name, not all result handling will properly work.
                        param_name = cfg_service_param.get("name", cfg_service_param.get("parameter_name"))
                        body[param_name] = param_value
                else:
                    # Parameter is a "real" URL parameter: ?key1=value1&key2=value2&...
                    if first_qp:
                        url = url + "?"
                    else:
                        url = url + "&"
                    url = url + cfg_service_param["parameter_name"] + "=" + self.array2list(param)
                    first_qp = False

        try:
            url_response = None
            input_data = None
            if url:
                if service["http_method"] == "get":
                    if service["type"].endswith("json") or (
                        "body_config" in service and service["body_config"]["type"] == "json"
                    ):
                        kwargs = {"json": body}
                    else:
                        kwargs = {}
                    url_response = requests.get(url, headers=headers, **kwargs)
                elif service["http_method"] == "delete":
                    url_response = requests.delete(url, headers=headers)
                elif service["http_method"] == "post":
                    if service["type"].endswith("json") or (
                        "body_config" in service and service["body_config"]["type"] == "json"
                    ):
                        kwargs = {"json": body}
                    else:
                        kwargs = {"data": body}
                    url_response = requests.post(url, headers=headers, **kwargs)
                else:
                    # Should not happen, there should always be a method.
                    return [(False, None, None)]
                input_data = url_response.text
            elif "external_model" in service:  # get from external models database
                input_esdl = self.models_storage.get_model_run(state_params["run_id"]).get(INPUT_ESDL)
                output_esdl = self.models_storage.get_model_run(state_params["run_id"]).get(OUTPUT_ESDL)
                if service["external_model"] == "input_esdl":
                    input_data = input_esdl
                elif service["external_model"] == "output_esdl":
                    input_data = output_esdl
                else:
                    if output_esdl:
                        input_data = output_esdl
                    elif input_esdl:
                        input_data = input_esdl

            if not url or url_response.status_code == 200 or url_response.status_code == 201:
                # Process the result of the service call
                results = []
                for result_config in service["result"]:
                    try:
                        result = self._process_service_result(
                            pm,
                            url_response,
                            input_data,
                            result_config,
                            service,
                            service_params,
                            state_params,
                            body,
                        )
                        if result:
                            results.append(result)
                    except Exception:
                        logger.exception("Error processing service result.")
                        results.append((False, None, None))
                return results
            else:
                if url_response is not None:
                    logger.warning(
                        "Error running ESDL service - response "
                        + str(url_response.status_code)
                        + " with reason: "
                        + str(url_response.reason)
                        + " with text: "
                        + str(url_response.text),
                    )
                else:
                    logger.warning("Error running ESDL service ", input_data)
                return [(False, str(input_data), None)]
        except Exception:
            logger.exception("Error accessing external ESDL service.")
            return [(False, None, None)]

    def _process_service_result(
        self,
        pm: ProjectManager,
        url_response: Response,
        input_data,
        result_config,
        service: dict,
        service_params: dict,
        state_params,
        body: dict[str, Any],
    ) -> None | Tuple[bool, str | dict | None, dict | None]:
        """
        Process the result of an ESDL service call. This can be adding an ESDL object to the current EnergySystem, printing
        the result, or adding assets to the main area.

        :param pm: The Project Manager
        :param url_response: The response from the service call.
        :param result_config: The service result configuration, which defines what to do with the result.
        :param service: The service configuration.
        :param service_params:
        :param body: The body of the request sent to the service.
        :return: None or a tuple with a boolean indicating success, a message, and a dictionary with additional information.
        """
        es = pm.get_active_energy_system()
        active_es_id = pm.get_active_energy_system().id

        if "model_short_name" in result_config:
            model_short_name = result_config["model_short_name"]
        else:
            model_short_name = "Model"

        if result_config["action"] == "esdl":
            if "json_field" in service["result"][0]:
                esdl_data = url_response.json()[result_config["json_field"]]
            else:
                esdl_data = input_data

            esdl_response = esdl_data
            if "encoding" in service["result"][0]:
                if service["result"][0]["encoding"] == "url_encoded":
                    esdl_response = urllib.parse.quote(esdl_data)
                elif service["result"][0]["encoding"] == "base64_encoded":
                    esdlstr_bytes = esdl_data.encode("utf-8")
                    esdlstr_base64_bytes = base64.b64decode(esdlstr_bytes)
                    esdl_response = esdlstr_base64_bytes.decode("utf-8")

            temp_es, _ = load_external_string(esdl_string=esdl_response, name=service["name"])
            duplicate_vc, match_id, match_name, matched_es = find_duplicate_variant_collection(
                pm, temp_es.id, temp_es.name
            )
            if duplicate_vc:
                user_email = get_session("user-email")
                PromptManager.get_instance().send(DuplicatePrompt(
                    user_email=user_email,
                    continuation_id="esdl_duplicate_service_import",
                    match_id=match_id,
                    match_name=match_name,
                    matched_es=matched_es,
                    context={
                        "esdl_response": esdl_response,
                        "service": service,
                        "result_config": result_config,
                        "state_params": state_params,
                    },
                ))
                return True, {"prompt_pending": True}, {"skip_processing": True}

            return self._handle_esdl_result(pm, esdl_response, result_config, service, state_params, model_short_name)
        elif service["result"][0]["action"] == "esdl_store":
            # Temporarily store the ESDL for later use in next steps
            if "encoding" in service["result"][0]:
                if service["result"][0]["encoding"] == "url_encoded":
                    esdl_response = urllib.parse.quote(url_response.text)
                elif service["result"][0]["encoding"] == "base64_encoded":
                    response_with_esdl = url_response.text
                    if "json_field" in service["result"][0]:  # use specific json field in result
                        response_with_esdl = url_response.json()[service["result"][0]["json_field"]]
                    esdlstr_bytes = response_with_esdl.encode("utf-8")
                    esdlstr_base64_bytes = base64.b64decode(esdlstr_bytes)
                    esdl_response = esdlstr_base64_bytes.decode("utf-8")
                else:
                    esdl_response = url_response.text
            else:
                esdl_response = url_response.text

            set_session("esdl_store", esdl_response)
            return True, {"continue_workflow": True}, None
        elif result_config["action"] == "print":
            return True, json.loads(input_data), None
        elif result_config["action"] == "add_assets":
            es_edit = pm.get_active_energy_system()
            instance = es_edit.instance
            area = instance[0].area
            add_assets_service_result = json.loads(input_data)
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
                        return (False, "add_assets service config not handled properly yet!", None)

            # If service returns an ESDL string that represents one asset, add it to the main area
            if isinstance(add_assets_service_result, str):
                add_assets_to_area = {area.id: [add_assets_service_result]}
            # If service returns a list of ESDL strings, add them to main area
            if isinstance(add_assets_service_result, list):
                add_assets_to_area = {area.id: add_assets_service_result}

            try:
                # with undo_record_changes(service.get("name")):
                for area_id, asset_str_list in add_assets_to_area.items():
                    area_to_be_added_to = pm.get_by_id(active_es_id, area_id)
                    if not area_to_be_added_to:
                        # If service returns an Area ID that cannot be found, add asset to main Area
                        area_to_be_added_to = area

                    area_shape = None
                    possible_locations = None
                    if "mode" in result_config and result_config["mode"] == "give_coordinates":
                        # The assets that will be added must be placed on a grid within the area boundary
                        shape_dictionary = get_session("shape_dictionary")
                        if area_to_be_added_to.id in shape_dictionary:
                            area_shape = shape_dictionary[area_to_be_added_to.id]
                            # Calculate "enough" possible locations for assets inside the area
                            possible_locations = calc_possible_locations_in_area(area_shape, len(asset_str_list))

                    for asset_str in asset_str_list:
                        asset = ESDLAsset.load_asset_from_string(asset_str)
                        # Only assign a new location if the asset didn't already have a location
                        if not asset.geometry and area_shape and possible_locations:
                            # The asset gets a random location from the list of possible locations
                            asset.geometry = choose_location(possible_locations).get_esdl()

                        # Assign a sector to the asset when configured in the service configuration
                        if "sector_id" in service["result"][0]:
                            sector_id = service["result"][0]["sector_id"]
                            if sector_id:
                                sector = pm.get_by_id(active_es_id, sector_id)
                                if sector:
                                    asset.sector = sector

                        if "mode" in service["result"][0] and service["result"][0][
                            "mode"] == "location_based_addition_to_area":
                            area_to_be_added_to_id = find_area_location_based(pm, active_es_id, asset.geometry)
                        else:
                            area_to_be_added_to_id = area_to_be_added_to.id
                        zoom = False
                        if "zoom" in service["result"][0]:
                            zoom = bool(service["result"][0]["zoom"])
                        pm.add_object_to_dict(active_es_id, asset, recursive=True)
                        ESDLAsset.add_object_to_area(es_edit, asset, area_to_be_added_to_id)
                        asset_ui, conn_list = energy_asset_to_ui(pm, active_es_id, asset)
                        if asset_ui:
                            emit(
                                "add_esdl_objects",
                                {
                                    "es_id": active_es_id,
                                    "asset_pot_list": [asset_ui],
                                    "zoom": zoom,
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

            return True, {"send_message_to_UI_but_do_nothing": {}}, {"es": es}
        elif result_config["action"] == "add_potentials":
            es_edit = pm.get_active_energy_system()
            instance = es_edit.instance
            area = instance[0].area
            potential_str_list = json.loads(input_data)

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

                    coords = ESDLGeometry.parse_esdl_subpolygon(potential.geometry.exterior, False)  # [lon, lat]
                    coords = ESDLGeometry.exchange_coordinates(coords)
                    potentials_to_be_added.append(
                        [
                            "polygon",
                            "potential",
                            potential.name,
                            potential.id,
                            type(potential).__name__,
                            coords,
                        ]
                    )

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

            return True, {"send_message_to_UI_but_do_nothing": {}}, {"es": es}
        elif result_config["action"] == "add_profile":
            rset = ResourceSet()

            profile_str = input_data
            uri = StringURI("profile.esdl", profile_str)
            resource = rset.create_resource(uri)
            resource.load()
            profile = resource.contents[0]

            if isinstance(profile, esdl.GenericProfile):
                # hack for now, how to find the asset for which the service was called
                b64_esdl = body["esdl"]
                ascii_esdl_str = base64.b64decode(b64_esdl.encode("utf-8")).decode("utf-8")
                uri = StringURI("asset.esdl", ascii_esdl_str)
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
                return True, {"send_message_to_UI_but_do_nothing": {}}, {"es": es}
            else:
                logger.error("Service was expected to give back a profile")
                return False, None, None
        elif result_config["action"] == "add_notes":
            es_edit = pm.get_active_energy_system()
            esi = es_edit.energySystemInformation
            if not esi:
                esi = es_edit.energySystemInformation = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
                pm.add_object_to_dict(active_es_id, esi)
            notes = esi.notes
            if not notes:
                notes = esi.notes = esdl.Notes(id=str(uuid.uuid4()))
                pm.add_object_to_dict(active_es_id, notes)

            notes_from_service = ESDLAsset.load_asset_from_string(esdl_string=input_data)
            if isinstance(notes_from_service, esdl.Notes):
                notes_list = []
                for note in list(notes_from_service.note):
                    notes.note.append(note)
                    pm.add_object_to_dict(active_es_id, note)
                    map_location = note.mapLocation
                    if map_location:
                        coords = {
                            "lng": map_location.lon,
                            "lat": map_location.lat,
                        }
                        notes_list.append(
                            {
                                "id": note.id,
                                "location": coords,
                                "title": note.title,
                                "text": note.text,
                                "author": note.author,
                            }
                        )  # , 'date': n.date})
                emit(
                    "add_notes",
                    {"es_id": active_es_id, "notes_list": notes_list},
                )
            else:
                logger.error("Service with id " + service_params["service_id"] + " did not return a esdl.Notes object")
                return False, None, None

            return True, {"send_message_to_UI_but_do_nothing": {}}, {"es": es}
        elif result_config["action"] == "asset_feedback":
            service_results = json.loads(input_data)

            asset_results_dict = dict()
            for sr in service_results:
                asset_results_dict[sr["assetID"]] = sr["messages"]
            return True, {"asset_feedback": asset_results_dict}, {"es": es}
        elif result_config["action"] == "show_message":
            message = result_config["message"]
            if "json_field" in result_config:
                message = url_response.json()[result_config["json_field"]]
                import html  # escape html entities in log file of NWN

                message = html.escape(message)
                message = message.replace("\n", "<br/>")
            return True, {"message": message}, {"es": es}
        elif result_config["action"] == "download_file":
            # Needs json_field to be set to the field in the response that contains the file.
            response_with_file = url_response.json()[result_config["json_field"]]
            filename = result_config["filename"]
            content_type = result_config["content_type"]
            return True, {"file": response_with_file, "filename": filename, "content_type": content_type}, None
        elif service["result"][0]["action"] == "save_model_run":
            esdl_str = pm.energy_system_to_string(active_es_id)
            response_json = url_response.json()

            if service["result"][0]["external_model_id_response_param"] in response_json:
                model_job_id = response_json[service["result"][0]["external_model_id_response_param"]]
                status = RunStatus.SUBMITTED
            else:  # if no external model id returned: model run failed
                model_job_id = "0"
                status = RunStatus.ERROR

            logs = None
            if (
                "external_model_logs_response_param" in service["result"][0]
                and service["result"][0]["external_model_logs_response_param"] in response_json
            ):
                logs = response_json[service["result"][0]["external_model_logs_response_param"]]

            parameters = state_params.copy()
            run_name = parameters[service["result"][0]["run_name_state_param"]]
            del parameters[service["result"][0]["run_name_state_param"]]

            user = get_session("user-email")

            model_run_doc = self.models_storage.add_model_run(
                model_name=service["result"][0]["external_model_name"],
                model_job_id=model_job_id,
                run_name=run_name,
                input_esdl=esdl_str,
                run_input_data=parameters,
                user_name=user,
                logs=logs,
                status=status,
            )
            return (
                True,
                {
                    "message": f"Run submitted: '{state_params['run_name']}'",
                    "model_run_doc": model_run_doc,
                    "model_job_id": model_job_id,
                    "hide_button": True,
                },
                None,
            )
        return None

    def _handle_esdl_result(
        self,
        pm: ProjectManager,
        esdl_response: str,
        result_config,
        service: dict,
        state_params,
        model_short_name: str,
    ) -> Tuple[bool, str | dict | None, dict | None]:
        """Apply an ESDL result and build backend actions."""
        variant, parse_info = pm.add_energy_system(StringURI(service["name"], esdl_response))
        pm.set_active_variant(variant)
        update_visualization_options(pm.get_active_energy_system())
        # TODO deal with parse_info?
        es = pm.get_energy_system(variant)

        message = None
        backend_action = {"force_update_es_id": es.id}

        if "show_asset_feedback" in result_config and result_config["show_asset_feedback"]:
            model_run_data = self.models_storage.get_model_run(state_params["run_id"])
            if ESDL_FEEDBACK in model_run_data:
                feedback = model_run_data[ESDL_FEEDBACK]
            else:
                feedback = {}

            variant, parse_info = pm.add_energy_system(StringURI(service["name"], esdl_response))
            # TODO deal with parse_info?
            message = {"asset_feedback": feedback}
            backend_action["run_after_esdl_loaded"] = True

        if "animation" in result_config:
            influxdb_host_override = None
            if "influxdb_host_override" in result_config["animation"]:
                influxdb_host_override = result_config["animation"]["influxdb_host_override"]
            influxdb_port_override = None
            if "influxdb_port_override" in result_config["animation"]:
                influxdb_port_override = result_config["animation"]["influxdb_port_override"]

            try:
                animation_fields = Profiles.get_animation_fields(
                    es.id,
                    influxdb_host_override=influxdb_host_override,
                    influxdb_port_override=influxdb_port_override,
                )
                if animation_fields:
                    filter_tag_name = None
                    filter_tag_value = None
                    if "filter_on_tag" in service["result"][0]["animation"]:
                        model_run_data = self.models_storage.get_model_run(state_params["run_id"])
                        filter_tag_name = service["result"][0]["animation"]["filter_on_tag"]["tag_name"]
                        filter_tag_value = get_nested_dict_value(
                            model_run_data,
                            service["result"][0]["animation"]["filter_on_tag"]["value_database_key"],
                        )
                    emit(
                        "animation_esdl_data",
                        {
                            "es_id": es.id,
                            "fields": animation_fields,
                            "message": f"For {model_short_name} result: '{state_params['run_name']}'",
                            "filter_tag_name": filter_tag_name,
                            "filter_tag_value": filter_tag_value,
                            "influxdb_host_override": influxdb_host_override,
                            "influxdb_port_override": influxdb_port_override,
                        },
                    )
            except Exception as e:
                logger.error(e)
                return False, str(e), None

            # TODO: Check if this is correct?!
            return True, {}, {"es": pm.get_energy_system(variant)}
        if "external_link" in result_config:
            model_run_data = self.models_storage.get_model_run(state_params["run_id"])
            external_link_url = get_nested_dict_value(
                model_run_data, result_config["external_link"]["value_database_key"]
            )
            emit(
                "results_external_link",
                {
                    "description": result_config["external_link"]["description"],
                    "url": external_link_url,
                    "es_id": es.id,
                    "message": f"For {model_short_name} result: '{state_params['run_name']}'",
                },
            )
        return True, message, backend_action

    def _handle_esdl_duplicate_service_import(self, choice_key: str, context: dict):
        """Apply user choice for duplicate service-import prompts."""
        if choice_key == "cancel":
            return

        esdl_response = context.get("esdl_response")
        service = context.get("service")
        result_config = context.get("result_config")
        state_params = context.get("state_params")
        if not esdl_response or not service or not result_config or not state_params:
            logger.warning("Missing context for ESDL service duplicate prompt")
            return

        pm = get_project_manager()
        temp_es, _ = load_external_string(esdl_string=esdl_response, name=service["name"])

        if choice_key == "overwrite":
            duplicate_vc, _, _, _ = find_duplicate_variant_collection(pm, temp_es.id, temp_es.name)
            if duplicate_vc:
                pm.delete_variant(duplicate_vc)
        elif choice_key == "rename":
            new_name = f"{temp_es.name} ({temp_es.id[:8]})"
            esdl_response = generate_renamed_esdl_string(esdl_response, service["name"], new_name=new_name)

        model_short_name = result_config["model_short_name"] if "model_short_name" in result_config else "Model"
        esdl_service_ok, esdl_service_result, backend_action = self._handle_esdl_result(
            pm, esdl_response, result_config, service, state_params, model_short_name
        )

        esdl_service_result_post_esdl_load = None
        if esdl_service_ok:
            if esdl_service_result is not None:
                if backend_action and backend_action.get("run_after_esdl_loaded"):
                    esdl_service_result_post_esdl_load = esdl_service_result
                else:
                    emit('esdl_service_result', esdl_service_result)
            else:
                emit('esdl_service_result', esdl_service_result)
        else:
            logger.warning("ESDL service duplicate import failed", result=esdl_service_result)

        force_update_es_id = None
        if backend_action and "force_update_es_id" in backend_action:
            force_update_es_id = backend_action["force_update_es_id"]
        call_process_energy_system.submit(
            force_update_es_id=force_update_es_id,
            result_post_esdl_load=esdl_service_result_post_esdl_load,
        )
