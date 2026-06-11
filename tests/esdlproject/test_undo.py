import unittest
import uuid

from esdl import EnergySystem, Transformer
from esdlproject.ProjectManager import ProjectManager


class TestUndo(unittest.TestCase):
    def setUp(self):
        self.pm = ProjectManager()

    def test_undo_stack(self):
        """
        Test if the undo stack is working correctly.
        """
        es: EnergySystem = self.pm.get_active_energy_system()
        area = es.instance[0].area
        stack = self.pm.get_undo_redo_stack()
        self.assertIsNone(stack.top)
        self.assertIs(stack.can_undo(), False)
        self.assertIs(stack.can_redo(), False)

        stack.start_recording()
        transformer1 = Transformer(name="Transformer1")
        area.asset.append(transformer1)
        stack.stop_recording()

        self.assertIsNotNone(stack.top)
        self.assertIs(stack.can_undo(), True)
        self.assertIs(stack.can_redo(), False)

    def test_undo_stack_pausing(self):
        """
        Test that pausing the recording of the undo stack works correctly.
        """
        es: EnergySystem = self.pm.get_active_energy_system()
        area = es.instance[0].area
        stack = self.pm.get_undo_redo_stack()
        self.assertIs(stack.size(), 0)

        stack.start_recording()
        with stack.pause_recording():
            transformer2 = Transformer(name="Transformer2")
            area.asset.append(transformer2)
        stack.stop_recording()

        self.assertIs(stack.size(), 0)

        # Adding elements outside the recording should not be added to the stack.
        transformer1 = Transformer(name="Transformer1")
        area.asset.append(transformer1)

        self.assertIs(stack.size(), 0)

    def test_undo_redo_operation(self):
        """
        Test if undo and redo operations are working correctly.
        """
        es: EnergySystem = self.pm.get_active_energy_system()
        area = es.instance[0].area
        stack = self.pm.get_undo_redo_stack()
        self.assertIs(stack.size(), 0)

        # Add asset while recording.
        stack.start_recording()
        transformer = Transformer(name="Transformer", id=str(uuid.uuid4()))
        area.asset.append(transformer)
        stack.stop_recording()

        # We should have something on the stack we can undo, and the asset is in the energy system.
        self.assertIs(stack.size(), 1)
        self.assertIs(stack.can_undo(), True)
        self.assertIn(transformer, es.instance[0].area.asset)

        # After undoing, we should still have the same size of the stack, but the asset should be removed.
        stack.undo()
        self.assertIs(stack.size(), 1)
        self.assertIs(stack.can_undo(), False)
        self.assertIs(stack.can_redo(), True)
        self.assertEquals(es.instance[0].area.asset, [])

        # After redoing, the asset should be back in the energy system.
        stack.redo()
        self.assertIs(stack.size(), 1)
        self.assertIs(stack.can_undo(), True)
        self.assertIs(stack.can_redo(), False)
        asset = es.instance[0].area.asset[0]
        # We cannot compare the objects directly with in, because actually a copy of the object is stored and applied.
        self.assertEquals(asset.id, transformer.id)


if __name__ == '__main__':
    unittest.main()
