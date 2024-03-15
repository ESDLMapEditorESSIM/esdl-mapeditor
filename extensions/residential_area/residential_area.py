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
import importlib
import json
from datetime import datetime, timedelta
from uuid import uuid4

import requests
from flask import Flask, request
from flask_executor import Executor
from flask_socketio import SocketIO, emit
from pyecore.resources import ResourceSet, URI

import esdl
from esdl.esdl_handler import StringURI
from esdl.processing import ESDLAsset
from extensions.session_manager import set_session
from extensions.settings_storage import SettingsStorage
from src.edr_client import EDRClient

from src.log import get_logger
from src.settings import edr_config

logger = get_logger(__name__)


RESIDENTIAL_AREA_SETTINGS = "RESIDENTIAL_AREA_SETTINGS"


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class ResidentialArea:
    """
    The Residential Area extension contains functions to build a custom residential area in the MapEditor and calculate
    energy usage.
    """

    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.settings = self.get_settings()
        self.building_list = list()
        self.building_list_datetime_retrieved = None

        self.register()

    def register(self):
        logger.info("Registering ResidentialArea extension")

        @self.flask_app.route("/residential_area/get_building_list")
        def get_building_list():
            buildings = self.get_edr_residential_area_buildings()

            blist = list()
            for b in buildings:
                blist.append({
                    "id": b["id"],
                    "name": b["title"],
                    "num": 0
                })

            return { "building_list": blist }

        @self.flask_app.route("/residential_area/form", methods=["GET", "POST"])
        def form():
            if request.method == "POST":
                buildings = self.get_edr_residential_area_buildings()
                blist = list()
                for b in buildings:
                    blist.append({
                        "id": b["id"],
                        "name": b["title"],
                        "num": request.json[b["title"].replace(" ", "_")]
                    })

                return self.create_aggregated_building(blist)

            elif request.method == "GET":

                # Get the data for the form
                buildings = self.get_edr_residential_area_buildings()
                bdict = dict()
                for b in buildings:
                    bdict[b["title"].replace(" ", "_")] = 0

                # Define the JSON schena
                schema = {
                    "properties": {}
                }
                for b in buildings:
                    schema["properties"][b["title"].replace(" ", "_")] = {"type": "integer"}

                # Define the JSON form schema
                uischema = {
                  "type": "VerticalLayout",
                  "elements": []
                }
                for b in buildings:
                    uischema["elements"].append({
                        "type": "Control",
                        "scope": "#/properties/" + b["title"].replace(" ", "_"),
                        "label": b["title"]
                    })

                return {
                    "schema": schema,
                    "data": bdict,
                    "uischema": uischema
                }
            else:
                return "Method not allowed", 500

            return {}

        @self.flask_app.route("/residential_area/create", methods=["POST"])
        def create():
            bld_composition = request.json["building_composition"]
            return self.create_aggregated_building(bld_composition)

    def get_settings(self):
        if self.settings_storage.has_system(RESIDENTIAL_AREA_SETTINGS):
            settings = self.settings_storage.get_system(RESIDENTIAL_AREA_SETTINGS)
        else:
            settings = {
                "tags": "residential_area_plugin"
            }
            self.settings_storage.set_system(RESIDENTIAL_AREA_SETTINGS, settings)

        return settings

    def create_aggregated_building(self, bld_composition):
        edr_client = EDRClient.get_instance()
        for bld in bld_composition:
            edr_asset_str = edr_client.get_object_from_EDR(bld["id"])
            if edr_asset_str:
                edr_asset = ESDLAsset.load_asset_from_string(edr_asset_str)
                bld["esdl"] = edr_asset

        totals = dict()
        for bld in bld_composition:
            if int(bld["num"]) > 0:
                bld_esdl = bld["esdl"]
                for asset in bld_esdl.asset:
                    if isinstance(asset, esdl.Producer) or isinstance(asset, esdl.Consumer):
                        port = asset.port[0]  # Assume 1st port provides the profile
                        if port.profile:
                            profile = port.profile[0]  # Assume 1st profile is relevant
                            if isinstance(profile, esdl.SingleValue):
                                value = profile.value
                                qau = profile.profileQuantityAndUnit

                                if asset.eClass.name in totals:
                                    if asset.name in totals[asset.eClass.name]:
                                        totals[asset.eClass.name][asset.name]["value"] += value
                                    else:
                                        totals[asset.eClass.name][asset.name] = {"name": asset.name, "value": value,
                                                                 "qau": qau.deepcopy()}
                                else:
                                    totals[asset.eClass.name] = {asset.name: {"name": asset.name, "value": value,
                                                                 "qau": qau.deepcopy()}}

        aggr_bld = esdl.AggregatedBuilding(id=str(uuid4()), name="Woonwijk")
        for asset_class, asset_info in totals.items():
            for asset_instance, asset_sub_info in asset_info.items():
                asset = esdl.getEClassifier(asset_class)()
                asset.id = str(uuid4())
                asset.name = asset_instance

                if isinstance(asset, esdl.Producer):
                    port = esdl.OutPort(id=str(uuid4()), name="OutPort")
                elif isinstance(asset, esdl.Consumer):
                    port = esdl.InPort(id=str(uuid4()), name="InPort")

                asset.port.append(port)

                profile = esdl.SingleValue(id=str(uuid4()), name=asset_sub_info["name"])
                profile.value = asset_sub_info["value"]
                profile.profileQuantityAndUnit = asset_sub_info["qau"]
                profile.profileQuantityAndUnit.id = str(uuid4())
                port.profile.append(profile)

                aggr_bld.asset.append(asset)

        # TODO: add EConnection and Network

        rset = ResourceSet()
        resource = rset.create_resource(URI("aggr_bld.esdl"))
        resource.append(aggr_bld)
        uri = StringURI("aggr_bld_str.esdl")
        resource.save(uri)

        set_session("adding_edr_assets", uri.getvalue())

        return {}

    def get_edr_residential_area_buildings(self):
        now = datetime.now()
        if self.building_list and self.building_list_datetime_retrieved:
            if now - self.building_list_datetime_retrieved < timedelta(days=1):
                # If data is less than a day old, return old data
                return self.building_list

        url = edr_config["host"] + "/store/edr/query?tag=" + self.settings["tags"]

        try:
            r = requests.get(url)
            if r.status_code == 200:
                result = json.loads(r.text)
                self.building_list = result
                self.building_list_datetime_retrieved = now
                return result
            else:
                print('EDR returned unexpected result. Check ResidentialArea settings')
                send_alert('EDR returned unexpected result. Check ResidentialArea settings')
                return None

        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return None

