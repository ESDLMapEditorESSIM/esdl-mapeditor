from esdl import esdl
import esdl_config
import requests
import urllib.parse
from extensions.session_manager import get_handler, get_session


class ESDLServices:

    def __init__(self):
        self.config = esdl_config.esdl_config['predefined_esdl_services']

    def get_services_list(self):
        return self.config

    def array2list(self, ar):
        if isinstance(ar, list):
            return ','.join(ar)
        else:
            return ar

    def call_esdl_service(self, service_params):

        esh = get_handler()
        active_es_id = get_session('active_es_id')

        # {'service_id': '18d106cf-2af1-407d-8697-0dae23a0ac3e', 'area_scope': 'provincies', 'area_id': '12',
        #  'query_params': {'bebouwingsafstand': '32432', 'restrictie': 'vliegveld', 'preferentie': 'infrastructuur', 'geometrie': 'true'}}
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
                    ares_id = service_params['area_id']

                    url = url.replace(area_scope_tag, area_scope)
                    url = url.replace(area_id_tag, ares_id)

                    query_params = service_params['query_params']
                    if query_params:
                        url = url + '?'
                        first_qp = True
                        for key in query_params:
                            if query_params[key]:  # to filter empty lists for multi-selection parameters
                                if not first_qp:
                                    url = url + '&'
                                url = url + key + '=' + self.array2list(query_params[key])
                                first_qp = False

                    print(url)
                elif service['type'] == 'send_esdl':
                    esdlstr = esh.to_string(active_es_id)

                    if service['body'] == 'url_encoded':
                        body = urllib.parse.quote(esdlstr)
                    else:
                        body = esdlstr

                try:
                    if service['http_method'] == 'get':
                        r = requests.get(url, headers=headers)
                    elif service['http_method'] == 'post':
                        r = requests.post(url, headers=headers, data="energysystem="+body)

                    if r.status_code == 200:
                        print(r.text)
                        if service['result'] == 'esdl':
                            esh.add_from_string(service['name'], r.text)
                            return None
                        elif service['result'] == 'print':
                            return r.text
                    else:
                        print(
                            'Error running ESDL service - response ' + str(r.status_code) + ' with reason: ' + str(
                                r.reason))
                        print(r)
                        print(r.content)
                        return None
                except Exception as e:
                    print('Error accessing external ESDL service: ' + str(e))
                    return 0
