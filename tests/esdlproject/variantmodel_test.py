import unittest
from uuid import uuid4

from pyecore.ecore import EObject
from pyecore.resources import ResourceSet
from pyecore.resources.json import JsonResource

from esdl import EnergySystem, Pipe, Instance, Area, InPort, OutPort
from esdl.esdl_handler import EnergySystemHandler
from esdl.processing.string_uri import StringURI
from esdl.resources.xmlresource import XMLResource
from esdl.undo import ChangeTracker
from esdlproject import VariantCollection, Variant, ESDLProject, HighLevelChange, Add, Set
from esdl.support_functions import clone, deepcopy
from esdlproject.ChangeHandler import ChangeHandler


class VariantModelTestCase(unittest.TestCase):

    # def test_read_generated_eps_model(self):
    #     input_file = URI('output/115_Test_project_me_9_pand.project')
    #
    #     setattr(EObject, 'clone', clone)
    #     setattr(EObject, 'deepcopy', deepcopy)
    #     setattr(EObject, '__deepcopy__', deepcopy)
    #
    #     rset = ResourceSet()
    #     rset.resource_factory['esdl'] = XMLResource  #
    #     rset.resource_factory['project'] = XMLResource
    #     project_resource = rset.get_resource(input_file)
    #     project: ESDLProject = project_resource.contents[0]
    #     print(f'Loaded project {project.name}, containing {len(project.baseVariant)} base variants: {[v.name for v in project.baseVariant]}')
    #
    #     for baseVariant in project.baseVariant:
    #         print(f'processing {baseVariant.name}')
    #         if baseVariant.energysystem is not None and len(baseVariant.variant) > 0:
    #             print(f'{baseVariant.name} contains a snapshot that is considered the base variant, replaying any tracked changes')
    #             for v in baseVariant.variant:
    #                 print(v.name)
    #                 for highlevelchange in v.changes:
    #                     if isinstance(highlevelchange, HighLevelChange):
    #                         print(f'Handling High level change {highlevelchange.label}')
    #                         for change in highlevelchange.changes:
    #                             print(f'Processing {change.eClass.name}')
    #                             if isinstance(change, Set):
    #                                 if change.objectValue is not None:
    #                                     change.owner.eSet(change.feature, change.objectValue)
    #                                 elif change.objectReference:
    #                                     # todo
    #                                     pass
    #                             elif isinstance(change, Add):
    #                                 if change.objectValue is not None:
    #                                     abstractList = change.owner.eGet(change.feature)
    #                                     abstractList.append(change.objectValue)
    #                                 elif change.objectReference:
    #                                     pass # TODO
    #         print('Ready processing changes, result is:')
    #         print(eobject_tree_to_string(baseVariant.energysystem))




    def test_variantModel(self):
        # add deepcopy support to EObjects
        setattr(EObject, 'clone', clone)
        setattr(EObject, 'deepcopy', deepcopy)
        setattr(EObject, '__deepcopy__', deepcopy)

        es = EnergySystem(name="Base EnergySystem", id="esid")
        instance = Instance(name="i1")
        area = Area(name="area51")
        es.instance.append(instance)
        instance.area = area
        pipe = Pipe(name="pipe", id='pipe1')
        inPort = InPort(name="pipe_inport")
        pipe.port.append(inPort)
        area.asset.append(pipe)
        es_copy = es.deepcopy()

        project = ESDLProject(name="Test variants Project", description="This is a test case", version="1")
        collection = VariantCollection(name="VariantCollection 1" )
        v1 = Variant(name="1st variant")

        #vb.snapshot = es
        collection.energysystem = es
        project.variantCollection.append(collection)
        collection.variant = v1

        h = HighLevelChange(label="HighlevelChange", commitMessage="Added a pipe")
        v1.change.append(h)
        a1 = Add(owner=area, feature="asset", objectValue=pipe.deepcopy())
        a2 = Add(owner=area, feature="asset", objectReference=pipe)
        h.change.extend((a1,a2))

        rset_config = create_rset(project, es_copy, json=False)

        #print(pprint(json.loads(to_string2(p,es))))
        rset_config['project_resource'].save()
        rset_config['es_resource'].save()
        print(rset_config['project_uri'].getvalue())
        print(rset_config['es_uri'].getvalue())

    def test_variantModel_delete(self):

        rset = ResourceSet()
        rset.resource_factory['esdl'] = XMLResource
        rset.resource_factory['project'] = XMLResource
        project_resource = rset.create_resource(StringURI('test.project'))
        es_resource = rset.create_resource(StringURI('active.esdl'))

        project = ESDLProject(name="Test variants Project", description="This is a test case", version="1")
        collection = VariantCollection(name="Variant collection")
        v1 = Variant(name="1st variant")

        project_resource.append(project)

        # add deepcopy support to EObjects by importing the ESH
        esh = EnergySystemHandler()
        # create simple energy system
        es: EnergySystem = esh.create_empty_energy_system(name="delete test", es_description="none", area_title="area52", inst_title="instance1")
        es_resource.append(es)

        #vb.energysystem = es
        collection.energysystemRef = es
        project.variantCollection.append(collection)
        collection.variant = v1

        #undoredo: UndoRedoCommandStack = esh.change_tracker.get_tracker_stack(es)
        ct = ChangeTracker()
        tracker = ct.newTracker( eobj=es )
        undoredo = tracker.stack

        undoredo.start_recording(label="Add Pipe")
        pipe = Pipe(name="pipe", id='pipe1')
        inPort = InPort(name="pipe_inport")
        pipe.port.append(inPort)
        area: Area = es.instance[0].area
        area.asset.append(pipe)
        undoredo.stop_recording()

        print(f'project resource: {project.eResource}: {project.eResource.uri}')
        ch = ChangeHandler(es_resource)
        action = undoredo.top
        ch.covertActionToVariantChanges(action, v1)

        print("** Current project after adding 1st pipe add: ")
        project_resource.save()
        print(project_resource.uri.getvalue())

        snapshot1 = ch.createSnapshot2(v1, rset)

        print("Snapshot1: ")
        print(ch.eobject_tree_to_string(snapshot1))
        #snapshot1.eResource.save()
        #uri: StringURI = snapshot1.eResource.uri
        #print(uri.getvalue())
        #print("project1 after creating snapshot:")
        #print(ch.eobject_tree_to_string(project))

        #active_es_resource: XMLResource = self.get_or_create_resource(rset, StringURI('active.esdl'))
        #rset.resources['active.esdl'].contents[0]
        ct.newTracker(eobj=rset.resources[StringURI('active.esdl').normalize()].contents[0])

        undoredo = tracker.stack
        undoredo.start_recording(label="add 2nd pipe and connect")
        pipe = Pipe(name="pipe2", id='pipe2')
        outPort = OutPort(name="pipe2_outport")
        pipe.port.append(outPort)
        area.asset.append(pipe)
        outPort.connectedTo.append(inPort)
        undoredo.stop_recording()

        v2 = Variant(name="Add 2nd pipe")
        v1.variant.append(v2)
        action = undoredo.top
        ch.covertActionToVariantChanges(action, v2)

        print("current project after adding 2nd pipe and connect: ")
        project_resource.save()
        print(project_resource.uri.getvalue())


        print("Snapshot2: ")
        snapshot2 = ch.createSnapshot2(v2, rset)
        print(ch.eobject_tree_to_string(snapshot2))

        rset_config = create_rset(project, snapshot2.deepcopy(), json=False)
        # print(pprint(json.loads(to_string2(p,es))))
        rset_config['project_resource'].save()
        rset_config['es_resource'].save()
        print("\n\n\nPrinting current state")
        print(rset_config['project_uri'].getvalue())
        print(rset_config['es_uri'].getvalue())




def create_rset(project: ESDLProject, es: EnergySystem, json: bool = True) -> dict:
    uri = StringURI("variant_project_" + str(uuid4()) + ".project")
    esuri = StringURI("energysystem_" + str(uuid4()) + ".esdl")
    rset = ResourceSet()
    rset.resource_factory['esdl'] = XMLResource  #
    if json:
        rset.resource_factory['project'] = JsonResource
        # hack such that we can use indent=2 on this resource
        project_resource = JsonResource(uri=uri, indent=2) #rset.create_resource(uri)
        rset.resources[uri.normalize()] = project_resource
        project_resource.resource_set = rset
        project_resource.decoders.insert(0, rset)
    else:
        rset.resource_factory['project'] = XMLResource
        project_resource = rset.create_resource(uri)
    # resource = JsonResource(uri)
    es_resource = rset.create_resource(esuri)  # JsonResource(esuri)
    project_resource.append(project)
    es_resource.append(es)
    return {'project_resource': project_resource,
            'es_resource': es_resource,
            'project_uri': uri,
            'es_uri': esuri
        }

# def to_string2(project: Project, es: EnergySystem):
#
#
#     resource.save()
#     return uri.getvalue()

def eobject_tree_to_string(eobject: EObject):
    deepcopy = eobject.deepcopy()
    string_uri = StringURI('variant1_output_shapshot.esdl')
    resource = XMLResource(string_uri)
    resource.append(deepcopy)
    resource.save()
    return string_uri.getvalue()

# remove me
#  def test_variantModel_delete_old(self):
#         # add deepcopy support to EObjects
#         esh = EnergySystemHandler()
#         es: EnergySystem = esh.create_empty_energy_system(name="delete test", es_description="none", area_title="area52", inst_title="instance1")
#
#         undoredo: UndoRedoCommandStack = esh.change_tracker.get_tracker_stack(es)
#
#         undoredo.start_recording(label="Add Pipe")
#         pipe = Pipe(name="pipe", id='pipe1')
#         inPort = InPort(name="pipe_inport")
#         pipe.port.append(inPort)
#         area: Area = es.instance[0].area
#         area.asset.append(pipe)
#         undoredo.stop_recording()
#
#
#         es_copy = es.deepcopy()
#
#         project = ESDLProject(name="Test variants Project", description="This is a test case", version="1")
#         vb = BaseVariant(name="Base variant")
#         v1 = Variant(name="1st variant")
#
#         print(f'resource: {esh.resource}, {esh.resource.contents}')
#         vb.energysystem = es
#         project.baseVariant.append(vb)
#         vb.variant.append(v1)
#
#         print(f'resource: {esh.resource}, {esh.resource.contents}')
#
#         rset = ResourceSet()
#         resource = rset.create_resource(StringURI('test.project'))
#         resource.contents.append(project)
#
#         print(f'project resource: {project.eResource}')
#         ch = ChangeHandler(resource)
#         ch.covertActionToVariantChanges(undoredo.top, v1)
#         snapshot1 = ch.createSnapshot(v1)
#
#         print("Snapshot1: ")
#         print(ch.eobject_tree_to_string(snapshot1))
#         #print("project1 after creating snapshot:")
#         #print(ch.eobject_tree_to_string(project))
#
#         undoredo.start_recording(label="add 2nd pipe and connect")
#         pipe = Pipe(name="pipe2", id='pipe2')
#         outPort = OutPort(name="pipe2_outport")
#         pipe.port.append(outPort)
#         area.asset.append(pipe)
#         outPort.connectedTo.append(inPort)
#         undoredo.stop_recording()
#
#         v2 = Variant(name="Add 2nd pipe")
#         v1.variant.append(v2)
#         ch.covertActionToVariantChanges(undoredo.top, v2)
#
#         print("current project after adding 2nd pipe and connect: ")
#         resource.save()
#         print(resource.uri.getvalue())
#
#
#         print("Snapshot2: ")
#         snapshot2 = ch.createSnapshot(v2)
#         print(ch.eobject_tree_to_string(snapshot2))
#
#         rset_config = create_rset(project, snapshot2.deepcopy(), json=False)
#         # print(pprint(json.loads(to_string2(p,es))))
#         rset_config['project_resource'].save()
#         rset_config['es_resource'].save()
#         print("\n\n\nPrinting current state")
#         print(rset_config['project_uri'].getvalue())
#         print(rset_config['es_uri'].getvalue())


if __name__ == '__main__':
    unittest.main()


