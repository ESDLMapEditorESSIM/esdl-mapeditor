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

from esdl.processing.ESDLEcore import instantiate_type
from esdl.processing.ESDLQuantityAndUnits import unit_to_string, build_qau_from_unit_string, get_or_create_esi_qau
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
from utils.utils import camelCaseToWords, str2float

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

    def get_or_create_qau(self, qau_id):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        try:
            qau = esh.get_by_id(active_es_id, qau_id)
            return qau
        except KeyError:
            # qua does not exist, create it
            global_qua = get_or_create_esi_qau(esh, active_es_id)
            if qau_id == 'flow':
                qau = esdl.QuantityAndUnitType(id=qau_id)
                qau.physicalQuantity = esdl.PhysicalQuantityEnum.FLOW
                qau.unit = esdl.UnitEnum.CUBIC_METRE
                qau.perTimeUnit = esdl.TimeUnitEnum.HOUR
                qau.description = "Flow in m³/h"
            if qau_id == 'head':
                qau = esdl.QuantityAndUnitType(id=qau_id)
                qau.physicalQuantity = esdl.PhysicalQuantityEnum.HEAD
                qau.unit = esdl.UnitEnum.METRE
                qau.description = "Head in m"
            if qau_id == 'efficiency':
                qau = esdl.QuantityAndUnitType(id=qau_id)
                qau.physicalQuantity = esdl.PhysicalQuantityEnum.COEFFICIENT
                qau.unit = esdl.UnitEnum.PERCENT
                qau.description = "Efficiency in %"
            if qau_id == 'position':
                qau = esdl.QuantityAndUnitType(id=qau_id)
                qau.physicalQuantity = esdl.PhysicalQuantityEnum.POSITION
                qau.unit = esdl.UnitEnum.NONE
                qau.description = "Position [-]"
            if qau_id == 'kv_coefficient':
                qau = esdl.QuantityAndUnitType(id=qau_id)
                qau.physicalQuantity = esdl.PhysicalQuantityEnum.COEFFICIENT
                qau.unit = esdl.UnitEnum.CUBIC_METRE
                qau.perTimeUnit = esdl.TimeUnitEnum.HOUR
                qau.perUnit = esdl.UnitEnum.BAR
                qau.description = "Coefficient in m³/h/bar"
            global_qua.quantityAndUnit.append(qau)
            esh.add_object_to_dict(active_es_id, qau)
            return qau



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
            c_dict['name'] = container.name
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

    def get_recently_used_edr_assets(self):
        recently_used_edr_assets = get_session('recently_used_edr_assets')
        if recently_used_edr_assets is None:
            recently_used_edr_assets = list()
        return recently_used_edr_assets

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

    def get_default_qau_for_env_profile(self, name):
        # Note: Spelling mistake in ESDL: outsideTemparatureProfile instead of outsideTemperatureProfile
        if name == 'outsideTemparatureProfile' or name == 'soilTemperatureProfile':
            return "\u2103"     # Sign for degrees Celcius
        if name == 'solarIrradianceProfile':
            return "W/m2"
        if name == 'relativeHumidityProfile':
            return "%"
        if name == 'windDirectionProfile':
            return ""       # No degrees as unit in ESDL yet
        if name == 'windSpeedProfile':
            return "m/s"
        return ""

    def update_quantity_in_qau(self, qau, name):
        # Note: Spelling mistake in ESDL: outsideTemparatureProfile instead of outsideTemperatureProfile
        if name == 'outsideTemparatureProfile' or name == 'soilTemperatureProfile':
            qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string('TEMPERATURE')
        if name == 'solarIrradianceProfile':
            qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string('IRRADIANCE')
        if name == 'relativeHumidityProfile':
            qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string('RELATIVE_HUMIDITY')
        if name == 'windDirectionProfile':
            qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string('DIRECTION')
        if name == 'windSpeedProfile':
            qau.physicalQuantity = esdl.PhysicalQuantityEnum.from_string('SPEED')

    def get_environmental_profiles(self):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        result = list()

        es = esh.get_energy_system(active_es_id)
        esi = es.energySystemInformation

        for x in esdl.EnvironmentalProfiles.eClass.eAllStructuralFeatures():
            if isinstance(x, EReference):
                ep_instance = dict()
                ep_instance['key'] = str(uuid4())
                ep_instance['name'] = x.name
                ep_instance['uiname'] = camelCaseToWords(x.name)
                ep_instance['type'] = 'Unset'
                ep_instance['default_unit'] = self.get_default_qau_for_env_profile(x.name)

                if esi and esi.environmentalProfiles:
                    env_profiles = esi.environmentalProfiles
                    profile = env_profiles.eGet(x)
                    if profile:
                        if isinstance(profile, esdl.SingleValue):
                            ep_instance['type'] = 'SingleValue'
                            ep_instance['value'] = profile.value
                        elif isinstance(profile, esdl.InfluxDBProfile):
                            ep_instance['type'] = 'InfluxDBProfile'
                            # check if it is a 'standard profile' that is present in our configuration
                            profiles = Profiles.get_instance().get_profiles()['profiles']
                            for pkey in profiles:
                                std_profile = profiles[pkey]
                                if profile.database == std_profile['database'] and \
                                    profile.measurement == std_profile['measurement'] and \
                                    profile.field == std_profile['field']:
                                    ep_instance['profile_id'] = pkey
                        else:
                            logger.warn('Environmental profiles other than SingleValue/InfluxDB are not supported')
                            ep_instance['value'] = ''

                        if profile.profileQuantityAndUnit:
                            qau = profile.profileQuantityAndUnit
                            if isinstance(qau, esdl.QuantityAndUnitReference):
                                qau = qau.reference
                            ep_instance['unit'] = unit_to_string(qau)
                        else:
                            ep_instance['unit'] = ''

                    else:
                        ep_instance['value'] = ''

                result.append(ep_instance)

        return result

    def update_environmental_profiles(self, action, profile_info):
        active_es_id = get_session('active_es_id')
        esh = get_handler()

        es = esh.get_energy_system(active_es_id)
        esi = es.energySystemInformation

        print(profile_info)

        if action == 'save':
            for x in esdl.EnvironmentalProfiles.eClass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    if profile_info['name'] == x.name:
                        if not esi:
                            esi = es.energySystemInformation = esdl.EnergySystemInformation(id=str(uuid4()))
                            esh.add_object_to_dict(active_es_id, esi)
                        if not esi.environmentalProfiles:
                            esi.environmentalProfiles = esdl.EnvironmentalProfiles(id=str(uuid4()))
                            esh.add_object_to_dict(active_es_id, esi.environmentalProfiles)
                        env_profiles = esi.environmentalProfiles

                        profile = env_profiles.eGet(x)
                        if not profile:
                            profile = instantiate_type(profile_info['type'])
                            profile.id = str(uuid4())
                            esh.add_object_to_dict(active_es_id, profile)
                        else:
                            if type(profile) != profile_info['type']:
                                profile = instantiate_type(profile_info['type'])

                        if isinstance(profile, esdl.SingleValue):
                            profile.value = str2float(profile_info['value'])
                        if isinstance(profile, esdl.InfluxDBProfile):
                            std_profiles = Profiles.get_instance().get_profiles()['profiles']
                            if profile_info['profile_id'] in std_profiles:
                                std_profile = std_profiles[profile_info['profile_id']]
                                print(std_profile)

                                profile.id = str(uuid4())
                                profile.name = std_profile.name
                                profile.host = std_profile.host
                                profile.port = std_profile.port
                                profile.database = std_profile.database
                                profile.measurement = std_profile.measurement
                                profile.field = std_profile.field
                                profile.filters = std_profile.filters
                                profile.startDate = std_profile.startDate
                                profile.endDate = std_profile.endDate
                            else:
                                logger.error('Profile is referenced that was not communicated before')

                        # Create a QuantityAndUnit instance and set the unit based on the information received
                        if 'unit' in profile_info:
                            profile.profileQuantityAndUnit = build_qau_from_unit_string(profile_info['unit'])
                            esh.add_object_to_dict(active_es_id, profile.profileQuantityAndUnit)
                        elif 'default_unit' in profile_info:
                            profile.profileQuantityAndUnit = build_qau_from_unit_string(profile_info['default_unit'])
                            esh.add_object_to_dict(active_es_id, profile.profileQuantityAndUnit)

                        # Set the physical quantity based on the name of the profile reference
                        self.update_quantity_in_qau(profile.profileQuantityAndUnit, x.name)
                        env_profiles.eSet(x, profile)
        elif action == 'delete':
            env_profile_refname = profile_info['name']
            env_profiles = esi.environmentalProfiles
            env_profiles.eSet(env_profile_refname, None)
        else:
            logger.error('Unknown action on environmental profiles')
