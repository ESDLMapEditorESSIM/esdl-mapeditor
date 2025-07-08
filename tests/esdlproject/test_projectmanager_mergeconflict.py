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
from typing import TypeVar, cast

from pyecore.ecore import EObject

from esdl import esdl
from esdlproject import Variant
from esdlproject.ProjectManager import ProjectManager
from src.log import get_logger

logger = get_logger(__name__)


# Helper function to get an EObject by its ID from the container's resource's uuid_dict
def get_by_id(container: EObject, id_: str):
    resource = container.eResource
    uuid_dict = resource.uuid_dict
    return uuid_dict[id_]

T = TypeVar('T')
# Helper function to get an EObject by its ID from the container's resource's uuid_dict
# and cast it to a specific type to help the IDE to understand the type
def get_by_id_t(container: EObject, id_: str, esdl_type: T) -> T:
    resource = container.eResource
    uuid_dict = resource.uuid_dict
    return cast(type[esdl_type], uuid_dict[id_])  # add explicit type

class test_merge_conflict(unittest.TestCase):
    def test_merge(self):
        # setup esdl
        pm = ProjectManager()
        es = pm.get_active_energy_system()
        v1 = pm.get_active_variant()
        v1.name = "Variant1"
        es.name = "Variant1"
        v1_ct = pm.get_change_tracker_for_variant(pm.get_active_variant())
        v1_ct.stack.start_recording(label="Setup areas")
        main_area = es.instance[0].area
        area1 = esdl.Area(name="Area1", id="area1")

        t1 = esdl.Transformer(name="transformer1", id="transformer1")
        t1.port.append(esdl.OutPort(name="t1_op1", id="t1_op1"))
        t1.port.append(esdl.InPort(name="t1_ip1", id="t1_ip1"))
        area1.asset.append(t1)

        area2 = esdl.Area(name="Area2", id="area2")
        t2 = esdl.Transformer(name="transformer2", id="transformer2")
        t2.port.append(esdl.OutPort(name="t2_op1", id="t2_op1"))
        t2.port.append(esdl.InPort(name="t2_ip1", id="t2_ip1"))
        area2.asset.append(t2)

        area3 = esdl.Area(name="Area3", id="area3")
        t3 = esdl.Transformer(name="transformer3", id="transformer3")
        t3.port.append(esdl.OutPort(name="t3_op1", id="t3_op1"))
        t3.port.append(esdl.InPort(name="t3_ip1", id="t3_ip1"))
        area3.asset.append(t3)

        main_area.area.append(area1)
        main_area.area.append(area2)
        main_area.area.append(area3)
        v1_ct.stack.stop_recording()

        v1_ct.stack.start_recording(label="add ED")
        ed = esdl.ElectricityDemand(name="ElectricityDemand1", id="ed1")
        ed.port.append(esdl.InPort(name="ed1_ip1", id="ed1_ip1"))
        area1.asset.append(ed)
        t1_op1 = get_by_id(ed, "t1_op1")
        ed1_ip1 = get_by_id_t(ed, "ed1_ip1", esdl.InPort)
        ed1_ip1.connectedTo.append(t1_op1)

        self.assertEqual(len(area1.asset), 2)  # Check that area1 has 2 assets (t1 and ed)
        self.assertEqual(len(t1_op1.connectedTo), 1)  # Check that t1_op1 is connected to ed1_ip1
        self.assertEqual(t1_op1.connectedTo[0], ed1_ip1)
        v1_ct.stack.stop_recording()


        v1 = pm.get_active_variant()
        v2a = Variant(name="Variant2a", id="variant2a")
        v1.variant.append(v2a)
        #pm.debug(dump_project=True)
        # add to second variant
        pm.set_active_variant(v2a)
        v2a_ct = pm.get_change_tracker_for_variant(v2a)
        v2a_ct.stack.start_recording(label="add WindTurbine")
        wt = esdl.WindTurbine(name="WindTurbine1", id="wt1")
        wt.port.append(esdl.OutPort(name="wt1_op1", id="wt1_op1"))
        v2a_es = pm.get_active_energy_system()
        v2a_area3 = v2a_es.instance[0].area.area[2]  # area1 in variant v2
        v2a_area3.asset.append(wt)
        get_by_id_t(wt, "wt1_op1", esdl.OutPort).connectedTo.append(get_by_id(wt, "t3_ip1"))  # connect wt to t3_ip1

        self.assertEqual(len(v2a_area3.asset), 2) # Check that area3 in variant v2 has 2 assets (t1 and wt)
        self.assertEqual(len(get_by_id_t(wt, "wt1_op1", esdl.OutPort).connectedTo), 1)  # Check that wt1_op1 is connected to t1_ip1

        v2a_ct.stack.add_undo_step(label="move wind turbine to area2")
        v2a_area2 = v2a_es.instance[0].area.area[1]  # area2 in variant v2
        v2a_area2.asset.append(wt) # moves it from area1 to area2
        get_by_id_t(wt, "wt1_op1", esdl.OutPort).connectedTo.remove(get_by_id(wt, "t3_ip1"))  # disconnect wt from t3_ip1
        get_by_id_t(wt, "wt1_op1", esdl.OutPort).connectedTo.append(get_by_id(wt, "t2_ip1"))  # connect wt to t2_ip1
        v2a_ct.stack.stop_recording()

        self.assertEqual(len(v2a_area2.asset), 2)  # Check that area1 in variant v2a has 2 assets (t1 and wt)
        self.assertEqual(len(get_by_id_t(wt, "t2_ip1", esdl.InPort).connectedTo),1)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(wt, "t2_ip1", esdl.InPort).connectedTo[0], get_by_id_t(wt, "wt1_op1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1
        # clean up to make sure we don't get memory leaks during this test.
        del v2a_ct, v2a_area3, v2a_area2
        del v2a_es, wt

        # move energy demand in variant v1 to area2
        pm.set_active_variant(v1)
        v1_ct.stack.start_recording(label="Move energy demand to area2")
        es = pm.get_active_energy_system()
        ed = get_by_id(es, "ed1") # ElectricityDemand1 in variant v1
        get_by_id(es, 'area2').asset.append(ed) # move asset from area1 to area2
        get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo.remove(get_by_id(es, "t1_op1"))  # disconnect from t1_op1
        get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo.append(get_by_id(es, "t2_op1"))
        v1_ct.stack.stop_recording()

        self.assertEqual(len(get_by_id(es, 'area2').asset), 2)  # Check that area1 in variant v2 has 2 assets (t1 and wt)
        self.assertEqual(len(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo),1)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo[0], get_by_id_t(es, "ed1_ip1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1

        #pm.debug(dump_project=True)
        # now activate variant v2a and see merge conflict if no merge conflict handler is used
        pm.set_active_variant(v2a)
        es = pm.get_active_energy_system()
        #time.sleep(1)
        print(f'assets in area1: {get_by_id_t(es, "area1", esdl.Area).asset}')
        print(f'assets in area2: {get_by_id_t(es, "area2", esdl.Area).asset}')
        print(f'assets in area3: {get_by_id_t(es, "area3", esdl.Area).asset}')
        print(f't2_op1 connectedTo: {get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo}')
        print(f't2_ip1 connectedTo: {get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo}')
        print(f't1_op1 connectedTo: {get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo}')
        print(f't1_ip1 connectedTo: {get_by_id_t(es, "t1_ip1", esdl.InPort).connectedTo}')
        print(f'ed1_ip1 connectedTo: {get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo}')
        print(f'wt1_op1 connectedTo: {get_by_id_t(es, "wt1_op1", esdl.OutPort).connectedTo}')

        # lets see if there are conflicts again?
        #time.sleep(1)

        self.assertEqual(len(get_by_id(es, 'area2').asset), 3)  # Check that area1 in variant v2 has 3 assets (t1, wt and ed)
        self.assertEqual(len(get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo),1)  # Check t2_ip1 has a connection
        self.assertEqual(len(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo),1)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo[0], get_by_id_t(es, "wt1_op1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1
        self.assertEqual(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo[0], get_by_id_t(es, "ed1_ip1", esdl.InPort))  # Check t2_op1 has a connection to ed1_ip1
        self.assertEqual(0, len(get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo))  # Check t1_op1 has no connections
        self.assertEqual(0, len(get_by_id_t(es, "t1_ip1", esdl.OutPort).connectedTo))  # Check t1_ip1 has no connections
        #pm.debug(dump_project=True)

        # create a new variant on based on v1, call it v2b
        v2b = Variant(name="Variant2b", id="variant2b")
        v1.variant.append(v2b)
        # if merging is not implemented correctly this will generate an error
        pm.set_active_variant(v2b)


        pm.set_active_variant(v1)
        # move in v1 the ED away from area2 back to area1 again
        # this should show that there is no conflict anymore with variant v2a, as the ED is not in area2 anymore
        es = pm.get_active_energy_system()
        v1_ct.stack.start_recording(label="Move EnergyDemand back to area1 again")
        get_by_id_t(es, "area1", esdl.Area).asset.append(get_by_id(es, "ed1"))  # move asset from area2 to area1
        get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo.remove(get_by_id(es, "t2_op1"))
        get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo.append(get_by_id(es, "t1_op1"))
        v1_ct.stack.stop_recording()

        #time.sleep(1)
        print(f't2_op1 connectedTo: {get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo}')
        print(f't2_ip1 connectedTo: {get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo}')
        print(f't1_op1 connectedTo: {get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo}')
        print(f't1_ip1 connectedTo: {get_by_id_t(es, "t1_ip1", esdl.InPort).connectedTo}')
        # lets see if there are conflicts again?
        #time.sleep(1)
        pm.set_active_variant(v2a)
        es = pm.get_active_energy_system()
        self.assertEqual(len(get_by_id(es, 'area1').asset), 2)  # Check that area1 in variant v2 has 2 assets (t1 and ed)
        self.assertEqual(len(get_by_id(es, 'area2').asset), 2)  # Check that area1 in variant v2 has 2 assets (t2 and wt)
        print(f't2_op1 connectedTo: {get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo}')
        print(f't2_ip1 connectedTo: {get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo}')
        print(f't1_op1 connectedTo: {get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo}')
        print(f't1_ip1 connectedTo: {get_by_id_t(es, "t1_ip1", esdl.InPort).connectedTo}')
        #self.assertEqual(len(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo),)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo[0], get_by_id_t(es, "ed1_ip1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1

        # now test undoing this stuff
        # first undo moving ED back in V1
        # here we should be back in a conflict situation
        pm.set_active_variant(v1)
        v1_ct.stack.undo()
        es = pm.get_active_energy_system()
        self.assertEqual(len(get_by_id(es, 'area1').asset), 1)  # Check that area1 in variant v2 has 2 assets (t1 and ed)
        self.assertEqual(len(get_by_id(es, 'area2').asset),2)  # Check that area1 in variant v2 has 2 assets (t1 and wt)
        self.assertEqual(len(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo), 1)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo[0],
                         get_by_id_t(es, "ed1_ip1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1

        pm.set_active_variant(v2a)
        es = pm.get_active_energy_system()
        self.assertEqual(len(get_by_id(es, 'area2').asset),3)  # Check that area1 in variant v2 has 3 assets (t1, wt and ed)
        self.assertEqual(len(get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo), 1)  # Check t2_ip1 has a connection
        self.assertEqual(len(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo), 1)  # Check t2_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo[0],
                         get_by_id_t(es, "wt1_op1", esdl.OutPort))  # Check t2_ip1 has a connection to wt1_op1
        self.assertEqual(get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo[0],
                         get_by_id_t(es, "ed1_ip1", esdl.InPort))  # Check t2_op1 has a connection to ed1_ip1
        self.assertEqual(0, len(get_by_id_t(es, "t1_op1",
                                            esdl.OutPort).connectedTo))  # Check t1_op1 has no connections
        self.assertEqual(0, len(get_by_id_t(es, "t1_ip1",
                                            esdl.OutPort).connectedTo))  # Check t1_ip1 has no connections

        # process:
        # Setup areas
        # add ED
        # add WindTurbine
        # move wind turbine to area2
        # Move energy demand to area2
        # Move EnergyDemand back to area1 again
        # undo "Move EnergyDemand back to area1 again"
        # activate variant v2a
        # undo Move energy demand to area2


        # let's undo "Move wind turbine to area2" to see if the merge conflict resolution can be undo-ed.
        # (i.e. move the windturbine back to area3)
        v2a_ct = pm.get_change_tracker_for_variant(v2a)
        print(v2a_ct.stack.stack)
        #import objgraph
        #objgraph.show_refs(pm)
        v2a_ct.stack.undo()
        es = pm.get_active_energy_system()

        #time.sleep(1)
        print(f'assets in area1: {get_by_id_t(es, "area1", esdl.Area).asset}')
        print(f'assets in area2: {get_by_id_t(es, "area2", esdl.Area).asset}')
        print(f'assets in area3: {get_by_id_t(es, "area3", esdl.Area).asset}')
        print(f't1_op1 connectedTo: {get_by_id_t(es, "t1_op1", esdl.OutPort).connectedTo}')
        print(f't1_ip1 connectedTo: {get_by_id_t(es, "t1_ip1", esdl.InPort).connectedTo}')
        print(f't2_op1 connectedTo: {get_by_id_t(es, "t2_op1", esdl.OutPort).connectedTo}')
        print(f't2_ip1 connectedTo: {get_by_id_t(es, "t2_ip1", esdl.InPort).connectedTo}')
        print(f't3_op1 connectedTo: {get_by_id_t(es, "t3_op1", esdl.OutPort).connectedTo}')
        print(f't3_ip1 connectedTo: {get_by_id_t(es, "t3_ip1", esdl.InPort).connectedTo}')
        print(f'ed1_ip1 connectedTo: {get_by_id_t(es, "ed1_ip1", esdl.InPort).connectedTo}')
        print(f'wt1_op1 connectedTo: {get_by_id_t(es, "wt1_op1", esdl.OutPort).connectedTo}')
        #print(pm.active_energy_system_to_string())
        #pm.debug(dump_project=True)

        # check if WT is in area3

        self.assertEqual(len(get_by_id_t(es, "area1", esdl.Area).asset), 1)  # Check that area1 in variant v2a has 2 assets (t1 and ed)
        self.assertEqual(len(get_by_id_t(es, "area2", esdl.Area).asset), 2)  # Check that area2 in variant v2a has 2 assets (t2 and wt)
        self.assertEqual(len(get_by_id_t(es, "area3", esdl.Area).asset), 2)  # Check that area2 in variant v2a has 2 assets (t2 and wt)
        self.assertEqual(len(get_by_id_t(es, "t3_ip1", esdl.InPort).connectedTo), 1)  # Check t3_ip1 has a connection
        self.assertEqual(get_by_id_t(es, "t3_ip1", esdl.InPort).connectedTo[0],
                         get_by_id_t(es, "wt1_op1", esdl.OutPort))  # Check t3_ip1 has a connection to wt1_op1




if __name__ == '__main__':
    unittest.main()
