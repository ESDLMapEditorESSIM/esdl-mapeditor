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
        # alias('start', esdl.ProfileElement.findEStructuralFeature('from'))
        esdl.ProfileElement.from_.name = 'from'
        setattr(esdl.ProfileElement, 'from', esdl.ProfileElement.from_)
        alias('start', esdl.ProfileElement.from_)

        esdl.FromToIntItem.from_.name = 'from'
        setattr(esdl.FromToIntItem, 'from', esdl.FromToIntItem.from_)
        alias('start', esdl.FromToIntItem.from_)

        esdl.FromToDoubleItem.from_.name = 'from'
        setattr(esdl.FromToDoubleItem, 'from', esdl.FromToDoubleItem.from_)
        alias('start', esdl.FromToDoubleItem.from_)

        # add support for shallow copying or cloning an object
        # it copies the object's attributes (e.g. clone an object), does only shallow copying
        def clone(self):
            """
            Shallow copying or cloning an object
            It only copies the object's attributes (e.g. clone an object)
            Usage object.clone() or copy.copy(object) (as _copy__() is also implemented)
            :param self:
            :return: A clone of the object
            """
            newone = type(self)()
            eclass = self.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EAttribute):
                    #logger.trace("clone: processing attribute {}".format(x.name))
                    if x.many:
                        eOrderedSet = newone.eGet(x.name)
                        for v in self.eGet(x.name):
                            eOrderedSet.append(v)
                    else:
                        newone.eSet(x.name, self.eGet(x.name))
            return newone

        setattr(EObject, '__copy__', clone)
        setattr(EObject, 'clone', clone)

        """
        Deep copying an EObject.
        Does not work yet for copying references from other resources than this one.
        """
        def deepcopy(self, memo=None):
            logger.debug("deepcopy: processing {}".format(self))
            first_call = False
            if memo is None:
                memo = dict()
                first_call = True
            if self in memo:
                return memo[self]

            copy: EObject = self.clone()
            logger.debug("Shallow copy: {}".format(copy))
            eclass: EClass = self.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    #logger.debug("deepcopy: processing reference {}".format(x.name))
                    ref: EReference = x
                    value: EStructuralFeature = self.eGet(ref)
                    if value is None:
                        continue
                    if ref.containment:
                        if ref.many and isinstance(value, ECollection):
                            #clone all containment elements
                            eAbstractSet = copy.eGet(ref.name)
                            for ref_value in value:
                                duplicate = ref_value.__deepcopy__(memo)
                                eAbstractSet.append(duplicate)
                        else:
                            copy.eSet(ref.name, value.__deepcopy__(memo))
                    #else:
                    #    # no containment relation, but a reference
                    #    # this can only be done after a full copy
                    #    pass
            # now copy should a full copy, but without cross references

            memo[self] = copy

            if first_call:
                logger.debug("copying references")
                for k, v in memo.items():
                    eclass: EClass = k.eClass
                    for x in eclass.eAllStructuralFeatures():
                        if isinstance(x, EReference):
                            #logger.debug("deepcopy: processing x-reference {}".format(x.name))
                            ref: EReference = x
                            orig_value: EStructuralFeature = k.eGet(ref)
                            if orig_value is None:
                                continue
                            if not ref.containment:
                                opposite = ref.eOpposite
                                if opposite and opposite.containment:
                                    # do not handle eOpposite relations, they are handled automatically in pyEcore
                                    continue
                                if x.many:
                                    eAbstractSet = v.eGet(ref.name)
                                    for orig_ref_value in orig_value:
                                        try:
                                            copy_ref_value = memo[orig_ref_value]
                                        except KeyError:
                                            logger.warning(f'Cannot find reference of type {orig_ref_value.eClass.Name} \
                                                for reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                            copy_ref_value = orig_ref_value
                                        eAbstractSet.append(copy_ref_value)
                                else:
                                    try:
                                        copy_value = memo[orig_value]
                                    except KeyError:
                                        logger.warning(f'Cannot find reference of type {orig_value.eClass.name} of \
                                            reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                        copy_value = orig_value
                                    v.eSet(ref.name, copy_value)
            return copy
        setattr(EObject, '__deepcopy__', deepcopy)
        setattr(EObject, 'deepcopy', deepcopy)
        # show deleted object from memory
        # setattr(EObject, '__del__', lambda x: print('Deleted {}'.format(x.eClass.name)))

        # def update_id(n: Notification):
        #     if isinstance(n.feature, EAttribute):
        #         #print(n)
        #         if n.feature.name == 'id':
        #             resource = n.notifier.eResource
        #             if resource is not None and (n.kind != Kind.UNSET and n.kind != Kind.REMOVE):
        #                 print('ADDING to UUID dict {}#{}, notification type {}'.format(n.notifier.eClass.name, n.feature.name, n.kind.name))
        #                 resource.uuid_dict[n.new] = n.notifier
        #                 if n.old is not None and n.old is not '':
        #                     del resource.uuid_dict[n.old]
        # observer = EObserver()
        # observer.notifyChanged = update_id
        #
        # old_init = EObject.__init__
        # def new_init(self, **kwargs):
        #     observer.observe(self)
        #     old_init(self, **kwargs)
        #
        # setattr(EObject, '__init__', new_init)

        # Methods to automatically update the uuid_dict.
        # Currently disabled, because it does not work in all circumstances
        # This only works when the object which id is to be added to the dict is already part
        # of the energysystem xml tree, otherwise there is no way of knowing to which uuid_dict it should be added.
        # E.g.
        # > asset = esdl.Asset(id='uuid)
        # > asset.port.append(esdl.InPort(id='uuid)) # this does not work because asset is not part of the energy system yet
        # > area.asset.append(asset) #works for asset, but not for port. In order to have port working too, this statement
        # should be executed bofore adding the port...

        # old_set = EObject.__setattr__
        # def updated_set(self, feature, value):
        #     old_set(self, feature, value)
        #     #if feature == 'id':
        #     #print('Feature :{}#{}, value={}, resource={}'.format(self.eClass.name, feature, value, '?'))
        #     #if isinstance(feature, EReference):
        #     if hasattr(value, 'id') and feature[0] != '_':
        #         print('*****Update uuid_dict {}#{} for {}#id'.format(self.eClass.name, feature, value.eClass.name))
        #         self.eResource.uuid_dict[value.id] = value
        # setattr(EObject, '__setattr__', updated_set)
        #
        #
        #
        # old_append = EAbstractSet.append
        # def updated_append(self, value, update_opposite=True):
        #     old_append(self, value, update_opposite)
        #     #print('EAbstractSet :{}, value={}, resource={}, featureEr={}'.format(self, value, value.eResource, self.feature.eResource))
        #     if hasattr(value, 'id'):
        #         if self.feature.eResource:
        #             print('****Update uuid_dict AbstractSet-{}#id'.format(value.eClass.name))
        #             self.feature.eResource.uuid_dict[value.id] = value
        #         elif value.eResource:
        #             print('****Update uuid_dict AbstractSet-{}#id'.format(value.eClass.name))
        #             value.eResource.uuid_dict[value.id] = value
        #
        # setattr(EAbstractSet, 'append', updated_append)




        # def toJSON(self):
        #     return json.dumps(self, default=lambda o: list(o),
        #                       sort_keys=True, indent=4)
        # setattr(EOrderedSet, 'toJSON', toJSON)

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

    def load_file(self, uri_or_filename):
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

    def load_uri(self, uri):
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
        self.add_object_to_dict(self.energy_system.id, self.energy_system, True)
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
        self.add_object_to_dict(tmp_resource.contents[0].id, tmp_resource.contents[0], True)
        return tmp_resource.contents[0], parse_info

    def load_from_string(self, esdl_string, name='from_string'):
        """
        Loads an energy system from a string and adds it to a *new* resourceSet
        :returns: EnergySystem and the parse warnings as a tuple (es, parse_info)
         """
        if name is '': name = str(uuid4())
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
            # Edwin: recursive moet hier toch False zijn?? immers elke resource heeft zijn eigen uuid_dict
            self.add_object_to_dict(self.energy_system.id, self.energy_system, True)
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
        uri = StringURI(name + '.esdl', esdl_string)
        # self.add_uri(uri)
        try:
            tmp_resource = self.rset.get_resource(uri)
            parse_info = []
            if isinstance(tmp_resource, XMLResource):
                parse_info = tmp_resource.get_parse_information()
            tmp_es = tmp_resource.contents[0]
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
            del self.rset.resources[my_uri]
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
    # Use get_by_id_slow() for that
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

    def remove_object_from_dict(self, es_id, esdl_object):
        if hasattr(esdl_object, 'id'):
            if esdl_object.id is not None:
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