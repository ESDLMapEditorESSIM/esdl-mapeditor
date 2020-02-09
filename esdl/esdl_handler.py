from pyecore.resources import ResourceSet, URI
from pyecore.ecore import EEnum, EAttribute, EOrderedSet, EObject, EReference, EClass, EStructuralFeature
from pyecore.utils import alias
from pyecore.resources.resource import HttpURI
from esdl.resources.xmlresource import XMLResource
from esdl import esdl
from uuid import uuid4
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


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
        alias('start', esdl.ProfileElement.from_)

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
                    log.debug("clone: processing attribute {}".format(x.name))
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
            log.debug("deepcopy: processing {}".format(self))
            first_call = False
            if memo is None:
                memo = dict()
                first_call = True
            if self in memo:
                return memo[self]

            copy: EObject = self.clone()
            log.debug("Shallow copy: {}".format(copy))
            eclass: EClass = self.eClass
            for x in eclass.eAllStructuralFeatures():
                if isinstance(x, EReference):
                    log.debug("deepcopy: processing reference {}".format(x.name))
                    ref: EReference = x
                    value: EStructuralFeature = self.eGet(ref)
                    if value is None:
                        continue
                    if ref.containment:
                        if ref.many and isinstance(value, EOrderedSet):
                            #clone all containment elements
                            eOrderedSet = copy.eGet(ref.name)
                            for ref_value in value:
                                duplicate = ref_value.__deepcopy__(memo)
                                eOrderedSet.append(duplicate)
                        else:
                            copy.eSet(ref.name, value.__deepcopy__(memo))
                    #else:
                    #    # no containment relation, but a reference
                    #    # this can only be done after a full copy
                    #    pass
            # now copy should a full copy, but without cross references

            memo[self] = copy

            if first_call:
                log.debug("copying references")
                for k, v in memo.items():
                    eclass: EClass = k.eClass
                    for x in eclass.eAllStructuralFeatures():
                        if isinstance(x, EReference):
                            log.debug("deepcopy: processing x-reference {}".format(x.name))
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
                                    eOrderedSet = v.eGet(ref.name)
                                    for orig_ref_value in orig_value:
                                        try:
                                            copy_ref_value = memo[orig_ref_value]
                                        except KeyError:
                                            log.warning(f'Cannot find reference of type {orig_ref_value.eClass.Name} \
                                                for reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                            copy_ref_value = orig_ref_value
                                        eOrderedSet.append(copy_ref_value)
                                else:
                                    try:
                                        copy_value = memo[orig_value]
                                    except KeyError:
                                        log.warning(f'Cannot find reference of type {orig_value.eClass.name} of \
                                            reference {k.eClass.name}.{ref.name} in deepcopy memo, using original')
                                        copy_value = orig_value
                                    v.eSet(ref.name, copy_value)
            return copy
        setattr(EObject, '__deepcopy__', deepcopy)
        setattr(EObject, 'deepcopy', deepcopy)


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
        :returns EnergySystem the first item in the resourceSet"""
        if uri_or_filename[:4] == 'http':
            uri = HttpURI(uri_or_filename)
        else:
            uri = URI(uri_or_filename)
        return self.load_uri(uri)

    def import_file(self, uri_or_filename):
        if uri_or_filename[:4] == 'http':
            uri = HttpURI(uri_or_filename)
        else:
            uri = URI(uri_or_filename)
        return self.add_uri(uri)

    def load_uri(self, uri):
        """Loads a new resource in a new resourceSet"""
        self._new_resource_set()
        self.resource = self.rset.get_resource(uri)
        # At this point, the model instance is loaded!
        self.energy_system = self.resource.contents[0]
        self.esid_uri_dict[self.energy_system.id] = uri
        self.add_object_to_dict(self.energy_system.id, self.energy_system)
        return self.energy_system

    def add_uri(self, uri):
        """Adds the specified URI to the resource set, i.e. load extra resources that the resource can refer to."""
        tmp_resource = self.rset.get_resource(uri)
        # At this point, the model instance is loaded!
        # self.energy_system = self.resource.contents[0]
        self.esid_uri_dict[tmp_resource.contents[0].id] = uri
        self.add_object_to_dict(tmp_resource.contents[0].id, tmp_resource.contents[0])
        return tmp_resource.contents[0]

    def load_from_string(self, esdl_string):
        """Loads an energy system from a string and adds it to the resourceSet
        :returns the loaded EnergySystem """
        uri = StringURI('from_string.esdl', esdl_string)
        #self._new_resource_set()
        self.resource = self.rset.create_resource(uri)
        try:
            self.resource.load()
            self.energy_system = self.resource.contents[0]
            self.esid_uri_dict[self.energy_system.id] = uri
            self.add_object_to_dict(self.energy_system.id, self.energy_system)
            return self.energy_system
        except Exception as e:
            return e            # TODO: how is this done nicely?

    def load_external_string(self, esdl_string):
        """Loads an energy system from a string but does NOT add it to the resourceSet (e.g. as a separate resource)
        It returns an Energy System, but it is not part of a resource in the ResourceSet """
        uri = StringURI('from_string.esdl', esdl_string)
        external_rset = ResourceSet()
        external_resource = external_rset.create_resource(uri)
        external_resource.load()
        external_energy_system = external_resource.contents[0]
        return external_energy_system

    def add_from_string(self, name, esdl_string):
        uri = StringURI(name + '.esdl', esdl_string)
        # self.add_uri(uri)
        tmp_resource = self.rset.get_resource(uri)
        try:
            if tmp_resource.contents[0].id is None:
                tmp_resource.contents[0].id = self.generate_uuid()
            self.esid_uri_dict[tmp_resource.contents[0].id] = uri
            # hack to add energySystem id to uuid_dict
            self.add_object_to_dict(tmp_resource.contents[0].id, tmp_resource.contents[0])
            return tmp_resource.contents[0]
        except Exception as e:
            return e            # TODO: how is this done nicely?


    def to_string(self, es_id=None):
        # to use strings as resources, we simulate a string as being a URI
        uri = StringURI('to_string.esdl')
        if es_id is None:
            self.resource.save(uri)
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                resource = self.rset.resources[my_uri.normalize()]
                resource.save(uri)
            else:
                # TODO: what to do? original behaviour
                self.resource.save(uri)
        # return the string
        return uri.getvalue()

    def to_bytesio(self):
        """Returns a BytesIO stream for the energy system"""
        uri = StringURI('to_string.esdl')
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
                    resource = self.rset.resources[my_uri.normalize()]
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
                    es = self.rset.resources[my_uri.normalize()].contents[0]
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
            if not uri[:4] == 'http':
                print('Saving {}'.format(uri))
                resource.save()  # raises an Error for HTTP resources
            else:
                print("Not saving {}, http-based resource saving is not supported yet".format(uri))

    def get_resource(self, es_id=None):
        if es_id is None:
            return self.resource
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                res = self.rset.resources[my_uri.normalize()]
                return res
            else:
                return None

    def get_energy_system(self, es_id=None):
        if es_id is None:
            return self.energy_system
        else:
            if es_id in self.esid_uri_dict:
                my_uri = self.esid_uri_dict[es_id]
                es = self.rset.resources[my_uri.normalize()].contents[0]
                return es
            else:
                return None

    def get_energy_systems(self):
        es_list = []
        # for esid in self.esid_uri_dict:
        #    uri = self.esid_uri_dict[esid]
        #    es_list.append(self.rset.resources[uri])

        for key in self.rset.resources.keys():
            es_list.append(self.rset.resources[key].contents[0])
        return es_list

    # Using this function you can query for objects by ID
    # After loading an ESDL-file, all objects that have an ID defines are stored in resource.uuid_dict automatically
    # Note: If you add things later to the resource, it won't be added automatically to this dictionary though.
    # Use get_by_id_slow() for that
    def get_by_id(self, es_id, object_id):
        if object_id in self.get_resource(es_id).uuid_dict:
            return self.get_resource(es_id).uuid_dict[object_id]
        else:
            print('Can\'t find asset for id={} in uuid_dict of the ESDL model'.format(object_id))
            print(self.get_resource(es_id).uuid_dict)
            raise KeyError('Can\'t find asset for id={} in uuid_dict of the ESDL model'.format(object_id))
            return None

    def add_object_to_dict(self, es_id, esdl_object):
        if hasattr(esdl_object, 'id'):
            if esdl_object.id is not None:
                self.get_resource(es_id).uuid_dict[esdl_object.id] = esdl_object
            else:
                print('Id has not been set for object {}({})', esdl_object.eClass.name, esdl_object)

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
    def get_all_assets_of_type(self, esdl_type):
        return esdl_type.allInstances()

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

    def create_empty_energy_system(self, name, es_description, inst_title, area_title):
        es_id = str(uuid4())
        self.energy_system = esdl.EnergySystem(id=es_id, name=name, description=es_description)

        instance = esdl.Instance(id=str(uuid4()), name=inst_title)
        self.energy_system.instance.append(instance)

        # TODO: check if this (adding scope) solves error????
        area = esdl.Area(id=str(uuid4()), name=area_title, scope=esdl.AreaScopeEnum.from_string('UNDEFINED'))
        instance.area = area

        uri = StringURI('empty_energysystem.esdl')
        self.resource = self.rset.create_resource(uri)
        # add the current energy system
        self.resource.append(self.energy_system)
        self.esid_uri_dict[self.energy_system.id] = uri

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
        state['energySystem'] = self.to_string();
        print('done')
        return state

    def __setstate__(self, state):
        self.__init__()
        #print('Deserialize rset {}'.format(self.rset.resources))
        print('Deserializing EnergySystem...', end="")
        self.load_from_string(state['energySystem'])
        print('done')

    @staticmethod
    def get_asset_attributes(asset, esdl_doc=None):
        attributes = list()
        for x in asset.eClass.eAllStructuralFeatures():
            #print('{} is of type {}'.format(x.name, x.eClass.name))
            if isinstance(x, EAttribute):
                attr = dict()
                attr['name'] = x.name
                attr['type'] = x.eType.name
                # if isinstance(x., EEnum):
                #    attr['value'] = list(es.eGet(x))
                attr['value'] = asset.eGet(x)
                if attr['value'] is not None:
                    if x.many:
                        if isinstance(attr['value'], EOrderedSet):
                            attr['value'] = [x.name for x in attr['value']]
                            attr['many'] = True
                        else:
                            attr['value'] = list(x.eType.to_string(attr['value']))
                    else:
                        attr['value'] = x.eType.to_string(attr['value'])
                if isinstance(x.eType, EEnum):
                    attr['type'] = 'EEnum'
                    attr['enum_type'] = x.eType.name
                    attr['options'] = list(lit.name for lit in x.eType.eLiterals)
                    attr['default'] = x.eType.default_value.name
                else:
                    attr['default'] = x.eType.default_value
                    if x.eType.default_value is not None:
                        attr['default'] = x.eType.to_string(x.eType.default_value)
                if x.eType.name == 'EBoolean':
                    attr['options'] = ['true', 'false']
                attr['doc'] = x.__doc__
                if x.__doc__ is None and esdl_doc is not None:
                    attr['doc'] = esdl_doc.get_doc(asset.eClass.name, x.name)

                attributes.append(attr)
        # print(attributes)
        attrs_sorted = sorted(attributes, key=lambda a: a['name'])
        return attrs_sorted


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