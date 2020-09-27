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

from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from flask_executor import Executor
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler, get_session, set_session, del_session
from src.essim_kpis import ESSIM_KPIs
import requests
import urllib
import json
import uuid
import base64
from datetime import datetime
import src.settings as settings
from src.process_es_area_bld import process_energy_system
import src.log as log

logger = log.get_logger(__name__)


ESSIM_SIMULATION_LIST = 'ESSIM_simulations'
ESSIM_FAVORITES_LIST = 'ESSIM_favorites'


def send_alert(message):
    print(message)
    # emit('alert', message, namespace='/esdl')


class ESSIM:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, essim_kpis: ESSIM_KPIs, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.executor = executor
        self.essim_kpis = essim_kpis

        self.register()

    def register(self):
        logger.info("Registering ESSIM extension")

        @self.socketio.on('essim_set_simulation_id', namespace='/esdl')
        def set_simulation_id(sim_id):
            with self.flask_app.app_context():
                esh = get_handler()

                print('Set ESSIM simulationRun ID: '+sim_id)
                set_session('simulationRun', sim_id)
                ESSIM_config = settings.essim_config
                url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/' + sim_id

                try:
                    r = requests.get(url)
                    if r.status_code == 200:
                        result = json.loads(r.text)
                        active_simulation = {
                            'sim_id': sim_id,
                            'scenarioID': result['scenarioID'],
                            'simulationDescription': result['simulationDescription'],
                            'startDate': result['startDate'],
                            'endDate': result['endDate'],
                            'dashboardURL': result['dashboardURL']
                        }
                        set_session('active_simulation', active_simulation)
                        esdlstr_base64 = result['esdlContents']
                        esdlstr_base64_bytes = esdlstr_base64.encode('ascii')
                        esdlstr_bytes = base64.decodebytes(esdlstr_base64_bytes)
                        esdlstr = esdlstr_bytes.decode('ascii')

                        res_es = esh.add_from_string(name=str(uuid.uuid4()), esdl_string=esdlstr)
                        set_session('active_es_id', res_es.id)

                        sdt = datetime.strptime(result['startDate'], '%Y-%m-%dT%H:%M:%S%z')
                        edt = datetime.strptime(result['endDate'], '%Y-%m-%dT%H:%M:%S%z')
                        influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
                        influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')

                        # Call init_simulation to enable the loadflow calculations
                        self.essim_kpis.init_simulation(res_es, sim_id, influxdb_startdate, influxdb_enddate)
                        self.executor.submit(process_energy_system, esh, 'test')  # run in seperate thread

                except Exception as e:
                    # print('Exception: ')
                    # print(e)
                    send_alert('Error accessing ESSIM API: ' + str(e))

        @self.flask_app.route('/simulation_progress')
        def get_simulation_progress():
            with self.flask_app.app_context():
                es_simid = get_session('es_simid')
                user_email = get_session('user-email')
                # print(es_simid)
                if es_simid:
                    active_simulation = get_session('active_simulation')

                    ESSIM_config = settings.essim_config
                    if active_simulation['essim_loadflow']:
                        url = ESSIM_config['ESSIM_host_loadflow'] + ESSIM_config['ESSIM_path'] + '/' + es_simid
                    else:
                        url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/' + es_simid

                    try:
                        r = requests.get(url + '/status')
                        if r.status_code == 200:
                            result = json.loads(r.text)
                            status = result["status"]
                            if "moreInfo" in result:
                                more_info = result["moreInfo"]
                            else:
                                more_info = ""

                            if status == -1:
                                descr = result["description"]
                                return (jsonify(
                                    {'percentage': '-1', 'url': '', 'simulationRun': es_simid, 'description': descr, 'moreInfo': more_info})), 200

                            if float(status) >= 1:
                                r = requests.get(url)
                                if r.status_code == 200:
                                    # del_session('es_simid')  # simulation ready
                                    result = json.loads(r.text)
                                    dashboardURL = result['dashboardURL']

                                    # Update the stored simulation with the dashboard URL
                                    active_simulation = get_session('active_simulation')
                                    active_simulation['dashboardURL'] = dashboardURL
                                    set_session('simulationRun', es_simid)
                                    self.update_stored_simulation(user_email, es_simid, 'dashboard_url', dashboardURL)

                                    # Initialize the essim kpi class instance, to be able to show load duration curves
                                    esh = get_handler()
                                    active_es_id = get_session('active_es_id')
                                    current_es = esh.get_energy_system(es_id=active_es_id)
                                    sdt = datetime.strptime(active_simulation['startDate'], '%Y-%m-%dT%H:%M:%S%z')
                                    edt = datetime.strptime(active_simulation['endDate'], '%Y-%m-%dT%H:%M:%S%z')
                                    influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
                                    influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')
                                    self.essim_kpis.init_simulation(current_es, es_simid, influxdb_startdate, influxdb_enddate)

                                    return (jsonify(
                                        {'percentage': '1', 'url': dashboardURL, 'simulationRun': es_simid})), 200
                                else:
                                    send_alert('Error in getting the ESSIM dashboard URL')
                                    abort(r.status_code, 'Error in getting the ESSIM dashboard URL')
                            else:
                                return (jsonify({'percentage': status, 'url': '', 'simulationRun': es_simid})), 200
                        else:
                            # print('code: ', r.status_code)
                            send_alert('Error in getting the ESSIM progress status')
                            abort(r.status_code, 'Error in getting the ESSIM progress status')
                    except Exception as e:
                        # print('Exception: ')
                        # print(e)
                        send_alert('Error accessing ESSIM API: ' + str(e))
                        abort(500, 'Error accessing ESSIM API: ' + str(e))
                else:
                    print("ERROR: Querying simulation progress - No es_simid in session")
                    print(session)
                    abort(500, 'Simulation not running')

        @self.flask_app.route('/favorites_list')
        def get_favorites_list():
            return self.retrieve_sim_fav_list(essim_list=ESSIM_FAVORITES_LIST)

        @self.flask_app.route('/simulations_list')
        def get_simulations_list():
            return self.retrieve_sim_fav_list()

        @self.flask_app.route('/<sim_fav>/<sim_id>', methods=["DELETE"])
        def delete_simulation(sim_fav, sim_id):
            if sim_fav == 'simulation' or sim_fav == 'favorite':
                if sim_fav == 'simulation': essim_list = ESSIM_SIMULATION_LIST
                if sim_fav == 'favorite': essim_list = ESSIM_FAVORITES_LIST

                with self.flask_app.app_context():
                    user_email = get_session('user-email')
                    sim_list = []
                    if user_email is not None:
                        if self.settings_storage.has_user(user_email, essim_list):
                            sim_list = self.settings_storage.get_user(user_email, essim_list)

                            for sim in list(sim_list):
                                if sim['simulation_id'] == sim_id:
                                    sim_list.remove(sim)

                            self.settings_storage.set_user(user_email, essim_list, sim_list)
                            print(sim_list)

                    return json.dumps(sim_list)
            else:
                return "Unknown operation", 404

        @self.flask_app.route('/simulation/<sim_id>/make_favorite')
        def make_simulation_favorite(sim_id):
            with self.flask_app.app_context():
                user_email = get_session('user-email')
                last_list = []
                fav_list = []
                if user_email is not None:
                    if self.settings_storage.has_user(user_email, ESSIM_SIMULATION_LIST):
                        last_list = self.settings_storage.get_user(user_email, ESSIM_SIMULATION_LIST)

                    if self.settings_storage.has_user(user_email, ESSIM_FAVORITES_LIST):
                        fav_list = self.settings_storage.get_user(user_email, ESSIM_FAVORITES_LIST)

                    for sim in list(last_list):
                        if sim['simulation_id'] == sim_id:
                            fav_list.insert(0, sim)
                            last_list.remove(sim)

                    print(fav_list)

                    self.settings_storage.set_user(user_email, ESSIM_SIMULATION_LIST, last_list)
                    self.settings_storage.set_user(user_email, ESSIM_FAVORITES_LIST, fav_list)

                return json.dumps({'simulations': last_list, 'favorites': fav_list})

        @self.flask_app.route('/essim_kpis')
        def essim_kpi_list():
            ESSIM_config = settings.essim_config
            url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/kpiModules'

            try:
                r = requests.get(url)
                if r.status_code == 200:
                    result = json.loads(r.text)

                    # only communicate unique KPI-modules (because they are deployed multiple times)
                    kpi_list = []
                    already_added_kpi_modules = []
                    for kpi in result:
                        if not kpi["calculator_id"] in already_added_kpi_modules:
                            kpi_list.append({
                                "id": kpi["calculator_id"],
                                "name": kpi["title"],
                                "descr": kpi["description"]
                            })
                            already_added_kpi_modules.append(kpi["calculator_id"])

                    # store kpi_list in session, in order to look up name/descr in a later stage
                    set_session('kpi_list', kpi_list)
                    return json.dumps(kpi_list), 200
                else:
                    send_alert('Error in getting the ESSIM KPI list')
                    abort(r.status_code, 'Error in getting the ESSIM KPI list')
            except Exception as e:
                send_alert('Error accessing ESSIM API: ' + str(e))
                abort(500, 'Error accessing ESSIM API: ' + str(e))

        @self.flask_app.route('/essim_kpi_results')
        def essim_kpi_results():
            with self.flask_app.app_context():
                es_simid = get_session('es_simid')
                print('Querying ESSIM KPI results for sim_id: ' + es_simid)
                if es_simid:
                    ESSIM_config = settings.essim_config
                    url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/' + es_simid + '/kpi'

                    try:
                        r = requests.get(url)
                        if r.status_code == 200:
                            result = json.loads(r.text)

                            # print("result from ESSIM:")
                            # print(result)
                            if result is None:
                                print("Error: No results from ESSIM KPI querying")
                                return [], 200
                            else:
                                kpi_result_list = self.process_kpi_results(result)
                                return json.dumps(kpi_result_list), 200
                        else:
                            send_alert('Error in getting the ESSIM KPI results')
                            abort(r.status_code, 'Error in getting the ESSIM KPI results')
                    except Exception as e:
                        send_alert('Error accessing ESSIM API: ' + str(e))
                        abort(500, 'Error accessing ESSIM API: ' + str(e))
                else:
                    print("ERROR: Querying KPI results - No es_simid in session")
                    print(session)
                    abort(500, 'Simulation not running')

        @self.socketio.on('kpi_visualization', namespace='/esdl')
        def kpi_visualization():
            with self.flask_app.app_context():
                kpi_result_list = get_session('kpi_result_list')
                self.emit_kpis_for_visualization(kpi_result_list)

        @self.socketio.on('show_previous_sim_kpis', namespace='/esdl')
        def show_previous_sim_kpis(info):
            sim_id = info['sim_id']
            sim_fav = info['sim_fav']
            with self.flask_app.app_context():
                # user_email = get_session('user-email')
                # self.update_stored_simulation(user_email, es_simid, 'kpis', kpi_result_list)
                if sim_fav == 'simulation' or sim_fav == 'favorite':
                    if sim_fav == 'simulation': essim_list = ESSIM_SIMULATION_LIST
                    if sim_fav == 'favorite': essim_list = ESSIM_FAVORITES_LIST

                    sim_fav_list = self.get_sim_fav_list(essim_list)
                    for sf in sim_fav_list:
                        if sf['simulation_id'] == sim_id:
                            kpi_result_list = sf['kpi_result_list']
                            self.emit_kpis_for_visualization(kpi_result_list)

    def retrieve_sim_fav_list(self, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            user_email = get_session('user-email')
            sim_list = self.get_sim_fav_list(essim_list)
            # print(sim_list)
            return json.dumps(sim_list)

    def get_sim_fav_list(self, essim_list=ESSIM_SIMULATION_LIST):
        user_email = get_session('user-email')
        sim_list = []
        if user_email is not None:
            if self.settings_storage.has_user(user_email, essim_list):
                sim_list = self.settings_storage.get_user(user_email, essim_list)

        return sim_list

    def store_simulation(self, user_email, simulation_id, simulation_datetime, simulation_descr, simulation_es_name=None, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            if user_email is not None:
                if self.settings_storage.has_user(user_email, essim_list):
                    sim_list = self.settings_storage.get_user(user_email, essim_list)
                else:
                    sim_list = []

                sim_list.insert(0, {
                    "simulation_id": simulation_id,
                    "simulation_datetime": simulation_datetime,
                    "simulation_descr": simulation_descr,
                    "simulation_es_name": simulation_es_name,
                    "dashboard_url": "",
                    "kpi_result_list": None
                })

                if sim_list.__len__ == 11:
                    sim_list.pop(10)
                # print(sim_list)
                self.settings_storage.set_user(user_email, essim_list, sim_list)

    def update_stored_simulation(self, user_email, simulation_id, param_name, param_value, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            if user_email is not None and self.settings_storage.has_user(user_email, essim_list):
                sim_list = self.settings_storage.get_user(user_email, essim_list)
                if sim_list[0]["simulation_id"] == simulation_id:
                    sim_list[0][param_name] = param_value
                # print(sim_list)
                self.settings_storage.set_user(user_email, essim_list, sim_list)

    def run_simulation(self, sim_description, sim_start_datetime, sim_end_datetime, essim_kpis, essim_loadflow):
        with self.flask_app.app_context():
            # Clear current active session information
            del_session('active_simulation')
            del_session('es_simid')

            esh = get_handler()
            active_es_id = get_session('active_es_id')
            user_email = get_session('user-email')
            user_fullname = get_session('user-fullname')
            if user_fullname is None:
                user_fullname = 'essim'

            current_es = esh.get_energy_system(es_id=active_es_id)
            current_es_name = current_es.name
            if current_es_name == "":
                current_es_name = "Untitled energysystem"
            esdlstr = esh.to_string(active_es_id)
            esdlstr_bytes = esdlstr.encode('ascii')
            esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
            esdlstr_base64 = esdlstr_base64_bytes.decode('ascii')

            ESSIM_config = settings.essim_config

            print("essim_loadflow: {}".format(essim_loadflow))
            if essim_loadflow:
                url = ESSIM_config['ESSIM_host_loadflow'] + ESSIM_config['ESSIM_path']
            else:
                url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path']
            # print('ESSIM url: ', url)

            payload = {
                'user': user_fullname.strip(),
                'scenarioID': active_es_id,
                'simulationDescription': sim_description,
                'startDate': sim_start_datetime,
                'endDate': sim_end_datetime,
                'influxURL': ESSIM_config['influxURL'],
                # 'grafanaURL': ESSIM_config['grafanaURL'],
                # 'esdlContents': urllib.parse.quote(esdlstr)
                'esdlContents': esdlstr_base64
            }

            if essim_kpis:
                kpi_module = {
                    # 'kafkaURL': ESSIM_config['kafka_url'],
                    'modules': []
                }
                # payload['kafkaURL'] = ESSIM_config['kafka_url']
                payload['natsURL'] = ESSIM_config['natsURL']

                # TODO: Fix hard-coded TimeResolution = hourly
                for kpi_id in essim_kpis:
                    kpi_module['modules'].append({
                        'id': kpi_id,
                        'config': {'TimeResolution': 'yearly'}
                        # 'config': [{'key': 'TimeResolution', 'value': 'hourly'}]
                    })
                payload['kpiModule'] = kpi_module

            # print(payload)

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

            try:
                r = requests.post(url, json=payload, headers=headers)
                # print(r)
                # print(r.content)
                if r.status_code == 201:
                    result = json.loads(r.text)
                    sim_id = result['id']
                    set_session('es_simid', sim_id)
                    print("ESSIM started, sim_id: " + sim_id)

                    self.store_simulation(user_email, sim_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sim_description, current_es_name)
                    # emit('', {})

                    active_simulation = {
                        'sim_id': sim_id,
                        'scenarioID': active_es_id,
                        'simulationDescription': sim_description,
                        'startDate': sim_start_datetime,
                        'endDate': sim_end_datetime,
                        'dashboardURL': '',
                        'kpi_result_list': None,
                        'essim_loadflow': essim_loadflow
                    }
                    set_session('active_simulation', active_simulation)
                else:
                    send_alert(
                        'Error starting ESSIM simulation - response ' + str(r.status_code) + ' with reason: ' + str(
                            r.reason))
                    print('Error starting ESSIM simulation - response ' + str(r.status_code) + ' with reason: ' + str(
                            r.reason))
                    print(r.content)
                    # emit('', {})
                    return 0
            except Exception as e:
                print('Error accessing ESSIM API at starting: ' + str(e))
                send_alert('Error accessing ESSIM API at starting: ' + str(e))
                return 0

            return 1

    def process_kpi_results(self, kpi_result_array):
        kpis_this_sim_run = []
        one_still_calculating = False
        kpi_list = get_session('kpi_list')  # contains id, name and description

        for kpi_result_item in kpi_result_array:
            kpi_id = list(kpi_result_item.keys())[0]
            kpi_result = kpi_result_item[kpi_id]

            kpi_info = dict()
            kpi_info['id'] = kpi_id
            kpi_info['name'] = None
            kpi_info['descr'] = None
            for kpi in kpi_list:
                if kpi['id'] == kpi_id:
                    kpi_info['name'] = kpi['name']
                    kpi_info['descr'] = kpi['descr']

            kpi_info['calc_status'] = kpi_result['status']
            if kpi_info['calc_status'] == 'Not yet started':
                one_still_calculating = True
            if kpi_info['calc_status'] == 'Calculating':
                kpi_info['progress'] = kpi_result['progress']
                one_still_calculating = True
            if kpi_info['calc_status'] == 'Success':
                kpi_info['kpi'] = kpi_result['kpi']
                if 'unit' in kpi_info:
                    kpi_info['unit'] = kpi_result['unit']

            kpis_this_sim_run.append(kpi_info)

        simid = get_session('es_simid')
        active_es_id = get_session('active_es_id')
        kpi_result_list = get_session('kpi_result_list')

        if kpi_result_list:
            kpis_per_simid = kpi_result_list["kpis_per_simid"]
            if active_es_id != kpi_result_list["es_id"]:    # if this is a simulation of a new energy system
                kpis_per_simid = dict()                     # start with an empty dict
                kpi_result_list["es_id"] = active_es_id     # set the current es_id
            kpis_per_simid[simid] = kpis_this_sim_run       # add the kpis of the last simulation run
        else:
            kpi_result_list = dict()                        # first KPIs for the energy system
            kpi_result_list["es_id"] = active_es_id
            kpi_result_list["kpis_per_simid"] = dict()
            kpi_result_list["kpis_per_simid"][simid] = kpis_this_sim_run

        result = {
            'still_calculating': one_still_calculating,
            'results': kpis_this_sim_run
        }

        # print("Processed results (sent back to client):")
        # print(result)
        if not one_still_calculating:
            # self.emit_kpis_for_visualization(kpi_result_list)
            print("All KPIs finished calculation")
            set_session('kpi_result_list', kpi_result_list)

            user_email = get_session('user-email')
            # TODO: fix storing per simid
            self.update_stored_simulation(user_email, simid, 'kpi_result_list', kpi_result_list)

        return result

    def emit_kpis_for_visualization(self, kpi_result_list):
        kpi_list = []

        for sim_id in kpi_result_list["kpis_per_simid"]:
            kpis_this_sim_run = kpi_result_list["kpis_per_simid"][sim_id]
            for kpi_result in kpis_this_sim_run:
                if kpi_result['calc_status'] == 'Success':
                    kpi = dict()
                    kpi['id'] = kpi_result['id']
                    kpi['name'] = kpi_result['name']
                    kpi['sim_id'] = sim_id

                    # ... 'kpi': [{'carrier': 'Warmte', 'value': 16969661811971.447},
                    # {'carrier': 'Elektriciteit', 'value': 89870082037933.03},
                    # {'carrier': 'Aardgas', 'value': 0.0028286240994930267}], ...
                    sub_kpi_list = kpi_result['kpi']

                    kpi['sub_kpi'] = list()
                    for sub_kpi in sub_kpi_list:
                        sub_kpi_res = dict()
                        if 'Unit' in sub_kpi:
                            sub_kpi_res['unit'] = sub_kpi['Unit']

                        sub_kpi_res['name'] = sub_kpi['Name']

                        if len(sub_kpi['Values']) > 1:
                            sub_kpi_res['type'] = 'Distribution'

                            parts = []
                            for kpi_part in sub_kpi['Values']:
                                print(kpi_part)
                                parts.append({
                                    'label': kpi_part['carrier'],
                                    'value': kpi_part['value']
                                })
                            sub_kpi_res['distribution'] = parts
                        else:
                            sub_kpi_res['type'] = 'Double'
                            sub_kpi_res['value'] = sub_kpi['Values']

                        kpi['sub_kpi'].append(sub_kpi_res)

                        # if len(kpi_res) > 1:
                        #     kpi['type'] = 'Distribution'
                        #
                        #     parts = []
                        #     for kpi_part in kpi_res:
                        #         parts.append({
                        #             'label': kpi_part['carrier'],
                        #             'percentage': kpi_part['value']
                        #         })
                        #     kpi['distribution'] = parts
                        # else:
                        #     kpi['value'] = kpi_res[0]['value']
                        #     kpi['type'] = 'Double'

                    kpi_list.append(kpi)

        if kpi_list:
            print("Emit kpi_list for visualization:")
            print(kpi_list)
            with self.flask_app.app_context():
                es_id = get_session('active_es_id')
                emit('kpis', {'es_id': es_id, 'scope': "essim kpis", 'kpi_list': kpi_list})