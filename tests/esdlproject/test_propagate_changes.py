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

import esdl
from esdlproject import Variant
from esdlproject.ProjectManager import ProjectManager, eobject_to_string, convertActionToVariantChanges


class PropagateChanges(unittest.TestCase):
    def test_propagate(self):
        pm = ProjectManager()
        es = pm.get_active_energy_system()
        print(eobject_to_string(es))

        # add a few variants
        huidig = pm.active_variant
        pm.active_variant.name = "Huidig"
        v2030 = Variant(name="2030")
        v2050 = Variant(name="2050")
        pm.active_variant.variant.append(v2030)
        v2030.variant.append(v2050)

        print(eobject_to_string(pm.project))


        area = es.instance[0].area
        tracker = pm.active_tracker
        tracker.stack.start_recording(label="Add WindTurbine")
        wt = esdl.WindTurbine(id="id1", name="WindTurbine1")
        area.asset.append(wt)
        tracker.stack.stop_recording()
        convertActionToVariantChanges(tracker.stack.top, pm.active_variant)

        print(eobject_to_string(pm.project))

        pm.set_active_variant(v2030)

        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))
        # add another asset to the huidig variant
        pm.set_active_variant(huidig)
        es = pm.get_active_energy_system()
        stack = pm.active_tracker.stack
        stack.start_recording(label="Add PowerPlant")
        pvpark = esdl.PowerPlant(id="pp1", name="PowerPlant1")
        es.instance[0].area.asset.append(pvpark)
        stack.stop_recording()

        convertActionToVariantChanges(stack.top, pm.active_variant)

        print("1--------------------------------------------------")
        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))

        # switch again to 2030, changes from parent should be added
        # but also merged with its current changes (none for now)
        print("2--------------------------------------------------")
        pm.set_active_variant(v2030)
        # count of assets should be 2
        self.assertEqual(2, len(pm.get_active_energy_system().instance[0].area.asset))
        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))


        # switch again to 2030, add a change
        print("3--------------------------------------------------")
        pm.set_active_variant(v2030)
        es = pm.get_active_energy_system()
        stack = pm.active_tracker.stack
        stack.start_recording(label="Add Import")
        pvpark = esdl.Import(id="import1", name="Import1")
        es.instance[0].area.asset.append(pvpark)
        stack.stop_recording()
        convertActionToVariantChanges(stack.top, pm.active_variant)
        # count of assets should be 3
        self.assertEqual(3, len(pm.get_active_energy_system().instance[0].area.asset))
        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))

        print("4--------------------------------------------------")
        pm.set_active_variant(huidig)
        es = pm.get_active_energy_system()
        stack = pm.active_tracker.stack
        stack.start_recording(label="Add PVPark")
        pvpark = esdl.PVPark(id="pvpark1", name="PVPark1")
        es.instance[0].area.asset.append(pvpark)
        stack.stop_recording()
        convertActionToVariantChanges(stack.top, pm.active_variant)
        # count of assets should be 3
        self.assertEqual(3, len(pm.get_active_energy_system().instance[0].area.asset))
        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))

        print("5--------------------------------------------------")
        pm.set_active_variant(huidig)
        es = pm.get_active_energy_system()
        stack = pm.active_tracker.stack
        stack.start_recording(label="Add PVPark")
        pvpark = esdl.PVPark(id="pvpark1", name="PVPark1")
        es.instance[0].area.asset.append(pvpark)
        stack.stop_recording()
        convertActionToVariantChanges(stack.top, pm.active_variant)
        print(eobject_to_string(pm.project))
        print(eobject_to_string(pm.get_active_energy_system()))


if __name__ == '__main__':
    unittest.main()
