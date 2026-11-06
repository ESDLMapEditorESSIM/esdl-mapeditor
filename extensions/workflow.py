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
import json

import base64
from werkzeug.http import parse_options_header
from flask_executor import Executor
from flask_socketio import emit
import os
import requests
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from typing import List
from urllib.parse import urlparse

import esdl
from extensions.esdl_drive.api import (
    DRIVE_URL,
    EsdlDriveException,
    esdl_drive_get_node,
    get_drive_post_headers,
    resource_endpoint,
    upload_esdl_to_drive,
)
from extensions.esdl_drive.esdl_drive import ESDLDriveHttpURI
from extensions.session_manager import get_project_manager, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger
from src.process_es_area_bld import process_energy_system
from src.tno.shared.util import response_error_message

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30
"""Default timeout for workflow proxy requests."""

WORKFLOW_SETTINGS_NAME = "workflows"


def unreachable_service_response(url: str, exception: Exception):
    """Build a 502 response explaining that the remote service could not be reached."""
    parsed = urlparse(url)
    target = parsed.netloc or url
    if isinstance(exception, requests.exceptions.Timeout):
        message = (
            f"The service at '{target}' did not respond within {DEFAULT_TIMEOUT} seconds. "
            "Please try again later or check whether the service is running."
        )
    else:
        message = (
            f"The service at '{target}' is not reachable. "
            "Please check whether the service is running and reachable from the MapEditor."
        )
    logger.warning("Could not reach %s: %s", target, exception)
    return jsonify({"message": message}), 502


def proxy_response(r: requests.Response):
    """Relay a remote response, preserving any error message the service returned."""
    if not r.ok:
        return jsonify({"detail": response_error_message(r)}), r.status_code
    try:
        return jsonify(r.json()), r.status_code
    except ValueError:
        return jsonify([]), r.status_code


class Workflow:
    """
    The workflow extension contains proxy endpoints, to allow the frontend to access defined services.
    """

    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        settings_storage: SettingsStorage,
        executor: Executor,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info("Registering workflow extension")

        @self.flask_app.route("/workflow/get_options")
        def get_options():
            """
            Proxy to do an OPTIONS call on a remote URL.
            """
            url = request.args["url"]
            other_args = dict(request.args)
            del other_args["url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )
            try:
                r = requests.options(
                    url, params=other_args, headers=headers, timeout=DEFAULT_TIMEOUT
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                return unreachable_service_response(url, e)
            return proxy_response(r)

        @self.flask_app.route("/workflow/get_data")
        def get_data():
            """
            Proxy to GET data from a remote URL.
            """
            url = request.args["url"]
            other_args = dict(request.args)
            del other_args["url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            email = get_session("user-email")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )
            for key, value in dict(other_args).items():
                if value == "session.email":  # assumes email in query or url param
                    other_args[key] = email
            url = url.format(**other_args)
            try:
                r = requests.get(
                    url, headers=headers, params=other_args, timeout=DEFAULT_TIMEOUT
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                return unreachable_service_response(url, e)
            return proxy_response(r)

        @self.flask_app.route("/workflow/download_file", methods=["POST"])
        def download_file():
            """
            Download a file by POSTing to a remote service, and providing some
            parameters, if they're provided.

            Returns a base64 encoded version of the file, which the frontend
            should be able to parse and offer as download to the user.
            """
            url = request.json["remote_url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )

            request_params = request.json.get("request_params")
            url = url.format(**request_params)
            try:
                r = requests.post(
                    url, json=request_params, headers=headers, timeout=DEFAULT_TIMEOUT
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                return unreachable_service_response(url, e)
            if r.status_code == 200:
                # Get the filename from the header.
                parsed_header = parse_options_header(r.headers["Content-Disposition"])[-1]
                filename = os.path.basename(parsed_header["filename"])
                # Encode the file to base64. In this way, we can send it to the frontend.
                result = base64.b64encode(r.content).decode()
                return jsonify({"base64file": result, "filename": filename}), 200
            else:
                return proxy_response(r)

        @self.flask_app.route("/workflow/post_data", methods=["POST"])
        def post_data():
            """Post provided data to external services.

            Request JSON is expected to have the following format:
            {
                'remote_url': <The remote URL to send the data to>,
                'request_params: {},
            }

            Returns:
                [type]: [description]
            """
            url = request.json["remote_url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )

            request_params = request.json.get("request_params")
            body = request.json.get("body")
            try:
                r = requests.post(
                    url, params=request_params, json=body, headers=headers, timeout=DEFAULT_TIMEOUT
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                return unreachable_service_response(url, e)

            return proxy_response(r)

        @self.socketio.on("/workflow/list", namespace="/esdl")
        def list_workflows():
            user_email = get_session("user-email")
            if self.settings_storage.has_user(user_email, WORKFLOW_SETTINGS_NAME):
                all_workflows_dict = self.settings_storage.get_user(
                    user_email, WORKFLOW_SETTINGS_NAME
                )
            else:
                all_workflows_dict = {}

            workflow_list = []
            for uuid, workflow_dict in all_workflows_dict.items():
                workflow_list.append(
                    dict(
                        uuid=uuid,
                        name=workflow_dict["name"],
                    )
                )
            return workflow_list

        @self.socketio.on("/workflow/persist", namespace="/esdl")
        def persist(message):
            """
            Persist this workflow.
            """
            workflow_id = message["workflow_id"]
            workflow_json = json.loads(message["workflow_json"])
            user_email = get_session("user-email")

            pm = get_project_manager()
            energy_systems: List[esdl.EnergySystem] = pm.get_energy_systems()
            drive_paths = []
            for energy_system in energy_systems:
                esdl_contents = pm.energy_system_to_string(energy_system.id).encode("utf-8")
                drive_path = f"/Users/{user_email}/workflows/{workflow_id}/{energy_system.name}.esdl"
                response = upload_esdl_to_drive(
                    esdl_contents,
                    drive_path,
                    dict(commitMessage="", overwrite=True),
                )
                if response.ok:
                    drive_paths.append(drive_path)

            # Only store those Drive paths that we just uploaded.
            workflow_json["drive_paths"] = drive_paths
            if self.settings_storage.has_user(user_email, WORKFLOW_SETTINGS_NAME):
                all_workflows_dict = self.settings_storage.get_user(
                    user_email, WORKFLOW_SETTINGS_NAME
                )
            else:
                all_workflows_dict = {}
            all_workflows_dict[workflow_id] = workflow_json
            self.settings_storage.set_user(
                user_email, WORKFLOW_SETTINGS_NAME, all_workflows_dict
            )

            return dict(drive_paths=drive_paths)

        @self.socketio.on("/workflow/load", namespace="/esdl")
        def load(message):
            """
            Load this workflow.
            """
            workflow_id = message["workflow_id"]
            user_email = get_session("user-email")

            if self.settings_storage.has_user(user_email, WORKFLOW_SETTINGS_NAME):
                all_workflows_dict = self.settings_storage.get_user(
                    user_email, WORKFLOW_SETTINGS_NAME
                )
                workflow = all_workflows_dict.get(workflow_id)
            else:
                workflow = None

            # TODO: Only retrieve drive paths from workflow.
            try:
                drive_items = esdl_drive_get_node(
                    f"/Users/{user_email}/workflows/{workflow_id}"
                )
            except EsdlDriveException as e:
                logger.exception("Error while loading workflow")
                return dict(message="Failed loading ESDLs from drive")
            pm = get_project_manager()
            for drive_item in drive_items:
                uri = ESDLDriveHttpURI(
                    DRIVE_URL + resource_endpoint + drive_item["id"],
                    headers_function=get_drive_post_headers,
                    getparams={},
                )
                #es, parse_info = esh.import_file(uri)
                variant, parse_info = pm.add_energy_system(uri)
                es = pm.get_energy_system(variant)
                if len(parse_info) > 0:
                    info = ""
                    for line in parse_info:
                        info += line + "\n"
                    message = "Warnings while opening {}:\n\n{}".format(
                        uri.last_segment, info
                    )
                    emit("alert", message, namespace="/esdl")
            self.executor.submit(process_energy_system, force_update_es_id="all", zoom=False)
            return workflow

        @self.socketio.on("/workflow/delete", namespace="/esdl")
        def delete(message):
            """
            Delete this workflow.
            """
            workflow_id = message["workflow_id"]
            user_email = get_session("user-email")

            if self.settings_storage.has_user(user_email, WORKFLOW_SETTINGS_NAME):
                all_workflows_dict = self.settings_storage.get_user(
                    user_email, WORKFLOW_SETTINGS_NAME
                )
                if workflow_id in all_workflows_dict:
                    del all_workflows_dict[workflow_id]
                self.settings_storage.set_user(
                    user_email, WORKFLOW_SETTINGS_NAME, all_workflows_dict
                )

            try:
                drive_items = esdl_drive_get_node(
                    f"/Users/{user_email}/workflows/{workflow_id}"
                )
            except EsdlDriveException:
                return dict(message="Failed deleting ESDLs from drive")
            for drive_item in drive_items:
                # TODO: Delete from Drive.
                pass
