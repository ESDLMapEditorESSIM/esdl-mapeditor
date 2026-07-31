from typing import Dict, List, Optional

from flask import Flask
from flask_socketio import SocketIO

import esdl
import esdl.processing.ESDLEcore as ESDLEcore
import src.log as log
from extensions.session_manager import get_project_manager, get_session
from extensions.settings_storage import SettingsStorage

logger = log.get_logger(__name__)

LAYER_VISUALIZATION_SETTINGS = "LAYER_VISUALIZATION"

class SpatialVisualization:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info("Registering SpatialVisualization extension")
        
        @self.flask_app.route("/spatial_visualization/asset_fields/<string:es_id>/<string:asset_id>", methods=["GET"])
        def _get_esdl_asset_fields(es_id: str, asset_id: str):
            return self.get_esdl_asset_attributes(es_id, asset_id)

        @self.socketio.on("spatial_visualization/get_layer_styles", namespace="/esdl")
        def _get_layer_styles():
            return self.get_layer_styles()

        @self.socketio.on("spatial_visualization/save_layer_styles", namespace="/esdl")
        def _save_layer_styles(params: Dict):
            if not isinstance(params, dict) or not isinstance(params.get('styles'), list):
                logger.error(f"Invalid request body for save_layer_styles: {params}")
                return None
            return self.save_layer_styles(params['styles'])

    def get_layer_styles(self) -> Optional[List[dict]]:
        """
        Fetches the saved layer styles for the currently logged in user.

        :return: The list of saved layer styles, or None if they could not be fetched.
        """
        user = get_session('user-email')
        if user is None:
            logger.warning("No active user session found; cannot fetch layer styles.")
            return None

        try:
            styles: List[dict] = []
            if self.settings_storage.has_user(user, LAYER_VISUALIZATION_SETTINGS):
                user_settings = self.settings_storage.get_user(user, LAYER_VISUALIZATION_SETTINGS)
                if user_settings and user_settings.get('layer_styles') is not None:
                    styles = user_settings.get('layer_styles')
            return styles
        except Exception as e:
            logger.error(f"An error occurred while fetching layer styles for {user}: {e}")
            return None

    def save_layer_styles(self, styles: List[dict]) -> Optional[List[dict]]:
        """
        Saves the given list of layer styles for the currently logged in user.

        :param styles: The full list of layer styles to persist.

        :return: The persisted list of layer styles, or None if they could not be saved.
        """
        user = get_session('user-email')
        if user is None:
            logger.warning("No active user session found; cannot save layer styles.")
            return None

        try:
            self.settings_storage.set_user(user, LAYER_VISUALIZATION_SETTINGS, {"layer_styles": styles})
            return styles
        except Exception as e:
            logger.error(f"An error occurred while saving layer styles for {user}: {e}")
            return None

    def get_esdl_asset_attributes(self, es_id: str, asset_id: str):
        attributes = []

        pm = get_project_manager()
        try:
            asset: esdl.Asset = pm.get_by_id(es_id, asset_id)
            attrs = ESDLEcore.get_asset_attributes(asset)
            for a in attrs:
                attributes.append({
                    'name': a['name'],
                    'type': a['type'],
                    'value': a['value']
                })
            # TODO: Support asset references
            # references = ESDLEcore.get_asset_references(asset, None, None)
        except KeyError:
            logger.error(f"Error getting asset with ES id {es_id} and asset id: {asset_id}")

        return attributes