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
from flask_executor import Executor
from datetime import datetime
from datetime import timedelta
from geojson import Feature, MultiLineString, FeatureCollection, dumps
from math import fabs
import pytz

from esdl import esdl
from esdl.processing.ESDLQuantityAndUnits import unit_to_string
from extensions.profiles import Profiles
from extensions.session_manager import get_project_manager, get_session, set_session
from extensions.settings_storage import SettingsStorage
from extensions.mapeditor_settings import MapEditorSettings, MAPEDITOR_UI_SETTINGS

import src.log as log

logger = log.get_logger(__name__)

# TIME_DIMENSION_SYSTEM_CONFIG = 'TIME_DIMENSION_SYSTEM_CONFIG'
TIME_DIMENSION_USER_CONFIG = "TIME_DIMENSION_SERVICE_USER_CONFIG"

default_colors = [
    "#ff0000",
    "#0000ff",
    "#00ff00",
    "#800080",
    "#ffa500",
    "#e31a1c",
    "#fdbf6f",
    "#ff7f00",
    "#cab2d6",
    "#6a3d9a",
    "#ffff99",
    "#b15928",
]


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    logger.warn(message)
    emit("alert", message, namespace="/esdl")


# ---------------------------------------------------------------------------------------------------------------------
#  TimeDimension
# ---------------------------------------------------------------------------------------------------------------------
class TimeDimension:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.register()
        me_settings = MapEditorSettings.get_instance()
        self.mapeditor_colors = self.get_colors_from_settings(me_settings)

    def get_colors_from_settings(self, me_settings):
        me_ui_setting = me_settings.get_system_setting(MAPEDITOR_UI_SETTINGS)
        if me_ui_setting:
            if "carrier_colors" in me_ui_setting:
                return me_ui_setting["carrier_colors"]
        return None

    def register(self):
        logger.info("Registering Time Dimension extension")

        @self.socketio.on("get_windowed_simulation_data", namespace="/esdl")
        def get_windowed_simulation_data(start, end):
            with self.flask_app.app_context():
                return self.get_windowed_simulation_data(start, end)

        @self.socketio.on("timedimension_initialize", namespace="/esdl")
        def timedimension_initialize(info):
            """ "
            This function is called when the user selects to use the TimeDimension functionality
            """
            with self.flask_app.app_context():
                database = info["database"]
                animation_column_name = info["animation_column_name"]
                simulation_id = info["simulation_id"]
                networks = info["networks"]

                set_session("timedimension-simulation-id", simulation_id)
                set_session("timedimension-parameter", animation_column_name)

                set_session("td_monitor_ids", [])

                active_es_id = get_session("active_es_id")
                set_session("active_es_id_animation", active_es_id)
                set_session(
                    "influxdb_connection", Profiles.connect_to_animation_profiles_database(active_es_id, database)
                )

                self.preprocess_data(networks)
                time_list = self.get_all_times_from_simulation()

                timedimension_colors = self.get_colors()
                set_session("timedimension-colors", timedimension_colors)

                return time_list

        @self.socketio.on("timedimension_get_asset_ids", namespace="/esdl")
        def timedimension_get_asset_ids():
            with self.flask_app.app_context():
                return get_session("timedimension-asset-ids")

        @self.socketio.on("time_dimension_get_settings", namespace="/esdl")
        def time_dimension_get_settings():
            user = get_session("user-email")
            user_settings = self.get_user_settings(user)
            return user_settings

        @self.socketio.on("time_dimension_set_settings", namespace="/esdl")
        def time_dimension_set_settings(user_settings):
            user = get_session("user-email")
            self.set_user_settings(user, user_settings)

        @self.socketio.on("td_monitor_asset", namespace="/esdl")
        def td_monitor_asset(info):
            if info:
                asset_id = info["id"]
                td_monitor_ids = get_session("td_monitor_ids")
                if asset_id in td_monitor_ids:
                    td_monitor_ids.remove(asset_id)
                else:
                    td_monitor_ids.append(asset_id)
                set_session("td_monitor_ids", td_monitor_ids)
            else:
                set_session("td_monitor_ids", [])

        @self.socketio.on("request_load_duration_curve", namespace="/esdl")
        def request_load_duration_curve(info):
            asset_id = info["id"]
            active_es_id = get_session("active_es_id_animation")
            timedimension_parameter = get_session("timedimension-parameter")
            esh = get_handler()
            asset = esh.get_by_id(active_es_id, asset_id)
            asset_name = asset.name
            power = None
            # TODO leave out for mesido for now
            if hasattr(asset, "power"):
                power = asset.power
            elif hasattr(asset, "capacity"):
                power = asset.capacity
            power_pos = None
            power_neg = None

            influxdb_client = get_session("influxdb_connection")

            measurements_query = "SHOW MEASUREMENTS"
            measurements_result = influxdb_client.query(measurements_query)
            first_key = list(measurements_result.keys())[0]
            measurements = [item["name"] for item in measurements_result[first_key]]
            logger.debug(f"MEASUREMENTS: {measurements}")

            results = dict()
            for m in measurements:
                try:
                    query = (
                        'SELECT "' + timedimension_parameter + '" FROM "' + m + "\" WHERE assetId='" + asset_id + "'"
                    )
                    logger.debug(query)
                    res = influxdb_client.query(query)
                    if res:
                        results = res
                        break
                except Exception as e:
                    logger.error("error with query: ", str(e))

            first_key = list(results.keys())[0]
            series = results[first_key]

            ldc_series = []
            for item in series:
                ldc_series.append(item[timedimension_parameter])
            ldc_series.sort(reverse=True)

            ldc_series_decimate = []
            for idx, item in enumerate(ldc_series):
                if idx % 40 == 0:
                    ldc_series_decimate.append(item * 1e6)
                    if item > 0:
                        power_pos = power
                    if item < 0:
                        power_neg = -power

            emit(
                "ldc-data",
                {
                    "asset_name": asset_name,
                    "ldc_series": ldc_series_decimate,
                    "power_pos": power_pos,
                    "power_neg": power_neg,
                },
            )

    def get_user_settings(self, user):
        if self.settings_storage.has_user(user, TIME_DIMENSION_USER_CONFIG):
            return self.settings_storage.get_user(user, TIME_DIMENSION_USER_CONFIG)
        else:
            user_settings = {"ab_visible": False}  # Animation bar visible on startup
            self.set_user_settings(user, user_settings)
            return user_settings

    def set_user_settings(self, user, user_settings):
        self.settings_storage.set_user(user, TIME_DIMENSION_USER_CONFIG, user_settings)

    def preprocess_data(self, networks):
        influxdb_client = get_session("influxdb_connection")
        # Figure out all the time stamps.

        determine_networks_automatically = True
        networks_list = list()
        if len(networks):
            networks_list = [f'"{network}"' for network in networks]
            determine_networks_automatically = False
        asset_ids = dict()

        logger.debug("finding all IDs from assets")
        query = 'SHOW TAG VALUES WITH KEY="assetId"'
        result = influxdb_client.query(query)
        if result:
            for key in list(result.keys()):
                # Create list of networks
                if determine_networks_automatically:
                    networks_list.append(f'"{key[0]}"')

                # Create list of assetIds per network
                asset_list = list()
                for kv in result[key]:
                    asset_list.append(kv["value"])
                asset_ids[key[0]] = asset_list

        set_session("timedimension-networks-list", networks_list)
        set_session("timedimension-asset-ids", asset_ids)

        logger.debug("calculating min/max per carrier")
        allocation_boundaries = dict()
        simulation_parameter = get_session("timedimension-parameter")
        query = "SELECT MIN({}), MAX({}) FROM {}".format(
            simulation_parameter, simulation_parameter, ",".join(networks_list)
        )
        logger.debug(f"query: {query}")
        result = allocation_energy = influxdb_client.query(query)
        if result:
            for key in list(allocation_energy.keys()):
                series = allocation_energy[key]
                for item in series:
                    allocation_boundaries[key] = (item["min"], item["max"])

            logger.debug(allocation_boundaries)

        set_session("timedimension-allocation-boundaries", allocation_boundaries)

    def get_colors(self):
        active_es_id = get_session("active_es_id_animation")
        pm = get_project_manager()
        colors = dict()
        color_index = 0

        es = pm.get_active_energy_system()
        esi = es.energySystemInformation
        if esi:
            carriers = esi.carriers
            if carriers:
                for c in carriers.carrier:
                    if active_es_id + c.id in self.mapeditor_colors:
                        colors[active_es_id + c.id] = self.mapeditor_colors[active_es_id + c.id]
                    else:
                        colors[active_es_id + c.id] = {
                            "es_id": active_es_id,
                            "carrier_id": c.id,
                            "color": default_colors[color_index],
                        }
                    color_index += 1

        return colors

    def generate_timed_geojson_for_line(
        self, coordinates, time, load, allocationEnergy, id, unit, color, min_en, max_en
    ):
        my_feature = Feature(geometry=MultiLineString(coordinates))
        my_feature["properties"]["id"] = id
        my_feature["properties"]["unit"] = unit
        my_feature["properties"]["time"] = time
        my_feature["properties"]["load"] = allocationEnergy
        my_feature["properties"]["stroke"] = color
        if allocationEnergy < 0:
            val = 10 * fabs(allocationEnergy / min_en) + 3
            my_feature["properties"]["pos"] = False
        else:
            val = 10 * allocationEnergy / max_en + 3
            my_feature["properties"]["pos"] = True

        # val = 10*((fabs(allocationEnergy)  - min_en)/(max_en - min_en)) + 3
        my_feature["properties"]["strokeWidth"] = val
        return my_feature

    # This function retrieves all timestamps for a measurement.
    def get_all_times_from_simulation(self):
        networks_list = get_session("timedimension-networks-list")
        simulation_id = get_session("timedimension-simulation-id")
        try:
            influxdb_client = get_session("influxdb_connection")
            query = "SELECT * FROM " + ",".join(networks_list)
            if simulation_id:
                query += ' WHERE "simulationRun" = \'' + simulation_id + "'"
            sim_results = influxdb_client.query(query)

            time_list = list()

            if sim_results:
                feature_list = []
                for key in list(sim_results.keys()):
                    series = sim_results[key]
                    fid = 1
                    for item in series:
                        time_list.append(item["time"])

            # Keep only unique time values.
            time_list = list(dict.fromkeys(time_list))
            return time_list

        except Exception as e:
            logger.error("error with query: ", str(e))

    def get_windowed_simulation_data(self, start, end):
        simulation_id = get_session("timedimension-simulation-id")

        # Functie get_windowed_simulation_data doet niets met self.time_list, dus denk niet dat aanroep hier nodig is?
        # self.get_all_times_from_simulation()

        logger.debug("--- Retrieving Simulation Data ---")
        influxdb_client = get_session("influxdb_connection")
        # active_simulation = get_session('active_simulation')
        active_es_id = get_session("active_es_id_animation")

        sdt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%f%z")
        edt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%f%z")
        influxdb_startdate = sdt.strftime("%Y-%m-%dT%H:%M:%SZ")
        influxdb_enddate = edt.strftime("%Y-%m-%dT%H:%M:%SZ")

        pm = get_project_manager()
        monitor_asset_ids = get_session("td_monitor_ids")
        networks_list = get_session("timedimension-networks-list")

        monitor_data = dict()
        logger.debug(monitor_asset_ids)
        if monitor_asset_ids:
            start_cet = sdt.astimezone(pytz.timezone("Europe/Amsterdam"))
            date_cet = start_cet.strftime("%Y-%m-%d")
            monitor_asset_data = dict()
            for aid in monitor_asset_ids:
                try:
                    asset = pm.get_by_id(active_es_id, aid)
                except:
                    logger.warning("(Monitor) Asset id not found.")
                    continue
                asset_name = asset.name + " - " + date_cet

                monitor_asset_data[aid] = {"name": asset_name, "data_x": list(), "data_y": list()}
            monitor_data = {"time": date_cet, "data": monitor_asset_data}

        sim_results = None
        try:
            # if start and end date are the same, it means that we have reached the end of the time series.
            # But this also means that we miss exactly the final entry, so handle this here.
            if influxdb_startdate == influxdb_enddate:
                influxdb_enddate = datetime.strptime(influxdb_enddate, "%Y-%m-%dT%H:%M:%SZ")
                influxdb_enddate = influxdb_enddate + timedelta(days=1)
                influxdb_enddate = influxdb_enddate.strftime("%Y-%m-%dT%H:%M:%SZ")

            query = (
                "SELECT * FROM "
                + ",".join(networks_list)
                + " WHERE (time >= '"
                + influxdb_startdate
                + "' AND time <= '"
                + influxdb_enddate
                + "'"
            )
            if simulation_id:
                query += ' AND "simulationRun" = \'' + simulation_id + "'"
            query += ")"

            sim_results = influxdb_client.query(query)
        except Exception as e:
            logger.error("error with query: ", str(e))

        simulation_parameter = get_session("timedimension-parameter")
        allocation_boundaries = get_session("timedimension-allocation-boundaries")
        colors = get_session("timedimension-colors")

        feature_collection_json_string = "{}"
        if sim_results:
            feature_list = []
            for key in list(sim_results.keys()):
                series = sim_results[key]
                fid = 1
                for item in series:
                    try:
                        if not item["assetId"]:
                            continue
                        current_asset = pm.get_by_id(active_es_id, item["assetId"])
                    except:
                        logger.warning("Asset id not found.")
                        continue

                    if not isinstance(current_asset, esdl.Pipe) and not isinstance(
                        current_asset, esdl.ElectricityCable
                    ):
                        logger.debug(f"Asset type for: '{current_asset}' not animated.")
                        continue

                    coordinates_segments = []
                    point_items = current_asset.geometry.point.items
                    for i_segment in range(len(point_items) - 1):
                        coordinates_segments.append(
                            [
                                [
                                    (point_items[i_segment].lon, point_items[i_segment].lat),
                                    (point_items[i_segment + 1].lon, point_items[i_segment + 1].lat),
                                ]
                            ]
                        )

                    if "carrierId" in item:  # for essim
                        color = colors[active_es_id + item["carrierId"]]["color"]
                    else:
                        color = colors[active_es_id + key[0]]["color"]

                    profile = Profiles.get_profile_of_asset_with_field(current_asset, simulation_parameter)
                    if profile and profile.profileQuantityAndUnit:
                        qau = profile.profileQuantityAndUnit
                        if isinstance(qau, esdl.QuantityAndUnitReference):
                            qau = qau.reference
                        unit = unit_to_string(qau)
                    else:
                        unit = ""

                    if abs(item[simulation_parameter]) > 1e-2:
                        for coordinates in coordinates_segments:
                            feature_list.append(
                                self.generate_timed_geojson_for_line(
                                    coordinates,
                                    item["time"],
                                    0.5,
                                    item[simulation_parameter],
                                    item["assetId"],
                                    unit,
                                    color,
                                    allocation_boundaries[key][0],
                                    allocation_boundaries[key][1],
                                )
                            )
                            fid += 1
                    if "data" in monitor_data and item["assetId"] in monitor_data["data"]:
                        monitor_data["data"][item["assetId"]]["data_x"].append(item["time"].split("T")[1].strip("Z"))
                        monitor_data["data"][item["assetId"]]["data_y"].append(item[simulation_parameter])

            logger.info("Number of features result from get_windowed_simulation_data: " + str(len(feature_list)))

            feature_collection = FeatureCollection(feature_list)
            feature_collection_json_string = dumps(feature_collection)
        else:
            logger.warn("query yielded no results")

        if monitor_asset_ids:
            # logger.debug(monitor_data)
            emit("td_monitor_asset_data", monitor_data)

        return feature_collection_json_string
