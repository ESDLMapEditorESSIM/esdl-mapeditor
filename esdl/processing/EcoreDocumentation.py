from pyecore.resources import ResourceSet, URI
from pyecore.utils import DynamicEPackage
from pyecore.resources.resource import HttpURI
from esdl.resources.xmlresource import XMLResource


class EcoreDocumentation:
    """This class loads the dynamic meta-model and returns the documentation for attributes as these are
    not present in the static meta-model"""
    def __init__(self, esdlEcoreFile=None):
            self.esdl = None
            self.rset = None
            self.esdl_model = None
            self.resource = None
            if esdlEcoreFile is None:
                self.esdlEcoreFile = 'https://raw.githubusercontent.com/EnergyTransition/ESDL/master/esdl/model/esdl.ecore'
            else:
                self.esdlEcoreFile = esdlEcoreFile
            self._init_metamodel()

    def _init_metamodel(self):
            self.rset = ResourceSet()

            # Assign files with the .esdl extension to the XMLResource instead of default XMI
            self.rset.resource_factory['esdl'] = lambda uri: XMLResource(uri)

            # Read esdl.ecore as meta model
            print('Initalizing ESDL metamodel for documentation from {}'.format(self.esdlEcoreFile))
            mm_uri = URI(self.esdlEcoreFile)
            if self.esdlEcoreFile[:4] == 'http':
                mm_uri = HttpURI(self.esdlEcoreFile)
            esdl_model_resource = self.rset.get_resource(mm_uri)

            esdl_model = esdl_model_resource.contents[0]
            self.esdl_model = esdl_model
            # print('Namespace: {}'.format(esdl_model.nsURI))
            self.rset.metamodel_registry[esdl_model.nsURI] = esdl_model

            # Create a dynamic model from the loaded esdl.ecore model, which we can use to build Energy Systems
            self.esdl = DynamicEPackage(esdl_model)


    def get_doc(self, className, attributeName):
        """ Returns the documentation of an attribute from the dynamic meta model,
        because the static meta model does not contain attribute documentation"""
        ecoreClass = self.esdl_model.getEClassifier(className)
        if ecoreClass is None: return None
        attr = ecoreClass.findEStructuralFeature(attributeName)
        if attr is None: return None
        #print('Retrieving doc for {}: {}'.format(attributeName, attr.__doc__))
        return (attr.__doc__)

