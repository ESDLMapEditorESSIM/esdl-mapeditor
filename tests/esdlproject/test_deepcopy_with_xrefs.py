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

from esdl import esdl, EnergySystem
from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonResource, JsonOptions
from esdlproject.ProjectManager import ProjectManager, eobject_to_string, ESDLFormat


class MyTestCase(unittest.TestCase):
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




if __name__ == '__main__':
    unittest.main()
