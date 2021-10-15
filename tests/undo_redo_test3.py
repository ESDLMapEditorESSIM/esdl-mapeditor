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

from pyecore.commands import Delete

import esdl
from esdl.esdl_handler import EnergySystemHandler


class UndoRedoTestCase3(unittest.TestCase):
    def test_delete(self):
        esh = EnergySystemHandler()
        es, _ = esh.load_file("C:\\Users\\werkmane\\OneDrive - TNO\\Documents\\ESDL\\EnergySystems\\Laurens_Ennatuurlijk.esdl")

        philips = esh.get_by_id(es.id, "64164e74-2f7a-4ce8-b8e7-d79119600cab")
        print(philips.name)
        tracker = esh.change_tracker.get_tracker_stack(es)
        tracker.start_recording(combineCommands=True, label="delete philips")
        philips.delete()
        tracker.stop_recording()
        print('Current stack', tracker.stack)
        l = []
        for action in tracker.stack:
            for c in action:
                if c.feature.name == "carrier":
                    print("------   Carrier:", c)
                    l.append(c)
        self.assertEqual(2, len(l))
        tracker.undo()
        print('Stack after undo', tracker.stack)
        #print(esh.to_string(es.id))

    def test_simple_delete(self):
        esh = EnergySystemHandler()
        es = esh.create_empty_energy_system("test delete", "", "test instance", "Area51")
        es.energySystemInformation = esdl.EnergySystemInformation(id="esi")
        es.energySystemInformation.carriers = esdl.Carriers(id="carriers")
        supplyhc = esdl.HeatCommodity(id="supply", name="supply")
        es.energySystemInformation.carriers.carrier.append(supplyhc)
        returnhc = esdl.HeatCommodity(id="return", name="return")
        es.energySystemInformation.carriers.carrier.append(returnhc)
        hd = esdl.HeatingDemand(id="hd1", name="HeatingDemand")
        pipe1 = esdl.Pipe(id="pipe_sup", name="pipe1_sup")
        pipe2 = esdl.Pipe(id="pipe_ret", name="pipe2_ret")
        es.instance[0].area.asset.extend([hd, pipe1, pipe2])
        hdip = esdl.InPort(id="hdIP", name="hdIP", carrier=supplyhc)
        hdop = esdl.OutPort(id="hdOP", name="hdOP", carrier=returnhc)
        hd.port.extend([hdip, hdop])
        p1op = esdl.OutPort(id="p1op", name="Pipe1OP", carrier=supplyhc)
        p2ip = esdl.InPort(id="p2IP", name="Pipe2IP", carrier=returnhc)
        pipe1.port.append(p1op)
        pipe2.port.append(p2ip)
        p1op.connectedTo.append(hdip)
        p2ip.connectedTo.append(hdop)
        print(esh.to_string(es.id))
        tracker = esh.change_tracker.get_tracker_stack(es)
        tracker.start_recording(combineCommands=True, label="delete heatingdemand")
        #tracker.add_undo_step(label="volgende actie")
        hd.delete()
        tracker.stop_recording()
        print('Current stack', tracker.stack)
        # check if carrier are removed
        # l = []
        # for action in tracker.stack:
        #     for c in action:
        #         if c.feature.name == "carrier":
        #             print("------   Carrier:", c)
        #             l.append(c)
        # self.assertEqual(2, len(l))
        tracker.undo()
        print(esh.to_string(es.id))
        self.assertTrue(hdip.carrier is not None)
        self.assertTrue(hdop.carrier is not None)
        print('Stack after undo', tracker.stack)


    def test_simple_delete2(self):
        esh = EnergySystemHandler()
        es = esh.create_empty_energy_system("test delete", "", "test instance", "Area51")
        es.energySystemInformation = esdl.EnergySystemInformation(id="esi")
        es.energySystemInformation.carriers = esdl.Carriers(id="carriers")
        supplyhc = esdl.HeatCommodity(id="supply", name="supply")
        es.energySystemInformation.carriers.carrier.append(supplyhc)
        returnhc = esdl.HeatCommodity(id="return", name="return")
        es.energySystemInformation.carriers.carrier.append(returnhc)
        hd = esdl.HeatingDemand(id="hd1", name="HeatingDemand")
        pipe1 = esdl.Pipe(id="pipe_sup", name="pipe1_sup")
        pipe2 = esdl.Pipe(id="pipe_ret", name="pipe2_ret")
        es.instance[0].area.asset.extend([hd, pipe1, pipe2])
        hdip = esdl.InPort(id="hdIP", name="hdIP", carrier=supplyhc)
        hdop = esdl.OutPort(id="hdOP", name="hdOP", carrier=returnhc)
        hd.port.extend([hdip, hdop])
        p1op = esdl.OutPort(id="p1op", name="Pipe1OP", carrier=supplyhc)
        p2ip = esdl.InPort(id="p2IP", name="Pipe2IP", carrier=returnhc)
        pipe1.port.append(p1op)
        pipe2.port.append(p2ip)
        p1op.connectedTo.append(hdip)
        p2ip.connectedTo.append(hdop)
        print(esh.to_string(es.id))
        #tracker = esh.change_tracker.get_tracker_stack(es)
        #tracker.start_recording(combineCommands=True, label="delete heatingdemand")
        #hd.delete()
        delete_command = Delete(hd)
        if delete_command.can_execute:
            delete_command.execute()
        print(esh.to_string(es.id))
        #tracker.stop_recording()
        #print('Current stack', tracker.stack)
        # check if carrier are removed
        # l = []
        # for action in tracker.stack:
        #     for c in action:
        #         if c.feature.name == "carrier":
        #             print("------   Carrier:", c)
        #             l.append(c)
        # self.assertEqual(2, len(l))
        delete_command.undo()
        self.assertTrue(hdip.carrier is not None)
        self.assertTrue(hdop.carrier is not None)
        self.assertTrue(p1op.carrier is not None)
        self.assertTrue(p2ip.carrier is not None)
        #print('Stack after undo', tracker.stack)
        print(esh.to_string(es.id))


if __name__ == '__main__':
    unittest.main()
