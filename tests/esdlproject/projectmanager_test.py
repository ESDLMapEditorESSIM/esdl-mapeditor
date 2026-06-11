import os
import unittest

from esdl import esdl, GenericProducer, InPort, OutPort, GenericConsumer, HeatCommodity
from esdl.processing.string_uri import StringURI
from esdlproject.ChangeSerializer import deepcopy_eobject_change
from esdlproject.ProjectManager import ProjectManager, resource_as_string
from esdlproject.variant_api import create_new_variant


class MyTestCase(unittest.TestCase):
    def test_basic_functionality(self):
        pm = ProjectManager()
        #string = pm.save()
        #print(string)
        print(pm.to_debug_string())
        print(pm.active_energy_system_to_string())
        print(pm.rset.resources)


    def test_track_changes(self):
        pm = ProjectManager()
        es = pm.get_active_energy_system()

        variant1 = pm.active_variant

        stack = pm.get_undo_redo_stack()
        stack.start_recording(label="Add pipe1")
        pipe1 = esdl.Pipe(name="pipe1")
        es.instance[0].area.asset.append(pipe1)
        stack.stop_recording()
        print(f'pipe1 resource: {pipe1.eResource}, {pipe1.eURIFragment()}')


        variant2 = create_new_variant(pm.active_variant, "Variant2")
        pm.set_active_variant(variant2)


        stack.start_recording(label="Add pipe2")
        pipe2 = esdl.Pipe(name="pipe2")
        es.instance[0].area.asset.append(pipe2)
        stack.stop_recording()


        pm.set_active_variant(variant1)
        print(f'=== pipe1 resource: {pipe1.eResource}, {pipe1.eURIFragment()}')

        pm.set_active_variant(variant2)

        # print(pm.to_string())
        #
        # print("active es:")
        # print(resource_as_string(pm.get_active_energy_system().eResource))

        print(f'pipe1 resource: {pipe1.eResource}, {pipe1.eURIFragment()}')
        variant3 = create_new_variant(pm.active_variant, "Variant3")
        pm.set_active_variant(variant3)
        active_resource = pm.get_active_energy_system().eResource
        print(resource_as_string(active_resource))
        stack.start_recording(label="Connect pipe1 and pipe2")
        pipe1: esdl.Pipe = active_resource.resolve(pipe1.eURIFragment())
        port1 = esdl.InPort(name='pipe1IP1', id='pipe1IP1')
        port2 = esdl.OutPort(name='pipe2OP1')
        pipe2: esdl.Pipe = active_resource.resolve(pipe2.eURIFragment())
        pipe1.port.append(port1)
        pipe2.port.append(port2)
        port1.connectedTo.append(port2)
        stack.stop_recording()

        pm.set_active_variant(variant1)
        pm.set_active_variant(variant3)


        stack.start_recording(label="Set ES name")
        pm.get_active_energy_system().name = "Updated Energy system (in variant3)"
        gp = esdl.GenericProducer()
        pm.get_active_energy_system().instance[0].area.asset.append(gp)
        stack.stop_recording()
        stack.start_recording(label="Set power value")
        gp.power = 1E6
        stack.stop_recording()

        stack.start_recording(label="Set power value")
        gp.power = 1E6
        stack.stop_recording()

        print(pm.to_debug_string())
        print("active es:")
        print(resource_as_string(active_resource))



    def test_load_existing_es(self):
        file = 'ECW_with_carriers.esdl'
        if not os.path.exists(file):
            self.skipTest(f'Missing test fixture: {file}')
        with open(file, "r") as f:
            esdl_string = f.read()

        pm = ProjectManager()
        ecw_variant = pm.add_energy_system(StringURI(uri=file, text=esdl_string))
        print(pm.rset.resources)
        print(pm.to_debug_string())
        print("active es:")
        print(resource_as_string(pm.get_active_energy_system().eResource))

        pm.delete_variant(pm.project.baseVariant[0])
        pm.set_active_variant(ecw_variant)

        print(pm.to_debug_string())
        print(pm.rset.resources)

        pm.get_undo_redo_stack().start_recording(label="Add GP")
        gp = esdl.GenericProducer(name="GenericProducer by Ewoud")
        pm.get_active_energy_system().instance[0].area.asset.append(gp)
        pm.get_undo_redo_stack().stop_recording()

        variant3 = create_new_variant(pm.active_variant, "Variant on ECW")
        pm.set_active_variant(variant3)

        pm.get_undo_redo_stack().start_recording(label="Add GP in variant on ECW")
        gp = esdl.GenericProducer(name="Cool GP")
        pm.get_active_energy_system().instance[0].area.asset.append(gp)
        pm.get_undo_redo_stack().stop_recording()


        print(pm.to_debug_string())
        print(pm.rset.resources)
        print("active es:")
        print(resource_as_string(pm.get_active_energy_system().eResource))

    def test_save_load_project(self):
        pm = ProjectManager()
        print("rset:", pm.rset.resources)
        pm.get_undo_redo_stack().start_recording()
        pm.get_active_energy_system().name = "Cool Energy system"
        pm.get_active_energy_system().instance[0].area.asset.append(esdl.GenericProducer(name="Nice GP"))
        pm.get_undo_redo_stack().stop_recording()
        project_string = pm.save()
        print(project_string)
        print("rset:", pm.rset.resources)

        pm.load(StringURI(uri='cool_project.project', text=project_string))
        new_project_string = pm.save()
        print(new_project_string)
        print("rset:", pm.rset.resources)
        print(pm.to_debug_string())
        print(resource_as_string(pm.get_active_energy_system().eResource))
        new_project_string2 = pm.save()
        print(new_project_string2)

        pm.load(StringURI(uri='cooler.project', text=new_project_string2))
        print(pm.active_energy_system_to_string())


    def test_serialized_deepcopy(self):
        pm=ProjectManager()
        es = pm.get_active_energy_system()
        gp1 = GenericProducer(name="producer")
        gp2 = GenericConsumer(name="consumer")
        ip = InPort(name="inport")
        op = OutPort(name="outport")
        gp1.port.append(ip)
        gp2.port.append(op)
        ip.connectedTo.append(op)
        es.instance[0].area.asset.append(gp1)
        es.instance[0].area.asset.append(gp2)

        copy, l = deepcopy_eobject_change(es)
        print(f'Copy: {copy}, list={[f"{m.ownerFragment}, {m.feature}={m.stringValue}" for m in l]}')

    def test_delete(self):
        pm = ProjectManager()
        es = pm.get_active_energy_system()
        area = es.instance[0].area

        pm.get_undo_redo_stack().start_recording(label="Add prod/cons")

        gp1 = GenericProducer(name="producer", id="producer")
        gc2 = GenericConsumer(name="consumer", id="consumer")
        ip = InPort(name="inport", id="inport")
        op = OutPort(name="outport", id="outport")
        gp1.port.append(ip)
        gc2.port.append(op)
        area.asset.append(gp1)
        area.asset.append(gc2)
        ip.connectedTo.append(op)

        pm.get_undo_redo_stack().stop_recording()

        v_delete = create_new_variant(pm.active_variant, variant_name="Variant for delete InPort")
        pm.set_active_variant(v_delete)
        v_delete_id = v_delete.id
        es = pm.get_active_energy_system()
        ip = pm.get_by_id(es.id, "inport")
        op = pm.get_by_id(es.id, "outport")

        pm.get_undo_redo_stack().start_recording(label="delete inport")
        ip.delete()
        pm.get_undo_redo_stack().stop_recording()

        pm.get_undo_redo_stack().start_recording(label="add carrier")
        es.energySystemInformation = esdl.EnergySystemInformation()
        es.energySystemInformation.carriers = esdl.Carriers()
        hc = HeatCommodity(name='heat', id="heat")
        es.energySystemInformation.carriers.carrier.append(hc)
        op.carrier = hc
        pm.get_undo_redo_stack().stop_recording()

        pm.get_undo_redo_stack().start_recording(label="change attribute")
        hc.name = "Heat"
        pm.get_undo_redo_stack().stop_recording()


        pm.get_undo_redo_stack().start_recording(label="delete carrier")
        op.carrier = None
        pm.get_undo_redo_stack().stop_recording()
        print("\n******************* before ***********************\n")
        print(pm.active_energy_system_to_string())
        print(pm.to_debug_string())

        project_string = pm.save()
        pm.load(StringURI('delete_carrier.project', text=project_string))
        v_delete = pm.get_variant_by_id(v_delete_id)
        pm.set_active_variant(v_delete)
        print("\n******************* after ***********************\n")
        print(pm.active_energy_system_to_string())


        print(pm.to_debug_string())

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
        print(v.id, v.eURIFragment())
        self.assertTrue(v.id == id)

    def test_create_delete_variants(self):
        pm = ProjectManager()
        pm.init_empty_project()
        print("PM created with empty project, now deleting")
        pm.clear_project(add_empty_energysystem=True)
        #pm.debug()




if __name__ == '__main__':
    unittest.main()
