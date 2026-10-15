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
import uuid
from datetime import datetime, timezone
from typing import Any

from bson import json_util
from flask import Flask, jsonify, session, request
from flask_socketio import SocketIO
import src.log as log
from extensions.session_manager import set_session, get_session
from extensions.settings_storage import SettingsStorage
from src.tno.live_model_interface.api import deactivate_live_model_interface, activate_live_model_interface
from src.tno.mongo.core import get_database
from src.roles import mapeditor_admin_required
from src.tno.mongo.models import ApplicationContext

logger = log.get_logger(__name__)

APPLICATION_CONTEXTS_SETTING = "APPLICATION_CONTEXT_IDS"


class ApplicationContextExtension:
    """
    This extension provides the ability to manage application contexts. Application contexts are used to give the user
    a way to switch between different types of user flows in the mapeditor. This should highlight and focus certain
    information, while hiding other information.
    """
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info('Registering ApplicationContext extension')

        @self.flask_app.route('/admin/context/applications')
        @mapeditor_admin_required
        def get_all_application_contexts():
            """
            Get all application contexts for the admin.
            """
            db = get_database()
            return self.flask_app.response_class(
                json_util.dumps(db.application_contexts.find()), mimetype='application/json'
            )

        @self.flask_app.route('/admin/context/applications', methods=['POST'])
        @self.flask_app.route('/admin/context/applications/<application_id>', methods=['PUT'])
        @mapeditor_admin_required
        def save_application_context(application_id: str | None = None) -> tuple[Any, int]:
            """
            Create or update an application context, keeping its application_id unchanged.
            """
            application_json = request.get_json()
            if not isinstance(application_json, dict):
                return jsonify({'error': 'Expected an application context object'}), 400

            for field in ('application_id', 'name'):
                value = application_json.get(field)
                if not isinstance(value, str) or not value.strip():
                    return jsonify({'error': f'{field} is required'}), 400
                application_json[field] = value.strip()

            context_id = application_json['application_id']
            if context_id == 'default' or '/' in context_id:
                return jsonify({'error': 'Application ID cannot be default or contain /'}), 400
            if application_id is not None and context_id != application_id:
                return jsonify({'error': 'Application ID cannot be changed'}), 400

            is_global = application_json.get('is_global', False)
            toast_text = application_json.get('toast_text')
            if not isinstance(is_global, bool) or (toast_text is not None and not isinstance(toast_text, str)):
                return jsonify({'error': 'Invalid global visibility or toast text'}), 400

            application_context = {
                'application_id': context_id,
                'name': application_json['name'],
                'is_global': is_global,
                'toast_text': toast_text,
            }
            db = get_database()
            if application_id is None:
                if db.application_contexts.find_one({'application_id': context_id}):
                    return jsonify({'error': 'Application ID already exists'}), 409
                application_context['live_model_interfaces'] = []
                db.application_contexts.insert_one(application_context)
                return {}, 201

            updated = db.application_contexts.update_one(
                {'application_id': application_id}, {'$set': application_context}
            )
            if not updated.matched_count:
                return jsonify({'error': 'Application ID not found'}), 404
            return {}, 200

        @self.flask_app.route('/admin/context/applications/<application_id>', methods=['DELETE'])
        @mapeditor_admin_required
        def delete_application_context(application_id: str) -> tuple[Any, int]:
            """
            Delete an application context by application_id.
            """
            db = get_database()
            deleted = db.application_contexts.delete_one({'application_id': application_id})
            if not deleted.deleted_count:
                return jsonify({'error': 'Application ID not found'}), 404
            return {}, 204

        @self.flask_app.route('/context/applications')
        def get_user_application_contexts():
            """
            Get the application contexts for the current user.
            :return:
            """
            context_ids = self.settings_storage.get_for_current_user(APPLICATION_CONTEXTS_SETTING, default=[])
            # Get the actual application contexts by querying mongodb for all entries with the given ids.
            db = get_database()
            # Find all application contexts with the given ids, and also get all contexts with global set to True
            application_contexts: list[ApplicationContext] = db.application_contexts.find({"$or": [{"application_id": {"$in": context_ids}}, {"is_global": True}]})
            active_context: ApplicationContext | None = get_session('application_context')
            response = dict(application_contexts=application_contexts, active_context_id=active_context["application_id"] if active_context else None)
            return json_util.dumps(response)

        @self.flask_app.route("/context/applications/<application_id>/activate", methods=["POST"])
        def activate_application_context(application_id):
            """
            Activate the application context for the given application_id.
            :param application_id:
            :return:
            """
            db = get_database()
            application_context: ApplicationContext | None = db.application_contexts.find_one({"application_id": application_id})
            if not application_context:
                return jsonify({"error": "Application ID not found"}), 404
            set_session('application_context', application_context)
            client_id = session['client_id']

            live_model_interfaces = application_context.get("live_model_interfaces", [])
            for lmi in live_model_interfaces:
                activate_live_model_interface(lmi["lmi_id"], client_id)
                set_session(f"lmi_{lmi['lmi_id']}", True)

            return {}, 200

        @self.flask_app.route("/context/applications/<application_id>/clear", methods=["POST"])
        def clear_application_context(application_id: str):
            """
            Clear the application context for the given application_id.
            :param application_id:
            :return:
            """
            db = get_database()
            application_context: ApplicationContext | None = db.application_contexts.find_one({"application_id": application_id})
            if not application_context:
                return jsonify({"error": "Application ID not found"}), 404
            client_id = session['client_id']
            set_session('application_context', None)

            live_model_interfaces = application_context.get("live_model_interfaces", [])
            for lmi in live_model_interfaces:
                deactivate_live_model_interface(lmi["lmi_id"], client_id)
                set_session(f"lmi_{lmi['lmi_id']}", False)

            return {}, 200

        @self.flask_app.route("/context/applications/<application_id>/lmis", methods=["POST"])
        def enable_disable_live_model_interface(application_id: str):
            """
            :return:
            """
            db = get_database()
            application_context: ApplicationContext | None = db.application_contexts.find_one({"application_id": application_id})
            if not application_context:
                return jsonify({"error": "Application ID not found"}), 404

            live_model_interfaces = application_context.get("live_model_interfaces", [])
            data = request.json
            lmi_id = data.get('lmi_id')
            # Find the live model interface with the lmi_id
            lmi = next((lmi for lmi in live_model_interfaces if lmi["lmi_id"] == lmi_id), None)
            if lmi is None:
                return jsonify({"error": "Live model interface not found"}), 404

            enabled = data.get('enabled')
            if enabled is None:
                return jsonify({"error": "No enabled status provided"}), 400
            client_id = session['client_id']
            if enabled:
                activate_live_model_interface(lmi_id, client_id)
                set_session(f"lmi_{lmi['lmi_id']}", True)
            else:
                deactivate_live_model_interface(lmi_id, client_id)
                set_session(f"lmi_{lmi['lmi_id']}", False)
            return {}, 200
