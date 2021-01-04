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

from uuid import uuid4
from esdl.processing import ESDLEcore
from pyecore.ecore import EReference
from esdl.processing.EcoreDocumentation import EcoreDocumentation
from extensions.esdl_browser import ESDLBrowser # for repr function
from extensions.session_manager import get_handler, get_session
from extensions.profiles import Profiles
from extensions.vue_backend.object_properties import get_object_properties_info
from extensions.vue_backend.cost_information import get_cost_information
from extensions.vue_backend.table_data import get_table_data, set_table_data
from extensions.vue_backend.messages.DLA_table_data_message import DLA_table_data_request, DLA_table_data_response, \
    DLA_set_table_data_request
from extensions.vue_backend.messages.DLA_delete_ref_message import DeleteRefMessage
from extensions.vue_backend.messages.identifier_message import Identifier
from src.esdl_helper import get_port_profile_info, get_connected_to_info
from src.view_modes import ViewModes
import esdl.esdl
import src.log as log


logger = log.get_logger(__name__)


class ESDLDataLayer:
    def __init__(self, esdl_doc: EcoreDocumentation):
        self.esdl_doc = esdl_doc
        pass

    def get_object_info_by_identifier(self, identifier: Identifier):
        esdl_object = self.get_object_from_identifier(identifier)
        return self.get_object_info(esdl_object)

    def get_object_parameters_by_identifier(self, identifier: Identifier):
        esdl_object = self.get_object_from_identifier(identifier)
        obj_info = self.get_object_info(esdl_object)
        attrs = obj_info['attributes']
        refs = obj_info['references']
        self._convert_attributes_to_primitive_types(attrs)

        view_mode = ViewModes.get_instance()
        cat_attrs = view_mode.categorize_object_attributes_and_references(esdl_object, attrs, refs)

        # Is this the right way?
        obj_info['attributes'] = cat_attrs

        if isinstance(esdl_object, esdl.EnergyAsset):
            obj_info['port_profile_info'] = get_port_profile_info(esdl_object)
            obj_info['port_connected_to_info'] = get_connected_to_info(esdl_object)
        else:
            obj_info['port_profile_info'] = list()
            obj_info['port_connected_to_info'] = list()

        if isinstance(esdl_object, esdl.Asset):
            obj_info['cost_information'] = get_cost_information(esdl_object)

        return obj_info

    def set_object_parameters_by_identifier(self, identifier: Identifier, parameters):
        esdl_object = self.get_object_from_identifier(identifier)

        # TODO: implement

    def get_standard_profiles_list(self):
        profiles = Profiles.get_instance().get_profiles()['profiles']
        profiles_list = list()
        for pkey in profiles:
            p = profiles[pkey]
            profiles_list.append({
                'id': pkey,
                'name': p['profile_uiname']
            })
        return profiles_list

    def get_datetime_profile(self):
        pass

    @staticmethod
    def get_area_object_list_of_type(type):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        
        es = esh.get_energy_system(active_es_id)
        area = es.instance[0].area
        object_list = list()
        for area_asset in area.eAllContents():
            if isinstance(area_asset, type):
                object_list.append({'id': area_asset.id, 'name': area_asset.name})
        return object_list       

    @staticmethod
    def remove_control_strategy(asset):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        cs = asset.controlStrategy
        if cs:
            services = cs.eContainer()
            services.service.remove(cs)
            esh.remove_object_from_dict(active_es_id, cs)
            asset.controlStrategy = None

    def get_services(self):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        es = esh.get_energy_system(active_es_id)
        services = es.services
        if not services:
            services = esdl.Services(id=str(uuid4()))
            es.services = services
        return services

    def get_table(self, message: DLA_table_data_request) -> DLA_table_data_response:
        esdl_object = self.get_object_from_identifier(message.parent_id)
        return get_table_data(self, esdl_object, message)

    def set_table(self, message: DLA_set_table_data_request):
        esdl_object = self.get_object_from_identifier(message.parent_id)
        set_table_data(self, esdl_object, message)

    def delete_ref(self, message: DeleteRefMessage):
        parent_object = self.get_object_from_identifier(message.parent)
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        reference: EReference = parent_object.eClass.findEStructuralFeature(message.ref_name)
        ref_object = parent_object.eGet(reference)
        print('deleting', message, ref_object)
        if reference.containment:
            try:
                esh.remove_object_from_dict(active_es_id, ref_object)
                resource = esh.get_resource(active_es_id)
                fragment = ref_object.eURIFragment()
                del resource._resolve_mem[fragment] # update fragment cache for pyecore<0.12.0
            except KeyError as e:
                print('ESDL Browser: can\'t delete id from uuid_dict', e)
            ref_object.delete(recursive=True)  # will automatically remove the reference from the list
        else:
            if reference.many:
                eOrderedSet = parent_object.eGet(reference)
                eOrderedSet.remove(ref_object)
            else:
                parent_object.eSet(reference, reference.get_default_value())
        # send updated reference description to frontend
        response = ESDLEcore.describe_reference_value(parent_object.eGet(reference), ESDLBrowser.generate_repr)
        print('delete ref response', response)
        return response

    def get_or_create_qau(self, qua_id):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        try:
            qua = esh.get_by_id(active_es_id, qua_id)
            return qua
        except KeyError:
            # qua does not exist, create it
            global_qua = self.get_or_create_esi_qau()
            if qua_id == 'flow':
                qua = esdl.QuantityAndUnitType(id=qua_id)
                qua.physicalQuantity = esdl.PhysicalQuantityEnum.FLOW
                qua.unit = esdl.UnitEnum.CUBIC_METRE
                qua.perTimeUnit = esdl.TimeUnitEnum.HOUR
                qua.description = "Flow in m³/h"
            if qua_id == 'head':
                qua = esdl.QuantityAndUnitType(id=qua_id)
                qua.physicalQuantity = esdl.PhysicalQuantityEnum.HEAD
                qua.unit = esdl.UnitEnum.METRE
                qua.description = "Head in m"
            if qua_id == 'efficiency':
                qua = esdl.QuantityAndUnitType(id=qua_id)
                qua.physicalQuantity = esdl.PhysicalQuantityEnum.COEFFICIENT
                qua.unit = esdl.UnitEnum.PERCENT
                qua.description = "Efficiency in %"
            if qua_id == 'position':
                qua = esdl.QuantityAndUnitType(id=qua_id)
                qua.physicalQuantity = esdl.PhysicalQuantityEnum.POSITION
                qua.unit = esdl.UnitEnum.NONE
                qua.description = "Position [-]"
            if qua_id == 'kv_coefficient':
                qua = esdl.QuantityAndUnitType(id=qua_id)
                qua.physicalQuantity = esdl.PhysicalQuantityEnum.COEFFICIENT
                qua.unit = esdl.UnitEnum.CUBIC_METRE
                qua.perTimeUnit = esdl.TimeUnitEnum.HOUR
                qua.perUnit = esdl.UnitEnum.BAR
                qua.description = "Coefficient in m³/h/bar"
            global_qua.quantityAndUnit.append(qua)

            return qua

    def get_or_create_esi_qau(self):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        es: esdl.EnergySystem = esh.get_energy_system(active_es_id)
        if not es.energySystemInformation:
            esi: esdl.EnergySystemInformation = esdl.EnergySystemInformation(id=str(uuid4()))
            es.energySystemInformation = esi
        if not es.energySystemInformation.quantityAndUnits:
            qua = esdl.QuantityAndUnits(id=str(uuid4()))
            es.energySystemInformation.quantityAndUnits = qua
        return es.energySystemInformation.quantityAndUnits

    def get_filtered_type(self, esdl_object, reference):
        """
        :param EObject esdl_object: the esdl class instance (e.g. 'esdl.WindTurbine')
        :param EReference reference: the reference to find the possible types for (e.g. 'controlStrategy')

        :return: list of possible types
        """
        types = []
        reference_type = reference.eType
        if isinstance(reference_type, esdl.ControlStrategy):
            if isinstance(esdl_object, esdl.Producer):
                types.append(esdl.CurtailmentStrategy.eClass.name)
            if isinstance(esdl_object, esdl.Storage):
                types.append(esdl.StorageStrategy.eClass.name)
            if isinstance(esdl_object, esdl.Conversion):
                types.append(esdl.DrivenByDemand.eClass.name)
                types.append(esdl.DrivenBySupply.eClass.name)
                types.append(esdl.DrivenByProfile.eClass.name)
        else:
            types = ESDLEcore.find_types(reference)
        return types

    def get_object_from_identifier(self, identifier: Identifier):
        active_es_id = get_session('active_es_id')
        esh = get_handler()
        if 'id' in identifier:
            object_id = identifier['id']
            try:
                the_object = esh.get_by_id(active_es_id, object_id)
            except KeyError:
                logger.error('KeyError for getting id {} in uuid_dict. Trying fragment.'.format(object_id))
                resource = esh.get_resource(active_es_id)
                the_object = resource.resolve(identifier['fragment'])
        else:
            resource = esh.get_resource(active_es_id)
            the_object = resource.resolve(identifier['fragment'])

        return the_object

    def get_object_info(self, esdl_object):
        esdl_object_descr = self.get_object_dict(esdl_object)
        container = esdl_object.eContainer()
        container_descr = self.get_container_dict(container)
        attributes = ESDLEcore.get_asset_attributes(esdl_object, self.esdl_doc)
        references = ESDLEcore.get_asset_references(esdl_object, self.esdl_doc, ESDLBrowser.generate_repr)
        return {
            'object': esdl_object_descr,
            'attributes': attributes,
            'references': references,
            'container': container_descr
        }
    
    def _convert_attributes_to_primitive_types(self, attributes):
        for attr in attributes:
            if attr['type'] == 'EDouble':
                attr['value'] = float(attr['value'])
                attr['default'] = float(attr['default'])
            if attr['type'] == 'EInt':
                attr['value'] = int(attr['value'])
                attr['default'] = int(attr['default'])

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

        object_dict = {
            'name': name,
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
        if item is None:
            return item
        if isinstance(item, esdl.Port):
            name = item.name
            if name is None:
                name = item.eClass.name
            return name + ' (' + item.eClass.name + ")"
        return item.eClass.name

    def get_asset_list(self):
        view_modes = ViewModes.get_instance()
        return view_modes.get_asset_list()

    def get_profile_names_list(self):
        """Build a list of all profile names in the ESDL file.
        """
        active_es_id = get_session('active_es_id')
        logger.info(active_es_id)
        esh = get_handler()
        energy_system = esh.get_energy_system(es_id=active_es_id)

        instance = energy_system.instance[0]
        profile_fields = []
        if instance and instance.area:
            for asset in instance.area.asset:
                for inner_asset in getattr(asset, 'asset', []):
                    for port in getattr(inner_asset, 'port', []):
                        for profile in getattr(port, 'profile', []):
                            profile_fields.append(profile.field)

        return profile_fields
