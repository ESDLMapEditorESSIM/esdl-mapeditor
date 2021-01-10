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
from flask_socketio import SocketIO
import src.log as log
from esdl.processing.ESDLAsset import get_asset_capability_type
from uuid import uuid4

logger = log.get_logger(__name__)


class AssetsToBeAdded:
    @staticmethod
    def get_assets_from_measures(es):
        area = es.instance[0].area

        assets_to_be_added = list()
        if area.measures:
            for m in area.measures.measure:
                if m.asset:
                    for asset in m.asset:

                        # TODO: Check annotation for 'to_be_added'
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
