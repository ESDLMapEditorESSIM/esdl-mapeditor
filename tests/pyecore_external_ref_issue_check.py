from esdl.esdl_handler import EnergySystemHandler
from esdl.processing.ESDLQuantityAndUnits import qau_to_string
from esdl import esdl
from uuid import uuid4
from pyecore.resources import ResourceSet, Resource, URI
from pyecore.resources.resource import HttpURI
from esdl.esdl_handler import StringURI
from esdl.resources.xmlresource import XMLResource
from extensions.esdl_drive import ESDLDriveHttpURI




def load_external_ref():
    rset = ResourceSet()
    rset.resource_factory['esdl'] = XMLResource
    rset.resource_factory['*'] = XMLResource
    #car_rs = rset.get_resource(HttpURI('https://edr.hesi.energy/store/esdl/80e3ac6a-94b1-4a85-a0d1-a68de4251243?format=xml'))
    #units_rs = rset.get_resource(HttpURI('http://localhost:9080/store/resource/public/QuantityAndUnits.esdl'))
    #es_rs = rset.get_resource(URI('ES with external ref.esdl'))
    es_rs = rset.get_resource(ESDLDriveHttpURI('http://localhost:9080/store/resource/public/ES%20with%20external%20ref.esdl'))
    print('initial rset', rset.resources)
    es = es_rs.contents[0]
#    uri = StringURI('http://test.esdl')
#    es_rs.save(uri)
#    string_esdl = uri.getvalue()

    # rset2 = ResourceSet()
    # rset2.resource_factory['esdl'] = XMLResource
    # rset2.resource_factory['*'] = XMLResource
    #
    # uri2 = StringURI('string://test2.esdl', text=string_esdl)
    # es_rs2 = rset2.create_resource(uri2)
    # es_rs2.load()
    # #es_rs2 = rset2.get_resource(uri=uri2)
    # es2 = es_rs2.contents[0]


    #uri = StringURI('to_string_' + 'es_ref' + '.esdl')
    #es_rs.save(uri)
    #print(uri.getvalue())
    print('before access, new rset:', rset.resources)
    ref = es.energySystemInformation.carriers.carrier[0].energyContentUnit.reference
    print(qau_to_string(ref))
    print(EnergySystemHandler.attr_to_dict(ref))
    print(list(rset.resources.values())[1].contents[0].id)
    print(rset.resources)



def create_external_ref():
    rset = ResourceSet()
    rset.resource_factory['esdl'] = XMLResource
    rset.resource_factory['*'] = XMLResource
    car_rs = rset.get_resource(HttpURI('https://edr.hesi.energy/store/esdl/80e3ac6a-94b1-4a85-a0d1-a68de4251243?format=xml'))
    units_rs = rset.get_resource(HttpURI('http://localhost:9080/store/resource/public/QuantityAndUnits.esdl'))
    es_rs = rset.get_resource('C:\\Users\\werkmane\\OneDrive - TNO\\Documents\\ESDL\\EnergySystems\\Untitled EnergySystem.esdl')

    units = units_rs.contents[0]
    ext_carriers = car_rs.contents[0]


    #es = esdl.EnergySystem(name='example', id=str(uuid4()))
    #es_rs = rset.create_resource(uri=StringURI('example.esdl'))
    #es_rs.append(es)
    es = es_rs.contents[0]
    esi = esdl.EnergySystemInformation()
    es.energySystemInformation = esi
    carriers = esdl.Carriers()
    esi.carriers = carriers

    """
    Containment relations are copied, not referenced.
    """
    #esi.carriers = ext_carriers
    #carriers.carrier.append(first)
    first: esdl.Carrier = ext_carriers.carrier[0]
    print(first.eURIFragment())
    print(first.eResource.uri.plain)


    ec = esdl.EnergyCarrier(id=str(uuid4()), name="test")
    powerUnit = units_rs.uuid_dict['powerUnit']
    ec.energyContentUnit = esdl.QuantityAndUnitReference(reference=powerUnit)
    carriers.carrier.append(ec)
    print(ec.energyContentUnit)

    uri = StringURI('to_string_' + 'left' + '.esdl')
    uri = URI('ES with external ref.esdl')
    es_rs.save(uri)
    #print(uri.getvalue())

    # uri = StringURI('to_string_' + 'carriers' + '.esdl')
    # car_rs.save(uri)
    # print(uri.getvalue())

from pyecore.resources.resource import URIConverter

def apply_relative_from_me(self, relative_path):
        # currently make all http-based uri's unique,
        # better would be to check each path's segment until there is a difference
        rel_uri = URI(relative_path)
        conv_uri:URI = URIConverter.convert(rel_uri)
        if conv_uri.protocol == self.protocol:
            not_common = conv_uri.protocol
            common = str()
            for i in range(len(self.segments)-1, 0, -1):
                if self.segments[i] == conv_uri.segments[i]:
                    common = self.segments[i] + '/' + common
                else:
                    for j in range(0, i-1):
                        not_common += self.segments[j]
                    break
            print('common', common)
            print('not_common', not_common)
            return
        print('relative path:', relative_path)
        return relative_path

class TestURI(URI):
    def apply_relative_from_me(self, relative_path):
        # currently make all http-based uri's unique,
        # better would be to check each path's segment until there is a difference
        rel_uri = URI(relative_path)
        conv_uri: URI = URIConverter.convert(rel_uri)
        print('rel_uri', rel_uri, rel_uri.plain)
        print('conv_uri', conv_uri, conv_uri.plain)
        print('self.segments', self.segments)
        print('conv.segments', conv_uri.segments)
        if conv_uri.protocol == self.protocol:
            not_common = str()
            common = str()
            for i in range(len(self.segments) - 1, -1, -1):
                if self.segments[i] == conv_uri.segments[i]:
                    common = self.segments[i] + '/' + common
                else:
                    not_common = (self.segments[i] + '/' + not_common ) if not_common is not '' else self.segments[i]

            common = self.protocol + '://' + common
            print('common', common)
            print('not_common', not_common)
            return not_common
        print('relative path:', relative_path)
        return relative_path


if __name__ == "__main__":
    # esh = EnergySystemHandler()
    # esdl.EnergySystem.__repr__ = lambda x: '{}(name={})'.format(x.eClass.name, x.name)
    # es, _ = esh.load_file('Left.esdl')
    # ext_carriers, parse_errors = esh.add_uri('https://edr.hesi.energy/store/esdl/80e3ac6a-94b1-4a85-a0d1-a68de4251243?format=xml')
    #load_external_ref()
    t = TestURI('http://localhost:9080/store/resource/public/QuantityAndUnits.esdl')
    result = t.apply_relative_from_me('http://www.rug.nl/store/resource/public/TestESDL.esdl')
    print('apply_relative_from_me', result)


