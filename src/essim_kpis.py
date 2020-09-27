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
from extensions.session_manager import get_handler, get_session
import src.settings as settings
from influxdb import InfluxDBClient
from datetime import datetime
import src.log as log

logger = log.get_logger(__name__)


class ESSIM_KPIs:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering ESSIM KPIs extension')

        @self.socketio.on('calculate_load_duration_curve', namespace='/esdl')
        def calculate_ldc(asset_id):
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                asset = esh.get_by_id(active_es_id, asset_id)

                self.calculate_load_duration_curve(asset_id, asset.name)

    def send_alert(self, msg):
        logger.warn(msg)
        self.socketio.emit('alert', msg, namespace='/esdl')

    def init_simulation(self, es=None, simulationRun=None, start_date=None, end_date=None):
        # TODO: This does not work with multiple concurrent users (es, simulationRun, scenario_id, start_date, and so on)
        self.kpis_results = {}
        self.carrier_list = []
        self.es = es
        self.simulationRun = simulationRun
        self.scenario_id = es.id
        self.config = self.init_config()
        self.database_client = None
        self.start_date = start_date
        self.end_date = end_date
        self.transport_networks = []

        self.connect_to_database()

    def init_config(self):
        return settings.essim_config

    def set_es(self, es=None, simulationRun=None):
        self.es = es
        self.scenario_id = es.id
        self.simulationRun = simulationRun

    def connect_to_database(self):
        self.database_client = InfluxDBClient(host=self.config['ESSIM_database_server'],
                                              port=self.config['ESSIM_database_port'], database=self.scenario_id)

    def calculate_load_duration_curve(self, asset_id, asset_name):
        logger.debug("--- calculate_load_duration_curve ---")

        active_simulation = get_session('active_simulation')
        if active_simulation:
            active_es_id = get_session('active_es_id')
            esh = get_handler()
            es = esh.get_energy_system(active_es_id)
            sdt = datetime.strptime(active_simulation['startDate'], '%Y-%m-%dT%H:%M:%S%z')
            edt = datetime.strptime(active_simulation['endDate'], '%Y-%m-%dT%H:%M:%S%z')
            influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
            influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')

            sim_id = active_simulation['sim_id']
            asset = esh.get_by_id(active_es_id, asset_id)
            power = None
            if hasattr(asset, 'power'):
                power = asset.power
            elif hasattr(asset, 'capacity'):
                power = asset.capacity
            power_pos = None
            power_neg = None

            allocation_energy = None
            try:
                query = 'SELECT "allocationEnergy" FROM /' + es.name + '.*/ WHERE (time >= \'' + influxdb_startdate + '\' AND time < \'' + influxdb_enddate + '\' AND "simulationRun" = \'' + sim_id + '\' AND "assetId" = \''+asset_id+'\')'
                logger.debug(query)
                allocation_energy = self.database_client.query(query)
            except Exception as e:
                logger.error('error with query: ', str(e))

            if allocation_energy:
                # logger.debug(allocation_energy)
                first_key = list(allocation_energy.keys())[0]
                series = allocation_energy[first_key]

                ldc_series = []
                for item in series:
                    ldc_series.append(item['allocationEnergy'])
                ldc_series.sort(reverse=True)

                ldc_series_decimate = []
                for idx, item in enumerate(ldc_series):
                    if idx % 40 == 0:
                        ldc_series_decimate.append(item / 3600)
                        if item > 0:
                            power_pos = power
                        if item < 0:
                            power_neg = -power

                # logger.debug(ldc_series_decimate)
                emit('ldc-data', {'asset_name': asset_name, 'ldc_series': ldc_series_decimate, 'power_pos': power_pos, 'power_neg': power_neg})

            else:
                logger.warn('query returned no results')
        else:
            self.send_alert('No active simulation')