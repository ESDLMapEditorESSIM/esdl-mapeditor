"""
ESDL Browser extension
Handles the messages belonging to utils/esdl_browser.js
"""

from flask import Flask, session
from flask_socketio import SocketIO
from extensions.session_manager import get_handler, get_session, get_session_for_esid
from esdl.processing.EcoreDocumentation import EcoreDocumentation


class ESDLBrowser:
    def __init__(self, flask_app: Flask, socket: SocketIO, esdl_doc: EcoreDocumentation):
        self.flask_app = flask_app
        self.socketio = socket
        self.esdl_doc = esdl_doc
        self.register()

    def register(self):
        print('Registering HeatNetwork extension')

        @self.socketio.on('esdl_browse_get_objectinfo', namespace='/esdl')
        def socketio_get_objectinfo(message):
            with self.flask_app.app_context():
                esdl_object_id = message['id'];
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                esdl_object = esh.get_by_id(active_es_id, esdl_object_id);
                attributes = esh.get_asset_attributes(esdl_object, self.esdl_doc)
                references = esh.get_asset_references(esdl_object, self.esdl_doc)
                self.socketio.emit('esdl_browse_to', {'es_id': active_es_id, 'attributes': attributes, 'references': references}, namespace='/esdl')



