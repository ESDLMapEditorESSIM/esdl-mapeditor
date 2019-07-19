from esdl import esdl
from esdl.processing import ESDLAsset
from essim_config import essim_config
from influxdb import DataFrameClient
from influxdb import InfluxDBClient
import pandas as pd
import numpy as np
import requests
import json

pd.set_option('display.max_rows', 16)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def send_alert(msg):
    print(msg)


class ESSIM_KPIs:

    def __init__(self, es=None, simulationRun=None, start_date=None, end_date=None):
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
        return essim_config

    def set_es(self, es=None, simulationRun=None):
        self.es = es
        self.scenario_id = es.id
        self.simulationRun = simulationRun

    def connect_to_database(self):
        self.database_client = DataFrameClient(host=self.config['ESSIM_database_server'],
                                               port=self.config['ESSIM_database_port'], database=self.scenario_id)
        # self.database_client = InfluxDBClient(host=self.config['ESSIM_database_server'], port=self.config['ESSIM_database_port'], database=self.scenario_id)

    def calculate_kpis(self):
        self.transport_networks = self.get_transport_networks()

        results = []
        # results.extend(self.calculate_total_energy_per_carrier())
        # self.get_total_production_consumption()   #TEST

        # self.get_total_production_per_carrier()
        # self.get_total_consumption_per_carrier()

        self.test_idb_client()

        return results

    def get_total_production_per_carrier(self):
        print("--- get_total_production_per_carrier ---")
        try:
            query = 'SELECT sum("allocationEnergy") FROM /' + self.es.name + '.*/ WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'' + self.simulationRun + '\' AND "assetType" = \'Producer\') GROUP BY fuelType'
            print(query)
            df_dict = self.database_client.query(query)
            print(df_dict)
        except Exception as e:
            print('error with query: ', str(e))

    def get_total_consumption_per_carrier(self):
        print("--- get_total_consumption_per_carrier ---")
        try:
            # query = 'SELECT sum("allocationEnergy") FROM /' + self.es.name + '.*/ WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'' + self.simulationRun + '\' AND "assetType" = \'Consumer\') GROUP BY fuelType'
            query = 'SELECT sum("allocationEnergy") FROM "Ameland 2015 Electricity Network 0" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'' + self.simulationRun + '\' AND "assetType" = \'Consumer\') GROUP BY fuelType'
            print(query)
            df_dict = self.database_client.query(query)
            # print(df_dict)

            for tn, res in df_dict.items():
                print("key: ", tn)
                print("------")
                print(res)

        except Exception as e:
            print('error with query: ', str(e))

    def calculate_total_energy_per_carrier(self):
        if not self.es:
            return

        results = []

        self.carrier_list = ESDLAsset.get_carrier_list(self.es)

        for car in self.carrier_list:
            car_name = car['name']
            car_id = car['id']

            results.append({'name': car_name, 'value': 10.4})

            self.get_data_from_influxdb(car)

        self.get_wadkabel_day_profile()  # TEST
        self.get_total_production_consumption()

        return results

    def get_data_from_influxdb(self, carrier):
        print("--- get_data_from_influxdb ---")
        measurement = self.es.name + ' ' + carrier['name'] + ' Network 0'

        try:
            query = 'SELECT sum(allocationEnergy) FROM "' + measurement + '" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + \
                    '\' AND simulationRun = \'' + self.simulationRun + '\')'

            # query = 'SELECT sum(allocationEnergy) FROM "Ameland 2015 Electricity Network 0" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND simulationRun = \'5d109d8afc4c767a42657048\' AND id = \'ElectricityCable_d72ce913-9914-4df0-b6b7-4369aad3228f\') GROUP BY time(1d), "type"'
            # query = 'SELECT sum(allocationEnergy) FROM "Ameland 2015 Electricity Network 0" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND simulationRun = \'5d109d8afc4c767a42657048\' AND id = \'ElectricityCable_d72ce913-9914-4df0-b6b7-4369aad3228f\') GROUP BY time(1d), type'
            print(query)
            df_dict = self.database_client.query(query)
            # print(df_dict)
            result = df_dict[measurement]
            # print(result.shape)
            print(result)
        except Exception as e:
            print('error with query: ', str(e))

    def get_total_production_consumption(self):
        print("--- get_total_production_consumption ---")
        try:
            query = 'SELECT sum("allocationEnergy") FROM /Ameland 2015.*/ WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'5d109d8afc4c767a42657048\' AND "assetType" = \'Producer\')'
            print(query)
            df_dict = self.database_client.query(query)
            print(df_dict)
            query = 'SELECT sum("allocationEnergy") FROM /Ameland 2015.*/ WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'5d109d8afc4c767a42657048\' AND "assetType" = \'Consumer\')'
            print(query)
            df_dict = self.database_client.query(query)
            print(df_dict)
        except Exception as e:
            print('error with query: ', str(e))

    def get_wadkabel_day_profile(self):
        print("--- get_wadkabel_day_profile ---")
        try:
            query = 'SELECT sum(allocationEnergy) FROM "Ameland 2015 Electricity Network 0" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND simulationRun = \'5d109d8afc4c767a42657048\' AND "name" = \'ElectricityCable_d72ce913-9914-4df0-b6b7-4369aad3228f\') GROUP BY time(1d)'
            # query = 'SELECT sum(allocationEnergy) FROM "Ameland 2015 Electricity Network 0" WHERE (simulationRun = \'5d109d8afc4c767a42657048\' AND id = \'ElectricityCable_d72ce913-9914-4df0-b6b7-4369aad3228f\') AND (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\') GROUP BY time(1d), type, fuelType, id'
            print(query)
            df_dict = self.database_client.query(query)
            print(df_dict)
        except Exception as e:
            print('error with query: ', str(e))

    def get_transport_networks(self):
        print("--- get_transport_networks ---")
        url = self.config['ESSIM_host'] + self.config['ESSIM_path'] + '/' + self.simulationRun + '/transport'
        print(url)

        headers = {
            'Content-Type': "application/json",
            'Accept': "application/json",
            'User-Agent': "ESDL Mapeditor/0.1"
            # 'Cache-Control': "no-cache",
            # 'Host': ESSIM_config['ESSIM_host'],
            # 'accept-encoding': "gzip, deflate",
            # 'Connection': "keep-alive",
            # 'cache-control': "no-cache"
        }

        names = []

        try:
            r = requests.get(url, headers=headers)
            # print(r)
            # print(r.content)
            if r.status_code == 200:
                result = json.loads(r.text)
                for netw in result:
                    names.append(netw['name'])
            else:
                send_alert('Error getting ESSIM list of transport networks - response ' + str(r.status_code)
                           + ' with reason: ' + str(r.reason))
                print(r)
                print(r.content)
                return []
        except Exception as e:
            print('Exception: ')
            print(e)
            send_alert('Error accessing ESSIM API at getting transport networks')
            return []

        return names

    def test_idb_client(self):
        print("--- get_total_consumption_per_carrier ---")
        try:
            query = 'SELECT sum("allocationEnergy") FROM /' + self.es.name + '.*/ WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'' + self.simulationRun + '\' AND "assetType" = \'Consumer\') GROUP BY fuelType'
            # query = 'SELECT sum("allocationEnergy") FROM "Ameland 2015 Electricity Network 0" WHERE (time >= \'' + self.start_date + '\' AND time < \'' + self.end_date + '\' AND "simulationRun" = \'' + self.simulationRun + '\' AND "assetType" = \'Consumer\') GROUP BY fuelType'
            print(query)
            rs = self.database_client.query(query)

            print(rs)

        except Exception as e:
            print('error with query: ', str(e))
