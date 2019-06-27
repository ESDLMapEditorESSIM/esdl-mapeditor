from pyecore.resources import ResourceSet, URI
from pyecore.utils import alias
from pyecore.resources.resource import HttpURI
from esdl.resources.xmlresource import XMLResource
from esdl import esdl
from uuid import uuid4
from io import BytesIO


class EnergySystemHandler:

    def __init__(self):
        self.energySystem = None
        self.resource = None
        self.rset = ResourceSet()

        # Assign files with the .esdl extension to the XMLResource instead of default XMI
        self.rset.resource_factory['esdl'] = lambda uri: XMLResource(uri)

        # fix python builtin 'from' that is also used in ProfileElement as attribute
        # use 'start' instead of 'from' when using a ProfileElement
        alias('start', esdl.ProfileElement.findEStructuralFeature('from'))

        # have a nice __repr__ for some ESDL classes when printing ESDL objects (includes all Assets and EnergyAssets)
        esdl.EnergySystem.python_class.__repr__ = \
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
        self.energySystem = self.resource.contents[0]
        return self.energySystem

    def load_from_string(self, esdl_string):
        uri = StringURI('from_string.esdl', esdl_string)
        # this overrides the current loaded resource
        self.resource = self.rset.create_resource(uri)
        self.resource.load()
        self.energySystem = self.resource.contents[0]
        return self.energySystem

    def to_string(self):
        # to use strings as resources, we simulate a string as being a URI
        uri = StringURI('to_string.esdl')
        self.resource.save(uri)
        # return the string
        return uri.getvalue()

    def save(self):
        self.resource.save()

    def save(self, filename):
        uri = URI(filename)
        fileresource = self.rset.create_resource(uri)
        # add the current energy system
        fileresource.append(self.energySystem)
        # save the resource
        fileresource.save()

    def getEnergySystem(self):
        return self.energySystem

    # returns a generator of all assets of a specific type. Not only the ones defined in  the main Instance's Area
    # e.g. QuantityAndUnits can be defined in the KPI of an Area or in the EnergySystemInformation object
    # this function returns all of them at once
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

    def create_empty_energy_system(self, es_title, es_description, inst_title, area_title):
        self.energySystem = esdl.EnergySystem()
        es_id = str(uuid4())
        self.energySystem.set_id(es_id)
        self.energySystem.set_name(es_title)
        self.energySystem.set_description(es_description)

        instance = esdl.Instance()
        instance.set_id(str(uuid4()))
        instance.set_name(inst_title)
        self.energySystem.add_instance(instance)

        area = esdl.Area()
        area.set_id(str(uuid4()))
        area.set_name(area_title)
        instance.set_area(area)

        return self.energySystem




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