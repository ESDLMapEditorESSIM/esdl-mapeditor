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
import logging


url = "http://localhost:9080/store"
browse_endpoint = "/browse"
resource_endpoint = "/resource"

logger = logging.getLogger(__name__)

class MondaineCDO:
    def __init__(self, flask_app: Flask, socket: SocketIO, oidc: OpenIDConnect, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.oidc = oidc
        self.executor = executor
        self.register()
        self.files = dict();

    def register(self):
        print('Registering Mondaine CDO extension')

        @self.socketio.on('cdo_browse', namespace='/esdl')
        def socketio_mondaine_browse(message):
            with self.flask_app.app_context():
                logger.debug('MondaineCDO: {}'.format(message))
                return self.browse_cdo(message)

        @self.socketio.on('cdo_open', namespace='/esdl')
        def socketio_mondaine_open(message):
            with self.flask_app.app_context():
                path = message['path']
                token = get_session('jwt-token')
                headers = {'Authorization': 'Bearer ' + token}
                uri = CDOHttpURI(url + resource_endpoint + path, headers_function=add_authorization_header)
                logger.debug('MondaineCDO open: {} ({})'.format(message, uri.plain))
                esh = get_handler()
                try:
                    es = esh.load_file(uri)
                except Exception as e:
                    logger.error("Error in loading file from MondaineCDO", e)
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
                logger.debug('Mondaine CDO saving resource', resource.uri)
                if resource.uri.normalize() == uri:
                    # resource already in CDO
                    logger.debug('Saving resource that is already loaded from CDO', resource.uri.plain)
                    resource.save()
                else:
                    logger.debug('Saving to a new resource in CDO', resource.uri.plain)
                    resource.uri = CDOHttpURI(uri, headers_function=add_authorization_header)
                    resource.save()
                    esh.esid_uri_dict[resource.contents[0].id] = resource.uri.normalize()
                    # new resource

        @self.socketio.on('cdo_upload', namespace='/esdl')
        def socketio_mondaine_open(message):
            with self.flask_app.app_context():
                message_type = message['message_type'] # start, next_chunk, done
                if (message_type == 'start'):
                    # start of upload
                    filetype = message['filetype']
                    name = message['name']
                    uuid = message['uuid']
                    size = message['size']

                    self.files[uuid] = message
                    self.files[uuid]['pos'] = 0
                    self.files[uuid]['content'] = []
                    logger.debug('Uploading to CDO {}, size='.format(name, size))
                    emit('cdo_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos']})

                if (message_type == 'next_chunk'):
                    name = message['name']
                    uuid = message['uuid']
                    size = message['size']
                    content = message['content']
                    pos = message['pos']
                    #print(content)
                    self.files[uuid]['content'][pos:len(content)] = content
                    self.files[uuid]['pos'] = pos + len(content)
                    if self.files[uuid]['pos'] >= size:
                        #print("Upload complete:", str(bytearray(self.files[uuid]['content'])))

                        ba = bytearray(self.files[uuid]['content'])
                        esdl = ba.decode(encoding='utf-8')
                        # upload ESDL
                        logger.debug("Uploading to CDO: ".format(name))
                        try:
                            response = self.save(self.files[uuid]['path'] + '/' + self.files[uuid]['name'], esdl)
                            logger.debug("Uploading done with status code {}".format(response.status_code))
                            emit('cdo_upload_done', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos'],
                                                    'path': self.files[uuid]['path'], 'success': True})
                        except Exception as e:
                            emit('cdo_upload_done', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos'],
                                                     'path': self.files[uuid]['path'], 'success': False, 'error': str(e)})


                        #clean up
                        del(self.files[uuid])
                    else:
                        #print("Requesting next chunk", str(bytearray(self.files[uuid]['content'])))
                        emit('cdo_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos']})



    def browse_cdo(self, params):
        with self.flask_app.app_context():
            #token = self.oidc.get_access_token()
            token = get_session('jwt-token')
            if token is None:
                print("Token is None!")
                return {'status': 403, 'error': "Token not available, please reauthenticate"}
            headers = {'Authorization': 'Bearer ' + token}
            r = requests.get(url + browse_endpoint, params=params, headers=headers)
            if 'Content-Type' in r.headers and r.headers.get('Content-Type').startswith('application/json'):
                return {'status': r.status_code, 'json': r.json()}
            if r.ok and 'Content-Type' in r.headers and r.headers['Content-Type'].startswith('text/html'):
                #print (r.text)
                return r.text
            else:
                try:
                    r.raise_for_status()
                except Exception as e:
                    print(e)
                print(r.headers)
                return {'status': r.status_code, 'error': "Error communicating with CDO: " + str(r.status_code)}

    def save(self, path, content_as_string):
        location = url + resource_endpoint + path
        esh = get_handler()

        #active_es_id = get_session('active_es_id')
        # esh.get_energy_system(active_es_id)
        #resource: Resource = esh.get_resource(active_es_id)
        logger.debug('Mondaine CDO saving resource', location)
        try:
            uri = CDOHttpURI(location, headers_function=add_authorization_header)
            uri.create_outstream(text_content=content_as_string)
            response = uri.close_stream()  # send content to CDO
            return response
        except Exception as e:
            logger.error("Error saving to Mondaine CDO", e)


def add_authorization_header():
    token = get_session('jwt-token')
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/xml'}
    return headers



class CDOHttpURI(URI):
    def __init__(self, uri, headers_function=None):
        self.headers_function = headers_function
        self.writing = False
        super().__init__(uri)

    def create_instream(self):
        if self.__stream is not None:
            return self.__stream # in case of a text content to be saved to CDO
        #self.__stream = urllib.request.urlopen(self.plain)
        print('Downloading {}'.format(self.plain))
        headers = self.headers_function()
        response = requests.get(self.plain, headers=headers)
        if response.status_code > 400:
            logger.error("Error reading from CDO: headers={}, response={}".format(response.headers, response.content))
            raise Exception("Error accessing {}: HTTP Status {}".format(self.plain, response.status_code))
        self.__stream = BytesIO(response.content)
        return self.__stream


    def create_outstream(self, text_content=None):
        """

        Parameters
        ----------
        text_content optional, write this text content to the URI, instead of using a resource.

        Returns
        -------
        the BytesIO stream
        """
        self.writing = True
        if text_content is not None:
            self.__stream = BytesIO(text_content.encode('UTF-8'))
        else:
            self.__stream = BytesIO()
        return self.__stream

    def close_stream(self):
        # content has been written to __stream()
        if self.writing:
            logger.debug("Writing to {}".format(self.plain))
            headers = self.headers_function()
            response = requests.put(self.plain, data=self.__stream.getvalue(), headers=headers)
            if response.status_code > 400:
                logger.error("Error writing to CDO: headers={}, response={}".format(response.headers, response.content))
                raise Exception("Error saving {}: HTTP Status {}".format(self.plain, response.status_code))
            print(response)
            self.writing = False
        super().close_stream()
        return response

    def apply_relative_from_me(self, relative_path):
        return self.plain
