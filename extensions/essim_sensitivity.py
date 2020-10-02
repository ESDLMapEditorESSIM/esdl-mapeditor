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
from si_prefix import si_format
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler, get_session, set_session, del_session
from esdl.processing import ESDLEcore
from src.esdl_helper import get_port_profile_info
from extensions.essim import ESSIM
import src.log as log
import time
import copy

logger = log.get_logger(__name__)


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
        logger.info("Registering ESSIM sensitivity extension")

        @self.socketio.on('essim_sensitivity_add_asset', namespace='/esdl')
        def essim_sensitivity_asset_info(id):
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                asset = esh.get_by_id(active_es_id, id)

                asset_info = dict()
                asset_info['attrs_sorted'] = ESDLEcore.get_asset_attributes(asset)
                asset_info['port_profile_list'] = get_port_profile_info(asset)

                return asset_info

        @self.socketio.on('essim_sensitivity_run_simulations', namespace='/esdl')
        def essim_sensitivity_run_simulations(sim_info):
            sim_period_start = sim_info['period']['start']
            sim_period_end = sim_info['period']['end']
            selected_kpis = sim_info['selected_kpis']

            del_session('kpi_result_list')        # Clear list of KPI
            sensitivity_info = sim_info['sens_anal_info']
            sa_mutations = list()
            var_list = list()
            self.get_sa_mutations(sensitivity_info, sa_mutations, var_list)
            logger.info('Starting sensitivity analysis with {} mutations'.format(len(sa_mutations)))

            sa_index = 0
            var_list = sa_mutations[sa_index]

            sim_title = ''
            for v in var_list:
                asset_id = v['asset_id']
                attr = v['attr']
                value = v['value']
                obj, attr_name = self.get_obj_attr_name(asset_id, attr)
                self.set_param(obj, attr_name, value)
                if sim_title != '':
                    sim_title += ' & '
                sim_title += attr_name + '=' + si_format(value, precision=2)

            result = self.essim.run_simulation(sim_title, sim_period_start, sim_period_end, selected_kpis, False)
            if result:
                set_session('sensitivity_analysis', {
                    'index': sa_index,
                    'info': sensitivity_info,
                    'mutations': sa_mutations,
                    'sim_period_start': sim_period_start,
                    'sim_period_end': sim_period_end,
                    'selected_kpis': selected_kpis
                })
            else:
                del_session('sensitivity_analysis')

            return result

        @self.socketio.on('essim_sensitivity_next_simulation', namespace='/esdl')
        def essim_sensitivity_next_simulation():
            time.sleep(1)
            sensitivity_analysis = get_session('sensitivity_analysis')
            if sensitivity_analysis:
                sensitivity_info = sensitivity_analysis['info']
                sa_mutations = sensitivity_analysis['mutations']
                sa_index = sensitivity_analysis['index']
                sim_period_start = sensitivity_analysis['sim_period_start']
                sim_period_end = sensitivity_analysis['sim_period_end']

                sa_index = sa_index + 1
                if sa_index == len(sa_mutations):
                    del_session('sensitivity_analysis')
                    return 0        # end of sensitivity analysis
                var_list = sa_mutations[sa_index]

                sim_title = ''
                for v in var_list:
                    asset_id = v['asset_id']
                    attr = v['attr']
                    value = v['value']
                    obj, attr_name = self.get_obj_attr_name(asset_id, attr)
                    self.set_param(obj, attr_name, value)
                    if sim_title != '':
                        sim_title += ' & '
                    sim_title += attr_name + '=' + si_format(value, precision=2)

                selected_kpis = sensitivity_analysis['selected_kpis']

                result = self.essim.run_simulation(sim_title, sim_period_start, sim_period_end, selected_kpis, False)
                if result:
                    set_session('sensitivity_analysis', {
                        'index': sa_index,
                        'info': sensitivity_info,
                        'mutations': sa_mutations,
                        'sim_period_start': sim_period_start,
                        'sim_period_end': sim_period_end,
                        'selected_kpis': selected_kpis
                    })

                return result
            else:
                return 0

    def get_sa_mutations(self, sensitivity_info, sa_mut: list, var_list: list, var_idx=0):
        num_vars = len(sensitivity_info)
        if var_idx < num_vars:
            if len(var_list) < num_vars:
                var_list.append(None)  # add an element to the list, element is 'filled in' in the while loop

            var_info = sensitivity_info[var_idx]
            asset_id = var_info['asset_id']
            attr = var_info['attr']
            current = float(var_info['attr_start'])
            attr_step = float(var_info['attr_step'])
            attr_end = float(var_info['attr_end'])

            while current <= attr_end:
                var_list[var_idx] = {
                    'asset_id': asset_id,
                    'attr': attr,
                    'value': current
                }

                self.get_sa_mutations(sensitivity_info, sa_mut, var_list, var_idx + 1)
                if current <= attr_end:
                    current = current + attr_step
        else:
            sa_mut.append(copy.deepcopy(var_list))

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
