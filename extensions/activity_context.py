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
from flask_socketio import SocketIO
import src.log as log
from extensions.settings_storage import SettingsStorage
from src.roles import mapeditor_admin_required
from src.tno.mongo.core import get_database
from src.tno.mongo.models import ActivityContext

logger = log.get_logger(__name__)

ACTIVITY_CONTEXTS_SETTING = "ACTIVITY_CONTEXT_IDS"


class ActivityContextExtension:
    """
    This extension provides the ability to manage activity contexts. Activity contexts are used to give the user an
    easy way to switch between different sets of activities.

    This extension provides the ability to get the activity contexts for the current user, and to manage activity
    contexts for the admin.
    """
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info('Registering ActivityContext extension')

        @self.flask_app.route('/context/activities')
        def get_user_activity_contexts():
            """
            Get the activity contexts for the current user.
            :return:
            """
            context_ids = self.settings_storage.get_for_current_user(ACTIVITY_CONTEXTS_SETTING, default=[])
            # Get the actual activity contexts by querying mongodb for all entries with the given ids.
            db = get_database()
            # Find all activity contexts with the given ids, and also get all contexts with global set to True
            context_filter = {"$or": [{"activity_id": {"$in": context_ids}}, {"is_global": True}]}
            application_id = request.args.get("application_id")
            if application_id:
                context_filter = {
                    "$and": [
                        context_filter,
                        {"$or": [{"application_ids": None}, {"application_ids": application_id}]},
                    ]
                }
            activity_contexts = db.activity_contexts.find(context_filter)
            json_result = json_util.dumps(activity_contexts)
            return json_result

        @self.flask_app.route("/admin/context/activities")
        @mapeditor_admin_required
        def get_all_activity_contexts():
            """
            Get all activity contexts from the database and return them as a json string.
            :return:
            """
            db = get_database()
            contexts_result = db.activity_contexts.find()
            return json_util.dumps(contexts_result), 200

        @self.flask_app.route("/admin/context/activities", methods=["POST"])
        @mapeditor_admin_required
        def create_activity_context():
            """
            Create a new activity context. The activity_id must be unique.
            :return:
            """
            activity_json = request.json
            activity_context = ActivityContext(**activity_json)
            activity_context._id = None
            db = get_database()
            # Check if the activity_id already exists
            if db.activity_contexts.find_one({"activity_id": activity_context.activity_id}):
                return jsonify({"error": "Activity ID already exists"}), 409
            db.activity_contexts.insert_one(asdict(activity_context))
            return {}, 201

        @self.flask_app.route("/admin/context/activities/<activity_id>", methods=["DELETE"])
        @mapeditor_admin_required
        def delete_activity_context(activity_id):
            """
            Delete a context by activity_id
            :param activity_id:
            :return:
            """
            db = get_database()
            db.activity_contexts.delete_one({"activity_id": activity_id})
            return {}, 204

