import base64
import cgi
import os

import requests
from flask import Flask, jsonify, request
from flask_socketio import SocketIO

from extensions.session_manager import get_session
from extensions.settings_storage import SettingsStorage
from log import get_logger

logger = get_logger(__name__)


class Workflow:
    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        print("Registering workflow extension")

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
            r = requests.get(url, headers=headers, params=other_args)
            if r.status_code == 200:
                return jsonify(r.json()), 200
            else:
                return jsonify([]), r.status_code

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
            r = requests.post(url, json=request_params, headers=headers)
            if r.status_code == 200:
                # Get the filename from the header.
                parsed_header = cgi.parse_header(r.headers["Content-Disposition"])[-1]
                filename = os.path.basename(parsed_header["filename"])
                # Encode the file to base64. In this way, we can send it to the frontend.
                result = base64.b64encode(r.content).decode()
                return jsonify({"base64file": result, "filename": filename}), 200
            else:
                return jsonify([]), r.status_code

        @self.flask_app.route("/workflow/upload_file", methods=["POST"])
        def upload_file():
            """
            Upload a file by POSTing to a remote service, and providing some
            parameters, if they're provided.
            """
            url = request.json["remote_url"]
            with_jwt_token = request.args.get("with_jwt_token", True)
            jwt_token = get_session("jwt-token")
            headers = (
                {"Authorization": f"Bearer {jwt_token}"} if with_jwt_token else None
            )

            request_params = request.json.get("request_params")
            r = requests.post(url, json=request_params, headers=headers)
            return jsonify([]), r.status_code
