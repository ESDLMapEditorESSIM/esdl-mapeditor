"""
ESDL Browser extension
Handles the messages belonging to utils/esdl_browser.js
"""

from flask import Flask, session
from flask_socketio import SocketIO
from extensions.session_manager import get_handler, get_session, get_session_for_esid
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl.processing.ESDLQuantityAndUnits import qau_to_string
from esdl import esdl


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
                esdl_object_descr = self.get_object_dict(esdl_object)
                container = esdl_object.eContainer()
                container_descr = self.get_container_dict(container)
                attributes = esh.get_asset_attributes(esdl_object, self.esdl_doc)
                references = esh.get_asset_references(esdl_object, self.esdl_doc, ESDLBrowser.generate_repr)

                self.socketio.emit('esdl_browse_to',
                                   {'es_id': active_es_id,
                                    'object': esdl_object_descr,
                                    'attributes': attributes,
                                    'references': references,
                                    'container': container_descr},
                                   namespace='/esdl')


    def get_container_dict(self, container):
        if container is None:
            return None
        if hasattr(container, 'name'):
            return {'name': container.name, 'doc':container.__doc__, 'type': container.eClass.name, 'id': container.id}
        else:
            return {'name': "No Name", 'doc':container.__doc__, 'type': container.eClass.name, 'id': container.id}

    def get_object_dict(self, esdl_object):
        if not hasattr(esdl_object, 'name'):
            name = esdl_object.eClass.name
        else:
            name = esdl_object.name

        if not hasattr(esdl_object, 'id'):
            id = None
        else:
            id = esdl_object.id
        return \
            {'name': name,
             'doc': esdl_object.__doc__,
             'type': esdl_object.eClass.name,
             'id': id}


    @staticmethod
    def generate_repr(item):
        """
         Simple function to create a representation of an object
         """
        if item is None:
            return item
        if hasattr(item, 'name') and item.name is not None:
            return item.name
        if isinstance(item, esdl.QuantityAndUnitType):
            return qau_to_string(item)
        if hasattr(item, 'id') and item.id is not None:
            return item.eClass.name + ' (id=' + item.id + ')'
        return item.eClass.name
