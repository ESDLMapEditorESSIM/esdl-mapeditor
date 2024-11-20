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

import unittest

from pyecore.resources import ResourceSet, URI

from esdl import esdl, EnergySystem
from esdl.patch import patch_esdl
from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonOptions
from esdl.resources.project_resource import ProjectResource
from esdl.resources.xmlresource import XMLResource
from esdlproject import ESDLProject
from esdlproject.ProjectManager import ProjectManager, eobject_to_string, ESDLFormat
from src.log import get_logger


class DeepCopyTest(unittest.TestCase):
    def test_deepcopy1(self):
        pm = ProjectManager()
        es: EnergySystem = pm.get_active_energy_system()
        transformer1 = esdl.Transformer(name="Transformer1")
        transformer2 = esdl.Transformer(name="Transformer2")
        windturbine = esdl.WindTurbine(name="WindTurbine1")
        inport1 = esdl.InPort(name="In1")
        inport2 = esdl.InPort(name="In2")
        outport = esdl.OutPort(name="Out")
        transformer1.port.append(inport1)
        transformer2.port.append(inport2)
        windturbine.port.append(outport)
        area = es.instance[0].area
        area.asset.append(transformer1)
        area.asset.append(transformer2)
        area.asset.append(windturbine)
        inport1.connectedTo.append(outport)

        pm.active_tracker.stack.start_recording(label="test-deepcopy")
        # now disconnect inport1 and connect it to Inport2 of transformer2
        p = inport1.connectedTo[0]
        inport1.connectedTo.remove(p)
        inport2.connectedTo.append(outport)
        pm.active_tracker.stack.stop_recording()

        hlc = pm.active_tracker.stack.top
        json = eobject_to_string(hlc, format=ESDLFormat.JSON, options={JsonOptions.INDENT: 2})

        print(json)
        print(f"InPort of transformer1: {inport1.connectedTo}")
        print(f"InPort of transformer2: {inport2.connectedTo}")
        print(f"OutPort of windturbine : {outport.connectedTo}")

        print("All below should be True")
        print(len(inport1.connectedTo) == 0)
        print(len(inport2.connectedTo) == 1)
        print(len(outport.connectedTo) == 1)

        print(pm.active_tracker.stack.stack)
        pm.active_tracker.stack.undo()

        print()
        print(f"InPort of transformer1: {inport1.connectedTo}")
        print(f"InPort of transformer2: {inport2.connectedTo}")
        print(f"OutPort of windturbine : {outport.connectedTo}")


    # def test_deepcopy_with_project(self):
    #     log = get_logger(__name__)
    #     patch_esdl()
    #     file = r"C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\RvE\Drenthe huidig met IIS.project"
    #     rset = ResourceSet()
    #     rset.resource_factory["esdl"] = XMLResource
    #     rset.resource_factory["project"] = ProjectResource
    #
    #     resource: XMLResource = rset.create_resource(URI(file))
    #     resource.load()
    #     project: ESDLProject = resource.contents[0]
    #     #es = project.variantCollection[0].energysystem
    #     variant_collection_resource: XMLResource = rset.create_resource(StringURI("variant_collection.esdl"))
    #     #variant_collection_resource.set_content(es)
    #     #project.variantCollection[0].energysystemRef = es
    #     es = project.variantCollection[0].energysystemRef
    #     variant_collection_resource.save(output=URI('../esdl/test_output.esdl'))
    #     new_resource = rset.create_resource(StringURI("test.esdl"))
    #     copy = es.deepcopy(uuid_dict = new_resource.uuid_dict)


    def test_deepcopy_with_project_issue(self):
        pm = ProjectManager()
        pm.add_energy_system(URI('../esdl/SimpleES.esdl'))
        pm.delete_variant(pm.active_variant.variantCollection)
        pm.add_energy_system(URI('../esdl/SimpleES.esdl'))
        pm.debug()
        s = pm.save()
        with open('../esdl/deepcopy_test.project', "w") as f:
            f.write(s)

        pm = ProjectManager()
        pm.delete_variant(pm.active_variant.variantCollection)
        pm.load(URI('../esdl/deepcopy_test.project'))
        pm.debug()
        es = pm.project.variantCollection[0].energysystemRef
        resource = es.eResource
        resource.save(URI('../esdl/vc_test.esdl'))




if __name__ == '__main__':
    unittest.main()
