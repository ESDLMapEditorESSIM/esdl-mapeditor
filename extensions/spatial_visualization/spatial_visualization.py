from flask import Flask

import esdl
import esdl.processing.ESDLEcore as ESDLEcore
import src.log as log
from extensions.session_manager import get_project_manager

logger = log.get_logger(__name__)

class SpatialVisualization:
    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info("Registering SpatialVisualization extension")
        
        @self.flask_app.route("/spatial_visualization/asset_fields/<string:es_id>/<string:asset_id>", methods=["GET"])
        def _get_esdl_asset_fields(es_id: str, asset_id: str):
            return self.get_esdl_asset_attributes(es_id, asset_id)
    
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