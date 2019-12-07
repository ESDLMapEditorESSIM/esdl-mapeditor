from esdl import esdl
import esdl_config
import requests
import json
import copy
import urllib.parse
from extensions.session_manager import get_handler, get_session
from esdl.processing import ESDLAsset
from esdl_helper import energy_asset_to_ui, create_port_asset_mapping
from extensions.session_manager import get_session_for_esid
from flask_socketio import emit


class ESDLServices:

    def __init__(self):
        self.config = esdl_config.esdl_config['predefined_esdl_services']

    def get_services_list(self, roles=[]):
        self.config = esdl_config.esdl_config['predefined_esdl_services']

        print(roles)
        this_config = copy.deepcopy(self.config)
        for s in list(this_config):
            if 'required_role' in s:
                if not s['required_role'] in roles:
                    this_config.remove(s)

        return this_config

    def array2list(self, ar):
        if isinstance(ar, list):
            return ','.join(ar)
        else:
            return ar

    def call_esdl_service(self, service_params):

        esh = get_handler()
        active_es_id = get_session('active_es_id')

        # {'service_id': '18d106cf-2af1-407d-8697-0dae23a0ac3e', 'area_scope': 'provincies', 'area_id': '12',
        #  'query_parameters': {'bebouwingsafstand': '32432', 'restrictie': 'vliegveld', 'preferentie': 'infrastructuur', 'geometrie': 'true'}}
        for service in self.config:
            if service['id'] == service_params['service_id']:
                url = service['url']
                headers = service['headers']
                body = {}
                #{
                #    'Accept': "application/esdl+xml",
                #    'User-Agent': "ESDL Mapeditor/0.1"
                #}

                if service['type'] == 'geo_query':
                    area_scope_tag = service['geographical_scope']['url_area_scope']
                    area_id_tag = service['geographical_scope']['url_area_id']

                    area_scope = service_params['area_scope']
                    url = url.replace(area_scope_tag, area_scope)
                    ares_id = service_params['area_id']
                    url = url.replace(area_id_tag, ares_id)
                    if "url_area_subscope" in service['geographical_scope']:
                        area_subscope_tag = service['geographical_scope']['url_area_subscope']
                        area_subscope = service_params['area_subscope']
                        url = url.replace(area_subscope_tag, area_subscope)
                elif service['type'] == 'send_esdl':
                    esdlstr = esh.to_string(active_es_id)

                    if service['body'] == 'url_encoded':
                        body = urllib.parse.quote(esdlstr)
                    else:
                        body = esdlstr
                elif service['type'] == 'simulation':
                    esdlstr = esh.to_string(active_es_id)

                    if service['body'] == 'url_encoded':
                        body = urllib.parse.quote(esdlstr)
                    else:
                        body = esdlstr

                query_params = service_params['query_parameters']
                config_service_params = service["query_parameters"]
                if query_params:
                    first_qp = True
                    for key in query_params:
                        if query_params[key]:  # to filter empty lists for multi-selection parameters
                            for cfg_service_param in config_service_params:
                                if cfg_service_param["parameter_name"] == key:
                                    if "location" in cfg_service_param:
                                        if cfg_service_param["location"] == "url":
                                            url = url.replace('<'+cfg_service_param["parameter_name"]+'>', query_params[key])
                                    else:
                                        if first_qp:
                                            url = url + '?'
                                        else:
                                            url = url + '&'
                                        url = url + key + '=' + self.array2list(query_params[key])
                                        first_qp = False
                    print(url)

                try:
                    if service['http_method'] == 'get':
                        r = requests.get(url, headers=headers)
                    elif service['http_method'] == 'post':
                        r = requests.post(url, headers=headers, data="energysystem="+body)

                    if r.status_code == 200:
                        # print(r.text)

                        if service['result'][0]['action'] == 'esdl':
                            esh.add_from_string(service['name'], r.text)
                            return True, None
                        elif service['result'][0]['action']  == 'print':
                            return True, json.loads(r.text)
                        elif service['result'][0]['action']  == 'add_assets':
                            es_edit = esh.get_energy_system(es_id=active_es_id)
                            instance = es_edit.instance
                            area = instance[0].area
                            mapping = get_session_for_esid(active_es_id, 'port_to_asset_mapping')

                            asset_str_list = json.loads(r.text)

                            try:
                                for asset_str in asset_str_list['add_assets']:
                                    asset = ESDLAsset.load_asset_from_string(asset_str)
                                    esh.add_object_to_dict(active_es_id, asset)
                                    ESDLAsset.add_asset_to_area(es_edit, asset, area.id)
                                    create_port_asset_mapping(asset, mapping)
                                    asset_ui, conn_list = energy_asset_to_ui(asset, mapping)
                                    emit('add_esdl_objects',
                                         {'es_id': active_es_id, 'asset_pot_list': [asset_ui],
                                          'zoom': True})
                                    emit('add_connections', {'es_id': active_es_id, 'conn_list': conn_list})
                            except Exception as e:
                                print ('Exception occurred: '+str(e))
                                return False, None

                            return True, { 'send_message_to_UI_but_do_nothing': {} }
                    else:
                        print(
                            'Error running ESDL service - response ' + str(r.status_code) + ' with reason: ' + str(
                                r.reason))
                        print(r)
                        print(r.content)
                        return False, None
                except Exception as e:
                    print('Error accessing external ESDL service: ' + str(e))
                    return False, None

        return False, None