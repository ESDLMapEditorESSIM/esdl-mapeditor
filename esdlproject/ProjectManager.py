from datetime import datetime
from typing import Final, List, Optional, Union
from uuid import uuid4

from pyecore.ecore import EObject, EReference, EClass, EStructuralFeature, EAttribute
from pyecore.resources import ResourceSet, URI, Resource
from pyecore import commands as pyecore_commands

from esdl import esdl, support_functions
from esdl.esdl_handler import EnergySystemHandler, StringURI
from esdl.resources.xmlresource import XMLResource
from esdl.undo import ChangeTracker, LabelledAction, Tracker, UndoRedoCommandStack
from esdlproject import Add, BaseVariant, Delete, ESDLProject, HighLevelChange, Remove, Set, Variant
from esdlproject.ChangeSerializer import deepcopy_eobject_change, filterDoubleConnectedTo
from esdlproject.variant_api import get_parent_variant, get_variant_path_list


def create_empty_energysystem(name, es_description, inst_title, area_title) -> esdl.EnergySystem:
    energy_system = esdl.EnergySystem(
        id=str(uuid4()), name=name, description=es_description
    )
    instance = esdl.Instance(id=str(uuid4()), name=inst_title)
    energy_system.instance.append(instance)
    area = esdl.Area(id=str(uuid4()), name=area_title)
    instance.area = area
    return energy_system


class ProjectManager:
    """
    Class that manages the project and its variants. It is responsible for loading and saving the project,
    and for keeping track of changes to the project. It also provides functions to apply changes to the project.

    The project manager is responsible for keeping track of the active variant. This is the variant to which
    changes are applied. The active variant is always a variant that is based on the base variant.
    """

    # The resource set that contains all resources.
    rset: Final[ResourceSet]
    project_resource: XMLResource
    project: ESDLProject
    # The change tracker that keeps track of changes.
    changeTracker: Final[ChangeTracker]
    # The currently selected variant to which changes should be applied.
    active_variant: Optional[Variant]
    base_variant_resources: Final[List[XMLResource]]

    # undoredo_stack: UndoRedoCommandStack

    def __init__(self, uri: URI = None):
        """
        Creates a new project manager with an empty project.
        If using uri to load a project, use StringURI(uri, text) to load a text string
        """
        # import ESH to have deepcopy and copy available.
        esh = EnergySystemHandler()
        setattr(EObject, 'serialized_deepcopy', support_functions.serialized_deepcopy)

        self.rset = ResourceSet()
        self.changeTracker = ChangeTracker()
        self.active_variant = None
        self.base_variant_resources = []
        self.rset.resource_factory["esdl"] = XMLResource
        self.rset.resource_factory["project"] = XMLResource
        if uri:
            self.load(uri)
            # TODO handle active esdl, is based on selected baseVariant
        else:
            self.init_empty_project()

    @property
    def active_tracker(self) -> Tracker:
        """
        Return the tracker from the currently active variant. If no variant is active, the first one is made active.

        :return: the tracker from the currently active variant
        """
        variant_snapshot = self.get_variant_snapshot(self.active_variant)
        active_tracker = self.changeTracker.get_tracker(variant_snapshot)
        if active_tracker is None:
            active_tracker = self.changeTracker.newTracker(variant_snapshot)
        return active_tracker

    def init_empty_project(self):
        """
        Initialize an empty project. This is called when no project is loaded. It creates a new project with a base variant.

        """
        self.project_resource = self.rset.create_resource(StringURI("test.project"))  # type: ignore
        # self.active_resource = self.rset.create_resource(StringURI("active.esdl"))  # type: ignore
        self.project = ESDLProject(name="New ESDL Project", description="Base variant")
        self.project_resource.append(self.project)
        base_variant = self.create_new_base_variant()
        # tracker = self.changeTracker.newTracker(resource=self.active_resource)
        # self.undoredo_stack = tracker.stack
        self.set_active_variant(base_variant.variant[0])

    def create_new_base_variant(self) -> BaseVariant:
        """
        Create a new, empty base variant.
        """
        count = len(self.project.baseVariant) + 1
        base_variant = BaseVariant(name=f"Base variant {count}", id=str(uuid4()))
        self.project.baseVariant.append(base_variant)
        variant = Variant(name="Untitled variant", id=str(uuid4()))
        base_variant.variant.append(variant)
        es = create_empty_energysystem("New Energy System", None, "Instance1", "Untitled Area")
        # self.active_resource.append(es)
        self.base_variant_resources.append(
            self.rset.create_resource(StringURI("base.esdl"))  # type: ignore
        )
        base_variant_idx = self.get_base_variant_index(base_variant)
        self.base_variant_resources[base_variant_idx].append(es.deepcopy())
        base_variant.energysystemRef = es
        return base_variant

    def get_active_energy_system(self) -> esdl.EnergySystem:
        """
        Retrieve the energy system from the currently active variant. If no variant is active, the first one is made active.
        """
        if self.active_variant is None:
            self.set_active_variant(self.project.baseVariant[0].variant[0])
        return self.active_variant.snapshotRef

    def add_energy_system(self, uri: StringURI) -> Variant:
        """
        Loads an external energy system as a base variant and create a new Variant for capturing future changes

        :param uri: a StringURI with a unique uri and the esdl as string
           e.g. StringURI('my_energy_system.esdl', esdl_string)

        :return: the newly created variant.
        """
        if uri.normalize() in self.rset.resources:
            orig_uri = uri.plain
            uri.__init__(f"{uri.plain}_{str(uuid4())[:4]}")  # update uri
            print(f"This energy system is already loaded: {orig_uri}, using a new URI: {uri.plain}")
        es_resource: XMLResource = self.rset.create_resource(uri)
        es_resource.load()
        es = es_resource.contents[0]

        base_variant = BaseVariant(name=f"Base variant for {es.name}", id=str(uuid4()))
        self.project.baseVariant.append(base_variant)
        es_variant = Variant(name=f"1st variant of {es.name}", id=str(uuid4()))
        base_variant.variant.append(es_variant)
        base_variant.energysystemRef = es
        self.base_variant_resources.insert(self.get_base_variant_index(base_variant), es_resource)
        return es_variant

    def get_base_variant_index(self, base_variant: BaseVariant) -> int:
        """ Returns the unique index in the baseVariant list"""
        return (
            base_variant.eContainer()
                .__getattribute__(base_variant.eContainmentFeature().name)
                .index(base_variant)
        )

    def get_variant_by_id(self, variant_id: str) -> Optional[Variant]:
        """
        Retrieve a variant by its id. This is a recursive function which searches through all base variants and their variants.

        :param variant_id: the id of the variant to retrieve
        :return: the variant with the given id, or None if not found
        """
        for bv in self.project.baseVariant:
            bv: BaseVariant
            result = self._get_variant_by_id_dfs(bv.variant, variant_id)
            if result is not None:
                return result
        return None

    def _get_variant_by_id_dfs(self, v: List[Variant], variant_id: str) -> Optional[Variant]:
        """
        Recursive function to search for a variant by its id. This function is called by get_variant_by_id.

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

    def convertActionToVariantChanges(self, action: LabelledAction, variant: Variant) -> List[Change]:
        """
        Convert an action, retrieved from the tracker stack, to a high level change containing the detailed changes which can be stored and serialized with projects.

        :param action: the action to convert
        :param variant: the variant to store the changes in

        :return: a list of changes
        """
        print(
            f'Converting LabelledAction {action.label} to changes in variant {variant.name} ({variant.eURIFragment()})')
        hlc = HighLevelChange(label=action.label, changedAt=datetime.now())  # EDate.from_string("2021-10-27T12:00:00")
        variant.change.append(hlc)
        change_list = []

        for command in action:
            command: pyecore_commands.AbstractCommand
            change = None
            print(f'------ Handling {command}')
            if isinstance(command, pyecore_commands.Add):
                if isinstance(command.value, EObject):  # could also be a numeric change or string change
                    if command.feature.containment:  # isinstance(command.feature, EReference):
                        # value = command.value.serialized_deepcopy(resource=self.active_resource) #clone()
                        value, x_ref_changes = deepcopy_eobject_change(command.value)
                        # TODO make deepcopy() work
                        change = Add(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name,
                                     objectValue=value)
                        change_list.extend(x_ref_changes)
                    else:
                        # this is a x-reference, zo add it to the changeList, to add it as last, otherwise
                        # some x-ref targets might not be available when deserializing
                        print(
                            f'convertActionToVariantChanges(): using ref for {command.value} to {command.value.eURIFragment()} ')
                        change = Add(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name,
                                     stringValue=command.value.eURIFragment())
                        change_list.append(change)
                        change = None
                else:
                    # TODO add numbers/enums to list
                    print(f'TODO Add: convert {command.value} to something')

            # variant.changes.append(change)
            if isinstance(command, pyecore_commands.Set):
                if isinstance(command.value, EObject) or isinstance(command.previous_value,
                                                                    EObject):  # could also be a numeric change or string change
                    if command.feature.containment:
                        value, x_ref_changes = deepcopy_eobject_change(command.value)
                        change = Set(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name,
                                     objectValue=value)
                        change_list.extend(x_ref_changes)
                    else:
                        if command.value:
                            print(
                                f'convertActionToVariantChanges(): using ref for {command.value} to {command.value.eURIFragment()} ')
                            refValue = command.valueURIFragment  # command.value.eURIFragment() -> See undo.py:230
                        else:
                            refValue = ""
                        change = Set(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name,
                                     stringValue=refValue)
                else:  # enums / strings / numbers
                    previousValue = None
                    if command.value is None:
                        stringValue = ""
                    else:
                        stringValue = command.feature.eType.to_string(command.value)
                    if command.previous_value:
                        previousValue = command.feature.eType.to_string(command.previous_value)
                    change = Set(ownerFragment=command.owner.eURIFragment(), feature=command.feature.name,
                                 stringValue=stringValue, previousValue=previousValue)

            if isinstance(command, pyecore_commands.Remove):
                if isinstance(command.value, EObject):  # could also be a numeric change or string change
                    if command.feature.containment:
                        change = Delete(ownerFragment=command.refURIFragment)
                    else:
                        # owner = command.owner.eURIFragment()
                        owner = command.ownerFragment
                        ref = command.refURIFragment
                        change = Remove(ownerFragment=owner, feature=command.feature.name, stringValue=ref)

            if change:  # in case of x-ref: add it to the changeList instead directly in this list
                hlc.change.append(change)

        if len(change_list) > 0:  # add last, to make sure that x-ref targets are present
            cleanedChangeList = filterDoubleConnectedTo(change_list)
            print(
                f'------ Adding cross-references of size {len(cleanedChangeList)}, (removed {len(change_list) - len(cleanedChangeList)} duplicates)')
            hlc.change.extend(cleanedChangeList)  # add x-references from deepcopy()

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

            print("Variant snapshot already generated. No need to do anything but switch the active variant.")
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
            print(
                f"set_active_variant(): Switching to new active energy system for variant {new_variant.name}"
            )
            # workflow is discontinued: different variant is selected
            # find base Variant energy system and set that as active variant

            # 0: store current es as active snapshot for current active es
            # 1: load base variant
            # 2: replay changes in this variant
            base_variant = self.get_base_variant(new_variant)
            # base_variant_resource = self.get_base_variant_resource(base_variant)
            # self.active_resource.set_content(base_variant_resource.contents[0].deepcopy())
            base_variant_resource = self.get_base_variant_resource(base_variant)
            base_variant.energysystemRef = base_variant_resource.contents[0]
            self.active_variant = new_variant
            variant_path_list = get_variant_path_list(new_variant)
            variant_path_list.reverse()
            # Ensure we have a snapshot.
            variant_snapshot = self.get_variant_snapshot(self.active_variant)

            # add changes to stack, clear stack
            for parent_variant in variant_path_list:
                print(
                    f"set_active_variant(): Replaying variant {parent_variant.name} @ {parent_variant.eURIFragment()}"
                )

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
        tracker = self.changeTracker.get_tracker(resource=resource)
        if tracker is None:
            tracker = self.changeTracker.newTracker(resource=resource)
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
            f'Processing {change.eClass.name}, owner={change.ownerFragment}, feature={change.feature} applying it to {resource.uri}')
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
                feature: EStructuralFeature = eClass.findEStructuralFeature(
                    change.feature
                )
                if isinstance(feature, EReference):
                    eReference: EReference = feature
                    if eReference.containment:
                        print("processChange(): Not handled reference.containment")
                    else:
                        print(
                            f"\- Add change reference {change.stringValue} applied to {change.ownerFragment}"
                        )
                        ref = resource.resolve(change.stringValue)
                        abstractList.append(ref)
                else:
                    print(
                        f"\- Add change attribute value {change.stringValue} applied to {change.ownerFragment}"
                    )
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
                    pass
            else:
                # stringvalue is a value (enum, string, int, etc)
                abstractList.remove(feature.eType.from_string(change.stringValue))
        elif isinstance(change, Delete):
            owner: EObject = resource.resolve(change.ownerFragment)
            owner.delete()

    def get_variant_snapshot(self, variant: Variant) -> esdl.EnergySystem:
        """
        Saves the current active energy system as the variant snapshot for this variant by saving this
        in a temporary resource.

        :param variant: the variant to save the snapshot for
        :return: the snapshot resource
        """
        if variant is None:
            return None

        if variant.snapshotRef is not None:
            return variant.snapshotRef

        snapshot_resource = self.rset.create_resource(StringURI(f'Snapshot_{variant.name}_{str(uuid4())[:4]}.esdl'))
        print(f'Saving variant snapshot for "{variant.name}" (in {variant.eResource}) to {snapshot_resource.uri}')
        base_variant_resource = self.get_base_variant_resource(variant)
        es = base_variant_resource.contents[0]

        snapshot_resource.append(es.deepcopy())
        variant.snapshotRef = snapshot_resource.contents[0]  # link to snapshot resource energy system
        variant.snapshotRef.id = str(uuid4())
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

    def delete_variant(self, variant: Union[BaseVariant, Variant]):
        """
        Delete a variant and all its subvariants. This will also delete the snapshot of the variant.
        :param variant: the variant to delete
        """
        for subvariant in variant.variant:
            self._delete_variant_recursive(subvariant)
        print(f"Deleting variant: {variant.name} @ {variant.eURIFragment()}")

        if variant in get_variant_path_list(self.active_variant) or self.get_base_variant(variant) == variant:
            # todo reset active variant to other variant and check if there is at least 1 variant
            print("Deleted variant was active variant. Please set a new active variant")
            self.active_variant = None

        if isinstance(variant, BaseVariant):
            variant: BaseVariant = variant
            if variant.energysystemRef:
                base_resource = self.base_variant_resources[self.get_base_variant_index(variant)]
                variant.energysystemRef = None
                print(f'Removing BaseVariant energy system {variant.name} at {base_resource.uri}')
                self.base_variant_resources.remove(base_resource)
                self.rset.remove_resource(base_resource)
            self.project.baseVariant.remove(variant)
        else:
            if variant.snapshotRef:
                resource = variant.snapshotRef.eResource
                variant.snapshotRef = None
                print(f"Removing snapshot of {variant.name} at {resource.uri}")
                self.rset.remove_resource(resource)
            parent = get_parent_variant(variant)
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
        print(
            "Saving project, assuming all changes on the stack are put in the active variant"
        )

        for bv in self.project.baseVariant:
            base_variant_resource = self.get_base_variant_resource(bv)
            bv.energysystem = base_variant_resource.contents[0].deepcopy()
            bv.energysystemRef = None
            for variant in bv.variant:
                if variant.snapshotRef:
                    variant_tracker = self.changeTracker.get_tracker(variant.snapshotRef)
                    if variant_tracker:
                        variant_stack = variant_tracker.stack
                        for action in variant_stack.stack:
                            self.convertActionToVariantChanges(action, variant)
                    variant.snapshotRef = None

        uri = StringURI(uri=f"to_string_{str(uuid4())}.project")
        self.project_resource.save(output=uri)
        project_as_string = uri.getvalue()

        # reset the energysystems in the project (might not be necessary as it is only used for serialization), but reduces memory consumption
        for bv in self.project.baseVariant:
            base_variant_resource = self.get_base_variant_resource(bv)
            bv.energysystem = None
            bv.energysystemRef = base_variant_resource.contents[0]

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
        self.base_variant_resources.clear()
        self.changeTracker.trackers.clear()

        filename = uri.plain
        print(f"Loading {filename}")
        self.project_resource = self.rset.create_resource(uri)
        self.project_resource.load()
        self.project = self.project_resource.contents[0]

        # self.active_resource = self.rset.create_resource(StringURI("active.esdl"))
        # tracker = self.changeTracker.newTracker(resource=self.active_resource)
        # self.undoredo_stack = tracker.stack

        if len(self.project.baseVariant) == 0:
            # no base variant exists: create one
            self.init_empty_project()

        # load the base variant energy systems into resources and set the references
        for bv in self.project.baseVariant:
            if bv.energysystem:
                bv: BaseVariant = bv
                index = self.get_base_variant_index(bv)
                bv_uri = StringURI(uri=f"BaseVariant.{index}_{str(uuid4())[:4]}.esdl")
                bv_resource = self.rset.create_resource(bv_uri)
                if not isinstance(bv_resource, XMLResource):
                    raise Exception(
                        "ESDL files are mapped to the wrong Resource type. Should be XMLResource."
                    )
                bv_resource: XMLResource = bv_resource
                self.base_variant_resources.insert(index, bv_resource)
                bv_resource.set_content(bv.energysystem)
                bv.energysystemRef = bv_resource.contents[0]

        self.active_variant = None
        self.set_active_variant(self.project.baseVariant[0].variant[0])
        return self.project

    def get_base_variant(self, variant: Union[BaseVariant, Variant]) -> BaseVariant:
        """
        TODO: Can be static / part of variant_api.
        """
        if isinstance(variant, BaseVariant):
            return variant
        elif variant.baseVariant is None and variant.parentVariant is not None:
            return self.get_base_variant(variant.parentVariant)
        else:
            return self.get_base_variant(variant.baseVariant)

    def get_base_variant_resource(
            self, variant: Union[BaseVariant, Variant]
    ) -> XMLResource:
        """
        TODO: Can be static / part of variant_api.
        """
        if isinstance(variant, Variant):
            base_variant = self.get_base_variant(variant)
        else:
            base_variant = variant
        index = self.get_base_variant_index(base_variant)
        return self.base_variant_resources[index]

    def get_base_variant_by_id(self, base_variant_id: str) -> Optional[BaseVariant]:
        """
        Get the base variant with the given id.

        :param base_variant_id: the id of the base variant
        :return: the base variant with the given id or None if it does not exist
        """
        for base_variant in self.project.baseVariant:
            if base_variant.id == base_variant_id:
                return base_variant
        return None

    def to_debug_string(self) -> str:
        """
        Converts the in-memory version of this project to a string, mainly for debugging.
        It will include references to other ESDL resources.

        For a full contained version of this project use save(). This will serialize also the referenced energy
        systems of BaseVariants inline in this project. This allows it to be passed on to others to load this project
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

    def active_energy_system_to_string(self):
        """
        TODO: This doesn't work right now. Fix to use variant energy system.
        """
        if isinstance(self.active_resource.uri, StringURI):
            uri: StringURI = self.active_resource.uri
            self.active_resource.save()
            return uri.getvalue()
        else:
            uri = StringURI("print.esdl")
            self.active_resource.save(output=uri)
            return uri.getvalue()

    def get_resource(self, es_id=None) -> Optional[Resource]:
        """
        Get the resource of the active energy system or the resource of the energy system with the given id. If no
        energy system with the given id exists, None is returned.

        :param es_id: the id of the energy system to get the resource for
        :return: the resource of the active energy system or the resource of the energy system with the given id
        """
        if es_id is None:
            return self.get_active_energy_system()

        for resource in self.base_variant_resources:
            id = resource.contents[0].id
            if id == es_id:
                return resource
        return None

    def get_undo_redo_stack(self, eobj: EObject = None) -> UndoRedoCommandStack:
        """
        Return the undo-redo stack of this EnergySystemHandler for a specific ESDL object (when eobj = not None)
        or by the current active es_id (es_id is not None)

        :param eobj: the ESDL object to get the undo-redo stack for
        :return: the undo-redo stack of this EnergySystemHandler for a specific ESDL object
        """
        if eobj:
            return self.changeTracker.get_tracker_stack(eobj=eobj)
        else:
            return self.active_tracker.stack

    def get_energy_system_by_id(self, es_id: str) -> Optional[esdl.EnergySystem]:
        """
        Attempts to find the energy system with the given ID, by inspecting the snapshots of the variants.

        :param es_id: the id of the energy system to get
        :return: the energy system with the given id or None if it does not exist
        """
        for base_variant in self.project.baseVariant:
            for variant in base_variant.variant:
                # TODO: Recursion (variant of variant etc).
                if variant.snapshotRef and variant.snapshotRef.id == es_id:
                    return variant.snapshotRef
        return None

    def get_by_id(self, es_id: str, object_id: str):
        """
        Get entity from ESDL by ID from the requested energy system.

        :param es_id: the id of the energy system to get the entity from
        :param object_id: the id of the entity to get

        :return: the entity with the given id
        """
        es = self.get_energy_system_by_id(es_id)
        if es is None:
            raise RuntimeError("ES does not exist.")
        # es = self.get_active_energy_system()
        # if es.id != es_id:
        #     raise RuntimeError("Active ES does not match requested ES. Needs a solution.")

        # TODO: This is relatively slow. We need to migrate to a better solution (use uuid_dict again?).
        for entity in es.eAllContents():
            if hasattr(entity, "id") and entity.id == object_id:
                return entity

        raise KeyError('Can\'t find asset for id={} in uuid_dict of the ESDL model'.format(object_id))


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
