from pyecore.resources import ResourceSet, URI
from pyecore.ecore import EEnum, EAttribute, EBoolean
from pyecore.utils import alias
from pyecore.resources.resource import HttpURI
from esdl.resources.xmlresource import XMLResource
from esdl import esdl
from uuid import uuid4
from io import BytesIO
import json


class EnergySystemHandler:

    def __init__(self, energy_system=None):
        if energy_system is not None:
            self.energy_system = energy_system
        else:
            self.energy_system = None
        self.resource = None
        self.rset = ResourceSet()

        # Assign files with the .esdl extension to the XMLResource instead of default XMI
        self.rset.resource_factory['esdl'] = lambda uri: XMLResource(uri)

        # fix python builtin 'from' that is also used in ProfileElement as attribute
        # use 'start' instead of 'from' when using a ProfileElement
        # alias('start', esdl.ProfileElement.findEStructuralFeature('from'))
        alias('start', esdl.ProfileElement.from_)

        # def toJSON(self):
        #     return json.dumps(self, default=lambda o: list(o),
        #                       sort_keys=True, indent=4)
        # setattr(EOrderedSet, 'toJSON', toJSON)

        # have a nice __repr__ for some ESDL classes when printing ESDL objects (includes all Assets and EnergyAssets)
        esdl.EnergySystem.__repr__ = \
            lambda x: '{}: ({})'.format(x.name, EnergySystemHandler.attr_to_dict(x))

    def load_file(self, uri_or_filename):
        if uri_or_filename[:4] == 'http':
            uri = HttpURI(uri_or_filename)
        else:
            uri = URI(uri_or_filename)
        return self.load_uri(uri)

    def load_uri(self, uri):
        self.resource = self.rset.get_resource(uri)
        # At this point, the model instance is loaded!
        self.energy_system = self.resource.contents[0]
        return self.energy_system

    def load_from_string(self, esdl_string):
        uri = StringURI('from_string.esdl', esdl_string)
        # this overrides the current loaded resource
        self.resource = self.rset.create_resource(uri)
        self.resource.load()
        self.energy_system = self.resource.contents[0]
        return self.energy_system

    def to_string(self):
        # to use strings as resources, we simulate a string as being a URI
        uri = StringURI('to_string.esdl')
        self.resource.save(uri)
        # return the string
        return uri.getvalue()

    def save(self, filename=None):
        if filename is None:
            self.resource.save()
        else:
            uri = URI(filename)
            fileresource = self.rset.create_resource(uri)
            # add the current energy system
            fileresource.append(self.energy_system)
            # save the resource
            fileresource.save()

    def get_energy_system(self):
        return self.energy_system

    # Using this function you can query for objects by ID
    # After loading an ESDL-file, all objects that have an ID defines are stored in resource.uuid_dict automatically
    # Note: If you add things later to the resource, it won't be added automatically to this dictionary though.
    # Use get_by_id_slow() for that
    def get_by_id(self, object_id):
        if object_id in self.resource.uuid_dict:
            return self.resource.uuid_dict[object_id]
        else:
            print('Can\'t find asset for id = {}'.format(object_id))
            return None

    def add_asset(self, asset):
        if hasattr(asset, 'id'):
            if id is not None:
                self.resource.uuid_dict[asset.id] = asset
            else:
                print('Id has not been set for asset {}({})', asset.eClass.name, asset)

    def remove_asset(self, asset):
        if hasattr(asset, 'id'):
            if id is not None:
                del self.resource.uuid_dict[asset.id]

    def remove_asset_by_id(self, asset_id):
        del self.resource.uuid_dict[asset_id]

    # returns a generator of all assets of a specific type. Not only the ones defined in  the main Instance's Area
    # e.g. QuantityAndUnits can be defined in the KPI of an Area or in the EnergySystemInformation object
    # this function returns all of them at once
    @staticmethod
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

        area = esdl.Area(id=str(uuid4()), name=area_title)
        instance.area = area

        self.resource = self.rset.create_resource(StringURI('string_resource.esdl'))
        # add the current energy system
        self.resource.append(self.energy_system)
        return self.energy_system

    # Support for Pickling when serializing the energy system in a session
    # The pyEcore classes by default do not allow for simple serialization for Session management in Flask
    # Furthermore, they can contain cyclic relations. Therefore we serialize to XMI and back if necessary.
    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = dict()
        state['energySystem'] = self.to_string();
        return state

    def __setstate__(self, state):
        self.__init__()
        self.load_from_string(state['energySystem'])

    @staticmethod
    def get_asset_attributes(asset):
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
                    print(attr['options'])
                attr['doc'] = x.__doc__
                attributes.append(attr)
        print(attributes)
        #attrs_sorted = sorted(attributes.items(), key=lambda kv: kv[0])
        return attributes #attrs_sorted


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