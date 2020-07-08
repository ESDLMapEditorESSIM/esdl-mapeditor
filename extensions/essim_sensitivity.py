from flask import Flask, jsonify, session, abort
from flask_socketio import SocketIO, emit
from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_handler, get_session, set_session, del_session
from esdl.processing import ESDLAsset, ESDLEcore
from esdl_helper import get_port_profile_info
from extensions.essim import ESSIM
from essim_kpis import ESSIM_KPIs

import requests
import json


ESSIM_SENSITIVITY_CONFIG = 'ESSIM_SENSITIVITY_CONFIG'


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class ESSIMSensitivity:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage, essim: ESSIM):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.essim = essim

        self.essim_sensitivity_plugin_settings = self.get_config()
        self.asset_dict = dict()

        self.register()

    def get_config(self):
        if self.settings_storage.has_system(ESSIM_SENSITIVITY_CONFIG):
            essim_sensitivity_plugin_settings = self.settings_storage.get_system(ESSIM_SENSITIVITY_CONFIG)
        else:
            essim_sensitivity_plugin_settings = {
                
            }
            self.settings_storage.set_system(ESSIM_SENSITIVITY_CONFIG, essim_sensitivity_plugin_settings)
        return essim_sensitivity_plugin_settings

    def register(self):
        print("Registering ESSIM sensitivity extension")

        @self.socketio.on('essim_sensitivity_add_asset', namespace='/esdl')
        def essim_sensitivity_asset_info(id):
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                asset = esh.get_by_id(active_es_id, id)

                if asset.id in self.asset_dict:
                    return self.asset_dict[asset.id]
                else:
                    asset_info = dict()

                    asset_info['attrs_sorted'] = ESDLEcore.get_asset_attributes(asset)
                    asset_info['port_profile_list'] = get_port_profile_info(asset)

                    self.asset_dict[asset.id] = asset_info
                    return asset_info

        @self.socketio.on('essim_sensitivity_run_simulations', namespace='/esdl')
        def essim_sensitivity_run_simulations(sim_info):
            sim_period_start = sim_info['period']['start']
            sim_period_end = sim_info['period']['end']
            selected_kpis = sim_info['selected_kpis']

            # TODO: Assume one line
            sensitivity_info = sim_info['sens_anal_info'][0];
            asset_id = sensitivity_info['asset_id']
            attr = sensitivity_info['attr']
            attr_start = sensitivity_info['attr_start']

            obj, attr_name = self.get_obj_attr_name(asset_id, attr)

            # for attr_value in range(attr_start, attr_end+1, attr_step):
            # No for-loop here, change es to the first value
            self.set_param(obj, attr_name, attr_start)

            set_value = obj.eGet(attr_name)
            obj_name = obj.name
            if not obj_name:
                obj_name = 'noname'
            print('Running simulation with {} of {} set to {}'.format(attr_name, obj_name, set_value))

            result = self.essim.run_simulation(obj_name+'-'+attr_name+':'+str(set_value), sim_period_start, sim_period_end, selected_kpis)
            if result:
                set_session('sensitivity_analysis', {
                    'value': attr_start,
                    'info': sensitivity_info,
                    'selected_kpis': selected_kpis
                })

            return result

        @self.socketio.on('essim_sensitivity_next_simulation', namespace='/esdl')
        def essim_sensitivity_next_simulation():
            sensitivity_analysis = get_session('sensitivity_analysis')
            if sensitivity_analysis:
                sensitivity_info = sensitivity_analysis['info']
                selected_kpis = sensitivity_analysis['selected_kpis']

                asset_id = sensitivity_info['asset_id']
                attr = sensitivity_info['attr']
                attr_step = sensitivity_info['attr_step']
                attr_end = sensitivity_info['attr_end']

                current_value = sensitivity_analysis['value'] + attr_step

                if current_value <= attr_end:

                    obj, attr_name = self.get_obj_attr_name(asset_id, attr)
                    # for attr_value in range(attr_start, attr_end+1, attr_step):
                    # No for-loop here, change es to the first value
                    self.set_param(obj, attr_name, current_value)

                    set_value = obj.eGet(attr_name)
                    obj_name = obj.name
                    if not obj_name:
                        obj_name = 'noname'
                    print('Running simulation with {} of {} set to {}'.format(attr_name, obj_name, set_value))

                    result = self.essim.run_simulation(obj_name+'-'+attr_name+':'+str(set_value), '2015-01-01T00:00:00+0100', '2016-01-01T00:00:00+0100', selected_kpis)
                    if result:
                        set_session('sensitivity_analysis', {
                            'value': current_value,
                            'info': sensitivity_info,
                            'selected_kpis': selected_kpis
                        })

                    return result
                else:
                    return 0

    def get_obj_attr_name(self, asset_id, attr):
        with self.flask_app.app_context():
            esh = get_handler()
            active_es_id = get_session('active_es_id')

            if attr.startswith('attr_name_'):
                object = esh.get_by_id(active_es_id, asset_id)
                attr_name = attr.replace('attr_name_', '')
            else:
                # profile_id_
                profile_id = attr.replace('profile_id_', '')
                object = esh.get_by_id(active_es_id, profile_id)
                attr_name = 'multiplier'

            return object, attr_name

    def set_param(self, object, attr_name, attr_value):
        with self.flask_app.app_context():
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            try:
                attribute = object.eClass.findEStructuralFeature(attr_name)
                if attribute is not None:
                    if attr_value == "":
                        parsed_value = attribute.eType.default_value
                    else:
                        parsed_value = attribute.eType.from_string(attr_value)
                    if attribute.many:
                        eOrderedSet = object.eGet(attr_name)
                        eOrderedSet.clear()  # TODO no support for multi-select of enums
                        eOrderedSet.append(parsed_value)
                        object.eSet(attr_name, eOrderedSet)
                    else:
                        if attribute.name == 'id':
                            esh.remove_object_from_dict(active_es_id, object)
                            object.eSet(attr_name, parsed_value)
                            esh.add_object_to_dict(active_es_id, object)
                        else:
                            object.eSet(attr_name, parsed_value)
                else:
                    print('Error setting attribute {} of {} to {}, unknown attribute'.format(attr_name,
                                                                                             object.name,
                                                                                             attr_value))
            except Exception as e:
                print('Error setting attribute {} of {} to {}, caused by {}'.format(attr_name, object.name,
                                                                                    attr_value, str(e)))