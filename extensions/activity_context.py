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
from dataclasses import asdict

from bson import json_util
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import src.log as log
from src.tno.mongo.core import get_database
from src.tno.mongo.models import ActivityContext

logger = log.get_logger(__name__)


class ActivityContextExtension:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering ActivityContext extension')

        @self.flask_app.route("/context/activities")
        def get_contexts():
            db = get_database()
            contexts_result = db.activity_contexts.find()
            return json_util.dumps(contexts_result), 200


        @self.flask_app.route("/context/activities", methods=["POST"])
        def create_context():
            activity_json = request.json
            activity_context = ActivityContext(**activity_json)
            activity_context._id = None
            db = get_database()
            # Check if the activity_id already exists
            if db.activity_contexts.find_one({"activity_id": activity_context.activity_id}):
                return jsonify({"error": "Activity ID already exists"}), 409
            db.activity_contexts.insert_one(asdict(activity_context))
            return {}, 201

        @self.flask_app.route("/context/activities/<activity_id>", methods=["DELETE"])
        def delete_context(activity_id):
            db = get_database()
            db.activity_contexts.delete_one({"activity_id": activity_id})
            return {}, 204
