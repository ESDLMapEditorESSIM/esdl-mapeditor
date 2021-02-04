"""
ESDL Drive extension - A CDO based ESDL storage solution
Connects to the ESDL Drive API for file sharing
"""

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
#
#  TNO licenses this work to you under the Apache License, Version 2.0
#  You may obtain a copy of the license at http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#         TNO             - Initial implementation
#
#  :license: Apache License, Version 2.0
#

from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session, set_session
import requests
from pyecore.resources import URI, Resource
from pyecore.resources.resource import URIConverter
from io import BytesIO
from src.process_es_area_bld import process_energy_system
from flask_executor import Executor
import src.log as log
from src.settings import esdl_drive_config

url = esdl_drive_config['hostname']
browse_endpoint = "/store/browse"
resource_endpoint = "/store/resource"
drive_name = "ESDl Drive"

logger = log.get_logger(__name__)


class ESDLDrive:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.register()
        self.files = dict()

    def register(self):
        logger.info('Registering ESDL Drive CDO extension at ' + esdl_drive_config['hostname'])

        @self.socketio.on('cdo_browse', namespace='/esdl')
        def socketio_esdldrive_browse(message):
            with self.flask_app.app_context():
                logger.debug('ESDLDrive: {}'.format(message))
                return self.browse_cdo(message)

        @self.socketio.on('cdo_open', namespace='/esdl')
        def socketio_esdldrive_open(message):
            with self.flask_app.app_context():
                path = message['path']
                params = dict()
                import_es = False
                if 'revision' in message:
                    params['revision'] = message['revision']
                if 'nocache' in message:
                    params['nocache'] = message['nocache']
                if 'import' in message:
                    import_es = message['import']

                logger.debug("Open params: {}".format(params))
                #token = get_session('jwt-token')
                uri = ESDLDriveHttpURI(url + resource_endpoint + path, headers_function=add_authorization_header, getparams=params)
                logger.debug('ESDLDrive open: {} ({})'.format(message, uri.plain))
                esh = get_handler()
                try:
                    if import_es:
                        es, parse_info = esh.import_file(uri)
                    else:
                        es, parse_info = esh.load_file(uri)
                    if len(parse_info) > 0:
                        info = ''
                        for line in parse_info:
                            info += line + "\n"
                        message = "Warnings while opening {}:\n\n{}".format(uri.last_segment, info)
                        emit('alert', message, namespace='/esdl')
                        print(esh.rset.resources)
                except Exception as e:
                    logger.error("Error in loading file from ESDLDrive: "+ str(e))
                    return

                if hasattr(es, 'name') and es.name:
                    title = drive_name + ': ' + es.name
                else:
                    title = drive_name + ' ES id: ' + es.id

                set_session('active_es_id', es.id)
                set_session('es_filename', uri.last_segment)  # TODO: separate filename and title
                es_info_list = {}
                set_session("es_info_list", es_info_list)
                emit('clear_ui')
                emit('clear_esdl_layer_list')
                self.executor.submit(process_energy_system, esh, uri.last_segment, title)  # run in seperate thread

        @self.socketio.on('cdo_save', namespace='/esdl')
        def socketio_esdldrive_save(message):
            with self.flask_app.app_context():
                path = message['path']
                overwrite = False
                commitMessage = ""
                params = {}
                if 'commitMessage' in message:
                    commitMessage = message['commitMessage']
                    params['commitMessage'] = commitMessage
                if 'forceOverwrite' in message:
                    overwrite = message['forceOverwrite']
                    params['overwrite'] = overwrite
                print(message)

                uri = url + resource_endpoint + path
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                esh.update_version(es_id=active_es_id)
                resource: Resource = esh.get_resource(active_es_id)
                logger.debug('ESDLDrive saving resource {}, commitMessage={}, overwrite={}'.format(resource.uri, commitMessage, overwrite))

                if resource.uri.normalize() == uri:
                    # resource already in CDO
                    logger.debug('Saving resource that is already loaded from ESDLDrive: {}'.format(resource.uri.plain))
                    # update uri with commit message
                    resource.uri = ESDLDriveHttpURI(uri, headers_function=add_authorization_header, putparams=params)
                    response = resource.save()
                else:
                    logger.debug('Saving to a new resource in ESDLDrive: {}'.format(resource.uri.plain))
                    resource.uri = ESDLDriveHttpURI(uri, headers_function=add_authorization_header, putparams=params)
                    response: requests.Response = resource.save()
                    esh.esid_uri_dict[resource.contents[0].id] = resource.uri.normalize()
                    # new resource
                if response.ok:
                    return {'path': path, 'success': True}
                else:
                    return {'path': path, 'success': False, 'error': str(response.content), 'status': response.status_code}

        @self.socketio.on('cdo_upload', namespace='/esdl')
        # BULK upload from MapEditor
        def socketio_esdldrive_upload(message):
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
                    logger.debug('Uploading to ESDLDrive {}, size={}'.format(name, size))
                    emit('cdo_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos']})

                if message_type == 'next_chunk':
                    name = message['name']
                    uuid = message['uuid']
                    size = message['size']
                    content = message['content']
                    pos = message['pos']
                    #print(content)
                    self.files[uuid]['content'][pos:len(content)] = content
                    self.files[uuid]['pos'] = pos + len(content)
                    if self.files[uuid]['pos'] >= size:
                        # upload complete
                        ba = bytearray(self.files[uuid]['content'])
                        esdl = ba.decode(encoding='utf-8')
                        # upload ESDL to ESDLDrive
                        self.executor.submit(self.threaded_save, name, uuid, esdl)
                    else:
                        # request next chunk of data for upload
                        emit('cdo_next_chunk', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos']})

    # check if putting save in a thread will not loose socketIO connection
    def threaded_save(self, name, uuid, esdl):
        logger.debug("Uploading to ESDLDrive (multi-threaded): ".format(name))
        try:
            response = self.save(self.files[uuid]['path'] + '/' + self.files[uuid]['name'], esdl)
            if response:
                logger.debug("Uploading done with status code {}".format(response.status_code))
            emit('cdo_upload_done', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos'],
                                     'path': self.files[uuid]['path'], 'success': True})
        except Exception as e:
            emit('cdo_upload_done', {'name': name, 'uuid': uuid, 'pos': self.files[uuid]['pos'],
                                     'path': self.files[uuid]['path'], 'success': False, 'error': str(e)})

        # clean up
        del (self.files[uuid])

    def browse_cdo(self, params):
        with self.flask_app.app_context():
            #token = self.oidc.get_access_token() -> does not work unfortunately
            token = get_session('jwt-token')
            if token is None:
                print("Token is None!")
                return {'status': 403, 'error': "ESDLDrive: Token not available, please reauthenticate"}
            headers = {'Authorization': 'Bearer ' + token}
            try:
                r = requests.get(url + browse_endpoint, params=params, headers=headers)
            except Exception as e:
                return {'status': 500, 'error': "Error communicating with ESDLDrive: " + str(e)}
            if 'Content-Type' in r.headers and r.headers.get('Content-Type').startswith('application/json'):
                return {'status': r.status_code, 'json': r.json()}
            if r.ok and 'Content-Type' in r.headers and r.headers['Content-Type'].startswith('text/html'):
                return r.text
            else:
                try:
                    r.raise_for_status()
                except Exception as e:
                    print(e)
                    print(r.headers)
                return {'status': r.status_code, 'error': "Error communicating with ESDLDrive: " + str(r.status_code)}

    def save(self, path, content_as_string):
        location = url + resource_endpoint + path
        esh = get_handler()

        #active_es_id = get_session('active_es_id')
        # esh.get_energy_system(active_es_id)
        #resource: Resource = esh.get_resource(active_es_id)
        logger.debug('ESDLDrive saving resource {}'.format(location))
        try:
            uri = ESDLDriveHttpURI(location, headers_function=add_authorization_header)
            uri.create_outstream(text_content=content_as_string)
            response = uri.close_stream()  # send content to CDO
            return response
        except Exception as e:
            logger.error("Error saving to ESDLDrive: "+str(e))
            # response = requests.Response()
            # response.status_code = 500
            # response.content = e
            return e


def add_authorization_header():
    token = get_session('jwt-token')
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/xml'}
    return headers

"""
ESDL resources in ESDLDrive are directly accessible by a URL. 
ESDLDriveHttpURI wraps this URL and adds support for JWT tokens for authentication when using a ESDL Drive URL.
header_function is used to query the JWT token that is at that moment in use and not expired. This token needs to be
added to the HTTP request just before it gets called.
"""
class ESDLDriveHttpURI(URI):
    def __init__(self, uri, headers_function=None, getparams: dict = None, putparams: dict=None):
        self.headers_function = headers_function
        if headers_function is None:
            self.headers_function = lambda: dict()
        self.putparams = putparams
        if putparams is None:
            self.putparams=dict()
        self.getparams = getparams
        if getparams is None:
            self.getparams=dict()
        self.writing = False
        super().__init__(uri)

    def create_instream(self):
        #if self.__stream:
        #    return self.__stream  # in case of a text content to be saved to CDO
        #self.__stream = urllib.request.urlopen(self.plain)
        print('ESDLDrive Downloading {}'.format(self.plain))
        headers = self.headers_function()
        response = requests.get(self.plain, headers=headers, params=self.getparams)
        if response.status_code > 400:
            logger.error("Error reading from ESDLDrive: headers={}, response={}".format(response.headers, response.content))
            raise Exception("Error accessing {}: HTTP Status {}".format(self.plain, response.status_code))
        self.__stream = BytesIO(response.content)
        return self.__stream


    def create_outstream(self, text_content=None):
        """
        Parameters
        ----------
        text_content optional, write this text content to the URI, instead of using a resource.
        Returns the BytesIO stream
        -------
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
            response = requests.put(self.plain, data=self.__stream.getvalue(), headers=headers, params=self.putparams)
            if response.status_code > 400:
                logger.error("Error writing to ESDLDrive: headers={}, response={}".format(response.headers, response.content))
                #raise Exception("Error saving {}: HTTP Status {}".format(self.plain, response.status_code))
            else:
                logger.debug('Saved successfully to ESDLDrive {} (HTTP status: {}) '.format(self.plain, response.status_code))
            self.writing = False
            super().close_stream()
            return response
        super().close_stream()

    def apply_relative_from_me(self, relative_path):
        # currently make all http-based uri's unique,
        # better would be to check each path's segment until there is a difference
        return relative_path
