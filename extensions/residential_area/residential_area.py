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
import codecs
import csv
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
from extensions.session_manager import set_session, get_project_manager, get_session
from extensions.settings_storage import SettingsStorage
from src.edr_client import EDRClient
from src.esdl_helper import energy_asset_to_ui

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
        self.primos_data = None

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

        @self.socketio.on("residential_area_create", namespace="/esdl")
        def residential_area_create(params):
            with self.flask_app.app_context():
                bld_composition = params["building_composition"]
                aggr_bld = self.create_aggregated_building(bld_composition)

                if 'id' in params:
                    # Request was sent by right-clicking on an Area / map location
                    area_id = params['id']
                    pm = get_project_manager()
                    active_es_id = get_session('active_es_id')
                    area = pm.get_by_id(active_es_id, area_id)
                    if area:
                        aggr_bld.geometry = esdl.Point(lat=float(params["lat"]), lon=float(params["lon"]))
                        area.asset.append(aggr_bld)

                        buildings_to_be_added_list = list()
                        extra_attributes = dict()
                        extra_attributes['assetType'] = aggr_bld.assetType
                        buildings_to_be_added_list.append(['point', aggr_bld.name, aggr_bld.id, type(aggr_bld).__name__,
                                                           [aggr_bld.geometry.lat, aggr_bld.geometry.lon],
                                                           False, {}, extra_attributes])

                        emit(
                            'add_building_objects',
                            {
                                'es_id': active_es_id,
                                'building_list': buildings_to_be_added_list,
                                'zoom': False
                            },
                            namespace='/esdl'
                        )
                    else:
                        logger.error("Area to which aggregated building should be added, could not be found")
                else:
                    # Request was sent from the menu, location still needs to be determined by the user
                    self.store_asset_for_drawing_on_map(aggr_bld)

                return {}

        @self.flask_app.route("/residential_area/get_primos", methods=["POST"])
        def get_primos():
            area_id = request.json["id"]
            return self.get_primos_data(area_id)

    def get_settings(self, force_reset=False):
        if self.settings_storage.has_system(RESIDENTIAL_AREA_SETTINGS) and not force_reset:
            settings = self.settings_storage.get_system(RESIDENTIAL_AREA_SETTINGS)
        else:
            settings = {
                "tags": "residential_area_plugin",
                "primos_file": "data/primos_2019.csv"
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

        aggr_bld = esdl.AggregatedBuilding(id=str(uuid4()), name="Woonwijk", aggregationCount=0)

        totals = dict()
        for bld in bld_composition:
            # check for wrong input (empty string or something other than a number)
            if str(bld["num"]).isnumeric() and int(bld["num"]) > 0:
                # Add number of this type of building to the total number of buildings in the AggregatedBuilding
                aggr_bld.aggregationCount += int(bld["num"])

                # Collect information about the assets and energy values in this type of building
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
                                        totals[asset.eClass.name][asset.name]["value"] += int(bld["num"]) * value
                                    else:
                                        totals[asset.eClass.name][asset.name] = {
                                            "name": asset.name,
                                            "value": int(bld["num"]) * value,
                                            "qau": qau.deepcopy()
                                        }
                                else:
                                    totals[asset.eClass.name] = {
                                        asset.name: {
                                            "name": asset.name,
                                            "value": int(bld["num"]) * value,
                                            "qau": qau.deepcopy()}
                                    }

        for asset_class, asset_info in totals.items():
            for asset_instance, asset_sub_info in asset_info.items():
                # Create the aggregated version of this asset over all building types
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

        # Add EConnection and ElectricityNetwork to the AggregatedBuilding
        aggr_bld_elec_netw = esdl.ElectricityNetwork(id=str(uuid4()), name="In-house electricity network")
        aggr_bld_elec_netw_inp = esdl.InPort(id=str(uuid4()), name="In")
        aggr_bld_elec_netw_outp = esdl.OutPort(id=str(uuid4()), name="Out")
        aggr_bld_elec_netw.port.extend([aggr_bld_elec_netw_inp, aggr_bld_elec_netw_outp])
        aggr_bld.asset.append(aggr_bld_elec_netw)

        aggr_bld_econn = esdl.EConnection(id=str(uuid4()), name="Electricity network connection")
        aggr_bld_econn_inp = esdl.InPort(id=str(uuid4()), name="In")
        aggr_bld_econn_outp = esdl.OutPort(id=str(uuid4()), name="Out")
        aggr_bld_econn.port.extend([aggr_bld_econn_inp, aggr_bld_econn_outp])
        aggr_bld.asset.append(aggr_bld_econn)

        # Connect EConnection to the in-house electricity network
        aggr_bld_econn_outp.connectedTo.append(aggr_bld_elec_netw_inp)

        # Connect all assets in the building to the in-house electricity network
        # For now assume all assets relate to electricity
        for bld_asset in aggr_bld.asset:
            if isinstance(bld_asset, esdl.Producer):
                bld_asset.port[0].connectedTo.append(aggr_bld_elec_netw_inp)
            elif isinstance(bld_asset, esdl.Consumer):
                bld_asset.port[0].connectedTo.append(aggr_bld_elec_netw_outp)

        # Expose the InPort of the EConnection to the outside of the Building
        aggr_bld.port.append(aggr_bld_econn_inp)

        return aggr_bld

    def store_asset_for_drawing_on_map(self, asset):
        # Create string representation of the ESDL of the Asset
        rset = ResourceSet()
        uri = StringURI("asset_to_be_drawn.esdl")
        resource = rset.create_resource(uri)
        resource.append(asset)
        resource.save(uri)

        # Put this string in the adding_edr_assets session variable so it can be used after asset placement on the map
        set_session("adding_edr_assets", uri.getvalue())

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

    def read_primos_data(self):
        if "primos_file" not in self.settings:
            self.settings = self.get_settings(force_reset=True)

        primos_file = self.settings['primos_file']

        self.primos_data = dict()
        with codecs.open(primos_file, encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                self.primos_data[row['gm_code']] = row

        logger.debug(f"Residential_area plugin read {len(self.primos_data)} municipalities from input file")

    def get_primos_data(self, area_id: str):
        """ Gets the data from the PRIMOS database for this municipality """

        if not self.primos_data:
            self.read_primos_data()

        if area_id in self.primos_data:
            mun_info = self.primos_data[area_id]

            return {
                "gm_naam": mun_info["gm_naam"],
                "gm_code": mun_info["gm_code"],
                "info": [
                    {
                        "label": '2019-2023',
                        "additions": "???",
                        "removals": "???",
                        "cumulative": "???"
                    },
                    {
                        "label": '2023-2025',
                        "additions": mun_info['2023-Nieuwbouw (cumulatief komende 2 jaren)'],
                        "removals": mun_info['2023-Onttrekkingen (cumulatief komende 2 jaren)'],
                        "cumulative": mun_info['2023-Woningvoorraadontwikkeling (cumulatief komende 2 jaren)']
                    },
                    {
                        "label": '2025-2030',
                        "additions": mun_info['2025-Nieuwbouw (cumulatief komende 5 jaren)'],
                        "removals": mun_info['2025-Onttrekkingen (cumulatief komende 5 jaren)'],
                        "cumulative": mun_info['2025-Woningvoorraadontwikkeling (cumulatief komende 5 jaren)']
                    },
                    {
                        "label": '2030-2035',
                        "additions": mun_info['2030-Nieuwbouw (cumulatief komende 5 jaren)'],
                        "removals": mun_info['2030-Onttrekkingen (cumulatief komende 5 jaren)'],
                        "cumulative": mun_info['2030-Woningvoorraadontwikkeling (cumulatief komende 5 jaren)']
                    },\
                    {
                        "label": '2035-2040',
                        "additions": mun_info['2035-Nieuwbouw (cumulatief komende 5 jaren)'],
                        "removals": mun_info['2035-Onttrekkingen (cumulatief komende 5 jaren)'],
                        "cumulative": mun_info['2035-Woningvoorraadontwikkeling (cumulatief komende 5 jaren)']
                    },

                ]
            }
        else:
            return None