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

from flask import Flask
from flask_socketio import SocketIO, emit
import src.log as log
from esdl.processing.ESDLAsset import get_asset_capability_type
from esdl import esdl
from uuid import uuid4

logger = log.get_logger(__name__)
assets_to_be_added_instance = None


class AssetsToBeAdded:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket

        global assets_to_be_added_instance
        if assets_to_be_added_instance:
            logger.error("ERROR: Only one AssetsToBeAdded object can be instantiated")
        else:
            assets_to_be_added_instance = self

    @staticmethod
    def get_instance():
        global assets_to_be_added_instance
        return assets_to_be_added_instance

    @staticmethod
    def get_assets_from_measures(es):
        area = es.instance[0].area

        assets_to_be_added = list()
        if area.measures:
            for m in area.measures.measure:
                if m.type == esdl.MeasureTypeEnum.ADD_GEOMETRY:
                    if m.asset:
                        for asset in m.asset:
                            if asset.aggregationCount > 0:
                                assets_to_be_added.append({
                                    'id': asset.id,
                                    'name': asset.name,
                                    'type': type(asset).__name__,
                                    'cap': get_asset_capability_type(asset),
                                    'count': str(asset.aggregationCount)
                                })

        print(assets_to_be_added)
        return assets_to_be_added

    @staticmethod
    def get_instance_of_measure_with_asset_id(es, asset_id):
        area = es.instance[0].area
        measures = area.measures
        if measures:
            for m in measures.measure:
                for asset in m.asset:
                    if asset.id == asset_id:
                        if asset.aggregationCount > 0:
                            asset.aggregationCount -= 1
                            new_asset = asset.deepcopy()
                            new_asset.id = str(uuid4())
                            return new_asset

        return None

    def reduce_ui_asset_count(self, es, asset_id):
        print('emitting ATBA_use_asset')
        emit('ATBA_use_asset', {'es_id': es.id, 'id': asset_id}, namespace='/esdl')

