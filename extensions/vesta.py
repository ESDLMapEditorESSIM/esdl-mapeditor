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

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler, get_session
from src.process_es_area_bld import get_area_id_from_mapeditor_id
from esdl import esdl
from esdl.processing import ESDLAsset, ESDLEnergySystem
import src.settings as settings
import requests
import json
import uuid
import src.log as log

logger = log.get_logger(__name__)


VESTA_SYSTEM_CONFIG = 'VESTA_CONFIG'


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class Vesta:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.vesta_plugin_settings = self.get_config()
        self.selected_measures = None

        self.register()

    def get_config(self):
        if self.settings_storage.has_system(VESTA_SYSTEM_CONFIG):
            vesta_plugin_settings = self.settings_storage.get_system(VESTA_SYSTEM_CONFIG)
        else:
            vesta_plugin_settings = {
                "edr_url": settings.edr_config['EDR_host'],
                "edr_measures_tags": "measures,vesta"
            }
            self.settings_storage.set_system(VESTA_SYSTEM_CONFIG, vesta_plugin_settings)
        return vesta_plugin_settings

    def register(self):
        logger.info("Registering VESTA extension")

        @self.socketio.on('vesta_area_restrictions', namespace='/esdl')
        def set_area_restrictions(area_id):
            with self.flask_app.app_context():
                esh = get_handler()
                print(area_id)
                area_id = get_area_id_from_mapeditor_id(area_id)

                active_es_id = get_session('active_es_id')
                current_es = esh.get_energy_system(active_es_id)
                top_area = current_es.instance[0].area

                area = ESDLEnergySystem.find_area(top_area, area_id)
                measures = area.measures
                current_area_measures_list = []
                if measures:
                    for m in measures.measure:
                        if isinstance(m, esdl.MeasureReference):
                            this_measure = m.reference
                        else:
                            this_measure = m

                        current_area_measures_list.append({"id": this_measure.id, "name": this_measure.name})

                data = {
                    "current_measures": current_area_measures_list,
                    "area_id": area_id
                }

                emit('vesta_restrictions_data', data)

        @self.socketio.on('select_area_restrictions', namespace='/esdl')
        def select_area_restrictions(measures_data):
            area_id = measures_data['area_id']
            area_id = get_area_id_from_mapeditor_id(area_id)
            measures = measures_data['selected_measures']

            with self.flask_app.app_context():
                esh = get_handler()

                active_es_id = get_session('active_es_id')
                current_es = esh.get_energy_system(active_es_id)
                top_area = current_es.instance[0].area

                area = ESDLEnergySystem.find_area(top_area, area_id)
                print(measures)
                self.set_area_measures(esh, area_id, measures)

        @self.flask_app.route('/vesta_restrictions')
        def get_vesta_restrictions():
            result = self.get_edr_vesta_measures_list()
            if result is None:
                return jsonify([]), 200
            else:
                return jsonify(result), 200

        @self.flask_app.route('/vesta_restriction/<id>')
        def get_vesta_restriction(id):
            result = self.get_edr_vesta_measures(id)
            if result is None:
                return jsonify([]), 200
            else:
                return jsonify(result), 200

    def set_area_measures(self, esh, area_id, measures_list):
        active_es_id = get_session('active_es_id')
        es = esh.get_energy_system(active_es_id)
        top_area = es.instance[0].area

        area_id = get_area_id_from_mapeditor_id(area_id)
        area = ESDLEnergySystem.find_area(top_area, area_id)
        area.measures = None

        if measures_list:
            es_measures = es.measures

            for m_id in measures_list:
                found_measure = False
                if es_measures:
                    for es_m in es_measures.measure:
                        if es_m.id == m_id:
                            m_ref = esdl.MeasureReference()
                            m_ref.id = str(uuid.uuid4())
                            m_ref.reference = es_m
                            found_measure = True
                            if not area.measures:
                                area.measures = esdl.Measures()
                            area.measures.measure.append(m_ref)
                            esh.add_object_to_dict(active_es_id, m_ref)

                if not found_measure:
                    for edr_m in self.selected_measures.measure:
                        if edr_m.id == m_id:
                            # Add measure to es.measures
                            this_m = edr_m.deepcopy()
                            if not es_measures:
                                es_measures = esdl.Measures()
                                es.measures = es_measures
                            es_measures.measure.append(this_m)
                            esh.add_object_to_dict(active_es_id, this_m, True)

                            # Create reference
                            m_ref = esdl.MeasureReference()
                            m_ref.id = str(uuid.uuid4())
                            m_ref.reference = this_m

                            if not area.measures:
                                area.measures = esdl.Measures()
                            area.measures.measure.append(m_ref)
                            esh.add_object_to_dict(active_es_id, m_ref)

    def get_edr_vesta_measures_list(self):
        url = self.vesta_plugin_settings["edr_url"] + "/store/tagged?tag=" + self.vesta_plugin_settings["edr_measures_tags"]

        try:
            r = requests.get(url)
            if r.status_code == 200:
                result = json.loads(r.text)
                return result
            else:
                print('EDR returned unexpected result. Check Vesta plugin settings')
                send_alert('EDR returned unexpected result. Check Vesta plugin settings')
                return None

        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return None

    def get_edr_vesta_measures(self, measures_id):
        url = self.vesta_plugin_settings["edr_url"] + "/store/esdl/" + measures_id + "?format=xml"

        try:
            r = requests.get(url)
            if r.status_code == 200:
                result = []
                self.selected_measures = ESDLAsset.load_asset_from_string(r.text)
                for m in self.selected_measures.measure:
                    result.append({
                        "id": m.id,
                        "name": m.name
                    })
                return result
            else:
                print('EDR returned unexpected result. Check Vesta plugin settings')
                send_alert('EDR returned unexpected result. Check Vesta plugin settings')
                return None

        except Exception as e:
            print('Error accessing EDR API: ' + str(e))
            send_alert('Error accessing EDR API: ' + str(e))
            return None
