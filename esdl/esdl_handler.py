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

from pyecore.resources import ResourceSet, URI
from pyecore.ecore import EEnum, EAttribute, EObject, EReference, EClass, EStructuralFeature
from pyecore.valuecontainer import ECollection
from pyecore.utils import alias
from pyecore.resources.resource import HttpURI
from esdl.resources.xmlresource import XMLResource
from esdl import esdl
from uuid import uuid4
from io import BytesIO
import src.log as log
from esdl import support_functions

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = log.get_logger(__name__)


class EnergySystemHandler:

    def __init__(self, energy_system=None):
        if energy_system is not None:
            self.energy_system = energy_system
        self.resource = None
        self.rset = ResourceSet()
        self.esid_uri_dict = {}

        self._set_resource_factories()

        # fix python builtin 'from' that is also used in ProfileElement as attribute
        # use 'start' instead of 'from' when using a ProfileElement
        # and make sure that it is serialized back as 'from' instead of 'from_'
        esdl.ProfileElement.from_.name = 'from'
        setattr(esdl.ProfileElement, 'from', esdl.ProfileElement.from_)
        alias('start', esdl.ProfileElement.from_)
        # also for FromToIntItem
        esdl.FromToIntItem.from_.name = 'from'
        setattr(esdl.FromToIntItem, 'from', esdl.FromToIntItem.from_)
        alias('start', esdl.FromToIntItem.from_)
        # also for FromToDoubleItem
        esdl.FromToDoubleItem.from_.name = 'from'
        setattr(esdl.FromToDoubleItem, 'from', esdl.FromToDoubleItem.from_)
        alias('start', esdl.FromToDoubleItem.from_)

        # add support for cloning of EObjects and coppy.copy()
        setattr(EObject, '__copy__', support_functions.clone)
        setattr(EObject, 'clone', support_functions.clone)

        # add support for deepcopying EObjects and copy.deepcopy()
        setattr(EObject, '__deepcopy__', support_functions.deepcopy)
        setattr(EObject, 'deepcopy', support_functions.deepcopy)

        # have a nice __repr__ for some ESDL classes when printing ESDL objects (includes all Assets and EnergyAssets)
        esdl.EnergySystem.__repr__ = \
            lambda x: '{}: ({})'.format(x.name, EnergySystemHandler.attr_to_dict(x))

    def _new_resource_set(self):
        """Resets the resourceset (e.g. when loading a new file)"""
        self.rset = ResourceSet()
        self.resource = None
        self._set_resource_factories()

    def _set_resource_factories(self):
        # Assign files with the .esdl extension to the XMLResource instead of default XMI
        self.rset.resource_factory['esdl'] = XMLResource
        self.rset.resource_factory['*'] = XMLResource

    def load_file(self, uri_or_filename) -> (esdl.EnergySystem, []):
        """Loads a EnergySystem file or URI into a new resourceSet
        :returns EnergySystem and the parse warnings as a tuple (es, parse_info)"""
        if isinstance(uri_or_filename, str):
            if uri_or_filename[:4] == 'http':
                uri = HttpURI(uri_or_filename)
            else:
                uri = URI(uri_or_filename)
        else:
            uri = uri_or_filename
        return self.load_uri(uri)

    def import_file(self, uri_or_filename):
        """
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
        """
        if isinstance(uri_or_filename, str):
            if uri_or_filename[:4] == 'http':
                uri = HttpURI(uri_or_filename)
            else:
                uri = URI(uri_or_filename)
        else:
            uri = uri_or_filename
        return self.add_uri(uri)

    def load_uri(self, uri) -> (esdl.EnergySystem, []):
        """Loads a new resource in a new resourceSet
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
        """
        self._new_resource_set()
        self.resource = self.rset.get_resource(uri)
        parse_info = []
        if isinstance(self.resource, XMLResource):
            parse_info = self.resource.get_parse_information()
        # At this point, the model instance is loaded!
        self.energy_system = self.resource.contents[0]
        if isinstance(uri, str):
            self.esid_uri_dict[self.energy_system.id] = uri
        else:
            self.esid_uri_dict[self.energy_system.id] = uri.normalize()
        self.add_object_to_dict(self.energy_system.id, self.energy_system, False)
        return self.energy_system, parse_info

    def add_uri(self, uri):
        """
        Adds the specified URI to the resource set, i.e. load extra resources that the resource can refer to.
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
        """
        tmp_resource = self.rset.get_resource(uri)
        parse_info = []
        if isinstance(tmp_resource, XMLResource):
            parse_info = tmp_resource.get_parse_information()
        # At this point, the model instance is loaded!
        # self.energy_system = self.resource.contents[0]
        self.validate(es=tmp_resource.contents[0])
        if isinstance(uri, str):
            self.esid_uri_dict[tmp_resource.contents[0].id] = uri
        else:
            self.esid_uri_dict[tmp_resource.contents[0].id] = uri.normalize()
        # Edwin: recursive moet hier toch False zijn?? immers elke resource heeft zijn eigen uuid_dict
        # Ewoud: precies, dus in False veranderd
        self.add_object_to_dict(tmp_resource.contents[0].id, tmp_resource.contents[0], False)
        return tmp_resource.contents[0], parse_info

    def load_from_string(self, esdl_string, name='from_string'):
        """
        Loads an energy system from a string and adds it to a *new* resourceSet
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
         """
        if name == '': name = str(uuid4())
        uri = StringURI(name+'.esdl', esdl_string)
        self._new_resource_set()
        self.resource = self.rset.create_resource(uri)
        try:
            self.resource.load()
            self.energy_system = self.resource.contents[0]
            parse_info = []
            if isinstance(self.resource, XMLResource):
                parse_info = self.resource.get_parse_information()
            self.validate()
            self.esid_uri_dict[self.energy_system.id] = uri.normalize()
            # set to False, otherwise all the ids are added again after loading, is not smart and is slow
            # is only here to make sure the id of the energy system is also in the uuid_dict
            self.add_object_to_dict(self.energy_system.id, self.energy_system, False)
            return self.energy_system, parse_info
        except Exception as e:
            logger.error("Exception when loading resource: {}: {}".format(name, e))
            raise

    def load_external_string(self, esdl_string, name='from_string'):
        """Loads an energy system from a string but does NOT add it to the resourceSet (e.g. as a separate resource)
        It returns an Energy System and parse info as a tuple, but the ES is not part of a resource in the ResourceSet
        """
        uri = StringURI(name+'.esdl', esdl_string)
        external_rset = ResourceSet()
        external_resource = external_rset.create_resource(uri)
        external_resource.load()
        parse_info = []
        if isinstance(external_resource, XMLResource):
            parse_info = external_resource.get_parse_information()
        external_energy_system = external_resource.contents[0]
        self.validate(es=external_energy_system)
        return external_energy_system, parse_info

    def add_from_string(self, name, esdl_string):
        """Loads an energy system from a string and adds it to the *existing* resourceSet
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
        """
        print("Adding new ESDL system", name)
        uu = str(uuid4())[:4]
        uri = StringURI(name + '.esdl', esdl_string)
        if uri in self.rset.resources:
            uri = StringURI(name + uu + '.esdl', esdl_string)
        # self.add_uri(uri)
        try:
            tmp_resource = self.rset.get_resource(uri)
            parse_info = []
            if isinstance(tmp_resource, XMLResource):
                parse_info = tmp_resource.get_parse_information()
            tmp_es = tmp_resource.contents[0]
            if tmp_es.id in self.esid_uri_dict:
                print("Detected duplicate Energy System id, adapting to a new one.")
                tmp_es.id = tmp_es.id + uu
                tmp_es.name = tmp_es.name + '_' + uu
            self.validate(es=tmp_es)
            self.esid_uri_dict[tmp_es.id] = uri.normalize()
            self.add_object_to_dict(tmp_es.id, tmp_es, True)
            return tmp_resource.contents[0], parse_info
        except Exception as e:
            logger.error("Exception when loading resource: {}: {}".format(name, e))
            raise


    def to_string(self, es_id=None):
        # to use strings as resources, we simulate a string as being a URI
        uri = StringURI('to_string_'+str(uuid4())+'.esdl')
        if es_id is None:
            self.resource.save(uri)
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                resource = self.rset.resources[my_uri]
                resource.save(uri)
            else:
                # TODO: what to do? original behaviour
                self.resource.save(uri)
        # return the string
        return uri.getvalue()

    def to_bytesio(self):
        """Returns a BytesIO stream for the energy system"""
        uri = StringURI('bytes_io_to_string.esdl')
        self.resource.save(uri)
        return uri.get_stream()

    def save(self, es_id=None, filename=None):
        """Add the resource to the resourceSet when saving"""
        if filename is None:
            if es_id is None:
                self.resource.save()
            else:
                if es_id in self.esid_uri_dict:
                    my_uri = self.esid_uri_dict[es_id]
                    resource = self.rset.resources[my_uri]
                    resource.save()
                else:
                    # TODO: what to do? original behaviour
                    self.resource.save()
        else:
            uri = URI(filename)
            fileresource = self.rset.create_resource(uri)
            if es_id is None:
                # add the current energy system
                fileresource.append(self.energy_system)
            else:
                if es_id in self.esid_uri_dict:
                    my_uri = self.esid_uri_dict[es_id]
                    es = self.rset.resources[my_uri].contents[0]
                    fileresource.append(es)
                else:
                    # TODO: what to do? original behaviour
                    # add the current energy system
                    fileresource.append(self.energy_system)
            # save the resource
            fileresource.save()
            self.rset.remove_resource(fileresource)

    def save_as(self, filename):
        """Saves the resource under a different filename"""
        self.resource.save(output=filename)

    def save_resourceSet(self):
        """Saves the complete resourceSet, including additional loaded resources encountered during loading of the
        initial resource"""
        for uri, resource in self.rset.resources.items():
            logger.info('Saving {}'.format(uri))
            resource.save()  # raises an Error for HTTP URI, but not for CDOHttpURI

    def get_resource(self, es_id=None):
        if es_id is None:
            return self.resource
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                res = self.rset.resources[my_uri]
                return res
            else:
                return None

    def get_energy_system(self, es_id=None):
        if es_id is None:
            return self.energy_system
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                es = self.rset.resources[my_uri].contents[0]
                return es
            else:
                return None

    def remove_energy_system(self, es_id=None):
        if es_id is None:
            return
        else:
            my_uri = self.esid_uri_dict[es_id]
            print(my_uri)
            del self.rset.resources[my_uri]
            print(self.rset.resources)
            del self.esid_uri_dict[es_id]

    def get_energy_systems(self):
        es_list = []
        # for esid in self.esid_uri_dict:
        #    uri = self.esid_uri_dict[esid]
        #    es_list.append(self.rset.resources[uri])

        for key in self.rset.resources.keys():
            es_list.append(self.rset.resources[key].contents[0])
        return es_list

    def validate(self, es=None):
        if es is None and self.energy_system is not None:
            es = self.energy_system
        if es is not None:
            if es.id is None:
                es.id = str(uuid4())
                logger.warning("Energysystem has no id, generating one: {}".format(es))
        else:
            logger.warning("Can't validate EnergySystem {}".format(es))

    # Using this function you can query for objects by ID
    # After loading an ESDL-file, all objects that have an ID defines are stored in resource.uuid_dict automatically
    # Note: If you add things later to the resource, it won't be added automatically to this dictionary though.
    # Use get_by_id_slow() for that or add them manually using add_object_to_dict()
    def get_by_id(self, es_id, object_id):
        if object_id in self.get_resource(es_id).uuid_dict:
            return self.get_resource(es_id).uuid_dict[object_id]
        else:
            logger.error('Can\'t find asset for id={} in uuid_dict of the ESDL model'.format(object_id))
            #print(self.get_resource(es_id).uuid_dict)
            raise KeyError('Can\'t find asset for id={} in uuid_dict of the ESDL model'.format(object_id))
            return None

    def add_object_to_dict(self, es_id: str, esdl_object: EObject, recursive=False):
        if recursive:
            for obj in esdl_object.eAllContents():
                self.add_object_to_dict(es_id, obj)
        if hasattr(esdl_object, 'id'):
            if esdl_object.id is not None:
                self.get_resource(es_id).uuid_dict[esdl_object.id] = esdl_object
            else:
                logger.warning('Id has not been set for object {}({})'.format(esdl_object.eClass.name, esdl_object))

    def remove_object_from_dict(self, es_id, esdl_object: EObject, recursive=False):
        if recursive:
            for obj in esdl_object.eAllContents():
                self.remove_object_from_dict(es_id, obj)
        if hasattr(esdl_object, 'id'):
            if esdl_object.id is not None and self.get_resource(es_id):
                del self.get_resource(es_id).uuid_dict[esdl_object.id]

    def remove_object_from_dict_by_id(self, es_id, object_id):
        del self.get_resource(es_id).uuid_dict[object_id]

    # returns a generator of all assets of a specific type. Not only the ones defined in  the main Instance's Area
    # e.g. QuantityAndUnits can be defined in the KPI of an Area or in the EnergySystemInformation object
    # this function returns all of them at once
    # @staticmethod
    def get_all_instances_of_type(self, esdl_type, es_id):
        all_instances = list()
        for esdl_element in self.get_energy_system(es_id=es_id).eAllContents():
            if isinstance(esdl_element, esdl_type):
                all_instances.append(esdl_element)
        return all_instances
        #return esdl_type.allInstances()

    # Creates a dict of all the attributes of an ESDL object, useful for printing/debugging
    @staticmethod
    def attr_to_dict(esdl_object):
        d = dict()
        d['esdlType'] = esdl_object.eClass.name
        for attr in dir(esdl_object):
            attr_value = esdl_object.eGet(attr)
            if attr_value is not None:
                d[attr] = attr_value
        return d

    # Creates a uuid: useful for generating unique IDs
    @staticmethod
    def generate_uuid():
        return str(uuid4())

    def create_empty_energy_system(self, name, es_description, inst_title, area_title, esdlVersion=None):
        es_id = str(uuid4())
        self.energy_system = esdl.EnergySystem(id=es_id, name=name, description=es_description, esdlVersion=esdlVersion)

        uri = StringURI('empty_energysystem.esdl')
        self.resource = self.rset.create_resource(uri)
        # add the current energy system
        self.resource.append(self.energy_system)
        self.esid_uri_dict[self.energy_system.id] = uri.normalize()

        instance = esdl.Instance(id=str(uuid4()), name=inst_title)
        self.energy_system.instance.append(instance)

        # TODO: check if this (adding scope) solves error????
        area = esdl.Area(id=str(uuid4()), name=area_title, scope=esdl.AreaScopeEnum.from_string('UNDEFINED'))
        instance.area = area

        # add generated id's to uuid dict
        self.add_object_to_dict(es_id, self.energy_system)
        self.add_object_to_dict(es_id, instance)
        self.add_object_to_dict(es_id, area)

        return self.energy_system

    # Support for Pickling when serializing the energy system in a session
    # The pyEcore classes by default do not allow for simple serialization for Session management in Flask.
    # Internally Flask Sessions use Pickle to serialize a data structure by means of its __dict__. This does not work.
    # Furthermore, ESDL can contain cyclic relations. Therefore we serialize to XMI and back if necessary.
    def __getstate__(self):
        state = dict()
        #print('Serialize rset {}'.format(self.rset.resources))
        print('Serializing EnergySystem...', end ="")
        state['energySystem'] = self.to_string()
        print('done')
        return state

    def __setstate__(self, state):
        self.__init__()
        #print('Deserialize rset {}'.format(self.rset.resources))
        print('Deserializing EnergySystem...', end="")
        self.load_from_string(state['energySystem'])
        print('done')


    def update_version(self, es_id) -> str:
        """
        Increments the version of this Energy System and returns it

        """
        es = self.get_energy_system(es_id)
        version = '' if es.version is None else str(es.version)
        try:
            import re
            splitted = re.split(r"\D", version)
            print(splitted)
            major = splitted[0]
            major = int(major) + 1
        except ValueError:
            major = 1
        es.version = str(major)
        return es.version




class StringURI(URI):
    def __init__(self, uri, text=None):
        super(StringURI, self).__init__(uri)
        if text is not None:
            self.__stream = BytesIO(text.encode('UTF-8'))

    def getvalue(self):
        readbytes = self.__stream.getvalue()
        # somehow stringIO does not work, so we use BytesIO
        string = readbytes.decode('UTF-8')
        return string

    def create_instream(self):
        return self.__stream

    def create_outstream(self):
        self.__stream = BytesIO()
        return self.__stream

    def get_stream(self):
        return self.__stream