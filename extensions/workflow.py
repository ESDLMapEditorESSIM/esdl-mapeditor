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
from flask_executor import Executor
from typing import List

import base64
import cgi
import os

import requests
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO

import esdl
from extensions.esdl_drive.api import (
    DRIVE_URL,
    get_drive_post_headers,
    get_node_drive,
    resource_endpoint,
    upload_to_drive,
)
from extensions.esdl_drive.esdl_drive import ESDLDriveHttpURI
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger
from src.process_es_area_bld import process_energy_system

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30
"""Default timeout for workflow proxy requests."""


class Workflow:
    """
    The workflow extension contains proxy endpoints, to allow the frontend to access defined services.
    """

    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage, executor: Executor
    ):
        self.flask_app = flask_app
        self.executor = executor
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
            r = requests.options(
                url, params=other_args, headers=headers, timeout=DEFAULT_TIMEOUT
            )
            try:
                resp_json = r.json()
            except Exception:
                resp_json = []
            return jsonify(resp_json), r.status_code

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
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )
            url = url.format(**other_args)
            r = requests.get(
                url, headers=headers, params=other_args, timeout=DEFAULT_TIMEOUT
            )
            try:
                resp_json = r.json()
            except Exception:
                resp_json = []
            return jsonify(resp_json), r.status_code

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
            r = requests.post(
                url, json=request_params, headers=headers, timeout=DEFAULT_TIMEOUT
            )
            if r.status_code == 200:
                # Get the filename from the header.
                parsed_header = cgi.parse_header(r.headers["Content-Disposition"])[-1]
                filename = os.path.basename(parsed_header["filename"])
                # Encode the file to base64. In this way, we can send it to the frontend.
                result = base64.b64encode(r.content).decode()
                return jsonify({"base64file": result, "filename": filename}), 200
            else:
                return jsonify([]), r.status_code

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
            r = requests.post(
                url, json=request_params, headers=headers, timeout=DEFAULT_TIMEOUT
            )
            try:
                resp_json = r.json()
            except Exception:
                resp_json = []
            return jsonify(resp_json), r.status_code

        @self.flask_app.route("/workflow/persist", methods=["POST"])
        def persist():
            """
            Persist this workflow.
            """
            workflow_id = request.json.get("workflow_id")
            user_email = get_session("user-email")
            esh = get_handler()
            energy_systems: List[esdl.EnergySystem] = esh.get_energy_systems()
            drive_paths = []
            for energy_system in energy_systems:
                esdl_contents = esh.to_string(energy_system.id)
                drive_path = f"/Users/{user_email}/workflows/{workflow_id}/{energy_system.name}.esdl"
                upload_to_drive(
                    esdl_contents,
                    drive_path,
                    dict(commitMessage="", overwrite=True),
                )
                drive_paths.append(drive_path)
            return jsonify(dict(drive_paths=drive_paths)), 200

        @self.flask_app.route("/workflow/load", methods=["POST"])
        def load():
            """
            Persist this workflow.
            """
            workflow_id = request.json.get("workflow_id")
            user_email = get_session("user-email")
            drive_items = get_node_drive(f"/Users/{user_email}/workflows/{workflow_id}")
            esh = get_handler()
            for drive_item in drive_items:
                uri = ESDLDriveHttpURI(
                    DRIVE_URL + resource_endpoint + drive_item["id"],
                    headers_function=get_drive_post_headers,
                    getparams={},
                )
                es, parse_info = esh.import_file(uri)
                self.executor.submit(
                    process_energy_system, esh, uri.last_segment, es.name or es.id
                )
            return jsonify(dict()), 200
