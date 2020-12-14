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
from dateutil import rrule
from influxdb import InfluxDBClient
from geojson import Feature, MultiLineString, FeatureCollection, dumps
from math import fabs
import pytz

from extensions.session_manager import get_handler, get_session, set_session
from extensions.settings_storage import SettingsStorage
from extensions.mapeditor_settings import MapEditorSettings, MAPEDITOR_UI_SETTINGS

import src.settings as settings
import src.log as log

logger = log.get_logger(__name__)

TIME_DIMENSION_SYSTEM_CONFIG = 'TIME_DIMENSION_SYSTEM_CONFIG'
TIME_DIMENSION_USER_CONFIG = 'TIME_DIMENSION_SERVICE_USER_CONFIG'

default_colors = ['#0000ff', '#ff0000', '#00ff00', '#800080', '#ffa500', '#e31a1c',
                  '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']

# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    logger.warn(message)
    emit('alert', message, namespace='/esdl')


# ---------------------------------------------------------------------------------------------------------------------
#  TimeDimension
# ---------------------------------------------------------------------------------------------------------------------
class TimeDimension:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage, me_settings: MapEditorSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.register()
        self.config = self.init_config()
        self.mapeditor_colors = self.get_colors_from_settings(me_settings)
        # self.allocation_boundaries = {}       # stored in user session now
        # self.asset_ids = dict()               # stored in user session now
        # self.networks = list()                # stored in user session now

        # these four are not used at all
        # self.simulation_result_keys = None             # To store the simulation data keys
        # self.preloaded_simulation_data = dict()        # To store the simulation data in a dict (networks) of dicts (times)
        # self.start_dt = None
        # self.stop_dt = None

        # TODO: Hardcoded parameters, change later.
        # self.scenario_id = "opera_results"                # stored in user session now
        # self.simulation_parameter = "allocationEnergy"    # stored in user session now
        # Store all the time stamps in this list.
        # self.time_list = []                               # stored in user session now

    def init_config(self):
        return settings.essim_config

    def get_colors_from_settings(self, me_settings):
        me_ui_setting = me_settings.get_system_setting(MAPEDITOR_UI_SETTINGS)
        if me_ui_setting:
            if 'carrier_colors' in me_ui_setting:
                return me_ui_setting['carrier_colors']
        return None

    # Do we want system_settings here, e.g. for the service endpoint configuration?
    def get_settings(self):
        if self.settings_storage.has_system(TIME_DIMENSION_SYSTEM_CONFIG):
            return self.settings_storage.get_system(TIME_DIMENSION_SYSTEM_CONFIG)
        else:
            time_dimension_plugin_settings = {
            }
            self.settings_storage.set_system(TIME_DIMENSION_SYSTEM_CONFIG, time_dimension_plugin_settings)
            return time_dimension_plugin_settings

    def register(self):
        logger.info('Registering Time Dimension extension')

        @self.socketio.on('get_windowed_simulation_data', namespace='/esdl')
        def get_windowed_simulation_data(start, end):
            with self.flask_app.app_context():
                return self.get_windowed_simulation_data(start, end)

        # @self.socketio.on('get_simulation_data', namespace='/esdl')
        # def get_simulation_data(dt_str):
        #     return self.get_simulation_data(dt_str)

        @self.socketio.on('timedimension_initialize', namespace='/esdl')
        def timedimension_initialize(info):
            """"
            This function is called when the user selects to use the TimeDimension functionality
            """
            with self.flask_app.app_context():
                database = info["database"]
                simulation_id = info["simulation_id"]
                networks = info["networks"]

                set_session('timedimension-database', database)
                set_session('timedimension-simulation-id', simulation_id)
                set_session('timedimension-parameter', 'allocationEnergy')  # To be decided if configurable

                set_session('ielgas_monitor_ids', [])

                self.preprocess_data(networks)
                time_list = self.get_all_times_from_simulation()

                timedimension_colors = self.get_colors()
                set_session('timedimension-colors', timedimension_colors)

                # self.preload_simulation_data()
                # Return list of times.
                #return True
                return time_list

        @self.socketio.on('timedimension_get_asset_ids', namespace='/esdl')
        def timedimension_get_asset_ids():
            with self.flask_app.app_context():
                return get_session('timedimension-asset-ids')

    def connect_to_database(self):
        database = get_session('timedimension-database')
        return InfluxDBClient(host=self.config['ESSIM_database_server'],
                                              port=self.config['ESSIM_database_port'], database=database)

    def preprocess_data(self, networks):
        influxdb_client = self.connect_to_database()
        # Figure out all the time stamps.

        determine_networks_automatically = True
        networks_list = list()
        if len(networks):
            networks_list = networks
            determine_networks_automatically = False
        asset_ids = dict()

        logger.debug("finding all IDs from assets")
        query = "SHOW TAG VALUES WITH KEY=\"assetId\""
        result = influxdb_client.query(query)
        if result:
            for key in list(result.keys()):
                # Create list of networks
                if determine_networks_automatically:
                    networks_list.append(key[0])

                # Create list of assetIds per network
                asset_list = list()
                for kv in result[key]:
                    asset_list.append(kv["value"])
                asset_ids[key[0]] = asset_list

        set_session('timedimension-networks-list', networks_list)
        set_session('timedimension-asset-ids', asset_ids)

        logger.debug("calculating min/max per carrier")
        allocation_boundaries = dict()
        simulation_parameter = get_session('timedimension-parameter')
        query = "SELECT MIN({}), MAX({}) FROM {}".format(simulation_parameter, simulation_parameter, ",".join(networks_list))
        result = allocation_energy = influxdb_client.query(query)
        if result:
            for key in list(allocation_energy.keys()):
                series = allocation_energy[key]
                for item in series:
                    allocation_boundaries[key] = (item['min'], item['max'])

            logger.debug(allocation_boundaries)

        set_session('timedimension-allocation-boundaries', allocation_boundaries)

    def get_colors(self):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        colors = dict()
        num_default_colors = 0

        es = esh.get_energy_system(active_es_id)
        esi = es.energySystemInformation
        if esi:
            carriers = esi.carriers
            if carriers:
                for c in carriers.carrier:
                    if active_es_id+c.id in self.mapeditor_colors:
                        colors[active_es_id+c.id] = self.mapeditor_colors[active_es_id+c.id]
                    else:
                        colors[active_es_id+c.id] = {
                            "es_id": active_es_id,
                            "carrier_id": c.id,
                            "color": default_colors[num_default_colors]
                        }
                        num_default_colors += 1

        return colors

    def generate_timed_geojson_for_line(self, coordinates, time, load, allocationEnergy, id, color, min_en, max_en):
        my_feature = Feature(geometry=MultiLineString(coordinates))
        my_feature['properties']['id'] = id
        my_feature['properties']['time'] = time
        my_feature['properties']['load'] = allocationEnergy
        my_feature['properties']['stroke'] = color
        if allocationEnergy < 0:
            val = 10*fabs(allocationEnergy/min_en) + 3
            my_feature['properties']['pos'] = False
        else:
            val = 10*allocationEnergy/max_en + 3
            my_feature['properties']['pos'] = True

        # val = 10*((fabs(allocationEnergy)  - min_en)/(max_en - min_en)) + 3
        my_feature['properties']['strokeWidth'] = val
        return my_feature

    # This function retrieves all timestamps for a measurement.
    def get_all_times_from_simulation(self):
        networks_list = get_session('timedimension-networks-list')
        simulation_id = get_session('timedimension-simulation-id')
        try:
            influxdb_client = self.connect_to_database()
            query = 'SELECT * FROM ' + ",".join(networks_list) + ' WHERE "simulationRun" = \'' + simulation_id + '\''
            sim_results = influxdb_client.query(query)

            time_list = list()

            if sim_results:
                feature_list = []
                for key in list(sim_results.keys()):
                    series = sim_results[key]
                    fid = 1
                    for item in series:
                        time_list.append(item['time'])

            # Keep only unique time values.
            time_list = list(dict.fromkeys(time_list))
            return time_list

        except Exception as e:
            logger.error('error with query: ', str(e))

    def get_windowed_simulation_data(self, start, end):
        simulation_id = get_session('timedimension-simulation-id')

        # Functie get_windowed_simulation_data doet niets met self.time_list, dus denk niet dat aanroep hier nodig is?
        # self.get_all_times_from_simulation()

        logger.debug("--- Retrieving Simulation Data ---")
        influxdb_client = self.connect_to_database()
        # active_simulation = get_session('active_simulation')
        active_es_id = get_session('active_es_id')
        # active_es_id = "ea50089c-0404-4048-97b8-94f0b0aa866b"

        sdt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S.%f%z')
        edt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S.%f%z')
        influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
        influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')

        esh = get_handler()
        monitor_asset_ids = get_session('ielgas_monitor_ids')
        networks_list = get_session('timedimension-networks-list')

        monitor_data = dict()
        logger.debug(monitor_asset_ids)
        if monitor_asset_ids:
            start_cet = sdt.astimezone(pytz.timezone("Europe/Amsterdam"))
            date_cet = start_cet.strftime('%Y-%m-%d')
            monitor_asset_data = dict()
            for aid in monitor_asset_ids:
                asset = esh.get_by_id(active_es_id, aid)
                asset_name = asset.name + ' - ' + date_cet

                monitor_asset_data[aid] = {
                    'name': asset_name,
                    'data_x': list(),
                    'data_y': list()
                }
            monitor_data = {
                'time': date_cet,
                'data': monitor_asset_data
            }

        sim_results = None
        try:
            # if start and end date are the same, it means that we have reached the end of the time series.
            # But this also eans that we miss exactly the final entry, so handle this here.
            if influxdb_startdate == influxdb_enddate:
                influxdb_enddate = datetime.strptime(influxdb_enddate, '%Y-%m-%dT%H:%M:%SZ')
                influxdb_enddate = influxdb_enddate + timedelta(days=1)
                influxdb_enddate = influxdb_enddate.strftime('%Y-%m-%dT%H:%M:%SZ')
            query = 'SELECT * FROM '+ ",".join(networks_list) +\
                    ' WHERE (time >= \'' + influxdb_startdate + '\' AND time <= \'' + influxdb_enddate + '\'' +\
                    ' AND "simulationRun" = \'' + simulation_id + '\')'
            sim_results = influxdb_client.query(query)
        except Exception as e:
            logger.error('error with query: ', str(e))

        simulation_parameter = get_session('timedimension-parameter')
        allocation_boundaries = get_session('timedimension-allocation-boundaries')
        colors = get_session('timedimension-colors')

        feature_collection_json_string = "{}"
        if sim_results:
            feature_list = []
            for key in list(sim_results.keys()):
                series = sim_results[key]
                fid = 1
                for item in series:
                    try:
                        current_asset = esh.get_by_id(active_es_id, item['assetId'])
                    except:
                        print("Asset id not found.")
                        continue
                    coordinates = [[(current_asset.geometry.point.items[0].lon, current_asset.geometry.point.items[0].lat),
                                    (current_asset.geometry.point.items[1].lon, current_asset.geometry.point.items[1].lat)]]

                    color = colors[active_es_id+item['carrierId']]['color']  # 32a852"
                    if item[simulation_parameter] > 1e-2:
                        feature_list.append(
                            self.generate_timed_geojson_for_line(coordinates, item['time'], 0.5,
                                                                 item[simulation_parameter], item['assetId'], color,
                                                                 allocation_boundaries[key][0], allocation_boundaries[key][1]))
                        fid += 1
                    if 'data' in monitor_data and item['assetId'] in monitor_data['data']:
                        monitor_data['data'][item['assetId']]['data_x'].append(item['time'].split('T')[1].strip('Z'))
                        monitor_data['data'][item['assetId']]['data_y'].append(item[simulation_parameter])

            logger.debug('Number of features result from get_windowed_simulation_data: ' + str(len(feature_list)))

            feature_collection = FeatureCollection(feature_list)
            feature_collection_json_string = dumps(feature_collection)
        else:
            logger.warn('query yielded no results')

        if monitor_asset_ids:
            # logger.debug(monitor_data)
            emit('ielgas_monitor_asset_data', monitor_data)

        return feature_collection_json_string

