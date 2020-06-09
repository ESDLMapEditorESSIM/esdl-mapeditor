"""
Mondaine CDO extension
Connects to Mondaine CDO HUB for file sharing
"""

from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, set_session
from flask_oidc import OpenIDConnect
import requests
from pyecore.resources import URI, Resource
from io import BytesIO
from process_es_area_bld import process_energy_system
from flask_executor import Executor


url = "http://localhost:9080/store"
browse_endpoint = "/browse"
resource_endpoint = "/resource"

class MondaineCDO:
    def __init__(self, flask_app: Flask, socket: SocketIO, oidc: OpenIDConnect, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.oidc = oidc
        self.executor = executor
        self.register()

    def register(self):
        print('Registering Mondaine CDO extension')

        @self.socketio.on('cdo_browse', namespace='/esdl')
        def socketio_mondaine_browse(message):
            with self.flask_app.app_context():
                print('MondaineCDO: {}'.format(message))
                return self.browse_cdo(message)

        @self.socketio.on('cdo_open', namespace='/esdl')
        def socketio_mondaine_open(message):
            with self.flask_app.app_context():
                path = message['path']
                token = get_session('jwt-token')
                headers = {'Authorization': 'Bearer ' + token}
                uri = CDOHttpURI(url + resource_endpoint + path, headers_function=add_authorization_header)
                print('MondaineCDO open: {} ({})'.format(message, uri.plain))
                esh = get_handler()
                try:
                    es = esh.load_file(uri)
                except Exception as e:
                    print(e)
                    #send_alert('Error loading ESDL file with id {} from store'.format(store_id))
                    return

                if es.name:
                    title = 'MondaineHUB ' + es.name
                else:
                    title = 'MondaineHUB ES id: ' + es.id

                set_session('active_es_id', es.id)
                set_session('es_filename', title)  # TODO: separate filename and title
                es_info_list = {}
                set_session("es_info_list", es_info_list)
                emit('clear_ui')
                emit('clear_esdl_layer_list')
                self.executor.submit(process_energy_system, esh, None, title)  # run in seperate thread

        @self.socketio.on('cdo_save', namespace='/esdl')
        def socketio_mondaine_open(message):
            with self.flask_app.app_context():
                path = message['path']
                uri = url + resource_endpoint + path
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                #esh.get_energy_system(active_es_id)
                resource:Resource = esh.get_resource(active_es_id)
                print('saving resource', resource.uri)
                if resource.uri.normalize() == uri:
                    # resource already in CDO
                    print('saving resource that is already in CDO', resource.uri.plain)
                    resource.save()
                else:
                    print('saving to a new resource in CDO', resource.uri.plain)
                    resource.uri = CDOHttpURI(uri, headers_function=add_authorization_header)
                    resource.save()
                    # new resource

    def browse_cdo(self, params):
        with self.flask_app.app_context():
            #token = self.oidc.get_access_token()
            token = get_session('jwt-token')
            if token is None:
                print("Token is None!")
                return {'status': 403, 'error': "Token not available, please reauthenticate"}
            headers = {'Authorization': 'Bearer ' + token}
            r = requests.get(url + browse_endpoint, params=params, headers=headers)
            print(r)
            if hasattr(r.headers, 'Content-Type') and r.headers['Content-Type'].startswith('application/json'):
                return {'status': r.status_code, 'json': r.json()}
            if r.status_code == 200 and r.headers['Content-Type'].startswith('text/html'):
                #print (r.text)
                return r.text
            else:
                r.raise_for_status()
                print(r.headers)
                return {'status': r.status_code, 'error': "Error communicating with CDO: " + str(r.status_code)}



def add_authorization_header():
    token = get_session('jwt-token')
    headers = {'Authorization': 'Bearer ' + token}
    return headers



class CDOHttpURI(URI):
    def __init__(self, uri, headers_function=None):
        self.headers_function = headers_function
        self.writing = False
        super().__init__(uri)

    def create_instream(self):
        #self.__stream = urllib.request.urlopen(self.plain)
        print('Downloading {}'.format(self.plain))
        headers = self.headers_function()
        response = requests.get(self.plain, headers=headers)
        if response.status_code > 400:
            print(response.headers, response.content)
            raise Exception("Error accessing {}: HTTP Status {}".format(self.plain, response.status_code))
        self.__stream = BytesIO(response.content)
        return self.__stream

    def create_outstream(self):
        self.writing = True
        self.__stream = BytesIO()
        return self.__stream

    def close_stream(self):
        # content has been written to __stream()
        if self.writing:
            print("Writing to {}".format(self.plain))
            headers = self.headers_function()
            response = requests.put(self.plain, data=self.__stream.getvalue(), headers=headers)
            print(response)
        super().close_stream()

    def apply_relative_from_me(self, relative_path):
        return self.plain
