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
        tracker.undo()
        print('Stack after undo', tracker.stack)
        print(esh.to_string(es.id))

if __name__ == '__main__':
    unittest.main()
