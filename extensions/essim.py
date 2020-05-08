from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from extensions.user_settings import SettingType, UserSettings
from extensions.session_manager import get_handler, get_session, set_session, del_session
import requests
import urllib
import json
from datetime import datetime
import settings

# Temporarily fix load_animation dependencies
# from app import essim_kpis


ESSIM_SIMULATION_LIST = 'ESSIM_simulations'
ESSIM_FAVORITES_LIST = 'ESSIM_favorites'


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class ESSIM:
    def __init__(self, flask_app: Flask, socket: SocketIO, user_settings: UserSettings):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings = user_settings

        self.register()

    def register(self):
        print("Registering ESSIM extension")

        @self.socketio.on('essim_set_simulation_id', namespace='/esdl')
        def set_simulation_id(sim_id):
            with self.flask_app.app_context():
                esh = get_handler()

                print('Set ESSIM simulation ID: '+sim_id)
                set_session('simulationRun', sim_id)
                ESSIM_config = settings.essim_config
                url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path'] + '/' + sim_id

                try:
                    r = requests.get(url)
                    if r.status_code == 200:
                        result = json.loads(r.text)
                        esdl_string = result["esdlContents"]
                        esh.add_from_string(name='test', esdl_string=urllib.parse.unquote(esdl_string))
                        # process_energy_system.submit(esh, 'test')  # run in seperate thread

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
                    ESSIM_config = settings.essim_config
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
                                    del_session('es_simid')  # simulation ready
                                    result = json.loads(r.text)
                                    dashboardURL = result['dashboardURL']
                                    set_session('simulationRun', es_simid)
                                    self.update_stored_simulation(user_email, es_simid, dashboardURL)
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
                    print("No es_simid in session")
                    print(session)
                    abort(500, 'Simulation not running')

        # @self.flask_app.route('/load_animation')
        # def animate_load():
        #     with self.flask_app.app_context():
        #         # session['simulationRun'] = "5d1b682f5fd62723bb6ba0f4"
        #         ESSIM_config = settings.essim_config
        #         active_es_id = get_session('active_es_id')
        #
        #         simulation_run = get_session('simulationRun')
        #         if simulation_run:
        #             esh = get_handler()
        #             es_edit = esh.get_energy_system(es_id=active_es_id)
        #
        #             sdt = datetime.strptime(ESSIM_config['start_datetime'], '%Y-%m-%dT%H:%M:%S%z')
        #             edt = datetime.strptime(ESSIM_config['end_datetime'], '%Y-%m-%dT%H:%M:%S%z')
        #
        #             influxdb_startdate = sdt.strftime('%Y-%m-%dT%H:%M:%SZ')
        #             influxdb_enddate = edt.strftime('%Y-%m-%dT%H:%M:%SZ')
        #
        #             essim_kpis.init_simulation(es_edit, simulation_run, influxdb_startdate, influxdb_enddate)
        #             animation = essim_kpis.animate_load_geojson()
        #             print(animation)
        #             return animation, 200
        #         else:
        #             abort(500, 'No simulation results')

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
                        if self.settings.has_user(user_email, essim_list):
                            sim_list = self.settings.get_user(user_email, essim_list)

                            for sim in list(sim_list):
                                if sim['simulation_id'] == sim_id:
                                    sim_list.remove(sim)

                            self.settings.set_user(user_email, essim_list, sim_list)
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
                    if self.settings.has_user(user_email, ESSIM_SIMULATION_LIST):
                        last_list = self.settings.get_user(user_email, ESSIM_SIMULATION_LIST)

                    if self.settings.has_user(user_email, ESSIM_FAVORITES_LIST):
                        fav_list = self.settings.get_user(user_email, ESSIM_FAVORITES_LIST)

                    for sim in list(last_list):
                        if sim['simulation_id'] == sim_id:
                            fav_list.insert(0, sim)
                            last_list.remove(sim)

                    print(fav_list)

                    self.settings.set_user(user_email, ESSIM_SIMULATION_LIST, last_list)
                    self.settings.set_user(user_email, ESSIM_FAVORITES_LIST, fav_list)

                return json.dumps({'simulations': last_list, 'favorites': fav_list})

    def retrieve_sim_fav_list(self, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            user_email = get_session('user-email')
            sim_list = []
            if user_email is not None:
                if self.settings.has_user(user_email, essim_list):
                    sim_list = self.settings.get_user(user_email, essim_list)

            print(sim_list)
            return json.dumps(sim_list)

    def store_simulation(self, user_email, simulation_id, simulation_datetime, simulation_descr, simulation_es_name=None, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            if user_email is not None:
                if self.settings.has_user(user_email, essim_list):
                    sim_list = self.settings.get_user(user_email, essim_list)
                else:
                    sim_list = []

                sim_list.insert(0, {
                    "simulation_id": simulation_id,
                    "simulation_datetime": simulation_datetime,
                    "simulation_descr": simulation_descr,
                    "simulation_es_name": simulation_es_name,
                    "dashboard_url": ""
                })

                if sim_list.__len__ == 11:
                    sim_list.pop(10)
                # print(sim_list)
                self.settings.set_user(user_email, essim_list, sim_list)

    def update_stored_simulation(self, user_email, simulation_id, simulation_db_url, essim_list=ESSIM_SIMULATION_LIST):
        with self.flask_app.app_context():
            if user_email is not None and self.settings.has_user(user_email, essim_list):
                sim_list = self.settings.get_user(user_email, essim_list)
                if sim_list[0]["simulation_id"] == simulation_id:
                    sim_list[0]["dashboard_url"] = simulation_db_url
                # print(sim_list)
                self.settings.set_user(user_email, essim_list, sim_list)

    def run_simulation(self, sim_description, sim_start_datetime, sim_end_datetime):
        with self.flask_app.app_context():
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            user_email = get_session('user-email')

            current_es = esh.get_energy_system(es_id=active_es_id)
            current_es_name = current_es.name
            if current_es_name == "":
                current_es_name = "Untitled energysystem"
            esdlstr = esh.to_string(active_es_id)

            ESSIM_config = settings.essim_config

            url = ESSIM_config['ESSIM_host'] + ESSIM_config['ESSIM_path']
            # print('ESSIM url: ', url)

            payload = {
                'user': ESSIM_config['user'],
                'scenarioID': active_es_id,
                'simulationDescription': sim_description,
                'startDate': sim_start_datetime,
                'endDate': sim_end_datetime,
                'influxURL': ESSIM_config['influxURL'],
                'grafanaURL': ESSIM_config['grafanaURL'],
                'esdlContents': urllib.parse.quote(esdlstr)
            }
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
                    # print(result)
                    sim_id = result['id']
                    set_session('es_simid', sim_id)

                    self.store_simulation(user_email, sim_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sim_description, current_es_name)
                    # emit('', {})
                else:
                    send_alert(
                        'Error starting ESSIM simulation - response ' + str(r.status_code) + ' with reason: ' + str(
                            r.reason))
                    print(r)
                    print(r.content)
                    # emit('', {})
                    return 0
            except Exception as e:
                print('Error accessing ESSIM API at starting: ' + str(e))
                send_alert('Error accessing ESSIM API at starting: ' + str(e))
                return 0

            return 1