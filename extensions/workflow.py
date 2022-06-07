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

import jwt
import base64
import cgi
import os

import requests
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO

from extensions.session_manager import get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30
"""Default timeout for workflow requests."""

class Workflow:
    """
    The workflow extension contains proxy endpoints, to allow the frontend to access defined services.
    """
    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage
    ):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info("Registering workflow extension")

        @self.flask_app.route("/workflow/get_options")
        def get_options():
            url = request.args["url"]
            other_args = dict(request.args)
            del other_args["url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )
            r = requests.options(url, params=other_args, headers=headers, timeout=DEFAULT_TIMEOUT)
            try:
                resp_json = r.json()
            except Exception:
                resp_json = []
            return jsonify(resp_json), r.status_code

        @self.flask_app.route("/workflow/get_data")
        def get_data():
            url = request.args["url"]
            other_args = dict(request.args)
            del other_args["url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )
            url = url.format(**other_args)
            r = requests.get(url, headers=headers, params=other_args, timeout=DEFAULT_TIMEOUT)
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
            r = requests.post(url, json=request_params, headers=headers, timeout=DEFAULT_TIMEOUT)
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
            logger.info(request.json)
            url = request.json["remote_url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )

            request_params = request.json.get("request_params")
            r = requests.post(url, json=request_params, headers=headers, timeout=DEFAULT_TIMEOUT)
            try:
                resp_json = r.json()
            except Exception:
                resp_json = []
            return jsonify(resp_json), r.status_code
