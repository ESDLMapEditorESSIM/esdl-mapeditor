import unittest

from esdl import esdl, GenericProducer, InPort, OutPort, GenericConsumer, HeatCommodity
from esdl.processing.string_uri import StringURI
from esdlproject.ChangeSerializer import deepcopy_eobject_change
from esdlproject.ProjectManager import ProjectManager, resource_as_string
from esdlproject.variant_api import create_new_variant, get_parent_variant


class TestProjectManager(unittest.TestCase):

    def test_track_changes(self):
        pm = ProjectManager()

        variant1 = pm.active_variant
        variant1.name = "Variant1"
        variant1_es = pm.get_active_energy_system()
        variant_collection = get_parent_variant(variant1)

        variant1_stack = pm.get_undo_redo_stack(variant1_es)
        with variant1_stack.track_changes("Add pipe1"):
            pipe1 = esdl.Pipe(name="pipe1")
            variant1_es.instance[0].area.asset.append(pipe1)

        # Check that the change is added to the variant.
        self.assertEquals(len(pm.get_active_variant().change), 1)
        self.assertEqual(pm.get_active_variant().change[0].label, "Add pipe1")

        variant2 = create_new_variant(variant_collection, "Variant2")
        pm.set_active_variant(variant2)
        variant2_es = pm.get_active_energy_system()
        variant2_stack = pm.get_undo_redo_stack(variant2_es)

        with variant2_stack.track_changes("Add pipe2"):
            pipe2 = esdl.Pipe(name="pipe2")
            variant2_es.instance[0].area.asset.append(pipe2)

        # Check that the change is not added to the previous variant.
        pm.set_active_variant(variant1)
        # TODO: This fails. I don't understand why.
        self.assertEquals(len(pm.get_active_variant().change), 1)
        self.assertEqual(pm.get_active_variant().change[0].label, "Add pipe1")

        pm.set_active_variant(variant2)
        variant2_resource = pm.get_active_energy_system().eResource
        with variant2_stack.track_changes("Connect pipe1 and pipe2"):
            pipe1: esdl.Pipe = variant2_resource.resolve(pipe1.eURIFragment())
            port1 = esdl.InPort(name='pipe1IP1', id='pipe1IP1')
            port2 = esdl.OutPort(name='pipe2OP1')
            pipe2: esdl.Pipe = variant2_resource.resolve(pipe2.eURIFragment())
            pipe1.port.append(port1)
            pipe2.port.append(port2)
            port1.connectedTo.append(port2)

        # Check that the change is added to the variant as a single change.
        self.assertEquals(len(pm.get_active_variant().change), 2)

        # TODO: Check that the high level change consists of the smaller ones.

        with variant2_stack.track_changes("Set ES name"):
            pm.get_active_energy_system().name = "Updated Energy system (in variant3)"
            gp = esdl.GenericProducer()
            pm.get_active_energy_system().instance[0].area.asset.append(gp)

        with variant2_stack.track_changes("Set power value"):
            gp.power = 1E6

        self.assertEquals(len(pm.get_active_variant().change), 1)

    def test_change_inheritance(self):
        pm = ProjectManager()
        parent_es = pm.get_active_energy_system()
        parent_variant = pm.active_variant
        parent_variant.name = "Parent variant"
        parent_variant_stack = pm.get_undo_redo_stack()
        with parent_variant_stack.track_changes("Add pipe1"):
            pipe1 = esdl.Pipe(name="pipe1")
            parent_es.instance[0].area.asset.append(pipe1)

        # Check that pipe1 is in parent variant.
        found_pipe1_parent = False
        contents = pm.get_active_energy_system().eAllContents()
        for asset in contents:
            if isinstance(asset, esdl.Pipe):
                if asset.name == "pipe1":
                    found_pipe1_parent = True
                    break
        self.assertTrue(found_pipe1_parent)

        # Add a child.
        child_variant = create_new_variant(parent_variant, "Child variant")
        pm.set_active_variant(child_variant)
        self.assertEquals(pm.get_active_variant().parentVariant, parent_variant)
        # The change from the parent is not in the child.
        self.assertEquals(len(pm.get_active_variant().change), 0)

        # Check that pipe1 is in child variant.
        found_pipe1_child = False
        contents = pm.get_active_energy_system().eAllContents()
        for asset in contents:
            if isinstance(asset, esdl.Pipe):
                if asset.name == "pipe1":
                    found_pipe1_child = True
                    break
        self.assertTrue(found_pipe1_child)

    def test_save_load_project(self):
        pm = ProjectManager()
        stack = pm.get_undo_redo_stack()
        with stack.track_changes("GP added"):
            pm.get_active_energy_system().name = "Cool Energy system"
            pm.get_active_energy_system().instance[0].area.asset.append(esdl.GenericProducer(name="Nice GP"))
        project_string = pm.save()
        self.assertIn("Cool Energy system", project_string)
        self.assertIn("Nice GP", project_string)

        second_pm = ProjectManager()
        loaded_project = second_pm.load_from_string(project_string)
        self.assertEquals(pm.get_active_energy_system().name, second_pm.get_active_energy_system().name)

    def test_search_variant(self):
        pm = ProjectManager()
        v1 = create_new_variant(pm.active_variant, variant_name="v1")
        v2 = create_new_variant(pm.active_variant, variant_name="v2")
        v3 = create_new_variant(pm.active_variant, variant_name="v3")
        v11 = create_new_variant(v1, variant_name="v11")
        v12 = create_new_variant(v1, variant_name="v12")
        v13 = create_new_variant(v1, variant_name="v13")

        v111 = create_new_variant(v11, variant_name="v111")
        v112 = create_new_variant(v11, variant_name="v112")
        v113 = create_new_variant(v11, variant_name="v113")

        id = v112.id
        v = pm.get_variant_by_id(id)
        self.assertTrue(v.id == id)


if __name__ == '__main__':
    unittest.main()
