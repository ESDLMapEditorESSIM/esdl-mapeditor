import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Final, Optional, Union, Tuple, List, Any
from uuid import uuid4

from pyecore.ecore import EObject
from pyecore.resources import ResourceSet, URI, Resource

import src.log as log
from esdl import EnergySystem, esdl
from esdl.patch import patch_esdl
from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonResource
from esdl.resources.project_resource import ProjectResource
from esdl.resources.xmlresource import XMLResource, ProjectManagerResourceType
from esdl.undo import ChangeTracker, Tracker, UndoRedoCommandStack, ChangeContext
from esdlproject import ESDLProject, HighLevelChange, Variant, VariantCollection, AbstractChange
from esdlproject.change_handler import applyChange
from esdlproject.variant_api import get_parent_variant, get_variant_path_list
from utils.utils import timed

logger = log.get_logger(__name__)

def create_empty_energysystem(name, es_description, inst_title, area_title) -> esdl.EnergySystem:
    energy_system = esdl.EnergySystem(id=str(uuid4()), name=name, description=es_description)
    instance = esdl.Instance(id=str(uuid4()), name=inst_title)
    energy_system.instance.append(instance)
    area = esdl.Area(id=str(uuid4()), name=area_title)
    instance.area = area
    return energy_system

def update_uuid_dict(eobject: EObject, recursive: bool = True):
    """
    Completely updates the uuid_dict with all the IDs defined in the contents of the eobject
    (could be a whole ESDL, or just a piece of an energy system). The uuid_dict of a resource is
    used to get object by id in an energy system, by using the energy systems' resource uuid_dict provided by pyEcore.
    Parameters
    ----------
    eobject the object to add including all subcontents
    recursive default True: iterate through all subcontents of this object and add these IDs too.

    """
    resource = eobject.eResource
    if resource == None:
        logger.error("Can't update uuid_dict for {eobject}, object not contained in a Resource")
        return
    logger.debug(f"Rebuilding uuid_dict for {eobject.eResource}")
    if hasattr(eobject, 'id'):
        resource.uuid_dict[eobject.id] = eobject
    if recursive:
        for obj in eobject.eAllContents():
            if hasattr(obj, 'id'):
                resource.uuid_dict[obj.id] = obj


def load_external_string(esdl_string, name='external_string') -> Tuple[esdl.EnergySystem, list]:
    """Loads an energy system from a string but does NOT add it to the resourceSet (e.g. as a separate resource)
    It returns an Energy System (or ESDL object tree) and parse info as a tuple,
    but the ES is not part of a resource in the ResourceSet
    """
    if not name.endswith('.esdl') and not name.endswith(".json"):
        name = name + ".esdl" # default to XML ESDL files
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
    rset: ResourceSet
    project_resource: XMLResource
    project: ESDLProject
    # The change tracker that keeps track of changes.
    change_tracker: Final[ChangeTracker]
    # The currently selected variant to which changes should be applied.
    active_variant: Variant | None = None
    # List of listeners that are informed of changes to the project.
    change_listeners: dict[str, callable]
    # Key is variant ID, value is the timestamp of the last activation of the variant.
    variant_activation_timestamps: dict[str, datetime]
    # Dict for all variant collections, key is the variant collection id. We need this because we juggle with the
    # energysystemRef while saving, which leads to race conditions.
    variant_collection_resources: dict[str, XMLResource]
    # Dict for snapshot references, key is the variant id, value is the snapshot reference. We need this because we
    # empty the snapshotRef when we save the project, leading to race conditions.
    variant_snapshots: dict[str, esdl.EnergySystem]

    lock: threading.Lock

    def __init__(self, uri: URI = None):
        """
        Creates a new project manager with an empty project.
        If using uri to load a project, use StringURI(uri, text) to load a text string
        """
        patch_esdl()
        self.change_listeners = dict()
        self.variant_activation_timestamps = dict()
        self.lock = threading.Lock()
        self.active_variant_lock = threading.Lock()
        self.rset = self.__create_resource_set()
        self.change_tracker = ChangeTracker(change_handler=self.change_handler)

        if uri:
            self.load(uri)
            # TODO handle active esdl, is based on selected VariantCollection
        else:
            self.init_empty_project()

    def __create_resource_set(self) -> ResourceSet:
        resource_set = ResourceSet()
        resource_set.resource_factory["esdl"] = XMLResource
        resource_set.resource_factory["project"] = ProjectResource
        resource_set.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)
        return resource_set

    @property
    def active_tracker(self) -> Tracker:
        """
        Return the tracker from the currently active variant. If no variant is active, the first one is made active.

        :return: the tracker from the currently active variant
        """
        return self.get_change_tracker_for_variant(self.active_variant)

    def get_change_tracker_for_variant(self, variant: Variant):
        variant_snapshot = self.get_or_create_variant_snapshot(variant)
        tracker = self.change_tracker.get_tracker(variant_snapshot)
        if tracker is None:
            tracker = self.change_tracker.new_tracker(variant, variant_snapshot)
        return tracker

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
            logger.warn(f"Cannot remove change listener with id={listener_id}")

    def change_handler(self, change: HighLevelChange, change_context: ChangeContext):
        """
        Generic change handler that informs all listeners of changes to the UndoRedoCommandStack.
        Parameters
        ----------
        change HighLevelChange to send to the listeners
        """
        if change is None:
            logger.error("ERROR: Change is none in change_handler()")
            return

        for listener_id, call_back_fun in self.change_listeners.items():
            logger.info(f"Change detected, informing {listener_id}")
            call_back_fun(change, change_context)

    def _reset_project_manager(self):
        """
        Clean up the project manager to prepare for a new project, but does not yet create a new project. Note that
        after this operation, the project manager is in an empty state and a new project has to be created.
        """
        # first delete existing resources
        for key, value in dict(self.rset.resources).items():
            del self.rset.resources[key]
        self.change_tracker.reset()  # reset changetracker
        self.variant_activation_timestamps = {}
        self.variant_collection_resources = {}
        self.variant_snapshots = {}
        self.active_variant = None
        # TODO check if this is necessary, i dont think so: self.change_listeners.clear() # reset listeners

    def init_empty_project(self,
                           es_name="New Energy System",
                           es_description=None,
                           instance_name="Untitled Instance",
                           top_area_name="Untitled Area"
                           ):
        """
        Initialize an empty project. This is called when no project is loaded. It creates a new project with a base variant.
        """
        self._reset_project_manager()

        self.project_resource = self.rset.create_resource(StringURI("Untitled ESDL project.project"))  # type: ignore
        self.project_resource.type = ProjectManagerResourceType.PROJECT
        self.project = ESDLProject(name="Untitled ESDL Project")
        self.project_resource.append(self.project)
        variant_collection = self.create_empty_variant_collection(es_name, es_description, instance_name, top_area_name)
        self.set_active_variant(variant_collection.variant)

    def create_empty_variant_collection(self,
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
        variant = Variant(name=es_name, id=str(uuid4()), lastChanged=datetime.now(timezone.utc))
        new_collection.variant = variant
        es = create_empty_energysystem(es_name, es_description, instance_name, top_area_name)
        variantCollection_resource: XMLResource = self.rset.create_resource(StringURI(f"VariantCollection_{count}.esdl"))
        variantCollection_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
        #variantCollection_resource.append(es)
        variantCollection_resource.set_content(es)
        self.variant_collection_resources[new_collection.id] = variantCollection_resource
        update_uuid_dict(es)  # Energy system is now attached to a resource, update UUID dict
        new_collection.energysystemRef = es
        return new_collection

    def get_active_energy_system(self) -> esdl.EnergySystem:
        """
        Retrieve the energy system from the currently active variant. If no variant is active, the first one is made active.
        """
        if self.active_variant is None:
            logger.warn("get_active_energy_system: Warning: no active variant, selecting first in the first variant collection")
            self.set_active_variant(self.project.variantCollection[0].variant)
        return self.get_or_create_variant_snapshot(self.active_variant)

    def add_energy_system(self, uri: URI, variant_id:str = None) -> Tuple[Variant, List[str]]:
        """
        Loads an external energy system as a base variant and create a new Variant for capturing future changes

        :param uri: a StringURI with a unique uri and the esdl as string
           e.g. StringURI('my_energy_system.esdl', esdl_string)
        :param variant_id: the id the variant should have (e.g. when syncing variants between different models), default
            None.

        :return: Tuple of [the newly created variant, parse information from reading the input)
        """

        # Make sure we add the esdl extension such that XML Resources are used instead of XMI Resources
        if not uri.plain.endswith('.esdl'):
            uri.__init__(uri.plain + '.esdl')

        if uri.normalize() in self.rset.resources and isinstance(uri, StringURI):
            orig_uri = uri.plain
            new_path = f"{orig_uri.rsplit('.esdl', 1)[0]}_{str(uuid4())[:4]}.esdl"
            uri.__init__(new_path)  # update uri
            logger.debug(f"This energy system is already loaded: {orig_uri}, using a new URI: {uri.plain}")
        try:
            es_resource: XMLResource = self.rset.create_resource(uri)
            es_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
            logger.debug(f"Loading {uri.plain}")
            start = time.time()
            es_resource.load()
            end = time.time()
            logger.debug(f"Loading of ESDL in {round(end - start, 2)}s")
            es = es_resource.contents[0]
            parse_info = []
            if isinstance(es_resource, XMLResource):
                parse_info = es_resource.get_parse_information()
                if len(parse_info) > 0:
                    # TODO: handle parse information to gui
                    logger.warn(f"Resource {uri} contains parse information/errors: {parse_info}")
            #self.validate(es=tmp_es)
            #self.esid_uri_dict[tmp_es.id] = uri.normalize()
            #return es_resource.contents[0], parse_info
        except Exception as e:
            logger.error("Exception when loading resource: {}: {}".format(uri, e))
            raise

        variant_collection = VariantCollection(name=f"VariantCollection for {es.name}", id=str(uuid4()))
        self.project.variantCollection.append(variant_collection)
        variant_collection.energysystemRef = es  # link variantCollection to the loaded EnergySystem
        # self.base_variant_resources.insert(self.get_base_variant_index(base_variant), es_resource)
        if not variant_id:
            variant_id = str(uuid4())
        es_variant = Variant(name=f"{es.name}", id=variant_id, lastChanged=datetime.now(timezone.utc))
        variant_collection.variant = es_variant
        snapshot_es = self.get_or_create_variant_snapshot(es_variant)  # create snapshot for this new variant
        #self.add_object_to_dict(es.id, es)  # TODO: check if this is still necessary: should at least be at the end
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

    @timed
    def set_active_variant(self, new_variant: Variant) -> bool:
        """
        Set the active variant. This will also generate a snapshot of the current active variant, if it is not already
        generated. If the new variant is a child of the current active variant, the snapshot will be used as a base for
        the new variant. If the new variant is not a child of the current active variant, the snapshot will be used as
        a base for the new variant, and the changes in the current active variant will be applied on top of the
        snapshot.

        :param new_variant: the new active variant
        :return: boolean indicating if the new_variant changed, during activation
         (and requires e.g. gui updates)
        """
        logger.info("Setting active variant", variant_id=new_variant.id, variant_name=new_variant.name)
        logger.debug("set_active_variant(): Acquiring lock")
        with self.active_variant_lock:
            logger.debug("set_active_variant(): Lock acquired")
            new_active_variant_changed = False
            snapshot = self.get_variant_snapshot(new_variant)
            if snapshot is not None:
                # Calculate the list of variants between the VariantCollection and this variant such that we can check
                # if there are changes there, newer than ours and apply them to the new snapshot
                variant_path_list = get_variant_path_list(new_variant)
                variant_path_list.remove(new_variant)
                variant_path_list.reverse()
                logger.debug("set_active_variant(): Checking parent variants for changes", variants=[v.name for v in variant_path_list])
                for parent_variant in variant_path_list:
                    # Find the latest change in the parent with the highest changedAt.
                    parent_variant_changes = [change for change in parent_variant.change if change.changedAt is not None]
                    parent_latest_change: datetime | None = max([change.changedAt for change in parent_variant_changes]) if parent_variant_changes else None
                    # check undo/redo stack, if there something changed
                    stack_latest_change: datetime = datetime.min.replace(tzinfo=timezone.utc)  # F##! Python with aware/naive datetime objects
                    parent_snapshot = self.get_variant_snapshot(parent_variant)
                    if parent_snapshot:
                        tracker = self.change_tracker.get_tracker(parent_snapshot)
                        if tracker:
                            stack_latest_change = tracker.stack.last_changed
                    parent_latest_change = max(parent_latest_change, stack_latest_change) if parent_latest_change else None
                    # Get the timestamp of the last activation of the variant.
                    variant_last_activated_at = self.variant_activation_timestamps.get(new_variant.id, None)
                    # Only recreate the snapshot if 1) the variant was never activated, or 2) the parent has changes that
                    # are newer than the last time we activated this variant.
                    if (variant_last_activated_at is None or
                            (parent_latest_change is not None and parent_latest_change > variant_last_activated_at)):
                        logger.debug(
                            f"set_active_variant(): Parent variant contains changes not in the snapshot, recreating",
                            parent_variant=parent_variant.name, variant=new_variant.name
                        )

                        self.remove_variant_snapshot(new_variant)  # delete previous variant snapshot
                        self.replay_parent_variant_changes(new_variant)  # generate new snapshot based on parent changes
                        self.active_variant = new_variant
                        new_active_variant_changed = True
                self.active_variant = new_variant
            else:
                # New variant is selected and activated for the first time.
                logger.debug(f"set_active_variant(): Switching to new active energy system for variant {new_variant.name}")
                self.replay_parent_variant_changes(new_variant)
                new_active_variant_changed = True
                self.active_variant = new_variant

            # Update the timestamp of the last activation of the variant.
            self.variant_activation_timestamps[new_variant.id] = datetime.now(timezone.utc)

        logger.debug("set_active_variant(): Releasing lock")
        return new_active_variant_changed

    def get_active_variant(self) -> Variant | None:
        return self.active_variant

    def remove_variant_snapshot(self, variant):
        """
        Remove the snapshot of the given variant. This will also remove the resource from the resource set. This is
        used when we want to recreate the snapshot of a variant.
        :param variant:
        :return:
        """
        snapshot = self.variant_snapshots.get(variant.id, None)
        logger.info(f"Removing {snapshot.eResource}")
        tracker = self.change_tracker.get_tracker(resource=snapshot.eResource)
        if tracker is not None:
            self.change_tracker.delete(tracker=tracker)
        self.rset.remove_resource(snapshot.eResource)
        del self.variant_snapshots[variant.id]
        variant.snapshotRef = None

    def replay_parent_variant_changes(self, new_variant: Variant):
        """
        Find base Variant energy system and set that as active variant
        0: store current es as active snapshot for current active es
        1: load base variant
        2: replay changes in this variant
        """
        collection = get_variant_collection(new_variant)
        # base_variant_resource = get_base_variant_resource(base_variant)
        # self.active_resource.set_content(base_variant_resource.contents[0].deepcopy())
        collection_resource = self.get_variant_collection_resource(collection)
        contents = collection_resource.contents
        contents_0 = contents[0]
        collection.energysystemRef = collection_resource.contents[0]

        variant_path_list = get_variant_path_list(new_variant)
        variant_path_list.reverse()
        # Ensure we have a snapshot.
        #variant_snapshot = self.get_variant_snapshot(new_variant)

        changes_list = []
        for parent_variant in variant_path_list:
            stack_index = len(parent_variant.change)  # current undo/redo stack index_pointer
            parent_snapshot = self.get_variant_snapshot(parent_variant)
            if parent_snapshot:
                tracker = self.change_tracker.get_tracker(eobj=parent_snapshot)
                if tracker:
                    stack_index = tracker.stack.stack_index
                    #print(f"Using stack_index for {parent_variant.name}:", stack_index)
            changes_list.extend(parent_variant.change[:stack_index+1])
        # sort list
        changes_list.sort(key=lambda k: k.changedAt)
        #print(changes_list)
        self.apply_changes_to_variant(changes_list, new_variant, False)

    def apply_changes_to_variant(self, change_list: List[AbstractChange], target_variant: Variant, record_changes: bool):
        es = self.get_or_create_variant_snapshot(target_variant)
        resource = es.eResource
        tracker = self.change_tracker.get_tracker(resource=resource)
        if tracker is None:
            tracker = self.change_tracker.new_tracker(target_variant, eobj=es, resource=resource)
        for high_level_change in change_list:
            if isinstance(high_level_change, HighLevelChange):
                if record_changes:
                    tracker.stack.start_recording(label=high_level_change.label)
                try:
                    logger.debug(f"Apply variant change: High level change {high_level_change.label}")
                    for change in high_level_change.change:
                        applyChange(change, resource)
                finally:
                    if record_changes:
                        tracker.stack.stop_recording()
            else:
                logger.warn(f"Fixme: ignoring DetailedChanges at this level")

    # def apply_variant_changes(self, variant: Variant, es: esdl.EnergySystem, record_changes: bool):
    #     """
    #     Apply all changes from the given variant to the given resource. The resource should represent an energy system
    #     which is consequently updated to contain all changes from the variant.
    #
    #     Using the record_changes boolean, we can immediately record the changes to the tracker stack.
    #
    #     :param variant: the variant to apply
    #     :param es: the energy system to apply the changes to
    #     :param record_changes: whether to record the changes to the tracker stack
    #     """
    #     resource = es.eResource
    #     tracker = self.change_tracker.get_tracker(resource=resource)
    #     if tracker is None:
    #         tracker = self.change_tracker.new_tracker(variant=variant, resource=resource)
    #     for high_level_change in variant.change:
    #         if isinstance(high_level_change, HighLevelChange):
    #             if record_changes:
    #                 tracker.stack.start_recording(label=high_level_change.label)
    #             logger.debug(f"Apply variant change: High level change {high_level_change.label}")
    #             for change in high_level_change.change:
    #                 applyChange(change, resource)
    #             if record_changes:
    #                 tracker.stack.stop_recording()
    #         else:
    #             logger.warn(f"Fixme: ignoring DetailedChanges at this level")

    def get_energy_systems(self) -> list[esdl.EnergySystem]:
        """"
        Creates a list of all the variants associated energy systems (but not of the variantCollection energy system,
        as each variantCollection has its own main variant by convention). This only returns the snapshots of the
        variants that have a snapshot; it doesn't create new snapshots.
        """
        variants: list[Variant] = []
        for vc in self.project.variantCollection:
            vc: VariantCollection = vc
            self.get_variant_list(vc.variant, variants)
        energy_systems: list[EnergySystem] = []
        for v in variants:
            es = self.get_variant_snapshot(v)
            if es:
                energy_systems.append(es)
        return energy_systems

    def remove_variant_by_energy_system_id(self, es_id: int) -> Variant | None:
        """
        Removes a variant by its energy system id. This will also remove the snapshot of the variant.
        :param es_id: the id of the energy system to remove
        :return: the removed variant or None if no variant was found with the given id
        """
        variants: list[Variant] = []
        for vc in self.project.variantCollection:
            vc: VariantCollection = vc
            self.get_variant_list(vc.variant, variants)
        for v in variants:
            es = self.get_or_create_variant_snapshot(v)
            if es.id == es_id:
                self.delete_variant(v)
                return v
        logger.warning("Did not find variant with energy system ID", es_id=es_id)
        return None

    def get_variant_list(self, v: Variant, variant_list: list[Variant]):
        """
        Flattens the tree structure of a variant and its sub variants into a list of Variants of this variants,
        including itself.
        :param v - Variant - start variant to build the list
        :param variant_list the list where all variants should be stored in
        """
        variant_list.append(v)
        for v in v.variant:
            self.get_variant_list(v, variant_list)

    def get_variant_snapshot(self, variant: Variant) -> esdl.EnergySystem | None:
        """
        Get the snapshot of a variant. If the snapshot does not exist, it is created.
        """
        return self.variant_snapshots.get(variant.id, None)

    def get_energy_system(self, variant: Variant) -> esdl.EnergySystem:
        """
        Get the energy system of a variant. If the snapshot does not exist, it is created.
        :param variant:
        :return:
        """
        return self.get_or_create_variant_snapshot(variant)

    def get_or_create_variant_snapshot(self, variant: Variant) -> esdl.EnergySystem | None:
        """
        Saves the current active energy system as the variant snapshot for this variant by saving this
        in a temporary resource.

        :param variant: the variant to save the snapshot for
        :return: the snapshot resource
        """
        if variant is None:
            return None

        with self.lock: # lock access to variant.snapshotRef to make sure no multiple snapshots are created by multiple threads from the gui
            variant_snapshot = self.get_variant_snapshot(variant)
            if variant_snapshot is not None:
                return variant_snapshot

            base_variant_resource = self.get_variant_collection_resource(variant)
            if base_variant_resource is None:
                logger.warning("Could not find base variant resource for variant", variant=variant.name)
                return None

            snapshot_resource: XMLResource = self.rset.create_resource(StringURI(f"Snapshot_{variant.name}_{str(uuid4())[:4]}.esdl"))
            snapshot_resource.type = ProjectManagerResourceType.SNAPSHOT
            logger.info(f'Saving variant snapshot for "{variant.name}" (in {variant.eResource}) to {snapshot_resource.uri}')

            es = base_variant_resource.contents[0]

            # TODO: This deepcopy is very slow.
            snapshot_resource.set_content(es.deepcopy(uuid_dict=snapshot_resource.uuid_dict))
            snapshot = snapshot_resource.contents[0]  # link to snapshot resource energy system
            variant.snapshotRef = snapshot
            snapshot.name = variant.name  # overwrite name of ES to match the variant name
            snapshot.id = variant.id  # str(uuid4())  # generate a new energy system id for this variant
            self.variant_snapshots[variant.id] = snapshot

            #snapshot_resource.uuid_dict = dict(es.eResource.uuid_dict) # copy uuid_dict to speed up lookups by id
            #update_uuid_dict(snapshot_resource.contents[0])
            snapshot_resource.uuid_dict[snapshot.id] = snapshot
            try:
                del snapshot_resource.uuid_dict[es.id]  # remove energy system id, as that gets updated
            except KeyError:
                pass
            # make sure there is a change tracker for this snapshot
            try:
                tracker = self.change_tracker.get_tracker(eobj=snapshot)
                if tracker is None:
                    self.change_tracker.new_tracker(variant=variant, eobj=snapshot)
            except ValueError:
                self.change_tracker.new_tracker(variant=variant, eobj=snapshot)
            return snapshot

    def _select_new_active_variant(self) -> Variant:
        for vc in self.project.variantCollection:
            if vc.variant:
                return vc.variant

    def clear_project(self, add_empty_variant: bool = True):
        """
        Removes all VariantCollections and subvariants from the project. Any changes are abandoned.
        """
        for vc in self.project.variantCollection:
            self.delete_variant(vc)
        self.project.variantCollection = []
        if add_empty_variant:
            new_collection = self.create_empty_variant_collection()
            self.set_active_variant(new_collection.variant)

    def delete_variant(self, variant: Union[VariantCollection, Variant]):
        """
        Delete a variant and all its subvariants. This will also delete the snapshot of the variant.
        :param variant: the variant to delete
        """
        logger.info(f"Deleting variant: {variant.name} @ {variant.eURIFragment()}")

        if variant in get_variant_path_list(self.active_variant):  # or get_variant_collection(variant) == variant:
            # TODO reset active variant to other variant and check if there is at least 1 variant
            logger.warn("Deleted variant was active variant. Please set a new active variant")
            #self.active_variant = None
            self.set_active_variant(self._select_new_active_variant())

        if isinstance(variant, VariantCollection):
            variant_collection: VariantCollection = variant
            del self.variant_collection_resources[variant_collection.id]
            if variant_collection.variant:
                self.delete_variant(variant_collection.variant)
            if variant_collection.energysystemRef:

                logger.info(f"Removing VariantCollection energy system {variant_collection.name} from "
                            f"{variant_collection.energysystemRef.eResource.uri}")
                # self.base_variant_resources.remove(base_resource)
                es = variant_collection.energysystemRef
                variant_collection.energysystemRef = None
                self.rset.remove_resource(es.eResource)
            logger.debug(f"Removing variantCollection {variant_collection.name} from resource")
            self.project.variantCollection.remove(variant_collection, update_opposite=False)
            logger.debug(f"Done removing variant collection")
        else:
            for subvariant in variant.variant:
                self.delete_variant(subvariant)
            snapshot = self.get_variant_snapshot(variant)
            if snapshot:
                resource = snapshot.eResource
                variant.snapshotRef = None
                del self.variant_snapshots[variant.id]
                logger.debug(f"Removing snapshot of {variant.name} at {resource.uri}")
                self.rset.remove_resource(resource)
            parent = get_parent_variant(variant)
            if isinstance(parent, VariantCollection):
                parent.variant = None
                # also delete VariantCollection, as this is the only variant in the variant collection
                self.delete_variant(parent)
            else:
                parent.variant.remove(variant)

    @timed
    def save(self) -> str:
        """
        Saves the current project by storing the active esdl in the project base variant and storing the current changes
        in the active variant and then returning the project description as a string for storage

        :returns: XML string of the project
        """
        # For that it clones the active energy system and puts it in the project
        # first store the active ES in the active BV
        logger.info("Saving project to string.")

        # TODO: not needed anymore? Check
        # TODO: as changes are saved in variant already (and the stack is same as variant.changes)
        all_variants: list[Variant] = []

        # Go through all variant collections and variants and empty the snapshotRef. Store this in the
        # variant_snapshot_refs dict to restore it after we are done saving.
        for variantCollection in self.project.variantCollection:
            collection_resource = self.get_variant_collection_resource(variantCollection)
            variantCollection.energysystem = collection_resource.contents[0]
            variantCollection.energysystemRef = None
            # Find all variants in the variant collection
            all_variants.append(variantCollection.variant)
            for variant in all_variants:
                variant.snapshotRef = None
                all_variants.extend(variant.variant)

        uri = StringURI(uri=f"to_string_{str(uuid4())}.project")
        self.project_resource.save(output=uri)
        project_as_string = uri.getvalue()

        # Reset everything (use reference instead of energysystem containment relations)
        for variantCollection in self.project.variantCollection:
            collection_resource = self.get_variant_collection_resource(variantCollection)
            # use set_content() here instead of append, somehow eResource does not get updated otherwise
            collection_resource.set_content(variantCollection.energysystem)
            variantCollection.energysystemRef = collection_resource.contents[0]
            variantCollection.energysystem = None
        for variant in all_variants:
            variant.snapshotRef = self.get_variant_snapshot(variant)

        return project_as_string

    def load_from_string(self, project_string: str) -> ESDLProject:
        """
        Loads a project from a string and returns the project object.

        :param project_string: the string to load the project from
        :return: the project object
        """
        uri = StringURI("from_string.project", project_string)
        return self.load(uri)

    @timed
    def load(self, uri: URI) -> ESDLProject:
        """
        Loads a project from a URI and returns the project object.

        :param uri: the URI to load the project from
        :return: the project object
        """

        # First check if the project is valid, so that we don't corrupt the project manager.
        potential_resource_set = self.__create_resource_set()
        potential_project_resource: ProjectResource = potential_resource_set.create_resource(uri)
        potential_project_resource.type = ProjectManagerResourceType.PROJECT
        potential_project_resource.load()
        potential_project = potential_project_resource.contents[0]
        if not isinstance(potential_project, ESDLProject):
            raise Exception("The project is not a valid ESDL project.")

        self._reset_project_manager()

        self.rset = potential_resource_set

        filename = uri.plain
        logger.info(f"Loading {filename}")
        self.project_resource = potential_project_resource
        self.project = self.project_resource.contents[0]

        # self.active_resource = self.rset.create_resource(StringURI("active.esdl"))
        # tracker = self.changeTracker.newTracker(resource=self.active_resource)
        # self.undoredo_stack = tracker.stack

        if len(self.project.variantCollection) == 0:
            # no base variant exists: create one
            self.init_empty_project()

        # load the base variant energy systems into resources and set the references
        for variant_collection in self.project.variantCollection:
            self.variant_collection_resources[variant_collection.id] = variant_collection.energysystemRef.eResource
            if variant_collection.energysystem:
                # with the new ProjectResource, this is not needed anymore and is skipped, because
                # variant_collection.energysystem is None and variant_collection.energysystemRef is set to the
                # content of the Resource that has loaded the energy system at variant_collection.energysystem
                variant_collection: VariantCollection = variant_collection
                index = get_variant_collection_index(variant_collection)
                bv_uri = StringURI(uri=f"VariantCollection.{index}_{str(uuid4())[:4]}.esdl")
                variant_collection_resource = self.rset.create_resource(bv_uri)
                variant_collection_resource.type = ProjectManagerResourceType.VARIANT_COLLECTION
                if not isinstance(variant_collection_resource, XMLResource):
                    raise Exception("ESDL files are mapped to the wrong Resource type. Should be XMLResource.")
                variant_collection_resource: XMLResource = variant_collection_resource
                # self.base_variant_resources.insert(index, bv_resource)
                variant_collection_resource.set_content(variant_collection.energysystem)
                variant_collection.energysystemRef = variant_collection_resource.contents[0]

        self.active_variant = None
        self.set_active_variant(self.project.variantCollection[0].variant)
        return self.project

    def get_variant_collection_resource(self, variant: Union[VariantCollection, Variant]) -> XMLResource | None:
        """
        Get the resource of the variant collection of the given variant.

        :param variant: the variant to get the base variant resource for
        :return: the resource of the base variant of the given variant
        """
        variant_collection = get_variant_collection(variant)
        return self.variant_collection_resources.get(variant_collection.id, None)

    def get_variant_collection_by_id(self, variant_collection_id: str) -> Optional[VariantCollection]:
        """
        Get the variant collection with the given id.

        :param variant_collection_id: the id of the variant collection
        :return: the base variant with the given id or None if it does not exist
        """
        for variant_collection in self.project.variantCollection:
            if variant_collection.id == variant_collection_id:
                return variant_collection
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

    def get_energy_system_by_id_with_variant(self, es_id: str, start_variant: Optional[Variant] = None) -> Optional[esdl.EnergySystem]:
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

                snapshot = self.get_variant_snapshot(variantCollection.variant)

                if snapshot is not None and snapshot.id == es_id:
                    return snapshot
                elif len(variantCollection.variant.variant) > 0:
                    variants = variantCollection.variant.variant
                    for v in variants:
                        found = self.get_energy_system_by_id_with_variant(es_id, v)
                        if found: return found
        else:
            snapshot = self.get_variant_snapshot(start_variant)
            if snapshot is not None and snapshot == es_id:
                return snapshot

            elif len(start_variant.variant) > 0:
                for v in start_variant.variant:
                    found = self.get_energy_system_by_id_with_variant(es_id, v)
                    if found: return found # make sure to continue if not found in this branch

        return None

    def get_energy_system_by_id(self, es_id: str) -> EnergySystem:
        """
        Fastest method to find energy system by id when multiple are loaded in the resource set.
        Parameters
        ----------
        es_id id of the energy system.

        Returns
        -------

        """
        for uri, resource in self.rset.resources.items():
            if hasattr(resource.contents[0], 'id') and resource.contents[0].id == es_id:
                return resource.contents[0]
        self.debug()
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
                logger.exception(f"Cant find energy system by ID: {es_id}")
                self.debug()

    def remove_object_from_dict(self, es_id: str, eobject: EObject, recursive=False):
        if recursive:
            for obj in eobject.eAllContents():
                self.remove_object_from_dict(es_id, obj)
        es = self.get_energy_system_by_id(es_id)
        if hasattr(eobject, 'id') and eobject.id is not None:
            try:
                del es.eResource.uuid_dict[eobject.id]
            except:
                logger.warn(f"IGNORE: AutoUpdateUUID work in progress: remove_object_from_dict(): can't find {eobject.id} in {es.eResource}")

    def get_by_id(self, es_id: str, object_id: str) -> Any:
        """
        Get entity from ESDL by ID from the requested energy system.

        :param es_id: the id of the energy system to get the entity from
        :param object_id: the id of the entity to get

        :return: the entity with the given id
        """
        es = self.get_energy_system_by_id(es_id)
        if es is None:
            logger.debug(f'get_by_id() error es_id={es_id}, object_id={object_id}')
            self.debug()
            raise RuntimeError(f"Cannot find Energy System with id {es_id}")
        # es = self.get_active_energy_system()
        # if es.id != es_id:
        #     raise RuntimeError("Active ES does not match requested ES. Needs a solution.")

        # check if we can find it in the uuid_dict of the resource (faster), if not do it slow
        resource: Resource = es.eResource
        if object_id in resource.uuid_dict:
            return resource.uuid_dict[object_id]
        else:
            logger.warn(f"Can't find object id {object_id} in uuid_dict, rebuilding uuid_dict for {es}")
            update_uuid_dict(es)
            try:
                found = resource.uuid_dict[object_id]
                logger.debug(f"Found: {found} for {object_id} after rebuild in {es.eResource}")
                return found
            except KeyError as e:
                #traceback.print_exc()
                #self.debug()
                #breakpoint()
                raise KeyError("Can't find asset for id={} in uuid_dict of the ESDL model {} "
                               "after rebuilding uuid_dict.".format(object_id, es.id)) from e

    @timed
    def active_energy_system_to_string(self):
        es = self.get_active_energy_system()
        return self.energy_system_to_string(es.id)

    def add_from_string(self, name: str, esdl_string: str) -> Tuple[EnergySystem, List[str]]:
        """
        For backwards compatibility with the EnergySystemHandler.
        Use load_external_string() from this module instead.

        This function converts and ESDL string to object model, but does NOT add it to the resource set
        of the ProjectManager. It keeps it external.
        Returns
        -------
        Tuple from ESDL object tree and the parse information
        """
        return load_external_string(name, esdl_string)

    def debug(self, dump_project=False):
        #if settings.FLASK_DEBUG:
        #    print("Creating memory snapshot")
        #    snapshot = tracemalloc.take_snapshot()
        #    print("Memory snapshot ready")
        #    display_mem_usage(snapshot)
        logger.info('ProjectManager debug:')
        logger.info('All resources: ', resources=self.rset.resources)
        for uri, resource in self.rset.resources.items():
            rs_type = resource.type.name if resource.type else None
            if resource.contents:
                if isinstance(resource.contents[0], esdl.EnergySystem):
                    logger.info(f"resource: {uri} ({rs_type}): es_name={resource.contents[0].name}, id={resource.contents[0].id}")
                else:
                    logger.info(f"resource: {uri} ({rs_type}): resource_root={resource.contents[0]}")
            else:
                logger.warning(f"No contents in resource {uri}")

        for vc in self.project.variantCollection:
            vc: VariantCollection
            if vc.energysystemRef:
                logger.info(f"- {vc.name}: ref RS={vc.energysystemRef.eResource.uri} ({vc.energysystemRef.eResource.type.name}), ES={vc.energysystemRef}")
            elif vc.energysystem:
                logger.info(f"- {vc.name}: RS={vc.energysystem.eResource.uri} ({vc.energysystem.eResource.type.name}), ES={vc.energysystem}")
            vc_snapshot = self.get_variant_snapshot(vc.variant)
            rs_uri = vc_snapshot.eResource.uri if vc_snapshot else None
            rs_type = vc_snapshot.eResource.type.name if vc_snapshot else None
            logger.info(f"\t- {vc.variant.name}(id={vc.variant.id}): RS={rs_uri} ({rs_type}), ES={vc_snapshot}")
            x = vc.variant.variant
            depth = 2
            todo_list: List[Tuple[int, Variant]] = []
            todo_list.extend([(depth, p) for p in x])
            while len(todo_list) > 0:
                for (d, v) in list(todo_list):
                    indent = "\t" * d
                    snapshot = self.get_variant_snapshot(v)
                    rs_uri = snapshot.eResource.uri if snapshot else None
                    rs_type = snapshot.eResource.type.name if snapshot else None
                    logger.info(f"{indent}- {v.name}(id={v.id}): RS={rs_uri} ({rs_type}), ES={snapshot}")
                    todo_list.remove((d,v))
                    if len(v.variant) > 0:
                        todo_list.extend([(d+1, p) for p in v.variant])
        if dump_project:
            logger.info(self.to_debug_string())
        #logger.debug("Current ESDL:")
        #logger.debug(self.active_energy_system_to_string())
        #for v in vc.variant.variant:
        #    logger.debug(f"\t\t- {v.name}: RS={v.snapshotRef.eResource.uri}, ES={v.snapshotRef}")


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

    Uses eobject.deepcopy() for XMIResources to make sure the eObject
        won't be moved/detached to another Resource (default Ecore behavior).
        For XMLResource and JSONResource this is not needed
        as it uses there the `set_content_without_detaching()` method.

    Parameters
    ----------
    eobject : any eobject than needs to be serialized (e.g. a part of an ESDL or a full EnergySystem)
    format : one of ESDLFormat.XML or ESDLFormat.JSON as serialization format
    options : dictionary with options passed to resource.save()
    """
    if options is None:
        options = dict()

    string_uri = StringURI('variant1_output_shapshot.esdl')
    resource = format.value(string_uri)
    # TODO: find out if we can do this: Seems to duplicate stuff in a single test
    #if isinstance(resource, XMLResource) or isinstance(resource, JsonResource):
    #    resource.set_content_without_detaching(eobject)
    #else:
    start = time.time()
    deepcopy = eobject.deepcopy()
    end = time.time()
    logger.debug(f"deepcopy() of {eobject.eClass.name} took {round(end - start, 2)}s")
    resource.append(deepcopy)
    resource.save(options=options)
    return string_uri.getvalue()


def get_variant_collection(variant: Union[VariantCollection, Variant]) -> VariantCollection | None:
    """
    Get the base variant of the given variant.

    :param variant: the variant to get the base variant for
    :return: the base variant of the given variant
    """
    if isinstance(variant, VariantCollection):
        return variant
    elif variant.variantCollection is None and variant.parentVariant is not None:
        return get_variant_collection(variant.parentVariant)
    elif variant.variantCollection is not None:
        return get_variant_collection(variant.variantCollection)
    else:
        logger.error(f"Can't find variantCollection for variant {variant}")
        return None

