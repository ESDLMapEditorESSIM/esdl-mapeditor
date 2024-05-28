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

from esdl import esdl
from esdl.resources.json import JsonOptions
from esdlproject.ProjectManager import eobject_to_string, ESDLFormat, ProjectManager


class TestNewUndo(unittest.TestCase):
    def test_high_level_change_undo(self):
        """"
        Note: due to deepcopying each change, undo/redo object will be recreated and therefore original refrences
        to objects are after and undo/redo are no longer valid.
        """


        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        stack.start_recording(label="setup simple ESDL: add transformer")
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
        stack.stop_recording()
        print('Stack: ', stack)

        hlc = stack.top
        json = eobject_to_string(hlc, format=ESDLFormat.JSON, options={JsonOptions.INDENT: 2})
        print(json)

        print(f"Undo {stack.top.label}")
        stack.undo()
        print('Stack after undo: ', stack)
        self.assertEqual(len(area.asset), 0)

        stack.redo()
        print('Area.asset list: ', area.asset)
        self.assertEqual(len(area.asset), 1)
        print('Stack after redo: ', stack)

        print(eobject_to_string(es))

        print(area.asset)

        with stack.track_changes(label="Add trafo2 and wt"):
            area.asset.append(transformer2)
            area.asset.append(windturbine)


        print(eobject_to_string(es))
        print(stack)
        stack.start_recording(label="connect ports")
        inport1 = area.asset[0].port[0]
        inport1.connectedTo.append(outport)
        stack.stop_recording()


        print(f"starting point:")
        inport1 = area.asset[0].port[0]
        inport2 = area.asset[1].port[0]
        outport = area.asset[2].port[0]
        print(f"InPort of transformer1: {inport1.connectedTo}")
        self.assertEqual(len(inport1.connectedTo), 1)
        self.assertIn(outport, inport1.connectedTo)
        print(f"InPort of transformer2: {inport2.connectedTo}")
        self.assertEqual(len(inport2.connectedTo), 0)
        print(f"OutPort of windturbine: {outport.connectedTo}")
        self.assertEqual(len(outport.connectedTo), 1)
        self.assertIn(inport1, outport.connectedTo)

        inport1 = area.asset[0].port[0]
        inport2 = area.asset[1].port[0]
        outport = area.asset[2].port[0]
        stack.start_recording(label="test-deepcopy")
        # now disconnect inport1 and connect it to Inport2 of transformer2
        p = inport1.connectedTo[0]
        inport1.connectedTo.remove(p)
        inport2.connectedTo.append(outport)
        stack.stop_recording()

        hlc = stack.top
        json = eobject_to_string(hlc, format=ESDLFormat.JSON, options={JsonOptions.INDENT: 2})

        print(json)
        inport1 = area.asset[0].port[0]
        inport2 = area.asset[1].port[0]
        outport = area.asset[2].port[0]
        print(f"InPort of transformer1: {inport1.connectedTo}")
        self.assertEqual(len(inport1.connectedTo), 0)
        print(f"InPort of transformer2: {inport2.connectedTo}")
        self.assertEqual(len(inport2.connectedTo), 1)
        self.assertIn(outport, inport2.connectedTo)
        print(f"OutPort of windturbine: {outport.connectedTo}")
        self.assertEqual(len(outport.connectedTo), 1)
        self.assertIn(inport2, outport.connectedTo)

        print("Undo connecting ports")
        # for change in hlc.change:
        #     print(change)
        #     undoChange(change, es.eResource)
        stack.undo()

        inport1 = area.asset[0].port[0]
        inport2 = area.asset[1].port[0]
        outport = area.asset[2].port[0]
        print(f"InPort of transformer1: {inport1.connectedTo}")
        self.assertEqual(len(inport1.connectedTo), 1)
        self.assertIn(outport, inport1.connectedTo)
        print(f"InPort of transformer2: {inport2.connectedTo}")
        self.assertEqual(len(inport2.connectedTo), 0)
        print(f"OutPort of windturbine: {outport.connectedTo}")
        self.assertEqual(len(outport.connectedTo), 1)
        self.assertIn(inport1, outport.connectedTo)

    def test_attribute_change(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack
        es_name = es.name

        with stack.track_changes(label="change attribute"):
            new_name = "Cool Energy System"
            es.name = new_name
        print(stack)
        print("ES name: ", es.name)
        self.assertEqual(es.name, new_name)

        stack.undo()
        print("ES name: ", es.name)
        self.assertEqual(es.name, es_name)

        stack.redo()
        print("ES name: ", es.name)
        self.assertEqual(es.name, new_name)
        print(eobject_to_string(stack.top, ESDLFormat.JSON, {JsonOptions.INDENT: 2}))

    def test_multi_attribute_change(self):
        # TODO
        pass

    def test_reference_change(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        es.energySystemInformation = esdl.EnergySystemInformation()
        es.energySystemInformation.carriers = esdl.Carriers()
        carrier = esdl.ElectricityCommodity(name="electricity", id="electricity_id")
        es.energySystemInformation.carriers.carrier.append(carrier)

        windturbine = esdl.WindTurbine(name="WindTurbine1")
        outport = esdl.OutPort(name="Out")
        windturbine.port.append(outport)
        area = es.instance[0].area
        area.asset.append(windturbine)

        with stack.track_changes(label="change reference"):
            outport.carrier = carrier

        print(eobject_to_string(stack.top, ESDLFormat.JSON, {JsonOptions.INDENT: 2}))
        print(outport.carrier)
        self.assertEqual(outport.carrier, carrier)
        stack.undo()
        print(outport.carrier)
        self.assertEqual(outport.carrier, None)

    def test_add_object(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        with stack.track_changes("add object"):
            pp = esdl.PowerPlant(name="Cool PP", id="pp123", power=50000.0,
                                 type=esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
            es.instance[0].area.asset.append(pp)

        print(eobject_to_string(stack.top, ESDLFormat.JSON, {JsonOptions.INDENT: 2}))
        self.assertIn(pp, es.instance[0].area.asset)
        stack.undo()
        self.assertNotIn(pp, es.instance[0].area.asset)
        self.assertEqual(len(es.instance[0].area.asset), 0)
        stack.redo()
        # PowerPlant is applied again, but is a copy of the original, so we can't check for 'pp' object here
        # but on attributes is ok
        print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))
        self.assertEqual(len(es.instance[0].area.asset), 1)
        self.assertEqual(es.instance[0].area.asset[0].name, pp.name)
        self.assertEqual(es.instance[0].area.asset[0].type, esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
        print(pm.to_debug_string())

    def test_add_and_delete_object_with_xrefs(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        with stack.track_changes("add object"):
            # pp = esdl.PowerPlant(name="Cool PP", id="pp123", power=50000.0,
            #                      type=esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
            # es.instance[0].area.asset.append(pp)
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

        print(eobject_to_string(es, ESDLFormat.XML))
        self.assertIn(inport1, outport.connectedTo)
        self.assertIn(outport, inport1.connectedTo)
        self.assertNotIn(inport2, outport.connectedTo)

        with stack.track_changes("remove object with x_refs"):
            transformer1.delete()

        self.assertNotIn(inport1, outport.connectedTo)
        self.assertNotIn(transformer1, area.asset)
        print(eobject_to_string(stack.top, ESDLFormat.JSON, {JsonOptions.INDENT: 2}))

        stack.undo()
        # now all object delete are recreated with different memory locations, so can't use transformer1 and inport here
        print(eobject_to_string(es, ESDLFormat.XML))
        # TODO: why extra Remove...?
        #stack.redo()
        # Transformer is applied again, but is a copy of the original, so we can't check for 'pp' object here
        # but on attributes is ok
        # print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))
        # self.assertEqual(len(es.instance[0].area.asset), 1)
        # self.assertEqual(es.instance[0].area.asset[0].name, pp.name)
        # self.assertEqual(es.instance[0].area.asset[0].type, esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)


    def test_delete_object_without_xrefs(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        pp = esdl.PowerPlant(name="Cool PP", id="pp123", power=50000.0,
                             type=esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
        es.instance[0].area.asset.append(pp)
        self.assertIn(pp, es.instance[0].area.asset)

        with stack.track_changes("delete powerplant"):
            pp.delete()
        self.assertEqual(len(es.instance[0].area.asset), 0)
        print(stack)

        stack.undo()
        # self.assertIn(pp, es.instance[0].area.asset)  # not possible as pp is deepcopied in the change
        self.assertEqual(len(es.instance[0].area.asset), 1)
        self.assertEqual(es.instance[0].area.asset[0].name, pp.name)
        self.assertEqual(es.instance[0].area.asset[0].type, esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
        print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))

        stack.redo()
        # PowerPlant is applied again, but is a copy of the original, so we can't check for 'pp' object here
        # but on attributes is ok
        print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))
        self.assertEqual(len(es.instance[0].area.asset), 0)
        print(pm.to_debug_string())

    def test_delete_object_with_xrefs(self):
        pm = ProjectManager()
        es: esdl.EnergySystem = pm.get_active_energy_system()
        stack = pm.active_tracker.stack

        es.energySystemInformation = esdl.EnergySystemInformation()
        es.energySystemInformation.carriers = esdl.Carriers()
        carrier = esdl.ElectricityCommodity(name="electricity", id="electricity_id")
        es.energySystemInformation.carriers.carrier.append(carrier)

        pp = esdl.PowerPlant(name="Cool PP", id="pp123", power=50000.0,
                             type=esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
        outport = esdl.OutPort(name="Out", id="outport_id")
        pp.port.append(outport)
        outport.carrier = carrier
        es.instance[0].area.asset.append(pp)
        self.assertIn(pp, es.instance[0].area.asset)

        with stack.track_changes("delete powerplant"):
            pp.delete()
        self.assertEqual(len(es.instance[0].area.asset), 0)
        print(stack)

        stack.undo()
        # self.assertIn(pp, es.instance[0].area.asset)  # not possible as pp is deepcopied in the change
        self.assertEqual(len(es.instance[0].area.asset), 1)
        self.assertEqual(es.instance[0].area.asset[0].name, pp.name)
        self.assertEqual(es.instance[0].area.asset[0].type, esdl.PowerPlantTypeEnum.COMBINED_CYCLE_GAS_TURBINE)
        self.assertEqual(es.instance[0].area.asset[0].port[0].carrier, carrier)
        print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))

        stack.redo()
        # PowerPlant is applied again, but is a copy of the original, so we can't check for 'pp' object here
        # but on attributes is ok
        print(eobject_to_string(es, ESDLFormat.XML, {JsonOptions.INDENT: 2}))
        self.assertEqual(len(es.instance[0].area.asset), 0)
        print(pm.to_debug_string())


if __name__ == '__main__':
    unittest.main()
