import json
import threading
import traceback
from datetime import datetime
from enum import Enum
from typing import Final, Optional, Union, Tuple, List
from uuid import uuid4

from pyecore.ecore import EObject, EReference, EClass, EStructuralFeature, EAttribute
from pyecore.resources import ResourceSet, URI, Resource
from pyecore import commands as pyecore_commands

from esdl import EnergySystem, esdl, support_functions
from esdl.patch import patch_esdl
from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonResource
from esdl.resources.xmlresource import XMLResource, ProjectManagerResourceType
from esdl.undo import ChangeTracker, LabelledAction, Tracker, UndoRedoCommandStack
from esdlproject import Add, Delete, ESDLProject, HighLevelChange, Remove, Set, Variant, \
    VariantCollection
from esdlproject.ChangeSerializer import deepcopy_eobject_change, filterDoubleConnectedTo
from esdlproject.actions import convertActionToVariantChanges
from esdlproject.variant_api import get_parent_variant, get_variant_path_list

import src.log as log

logger = log.get_logger(__name__)

def create_empty_energysystem(name, es_description, inst_title, area_title) -> esdl.EnergySystem:
    energy_system = esdl.EnergySystem(id=str(uuid4()), name=name, description=es_description)
    instance = esdl.Instance(id=str(uuid4()), name=inst_title)
    energy_system.instance.append(instance)
    area = esdl.Area(id=str(uuid4()), name=area_title)
    instance.area = area
    return energy_system

def load_external_string(esdl_string, name='external_string') -> Tuple[esdl.EnergySystem, list]:
    """Loads an energy system from a string but does NOT add it to the resourceSet (e.g. as a separate resource)
    It returns an Energy System and parse info as a tuple, but the ES is not part of a resource in the ResourceSet
    """
    if not name.endswith('.esdl'):
        name = name + ".esdl"
    uri = StringURI(name, esdl_string)
    external_rset = ResourceSet()
    external_resource = external_rset.create_resource(uri)
    external_resource.load()
    parse_info = []
    if isinstance(external_resource, XMLResource):
        parse_info = external_resource.get_parse_information()
    external_energy_system = external_resource.contents[0]
    #self.validate(es=external_energy_system)
    return external_energy_system, parse_info


def update_energy_system_version(self, es: EnergySystem) -> str:
    """
    Increments the version of this Energy System and returns it

    """
    version = '' if es.version is None else str(es.version)
    try:
        import re
        splitted = re.split(r"\D", version)
        major = splitted[0]
        major = int(major) + 1
    except ValueError:
        major = 1
    es.version = str(major)
    return es.version


def get_variant_collection_index(variantCollection: VariantCollection) -> int:
    """Returns the unique index in the VariantCollection list"""
    return (
        variantCollection.eContainer()
        .__getattribute__(variantCollection.eContainmentFeature().name)
        .index(variantCollection)
    )


class ProjectManager:
    """
    Class that manages the project and its variants. It is responsible for loading and saving the project,
    and for keeping track of changes to the project. It also provides functions to apply changes to the project.

    The project manager is responsible for keeping track of the active variant. This is the variant to which
    changes are applied. The active variant is always a variant that is based on a VariantCollection that contains
    an esdl.EnergySystem.
    """

    # The resource set that contains all resources.
    rset: Final[ResourceSet]
    project_resource: XMLResource
    project: ESDLProject
    # The change tracker that keeps track of changes.
    change_tracker: Final[ChangeTracker]
    # The currently selected variant to which changes should be applied.
    active_variant: Optional[Variant]
    change_listeners = dict()

    lock = threading.Lock()

    # base_variant_resources: Final[list[XMLResource]]

    # undoredo_stack: UndoRedoCommandStack

    def __init__(self, uri: URI = None):
        """
        Creates a new project manager with an empty project.
        If using uri to load a project, use StringURI(uri, text) to load a text string
        """
        patch_esdl()

        self.rset = ResourceSet()
        self.change_tracker = ChangeTracker(change_handler=self.change_handler)
        self.active_variant = None
        # self.base_variant_resources = []
        self.rset.resource_factory["esdl"] = XMLResource
        self.rset.resource_factory["project"] = XMLResource
        self.rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)

        if uri:
            self.load(uri)
            # TODO handle active esdl, is based on selected VariantCollection
        else:
            self.init_empty_project()

    @property
    def active_tracker(self) -> Tracker:
        """
        Return the tracker from the currently active variant. If no variant is active, the first one is made active.

        :return: the tracker from the currently active variant
        """
        variant_snapshot = self.get_variant_snapshot(self.active_variant)
        active_tracker = self.change_tracker.get_tracker(variant_snapshot)
        if active_tracker is None:
            active_tracker = self.change_tracker.newTracker(variant_snapshot)
        return active_tracker

    def add_change_listener(self, listener_id: str, call_back_fun):
        """
        Adds a listener to changes of ProjectManager's managed resources by informing listeners of changes
        to the UndoRedoCommandStack
        Parameters
        ----------
        listener_id - string to uniquely identify a listener
        call_back_fun - function to call when a change is detected.
        """
        self.change_listeners[listener_id] = call_back_fun

    def remove_change_listener(self, listener_id):
        """ Remove listener_id from the list of listeners"""
        if listener_id in self.change_listeners:
            del self.change_listeners[listener_id]
        else:
            print(f"Cannot remove change listener with id={listener_id}")

    def change_handler(self, action: LabelledAction):
        """
        Generic change handler that informs all listeners of changes to the UndoRedoCommandStack.
        Parameters
        ----------
        action LabelledAction
        """
        for listener_id, call_back_fun in self.change_listeners.items():
            print(f"Change detected, informing {listener_id}")
            call_back_fun(action)

    def init_empty_project(self,
                           es_name="New Energy System",
                           es_description=None,
                           instance_name="Untitled Instance",
                           top_area_name="Untitled Area"
                           ):
        """
        Initialize an empty project. This is called when no project is loaded. It creates a new project with a base variant.

        """
        # first delete existing resources
        for key, value in dict(self.rset.resources).items():
            del self.rset.resources[key]
        self.change_tracker.reset()  # reset changetracker
        self.change_listeners.clear() # reset listeners
        self.project_resource = self.rset.create_resource(StringURI("Untitled ESDL project.project"))  # type: ignore
        self.project_resource.type = ProjectManagerResourceType.PROJECT
        # self.active_resource = self.rset.create_resource(StringURI("active.esdl"))  # type: ignore
        self.project = ESDLProject(name="Untitled ESDL Project")
        self.project_resource.append(self.project)
        variantCollection = self.add_new_variant_collection(es_name, es_description, instance_name, top_area_name)
        # tracker = self.changeTracker.newTracker(resource=self.active_resource)
        # self.undoredo_stack = tracker.stack
        self.set_active_variant(variantCollection.variant)

    def add_new_variant_collection(self,
                                   es_name="New Energy System",
                                   es_description=None,
                                   instance_name="Untitled Instance",
                                   top_area_name="Untitled Area") -> VariantCollection:
        """
        Create a new, empty base variant. With an empty energy system with specified name, description, instance_name
        and top_area_name
        """
        count = len(self.project.variantCollection) + 1
        new_collection = VariantCollection(name=f"Variant Collection - EnergySystem {count}", id=str(uuid4()))
        self.project.variantCollection.append(new_collection)
        variant = Variant(name=es_name, id=str(uuid4()), lastChanged=datetime.now())
        new_collection.variant = variant
        es = create_empty_energysystem(es_name, es_description, instance_name, top_area_name)
        # self.active_resource.append(es)
        # self.base_variant_resources.append(
        #     self.rset.create_resource(StringURI("base.esdl"))  # type: ignore
        # )
        # base_variant_idx = self.get_base_variant_index(base_variant)
        # self.base_variant_resources[base_variant_idx].append(es.deepcopy())

        variantCollection_resource = self.rset.create_resource(StringURI(f"VariantCollection_{count}.esdl"))
        variantCollection_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
        new_es: EnergySystem = es.deepcopy()
        variantCollection_resource.append(new_es)
        new_collection.energysystemRef = new_es
        return new_collection

    def get_active_energy_system(self) -> esdl.EnergySystem:
        """
        Retrieve the energy system from the currently active variant. If no variant is active, the first one is made active.
        """
        if self.active_variant is None:
            print("Warning: no active variant, selecting first in the first variant collection")
            self.set_active_variant(self.project.variantCollection[0].variant)
        if self.active_variant.snapshotRef is None:
            self.get_variant_snapshot(self.active_variant)
        return self.active_variant.snapshotRef  # return reference to current resource with active energy system

    def add_energy_system(self, uri: StringURI) -> Tuple[Variant, List[str]]:
        """
        Loads an external energy system as a base variant and create a new Variant for capturing future changes

        :param uri: a StringURI with a unique uri and the esdl as string
           e.g. StringURI('my_energy_system.esdl', esdl_string)

        :return: Tuple of [the newly created variant, parse information from reading the input)
        """
        if uri.normalize() in self.rset.resources:
            orig_uri = uri.plain
            uri.__init__(f"{uri.plain}_{str(uuid4())[:4]}")  # update uri
            print(f"This energy system is already loaded: {orig_uri}, using a new URI: {uri.plain}")
        try:
            es_resource: XMLResource = self.rset.create_resource(uri)
            es_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
            es_resource.load()
            es = es_resource.contents[0]
            parse_info = []
            if isinstance(es_resource, XMLResource):
                parse_info = es_resource.get_parse_information()
                if len(parse_info) > 0:
                    # TODO: handle parse information to gui
                    print(f"Resource {uri} contains parse information/errors: {parse_info}")
            #self.validate(es=tmp_es)
            #self.esid_uri_dict[tmp_es.id] = uri.normalize()
            #return es_resource.contents[0], parse_info
        except Exception as e:
            logger.error("Exception when loading resource: {}: {}".format(uri, e))
            raise


        variantCollection = VariantCollection(name=f"VariantCollection for {es.name}", id=str(uuid4()))
        self.project.variantCollection.append(variantCollection)
        variantCollection.energysystemRef = es  # link variantCollection to the loaded EnergySystem
        # self.base_variant_resources.insert(self.get_base_variant_index(base_variant), es_resource)
        es_variant = Variant(name=f"{es.name}", id=str(uuid4()), lastChanged=datetime.now())
        variantCollection.variant = es_variant
        snapshot_es = self.get_variant_snapshot(es_variant)  # create snapshot for this new variant
        self.add_object_to_dict(es.id, es)  # TODO: check if this is still necessary: should at least be at the end
        return es_variant, parse_info

    def get_variant_by_id(self, variant_id: str) -> Optional[Variant]:
        """
        Retrieve a variant by its id. This is a recursive function which searches through all base variants and their variants.

        :param variant_id: the id of the variant to retrieve
        :return: the variant with the given id, or None if not found
        """
        for variantCollection in self.project.variantCollection:
            variantCollection: VariantCollection
            result = self._get_variant_by_id_dfs([variantCollection.variant], variant_id)
            if result is not None:
                return result
        return None

    def _get_variant_by_id_dfs(self, v: list[Variant], variant_id: str) -> Optional[Variant]:
        """
        Recursive function to search for a variant by its id using Depth First Search (DFS).
        This function is called by get_variant_by_id.

        :param v: the list of variants to search through
        :param variant_id: the id of the variant to retrieve
        :return: the variant with the given id, or None if not found
        """
        if len(v) > 0:
            for variant in v:
                if variant.id == variant_id:
                    return variant
                result = self._get_variant_by_id_dfs(variant.variant, variant_id)
                if result is not None:
                    return result
        return None

    def set_active_variant(self, new_variant: Variant):
        """
        Set the active variant. This will also generate a snapshot of the current active variant, if it is not already
        generated. If the new variant is a child of the current active variant, the snapshot will be used as a base for
        the new variant. If the new variant is not a child of the current active variant, the snapshot will be used as
        a base for the new variant, and the changes in the current active variant will be applied on top of the
        snapshot.

        :param new_variant: the new active variant
        """

        if self.active_variant == new_variant:
            print("set_active_variant(): no change in variant")
        elif new_variant.snapshotRef is not None:
            # TODO: We need to handle the situation where changes were done in the parent. The snapshot should then be
            # regenerated, but the changes from the child should be maintained. This means that before switching, we
            # need to make sure that any variant changes are persisted.
            # Right now we ignore any changes in the parent if we already have a snapshot.

            print("Variant snapshot already generated. Creating new one based on changes (now always, should be smarter). "
                  "(WIP)")
            # if new_variant.snapshotRef:
            #     variant_tracker = self.change_tracker.get_tracker(new_variant.snapshotRef)
            #     if variant_tracker:
            #         variant_stack = variant_tracker.stack
            #         if variant_stack.lastChanged > new_variant.lastChanged:
            #             for action in variant_stack.stack:
            #                 convertActionToVariantChanges(action, new_variant)

            # Calculate the list of variants between the VariantCollection and this variant such that we can check
            # if there are changes there, newer than ours and apply them to the new snapshot
            variant_path_list = get_variant_path_list(new_variant)
            variant_path_list.remove(new_variant)
            variant_path_list.reverse()
            print("Checking following parent variants for changes: ", [v.name for v in variant_path_list])
            for v in variant_path_list:
                if v.lastChanged > new_variant.lastChanged:
                    print(f"Variant {v.name} contains changes not in the snapshot, recreating")

                    self.remove_variant_snapshot(new_variant)  # delete previous variant
                    self.replay_parent_variant_changes(new_variant)
                    self.active_variant = new_variant
                    if len(new_variant.change) > 0:
                        # this variant has changes, replay these
                        #self.apply_variant_changes(new_variant, new_variant.snapshotRef, False)
                        pass
            self.active_variant = new_variant

        # TODO: I think this special case should not need special handling.
        # elif get_parent_variant(new_variant) == self.active_variant:
        #     # current active variant is the parent, so we can continue with storing changes in this variant
        #     # without changing the current active ES, and only apply changes in this new active variant
        #     print(
        #         f"set_active_variant(): Continuing recording changes in new variant {new_variant.name}"
        #     )
        #     parent_variant = self.active_variant
        #     if len(parent_variant.change) > 0:
        #         print(
        #             f"set_active_variant(): Replaying variant {new_variant.name} @ {new_variant.eURIFragment()}"
        #         )
        #         self.apply_variant_changes(self.active_variant, new_variant.snapshotRef)
        #     self.active_variant = new_variant
        else:
            print(f"set_active_variant(): Switching to new active energy system for variant {new_variant.name}")
            # workflow is discontinued: different variant is selected
            self.replay_parent_variant_changes(new_variant)
            self.active_variant = new_variant

        self.debug()

    def remove_variant_snapshot(self, variant):
        print(f"Removing {variant.snapshotRef.eResource}")
        self.rset.remove_resource(variant.snapshotRef.eResource)
        variant.snapshotRef = None

    def replay_parent_variant_changes(self, new_variant):
        # find base Variant energy system and set that as active variant
        # 0: store current es as active snapshot for current active es
        # 1: load base variant
        # 2: replay changes in this variant
        collection = get_variant_collection(new_variant)
        # base_variant_resource = get_base_variant_resource(base_variant)
        # self.active_resource.set_content(base_variant_resource.contents[0].deepcopy())
        collection_resource = get_variant_collection_resource(collection)
        collection.energysystemRef = collection_resource.contents[0]

        variant_path_list = get_variant_path_list(new_variant)
        variant_path_list.reverse()
        # Ensure we have a snapshot.
        variant_snapshot = self.get_variant_snapshot(new_variant)
        # add changes to stack, clear stack
        for parent_variant in variant_path_list:
            print(f"replay_parent_variant_changes(): Replaying variant {parent_variant.name} @ {parent_variant.eURIFragment()}")
            self.apply_variant_changes(parent_variant, variant_snapshot, True)

    def apply_variant_changes(self, variant: Variant, es: esdl.EnergySystem, record_changes: bool):
        """
        Apply all changes from the given variant to the given resource. The resource should represent an energy system
        which is consequently updated to contain all changes from the variant.

        Using the record_changes boolean, we can immediately record the changes to the tracker stack.

        :param variant: the variant to apply
        :param es: the energy system to apply the changes to
        :param record_changes: whether to record the changes to the tracker stack
        """
        resource = es.eResource
        tracker = self.change_tracker.get_tracker(resource=resource)
        if tracker is None:
            tracker = self.change_tracker.newTracker(resource=resource)
        for high_level_change in variant.change:
            if isinstance(high_level_change, HighLevelChange):
                if record_changes:
                    tracker.stack.start_recording(label=high_level_change.label)
                print(f"Handling High level change {high_level_change.label}")
                for change in high_level_change.change:
                    self.processChange(change, resource)
                if record_changes:
                    tracker.stack.stop_recording()
            else:
                print(f"Fixme: ignoring DetailedChanges at this level")

    def processChange(self, change, resource: XMLResource):
        """
        Process a change and apply it to the given resource.

        :param change: the change to apply
        :param resource: the resource to apply the change to
        """
        print(
            f"Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature} applying it to {resource.uri}"
        )
        if isinstance(change, Set):
            if change.objectValue is not None:
                print(f"\- Set change applied to {change.ownerFragment}")
                owner = resource.resolve(change.ownerFragment)
                owner.eSet(change.feature, change.objectValue.deepcopy())
            elif change.stringValue is not None:
                owner = resource.resolve(change.ownerFragment)
                feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
                if isinstance(feature, EAttribute):
                    owner.eSet(change.feature, feature.eType.from_string(change.stringValue))
                else:  # eReference and not many
                    if change.stringValue == "":
                        owner.eSet(change.feature, None)
                    else:
                        target = resource.resolve(change.stringValue)
                        owner.eSet(change.feature, target)

        elif isinstance(change, Add):
            if change.objectValue is not None:
                print(f"\- Add change applied to {change.ownerFragment}")
                owner = resource.resolve(change.ownerFragment)
                abstractList = owner.eGet(change.feature)
                abstractList.append(change.objectValue.deepcopy())
            elif change.objectReference:
                pass  # TODO
            elif change.stringValue:
                owner: EObject = resource.resolve(change.ownerFragment)
                abstractList = owner.eGet(change.feature)
                eClass: EClass = owner.eClass
                feature: EStructuralFeature = eClass.findEStructuralFeature(change.feature)
                if isinstance(feature, EReference):
                    eReference: EReference = feature
                    if eReference.containment:
                        print("processChange(): Not handled reference.containment")
                    else:
                        print(f"\- Add change reference {change.stringValue} applied to {change.ownerFragment}")
                        ref = resource.resolve(change.stringValue)
                        abstractList.append(ref)
                else:
                    print(f"\- Add change attribute value {change.stringValue} applied to {change.ownerFragment}")
                    abstractList.append(change.stringValue)
        elif isinstance(change, Remove):
            # remove a value or reference from a list
            owner: EObject = resource.resolve(change.ownerFragment)
            feature: EStructuralFeature = owner.eClass.findEStructuralFeature(change.feature)
            abstractList = owner.eGet(change.feature)
            if isinstance(feature, EReference):
                try:
                    ref = resource.resolve(change.stringValue)
                    abstractList.remove(ref)
                except Exception:
                    print(f"\- ###: Cannot execute change, resolving of {change.stringValue} failed")
            else:
                # stringvalue is a value (enum, string, int, etc)
                abstractList.remove(feature.eType.from_string(change.stringValue))
        elif isinstance(change, Delete):
            owner: EObject = resource.resolve(change.ownerFragment)
            owner.delete()

    def get_energy_systems(self) -> List[esdl.EnergySystem]:
        """"
        Creates a list of all the variants associated energy systems (but not of the variantCollection energy system,
        as each variantCollection has its own main variant by convention)
        """
        variants: List[Variant] = []
        for vc in self.project.variantCollection:
            vc: VariantCollection = vc
            self.get_variant_list(vc.variant, variants)
        energy_systems: List[EnergySystem] = []
        for v in variants:
            es = self.get_variant_snapshot(v)
            energy_systems.append(es)
        return energy_systems

    def get_variant_list(self, v: Variant, variant_list: List[Variant]):
        """
        Flattens the tree structure of a variant and its sub variants into a list of Variants of this variants,
        including itself.
        :param v - Variant - start variant to build the list
        :param variant_list the list where all variants should be stored in
        """
        variant_list.append(v)
        for v in v.variant:
            self.get_variant_list(v, variant_list)

    def get_energy_system(self, variant: Variant) -> esdl.EnergySystem:
        return self.get_variant_snapshot(variant)

    def get_variant_snapshot(self, variant: Variant) -> esdl.EnergySystem:
        """
        Saves the current active energy system as the variant snapshot for this variant by saving this
        in a temporary resource.

        :param variant: the variant to save the snapshot for
        :return: the snapshot resource
        """
        if variant is None:
            return None

        with self.lock: # lock access to variant.snapshotRef to make sure no muliple snapshort are created by multiple threads from the gui
            if variant.snapshotRef is not None:
                return variant.snapshotRef

            snapshot_resource = self.rset.create_resource(StringURI(f"Snapshot_{variant.name}_{str(uuid4())[:4]}.esdl"))
            snapshot_resource.type = ProjectManagerResourceType.SNAPSHOT
            print(f'Saving variant snapshot for "{variant.name}" (in {variant.eResource}) to {snapshot_resource.uri}')
            base_variant_resource = get_variant_collection_resource(variant)
            es = base_variant_resource.contents[0]
            es.name = variant.name # overwrite name of ES to match the variant name

            snapshot_resource.append(es.deepcopy())
            snapshot_resource.uuid_dict = dict(es.eResource.uuid_dict) # copy uuid_dict to speed up lookups by id
            variant.snapshotRef = snapshot_resource.contents[0]  # link to snapshot resource energy system
            variant.snapshotRef.id = variant.id  # str(uuid4())  # generate a new energy system id for this variant
            return variant.snapshotRef

    def _delete_variant_recursive(self, variant: Variant):
        """
        Recursively delete a variant and all its subvariants. This will also delete the snapshot of the variant.
        :param variant: the variant to delete
        """
        for subvariant in variant.variant:
            self._delete_variant_recursive(subvariant)
        print(f"Deleting variant: {variant.name} @ {variant.eURIFragment()}")
        if variant.snapshotRef:
            resource = variant.snapshotRef.eResource
            variant.snapshotRef = None
            print(f"Removing snapshot of {variant.name} at {resource.uri}")
            self.rset.remove_resource(resource)
        parent = get_parent_variant(variant)
        parent.variant.remove(variant)

    def select_new_active_variant(self) -> Variant:
        for vc in self.project.variantCollection:
            if vc.variant:
                return vc.variant

    def clear_project(self):
        """
        Removes all VariantCollections and subvariants from the project

        Any changes are abandoned
        Returns
        -------

        """
        for vc in self.project.variantCollection:
            self.delete_variant(vc)

    def delete_variant(self, variant: Union[VariantCollection, Variant]):
        """
        Delete a variant and all its subvariants. This will also delete the snapshot of the variant.
        :param variant: the variant to delete
        """
        if variant.variant:
            for subvariant in variant.variant:
                self._delete_variant_recursive(subvariant)
        print(f"Deleting variant: {variant.name} @ {variant.eURIFragment()}")

        if variant in get_variant_path_list(self.active_variant): # or get_variant_collection(variant) == variant:
            # todo reset active variant to other variant and check if there is at least 1 variant
            print("Deleted variant was active variant. Please set a new active variant")
            #self.active_variant = None
            self.set_active_variant(self.select_new_active_variant())

        if isinstance(variant, VariantCollection):
            variantCollection: VariantCollection = variant
            if variantCollection.energysystemRef:
                # base_resource = self.base_variant_resources[ get_base_variant_index(variant)]

                print(f"Removing VariantCollection energy system {variantCollection.name} from "
                      f"{variantCollection.energysystemRef.eResource.uri}")
                # self.base_variant_resources.remove(base_resource)
                self.rset.remove_resource(variantCollection.energysystemRef.eResource)
                variantCollection.energysystemRef = None
            self.project.variantCollection.remove(variantCollection)
        else:
            if variant.snapshotRef:
                resource = variant.snapshotRef.eResource
                variant.snapshotRef = None
                print(f"Removing snapshot of {variant.name} at {resource.uri}")
                self.rset.remove_resource(resource)
            parent = get_parent_variant(variant)
            if isinstance(parent, VariantCollection):
                parent.variant = None
                # also delete VariantCollection, as this is the only variant in the variant collection
                self.delete_variant(parent)
            else:
                parent.variant.remove(variant)

    def save(self) -> str:
        """
        Saves the current project by storing the active esdl in the project base variant and storing the current changes
        in the active variant and then returning the project description as a string for storage

        :returns: XML string of the project
        """
        # For that it clones the active energy system and puts it in the project
        # first store the active ES in the active BV

        # todo add changes to current variant that are still on the stack
        print("Saving project, assuming all changes on the stack are put in the active variant")

        resources_dict = {}

        for variantCollection in self.project.variantCollection:

            collection_resource = get_variant_collection_resource(variantCollection)
            resources_dict[variantCollection.id] = collection_resource
            variantCollection.energysystem = collection_resource.contents[0].deepcopy()
            variantCollection.energysystemRef = None
            # todo: change such that we iterate over subvariants
            #for variant in variantCollection.variant:
            variant = variantCollection.variant  # main variant
            if variant.snapshotRef:
                variant_tracker = self.change_tracker.get_tracker(variant.snapshotRef)
                if variant_tracker:
                    variant_stack = variant_tracker.stack
                    for action in variant_stack.stack:
                        convertActionToVariantChanges(action, variant)
                variant.snapshotRef = None

        uri = StringURI(uri=f"to_string_{str(uuid4())}.project")
        self.project_resource.save(output=uri)
        project_as_string = uri.getvalue()

        # reset everything (use reference instead of energysystem containment relations)

        for variantCollection in self.project.variantCollection:
            #collection_resource = get_variant_collection_resource(variantCollection)
            collection_resource = resources_dict[variantCollection.id]
            variantCollection.energysystem = None
            variantCollection.energysystemRef = collection_resource.contents[0]

        resources_dict = None
        return project_as_string

    def load(self, uri: URI) -> ESDLProject:
        """
        Loads a project from a URI and returns the project object.

        :param uri: the URI to load the project from
        :return: the project object
        """
        # clear current ResourceSet
        for r_uri, resource in dict(self.rset.resources).items():
            self.rset.remove_resource(resource)
        # self.base_variant_resources.clear()
        self.change_tracker.trackers.clear()

        filename = uri.plain
        print(f"Loading {filename}")
        self.project_resource = self.rset.create_resource(uri)
        self.project_resource.type = ProjectManagerResourceType.PROJECT
        self.project_resource.load()
        self.project = self.project_resource.contents[0]

        # self.active_resource = self.rset.create_resource(StringURI("active.esdl"))
        # tracker = self.changeTracker.newTracker(resource=self.active_resource)
        # self.undoredo_stack = tracker.stack

        if len(self.project.variantCollection) == 0:
            # no base variant exists: create one
            self.init_empty_project()

        # load the base variant energy systems into resources and set the references
        for variantCollection in self.project.variantCollection:
            if variantCollection.energysystem:
                variantCollection: VariantCollection = variantCollection
                index = get_variant_collection_index(variantCollection)
                bv_uri = StringURI(uri=f"VariantCollection.{index}_{str(uuid4())[:4]}.esdl")
                variantCollection_resource = self.rset.create_resource(bv_uri)
                variantCollection_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
                if not isinstance(variantCollection_resource, XMLResource):
                    raise Exception("ESDL files are mapped to the wrong Resource type. Should be XMLResource.")
                variantCollection_resource: XMLResource = variantCollection_resource
                # self.base_variant_resources.insert(index, bv_resource)
                variantCollection_resource.set_content(variantCollection.energysystem)
                variantCollection.energysystemRef = variantCollection_resource.contents[0]

        self.active_variant = None
        self.set_active_variant(self.project.variantCollection[0].variant)
        return self.project

    def get_base_variant_by_id(self, base_variant_id: str) -> Optional[VariantCollection]:
        """
        Get the base variant with the given id.

        :param base_variant_id: the id of the base variant
        :return: the base variant with the given id or None if it does not exist
        """
        for base_variant in self.project.variantCollection:
            if base_variant.id == base_variant_id:
                return base_variant
        return None

    def to_debug_string(self) -> str:
        """
        Converts the in-memory version of this project to a string, mainly for debugging.
        It will include references to other ESDL resources.

        For a full contained version of this project use save(). This will serialize also the referenced energy
        systems of EnergySystemProxys inline in this project. This allows it to be passed on to others to load this project
        using the load() function
        """
        if isinstance(self.project_resource.uri, StringURI):
            uri: StringURI = self.project_resource.uri
            self.project_resource.save()
            return uri.getvalue()

        else:
            uri = StringURI("print.project")
            self.project_resource.save(output=uri)
            return uri.getvalue()

    def get_undo_redo_stack(self, eobj: EObject = None, es_id: str = None) -> UndoRedoCommandStack:
        """
        Return the undo-redo stack of this EnergySystemHandler for a specific ESDL object (when eobj = not None)
        or by the current active es_id (es_id is not None)

        :param eobj: the ESDL object to get the undo-redo stack for
        :param es_id: the ESDL energy system ID to get the undo-redo stack for
        :return: the undo-redo stack of this EnergySystemHandler for a specific ESDL object


        """
        if eobj:
            return self.change_tracker.get_tracker_stack(eobj=eobj)
        elif es_id:
            es = self.get_energy_system_by_id(es_id)
            return self.change_tracker.get_tracker_stack(eobj=es)
        else:
            return self.active_tracker.stack

    def energy_system_to_string(self, es_id: str) -> str:
        """
        """
        resource = self.get_energy_system_resource_by_id(es_id)
        return resource_as_string(resource)

    def get_energy_system_resource_by_id(self, es_id: str) -> Optional[Resource]:
        """
        Get the resource of the energy system with the given id.

        :param es_id: the id of the energy system to get the resource for
        :return: the resource of the active energy system or the resource of the energy system with the given id
        """
        es = self.get_energy_system_by_id(es_id)
        if es is None:
            return None
        return es.eResource
        # for resource in self.rset.resources.values():
        #     resource_es_id = resource.contents[0].id
        #     if resource_es_id == es_id:
        #         return resource
        # return None

    def get_energy_system_by_id(self, es_id: str, start_variant: Optional[Variant] = None) -> Optional[esdl.EnergySystem]:
        """
        Attempts to find the energy system with the given ID, by inspecting the snapshots of the variants.

        :param es_id: the id of the energy system to get
        :param start_variant: the variant to start searching (used for recursing into the hierarchy)
        :return: the energy system with the given id or None if it does not exist
        """
        if start_variant is None:
            for variantCollection in self.project.variantCollection:
                if variantCollection.energysystemRef and variantCollection.energysystemRef.id == es_id:
                    return variantCollection.energysystemRef

                if variantCollection.variant.snapshotRef and variantCollection.variant.snapshotRef.id == es_id:
                    return variantCollection.variant.snapshotRef
                elif len(variantCollection.variant.variant) > 0:
                    variants = variantCollection.variant.variant
                    for v in variants:
                        found = self.get_energy_system_by_id(es_id, v)
                        if found: return found
        else:
            if start_variant.snapshotRef and start_variant.snapshotRef.id == es_id:
                return start_variant.snapshotRef

            elif len(start_variant.variant) > 0:
                for v in start_variant.variant:
                    found = self.get_energy_system_by_id(es_id, v)
                    if found: return found # make sure to continue if not found in this branch

        return None

    def get_energy_system_by_id2(self, es_id: str):
        for uri, resource in self.rset.resources.items():
            if hasattr(resource.contents[0], 'id') and resource.contents[0].id == es_id:
                return resource.contents[0]
        raise Exception(f"EnergySystem ID es_id {es_id} not found in ResourceSet")

    def add_object_to_dict(self, es_id:str, eobject:EObject, recursive=False):
        if recursive:
            for obj in eobject.eAllContents():
                self.add_object_to_dict(es_id, obj)
        es = self.get_energy_system_by_id(es_id)
        if hasattr(eobject, 'id'):
            try:
                es.eResource.uuid_dict[eobject.id] = eobject
            except AttributeError as e:
                print(f"Cant find energy system by ID: {es_id}, stacktrace: ")
                for line in traceback.format_stack():
                    print(line.strip())
                self.debug()
    def remove_object_from_dict(self, es_id: str, eobject: EObject, recursive=False):
        if recursive:
            for obj in eobject.eAllContents():
                self.remove_object_from_dict(es_id, obj)
        es = self.get_energy_system_by_id(es_id)
        if hasattr(eobject, 'id') and eobject.id is not None:
            del es.eResource.uuid_dict[eobject.id]

    def get_by_id(self, es_id: str, object_id: str):
        """
        Get entity from ESDL by ID from the requested energy system.

        :param es_id: the id of the energy system to get the entity from
        :param object_id: the id of the entity to get

        :return: the entity with the given id
        """
        es = self.get_energy_system_by_id2(es_id)
        if es is None:
            print(f'get_by_id() error es_id={es_id}, object_id={object_id}')
            self.debug()
            raise RuntimeError(f"Cannot find Energy System with id {es_id}")
        # es = self.get_active_energy_system()
        # if es.id != es_id:
        #     raise RuntimeError("Active ES does not match requested ES. Needs a solution.")

        # check if we can find it in the uuid_dict of the resource (faster), if not do it slow
        resource: Resource = es.eResource
        if object_id in resource.uuid_dict:
            return resource.uuid_dict[object_id]

        # TODO: This is relatively slow. We need to migrate to a better solution (use uuid_dict again?).
        for entity in es.eAllContents():
            if hasattr(entity, "id") and entity.id == object_id:
                return entity

        self.debug()
        raise KeyError("Can't find asset for id={} in uuid_dict of the ESDL model {}".format(object_id, es.id))

    def active_energy_system_to_string(self):
        active_resource = self.active_variant.eResource
        if isinstance(active_resource.uri, StringURI):
            uri: StringURI = active_resource.uri
            active_resource.save()
            return uri.getvalue()
        else:
            uri = StringURI("print.esdl")
            active_resource.save(output=uri)
            return uri.getvalue()

    def debug(self):
        print('ProjectManager debug:')
        print('All resources: ', self.rset.resources)
        for uri, resource in self.rset.resources.items():
            rs_type = resource.type.name if resource.type else None
            if isinstance(resource.contents[0], esdl.EnergySystem):
                print(f"resource: {uri} ({rs_type}): es_name={resource.contents[0].name}, id={resource.contents[0].id}")
            else:
                print(f"resource: {uri} ({rs_type}): resource_root={resource.contents[0]}")

        for vc in self.project.variantCollection:
            vc: VariantCollection
            if vc.energysystemRef:
                print(f"- {vc.name}: ref RS={vc.energysystemRef.eResource.uri} ({vc.energysystemRef.eResource.type.name}), ES={vc.energysystemRef}")
            elif vc.energysystem:
                print(f"- {vc.name}: RS={vc.energysystem.eResource.uri} ({vc.energysystem.eResource.type.name}), ES={vc.energysystem}")
            rs_uri = vc.variant.snapshotRef.eResource.uri if vc.variant.snapshotRef else None
            rs_type = vc.variant.snapshotRef.eResource.type.name if vc.variant.snapshotRef else None
            print(f"\t- {vc.variant.name}: RS={rs_uri} ({rs_type}), ES={vc.variant.snapshotRef}")
            x = vc.variant.variant
            depth = 2
            todo_list: List[Tuple[int, Variant]] = []
            todo_list.extend([(depth, p) for p in x])
            while len(todo_list) > 0:
                for (d, v) in list(todo_list):
                    indent = "\t" * d
                    rs_uri = v.snapshotRef.eResource.uri if v.snapshotRef else None
                    rs_type = v.snapshotRef.eResource.type.name if v.snapshotRef else None
                    print(f"{indent}- {v.name}: RS={rs_uri} ({rs_type}), ES={v.snapshotRef}")
                    todo_list.remove((d,v))
                    if len(v.variant) > 0:
                        todo_list.extend([(d+1, p) for p in v.variant])
        print(self.to_debug_string())
            #for v in vc.variant.variant:
            #    print(f"\t\t- {v.name}: RS={v.snapshotRef.eResource.uri}, ES={v.snapshotRef}")


def resource_as_string(resource: Resource):
    """
    Get the string representation of the given resource. If the resource is a StringURI, the value of the StringURI
    is returned. Otherwise, the resource is saved to a StringURI and the value of the StringURI is returned.

    :param resource: the resource to get the string representation for
    :return: the string representation of the given resource
    """
    if isinstance(resource.uri, StringURI):
        uri: StringURI = resource.uri
        resource.save()
        return uri.getvalue()
    else:
        extension = "esdl"
        eobject = resource.contents[0]
        if isinstance(eobject, ESDLProject):
            extension = "project"
        uri = StringURI("print." + extension)
        resource.save(output=uri)
        return uri.getvalue()


class ESDLFormat(Enum):
    XML = XMLResource
    JSON = JsonResource


def eobject_to_string(eobject: EObject, format: ESDLFormat = ESDLFormat.XML, options: dict = None):
    """
    Converts any eObject (and its contents) to a string.

    Uses eobject.deepcopy() to make sure the eObject won't be moved to another Resource (default Ecore behavior)

    Parameters
    ----------
    eobject : any eobject than needs to be serialized (e.g. a part of an ESDL or a full EnergySystem)
    format : one of ESDLFormat.XML or ESDLFormat.JSON as serialization format
    options : dictionary with options passed to resource.save()
    """
    if options is None:
        options = dict()
    deepcopy = eobject.deepcopy()
    string_uri = StringURI('variant1_output_shapshot.esdl')
    resource = format.value(string_uri)
    resource.append(deepcopy)
    resource.save(options=options)
    return string_uri.getvalue()


def get_variant_collection(variant: Union[VariantCollection, Variant]) -> VariantCollection:
    """
    Get the base variant of the given variant.

    :param variant: the variant to get the base variant for
    :return: the base variant of the given variant
    """
    if isinstance(variant, VariantCollection):
        return variant
    elif variant.variantCollection is None and variant.parentVariant is not None:
        return get_variant_collection(variant.parentVariant)
    else:
        return get_variant_collection(variant.variantCollection)


def get_variant_collection_resource(variant: Union[VariantCollection, Variant]) -> XMLResource:
    """
    Get the resource of the variant collection of the given variant.

    :param variant: the variant to get the base variant resource for
    :return: the resource of the base variant of the given variant
    """
    variantCollection = get_variant_collection(variant)
    # index = self.get_base_variant_index(base_variant)
    return variantCollection.energysystemRef.eResource
    # return self.base_variant_resources[index]
