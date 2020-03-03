"""
ESDL Browser extension
Handles the messages belonging to utils/esdl_browser.js
"""

from flask import Flask
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler, get_session
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from esdl.processing.ESDLQuantityAndUnits import qau_to_string
from esdl import esdl
import esdl.processing.ESDLEcore as ESDLEcore
from pyecore.ecore import EObject, EReference


class ESDLBrowser:
    def __init__(self, flask_app: Flask, socket: SocketIO, esdl_doc: EcoreDocumentation):
        self.flask_app = flask_app
        self.socketio = socket
        self.esdl_doc = esdl_doc
        self.register()

    def register(self):
        print('Registering ESDL Browser extension')

        @self.socketio.on('esdl_browse_get_objectinfo', namespace='/esdl')
        def socketio_get_objectinfo(message):
            with self.flask_app.app_context():
                esdl_object = self.get_object_from_identifier(message)
                browse_data = self.get_browse_to_data(esdl_object)
                emit('esdl_browse_to', browse_data, namespace='/esdl')

        @self.socketio.on('esdl_browse_get_objectinfo_fragment', namespace='/esdl')
        def socketio_get_objectinfo_fragment(message):
            esdl_object = self.get_object_from_identifier(message)
            browse_data = self.get_browse_to_data(esdl_object)
            emit('esdl_browse_to', browse_data, namespace='/esdl')

        @self.socketio.on('esdl_browse_create_object', namespace='/esdl')
        def socketio_create_object(message):
            # {'parent': {'id': parent_object.id, 'fragment': parent_object.fragment}, 'name': reference_data.name, 'type': types[0]}
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            parent_object = self.get_object_from_identifier(message['parent'])
            reference_name = message['name']
            attribute = parent_object.eClass.findEStructuralFeature(reference_name)
            if attribute is not None:
                object_type = message['type']
                new_object = ESDLEcore.instantiate_type(object_type)
                if attribute.many:
                    eOrderedSet = parent_object.eGet(reference_name)
                    eOrderedSet.append(new_object)
                else:
                    parent_object.eSet(reference_name, new_object)
            else:
                print("Error: Can't find reference {} of {}", reference_name, parent_object.name)
                return
            if hasattr(new_object, 'id'):
                new_object.id = esh.generate_uuid()
                esh.add_object_to_dict(active_es_id, new_object)
                print('adding to uuid dict ' + new_object.id)
            if hasattr(new_object, 'name'):
                new_object.name = 'New' + new_object.eClass.name
            browse_data = self.get_browse_to_data(new_object)
            emit('esdl_browse_to', browse_data, namespace='/esdl')

        @self.socketio.on('esdl_browse_delete_ref', namespace='/esdl')
        def socket_io_delete_ref(message):
            # esdl_browse_delete_ref
            active_es_id = get_session('active_es_id')
            esh = get_handler()
            reference_name = message['name']
            ref_object = self.get_object_from_identifier(message['ref_id'])
            parent_object = self.get_object_from_identifier(message['parent'])
            reference: EReference = parent_object.eClass.findEStructuralFeature(reference_name)
            if reference.containment:
                esh.remove_object_from_dict(active_es_id, ref_object)
                ref_object.delete(recursive=True) # will automatically remove the reference from the list
            else:
                if reference.many:
                    eOrderedSet = parent_object.eGet(reference)
                    eOrderedSet.remove(ref_object)
                else:
                    parent_object.eSet(reference, reference.get_default_value())

            browse_data = self.get_browse_to_data(parent_object)
            emit('esdl_browse_to', browse_data, namespace='/esdl')


        #'esdl_browse_list_references'
        @self.socketio.on('esdl_browse_list_references', namespace='/esdl')
        def socket_io_list_references(message):
            reference_name = message['name']
            parent_object = self.get_object_from_identifier(message['parent'])
            reference = parent_object.eClass.findEStructuralFeature(reference_name)
            if reference is not None:
                types = ESDLEcore.find_types(reference)
                print("Creating list of references")
                reference_list = ESDLEcore.get_reachable_references(types, repr_function=ESDLBrowser.generate_repr)
                returnmsg = {'parent': message['parent'],
                             'ref': {'name': reference_name, 'type': reference.eType.eClass.name},
                             'xreferences': reference_list}
                print (returnmsg)
                emit('esdl_browse_select_cross_reference', returnmsg, namespace='/esdl')


        #esdl_browse_set_reference
        @self.socketio.on('esdl_browse_set_reference', namespace='/esdl')
        def socket_io_set_xreference(message):
            #{'parent': parent_object_identifier, 'name': data.ref.name, 'xref': data.xreferences[selected_ref]});
            parent_object: EObject = self.get_object_from_identifier(message['parent'])
            reference = parent_object.eClass.findEStructuralFeature(message['name'])
            print(get_handler().get_resource(get_session('active_es_id')).uuid_dict)
            xref = self.get_object_from_identifier(message['xref'])
            if not reference.many:
                parent_object.eSet(reference, xref)
            else:
                eOrderedSet = parent_object.eGet(reference)
                eOrderedSet.append(xref)
            browse_data = self.get_browse_to_data(parent_object)
            emit('esdl_browse_to', browse_data, namespace='/esdl')

    def get_object_from_identifier(self, identifier):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        if 'id' in identifier:
            object_id = identifier['id']
            #object_id is not None:
            try:
                the_object = esh.get_by_id(active_es_id, object_id)
            except KeyError:
                print('KeyError for getting id {} in uuid_dict. Trying fragment.', object_id)
                resource = esh.get_resource(active_es_id)
                the_object = resource.resolve(identifier['fragment'])
        else:
            resource = esh.get_resource(active_es_id)
            the_object = resource.resolve(identifier['fragment'])

        return the_object

    def get_browse_to_data(self, esdl_object):
        active_es_id = get_session('active_es_id')
        esdl_object_descr = self.get_object_dict(esdl_object)
        container = esdl_object.eContainer()
        container_descr = self.get_container_dict(container)
        attributes = ESDLEcore.get_asset_attributes(esdl_object, self.esdl_doc)
        references = ESDLEcore.get_asset_references(esdl_object, self.esdl_doc, ESDLBrowser.generate_repr)
        return {'es_id': active_es_id,
                'object': esdl_object_descr,
                'attributes': attributes,
                'references': references,
                'container': container_descr}


    def get_container_dict(self, container):
        if container is None:
            return None
        c_dict = {'doc': container.__doc__, 'type': container.eClass.name,}
        if hasattr(container, 'name'):
            c_dict['name']= container.name
        else:
            c_dict['name'] = None
        if not hasattr(container, 'id') or container.id is None:
            c_dict['fragment'] = container.eURIFragment()
        else:
            c_dict['id'] = container.id
        if container.eContainer() is not None:
            c_dict['container'] = self.get_container_dict(container.eContainer())
        return c_dict

    def get_object_dict(self, esdl_object):
        if not hasattr(esdl_object, 'name'):
            name = esdl_object.eClass.name
        else:
            name = esdl_object.name

        object_dict = {'name': name,
                        'doc': esdl_object.__doc__,
                        'type': esdl_object.eClass.name
                        }
        if not hasattr(esdl_object, 'id'):
            object_dict['id'] = None
            object_dict['fragment'] = esdl_object.eURIFragment()
        else:
            object_dict['id'] = esdl_object.id
        return object_dict

    @staticmethod
    def generate_repr(item):
        """
         Simple function to create a representation of an object
         """
        if item is None:
            return item
        if isinstance(item, esdl.Port):
            name = item.name
            if name is None:
                name = item.eClass.name
            return name + ' of ' + item.energyasset.eClass.name + " " + ESDLBrowser.generate_repr(item.energyasset)
        if isinstance(item, esdl.QuantityAndUnitType):
            return qau_to_string(item)
        if hasattr(item, 'name') and item.name is not None:
            return item.name
        #if hasattr(item, 'id') and item.id is not None:
        #    return item.eClass.name + ' (id=' + item.id + ')'
        return item.eClass.name
