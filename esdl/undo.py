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
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, List

from flask import Flask
from pyecore.ecore import EObject, EStructuralFeature, EReference, EAttribute
from pyecore.notification import EObserver, Notification, Kind
from pyecore.resources import Resource

import esdlproject.esdlproject as ep
import src.log as log
from esdl.resources.xmlresource import XMLResource
from esdl.undo_pyecore_patch import patch_notification_system
from esdlproject import HighLevelChange
from esdlproject.ChangeSerializer import deepcopy_eobject_change, filterDoubleConnectedTo
from esdlproject.change_handler import undoChange, applyChange

patch_notification_system()  # patch pyecores notification system, so notification are always send

logger = log.get_logger(__name__)


class ChangeSource(Enum):
    """
    Defines the source of a change. This allows change_handlers (registered in ProjectManager.add_change_listener())
    to distinguish between different changes
    """
    INTERNAL  = 0  # default case: by python programming code
    EXTERNAL  = 1  # currently only 1 LMI is distinguished. But from an LMI, external is MapEditor
    FRONT_END = 2  # for future: when user in front-end updates ESDL -> auto update UI

@dataclass
class ChangeContext:
    source: ChangeSource
    client_id: Optional[str] = None
    resource: Optional[XMLResource] = None
    flask_app: Optional[Flask] = None


class UndoRedoCommandStack:
    """
    Creates a undo and redo command stack for ESDL documents
    Use -1 to create an unlimited stack.
    change_handler is a callback function that receives a HighLevelChange when a new change is generated
    """
    #stack: list[HighLevelChange]

    def __init__(self, variant: ep.Variant, resource: XMLResource, max_stack_length: int = -1, change_handler=None):
        # The actual changes. Right now it is a list of pyEcore commands.
        self.variant = variant
        self.resource = resource  # target resource to apply and undo changes to
        self.stack = variant.change
        # The location in the stack where the last currently active change is stored.
        self.stack_index = len(self.stack) - 1  # -1
        self._recording = False
        self._combine_multiple_changes = True
        self._hlc: ep.HighLevelChange | None = None
        self.max_stack_length = max_stack_length
        self.last_changed: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self.change_handler = change_handler
        # post_process_list keeps track of notifications that cannot be processed directly (e.g. missing references)
        self.post_process_list: List[Notification] = []
        self.change_context: ChangeContext = ChangeContext(source=ChangeSource.INTERNAL, resource=self.resource)
        self.recording_lock = threading.Lock()
        self._failed_lock_acquire_count = 0

    @property
    def top(self) -> ep.AbstractChange | None:
        """
        Returns the element at the top of the stack. Returns None if the stack is empty.
        """
        if self.stack_index < 0:
            return None
        # make sure the stack index is not out of bounds.
        self.stack_index = min(len(self.stack) - 1, self.stack_index)
        return self.stack[self.stack_index]

    @property
    def next_top(self) -> ep.AbstractChange | None:
        """
        Returns the element above the current top of the stack. Returns None if there is no such element.
        """
        if self.stack_index + 1 >= len(self.stack):
            return None
        return self.stack[self.stack_index + 1]

    def is_empty(self):
        return len(self.stack) == 0

    def size(self):
        return len(self.stack)

    def _update_context(self, context: ChangeContext):
        """
        Fill in a Change context with information the stack has.
        """
        if context is None:
            self.change_context.source = ChangeSource.INTERNAL
            return

        if context.resource:
            self.change_context.resource = context.resource
        if context.client_id:
            self.change_context.client_id = context.client_id
        if context.flask_app:
            self.change_context.flask_app = context.flask_app
        if context.source:
            self.change_context.source = context.source

    def start_recording(self, combine_commands: bool = True, label: str = None,
                        change_context: ChangeContext = None):
        """
        Starts recording of changes in the loaded ESDL model

        :param bool combine_commands: collect all actions into one single HighLevelChange (default = True)
        :param label: name of the label of the action that is recorded.
        :param change_context: the context of the change, default INTERNAL
        """
        logger.debug("Acquiring recording lock", label=label)
        acquired = self.recording_lock.acquire() # timeout=60)  # lock is released in stop_recording()
        if acquired:
            self._failed_lock_acquire_count = 0
        else:
            self._failed_lock_acquire_count += 1
            logger.warning("Could not acquire recording lock", attempt=self._failed_lock_acquire_count, label=label)
            if self._failed_lock_acquire_count > 5:
                # Probably this is a deadlock. Some process is not releasing the lock.
                self.recording_lock.release()
                acquired = self.recording_lock.acquire(timeout=10)
                if not acquired:
                    raise TimeoutError("Could not acquire recording lock (even by forcing)")
            else:
                raise TimeoutError("Could not acquire recording lock")
        self._update_context(change_context)
        logger.debug(f"=== start recording: {label} =====================================")
        self._recording = True
        self._combine_multiple_changes = combine_commands
        if combine_commands:
            self._hlc = ep.HighLevelChange(label=label, changedAt=datetime.now(timezone.utc))

    def is_recording(self):
        return self._recording

    @contextmanager
    def track_changes(self, label: str, combine_commands: bool = True, change_context: ChangeContext = None,
                      call_change_handler: bool = True):
        """
        Convenience method with context manager to track changes using this stack.
        Does the same as stack.start_recording(label="label") and afterwards
        stack.stop_recording(call_change_hander=call_change_handler)
        Parameters
        ----------
        label - label for this set of changes (required)
        call_change_handler - whether the change_handler should be called afterwards (default=True)
        """
        self._update_context(change_context)
        self.start_recording(label=label, combine_commands=combine_commands, change_context=self.change_context)
        try:
            yield
        finally:
            self.stop_recording(call_change_handler=call_change_handler)

    @contextmanager
    def pause_recording(self):
        """
        Temporarily pause recording of changes.
        """
        reset = False
        # make sure pause_recording also works if you are not recording
        if self.recording_lock.locked() and self._recording:
            self.recording_lock.release()
            reset = True
            self._recording = False
        try:
            yield
        finally:
            if not self.recording_lock.locked() and reset:
                self.recording_lock.acquire(timeout=10)
                self._recording = True


    def stop_recording(self, call_change_handler: bool = True):
        """
        Stops recording of changes in a resource and stops putting them on the stack.
        The change_source (used in start_recording() is reset to INTERNAL)

        Parameters
        ----------
        call_change_handler if True the change_handler configured when creating this Stack
                            will be called. This is set to False if you dont want to react
                            on changes, e.g. when replaying changes to a resource.
        """
        logger.debug("=== stop recording =====================================")
        self._combine_multiple_changes = False  # this triggers that the HighLevelChange is added to the stack
        if self._hlc is not None and len(self._hlc.change) > 0:
            # filter out eOpposite relations that are double (e.g. connectedTo)
            filtered, _ = filterDoubleConnectedTo(self._hlc.change)
            if len(filtered) != len(self._hlc.change):
                logger.debug(f"=== Filtered {len(self._hlc.change) - len(filtered)} connectedTo relations")
            self._hlc.change = filtered
            post_process_high_level_change(self._hlc)
            self.push(self._hlc)

            # Notify listeners in ProjectManger of this change
            #logger.debug("undo.py stop recording: self._hlc:", _hlc=self._hlc)
            #logger.debug("undo.py stop recording: self.top:", top=self.top)
            if self.change_handler and call_change_handler:
                logger.debug("Propagating changes to change handler")
                self.change_handler(self.top, self.change_context)

            self._hlc = None
        self._recording = False
        self.change_context.source = ChangeSource.INTERNAL  # reset to default
        if self.recording_lock.locked():
            self.recording_lock.release()
        else:
            logger.warning("Recording lock was already released when stopping recording")

    def add_undo_step(self, label=None):
        """
        TODO: Is this used? If so, what for?
        Ewoud: This (can be) used when a large action is taken and you want to split it up in several undo steps
        e.g. an single user action that can be split up: load geometries, get ETM data for these geometries and calculate KPIs
        """
        if self._hlc is not None:
            self._combine_multiple_changes = False
            self.push(self._hlc)
            self._combine_multiple_changes = True
        self._hlc = ep.HighLevelChange(label=label, changedAt=datetime.now(timezone.utc))

    def push(self, abstract_change: ep.AbstractChange):
        """
        Pushes a high level change or detailed change to the stack. If the stack is full, the oldest command is removed.

        If _combineCommands is True, the commands are added to the high_level_change. The hlc is added to the stack when
        stop_recording() is called. This is used to combine multiple detailed changes into one high level change.
        """

        if not self._recording:
            logger.debug("Undo-redo: Ignoring change NOT RECORDING", abstract_change=abstract_change)
            return

        if self._combine_multiple_changes:
            # the connectedTo relation between ports will be only recorded once, as undoing 2x this 'Add' command
            # gives problems
            # if len(abstract_change) == 1 and len(self._hlc) > 0:
            #     if abstract_change[-1].feature.name == 'connectedTo' and self._hlc[-1].feature.name == 'connectedTo' and \
            #             abstract_change[-1].owner == self._hlc[-1].value:  # p1.connectedTo[0] = p2 p1 == owner, value = p2
            #         logger.debug('Ignore 2nd connectedTo', abstract_change)
            #         # todo add check if notifier is same as old
            #         return  # ignore 2nd controlStrategy/energyAsset bi-directional relation
            # elif commands[-1].feature.name == 'controlStrategy' and self._compound[-1].feature.name == 'energyAsset' and \
            #     commands[-1].owner == self._compound[-1].value:
            #     logger.debug('Ignore ControlStrategy bi-directional relation')
            # only adding multiple commands to the compound
            #logger.debug("Adding change {} to HighLevelChange '{}'".format(abstract_change, self._hlc.label))
            self._hlc.change.append(abstract_change)
            return

        if len(self.stack) > self.stack_index:
            while len(self.stack) > self.stack_index + 1:
                pop = self.stack.pop()  # remove changes after the stack index, because they are obsolete now
                logger.debug(f"Popped {pop} from the stack, as it is obsolete")

        index = self.stack_index + 1
        self.stack.insert(index, abstract_change)
        # self.stack[index] = abstract_change
        self.stack_index = min(index, len(self.stack) - 1)
        self.last_changed = datetime.now(timezone.utc)
        if isinstance(abstract_change, ep.HighLevelChange):
            logger.debug(f"Pushed {abstract_change.label} to the stack")
        else:
            logger.debug(f"Pushed {abstract_change} to the stack")

        # make sure the stack length is not larger than its max length
        if self.max_stack_length > 0:
            while len(self.stack) > self.max_stack_length and len(self.stack) > 1:
                self.stack.pop(0)
                self.stack_index = self.stack_index - 1

    def can_redo(self):
        return self.next_top is not None

    def redo(self):
        if self._combine_multiple_changes is True:
            logger.debug("Cannot redo while recording combined commands")
            return

        # self.next_top.redo()
        if self.can_redo():
            logger.debug("Redo")  #, next_top=self.next_top)
            with self.pause_recording():
                if isinstance(self.next_top, ep.HighLevelChange):
                    for change in self.next_top.change:
                        applyChange(change, self.resource)
                else:
                    applyChange(self.next_top, self.resource)
                self.last_changed = datetime.now(timezone.utc)
            self.stack_index += 1
        else:
            logger.debug("Cannot Redo")

    def can_undo(self):
        return self.top is not None and len(self) > 0

    def undo(self):
        if self._combine_multiple_changes is True:
            logger.debug("Cannot undo while recording combined commands")
            return

        # Suppress generated notification for undo
        with self.pause_recording():
            abstract_change = self.top
            self.last_changed = datetime.now(timezone.utc)
            logger.debug("Undo", abstract_change=abstract_change.label
                if isinstance(abstract_change, ep.HighLevelChange) else abstract_change)
            # if self.top.can_undo:
            if self.can_undo():
                # self.top.undo()
                if isinstance(self.top, ep.HighLevelChange):
                    for change in reversed(self.top.change):
                        undoChange(change, self.resource)
                else:
                    undoChange(self.top, self.resource)
                self.stack_index -= 1
            else:
                logger.debug("Cannot undo")

    def __len__(self):
        return len(self.stack)

    def update_label(self, new_label: str) -> None:
        if self._hlc:
            self._hlc.label = new_label

    def __repr__(self):
        #changes = "\n".join([f"- {s}" for s in self.stack[:5]])
        return f"<Stack len={len(self)}, index={self.stack_index}>"


def post_process_high_level_change(high_level_change: HighLevelChange):
    """
    This function filters out possible double connectedTo relations in the list of subchanges
    *and* the list of xrefs. These might be double because when deepcopying xrefs are also stored, but the notification
    system might also emmited them already.
    Parameters
    ----------
    high_level_change - the High Level change to postprocess

    Returns nothing, it updates in place
    -------

    """
    check_list = []
    for change in high_level_change.change:
        if change.feature == 'connectedTo':
            check_list.append(change)
        for xref_change in change.objectValue_xrefs:
            if xref_change.feature == 'connectedTo':
                check_list.append(xref_change)
    filtered, doubles = filterDoubleConnectedTo(check_list)
    if len(doubles) > 0:
        logger.debug(f"Filter doubles: removed {doubles}")
    for change in doubles:
        change.delete()  # this works because of ecore! :-)


def convertNotificationToChange(stack: UndoRedoCommandStack, notification: Notification):
    """
    Handles a notification from the pyEcore framework and creates a change for the UndoRedoCommandStack.

    :param stack: the UndoRedoCommandStack
    :param notification: the notification to handle

    :return: None
    """
    if notification.notifier.eResource is None:  # if the object has not been added to a resource, ignore it.
        logger.debug("=== convertNotificationToChange ====== !!! No eResource for", notification=notification)
        return
    if not stack.is_recording():  # ignore all notifications when not recording
        # logger.debug('Ignoring ', notification)
        return

    if notification.old is None and notification.new is None:
        # logger.debug('\ -- Ignoring (change=None)', notification)
        return

    if (
        (notification.kind == Kind.SET or notification.kind == Kind.UNSET)
        and isinstance(notification.feature, EReference)
        and notification.feature.eOpposite
        and notification.feature.eOpposite.containment
    ):
        # bi-directional references generate 2 notifications, we can ignore the opposite that is not a containment relation
        # SET and UNSET operations (e.g. asset.area and port.energyasset)
        # logger.debug("  \ -- Ignoring opposite setters for", f.name)
        return

    change = None
    feature_name = notification.feature.name
    value = notification.new
    previous_value = notification.old
    value_x_refs = []
    prev_value_x_refs = []

    if isinstance(value, EObject) or isinstance(previous_value, EObject):
        # disable handling of events during deepcopy() in code below
        with stack.pause_recording():
            try:
                value, value_x_refs = deepcopy_eobject_change(notification.new) if notification.new else (None, [])
                previous_value, prev_value_x_refs = (
                    deepcopy_eobject_change(notification.old) if notification.old else (None, [])
                )
            except KeyError:
                # object already removed from tree, ignore
                logger.debug("\\ object already removed from tree, ignore...")
                return

    # logger.debug(
    #     f"=== convertNotificationToChange ====== len(stack): {len(stack.stack)}, {notification} ============================="
    # )
    if notification.kind == Kind.SET or notification.kind == Kind.UNSET:
        # f: EStructuralFeature = notification.feature
        # if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
        #     # bi-directional references generate 2 notifications, we can ignore the opposite
        #     logger.debug("  \ -- Ignoring opposite setters for", f.name)
        #     return
        owner_fragment = notification.notifier.eURIFragment()
        if isinstance(notification.feature, EReference):
            if notification.feature.containment:
                if isinstance(previous_value, EObject):
                    change = ep.Set(
                        ownerFragment=owner_fragment,
                        feature=feature_name,
                        objectValue=value,
                        previousObjectValue=previous_value,
                    )
                else:
                    change = ep.Set(
                        ownerFragment=owner_fragment,
                        feature=feature_name,
                        objectValue=value,
                        previousValue=previous_value,
                    )
            else:
                previous_value = notification.old.eURIFragment() if notification.old else None
                change = ep.Set(
                    ownerFragment=owner_fragment,
                    feature=feature_name,
                    objectFragment=notification.new.eURIFragment() if notification.kind == Kind.SET else None,
                    previousValue=previous_value,
                )
        else:  # EAttribute
            previous_value = None
            if notification.new is None:
                string_value = ""
            else:
                string_value = notification.feature.eType.to_string(notification.new)
            if notification.old:
                previous_value = notification.feature.eType.to_string(notification.old)
            change = ep.Set(
                ownerFragment=owner_fragment,
                feature=feature_name,
                stringValue=string_value,
                previousValue=previous_value,
            )

    elif notification.kind == Kind.ADD:  # add an item to a collection
        owner_fragment = notification.notifier.eURIFragment()
        # only .new is available
        if notification.feature.containment:
            change = ep.Add(
                ownerFragment=owner_fragment,
                feature=feature_name,
                objectValue=value,
                objectFragment=notification.new.eURIFragment(),
            )
            # change.objectValue_xrefs.extend(value_x_refs)
        else:
            # this is a cross-reference
            if notification.new.eResource is None:
                logger.debug("Add: eResource is none, delay resolution of fragment for ", notification=notification)
                if notification not in stack.post_process_list:
                    stack.post_process_list.append(notification)
            else:
                change = ep.Add(
                    ownerFragment=owner_fragment, feature=feature_name, objectFragment=notification.new.eURIFragment()
                )
                value_x_refs = []  # don't need to include cross references here as this is the cross reference

    elif notification.kind == Kind.REMOVE:  # remove eobject from collection, only .old is available as previous value
        f = notification.feature
        if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
            # bi-directional references generate 2 notifications, we can ignore the opposite
            logger.debug("  \\ -- f.eOpposite and f.eOposite.containment", feature_name=f.name)
        owner_fragment = notification.notifier.eURIFragment()
        old_uri_fragment = notification.old.eURIFragment()
        try:
            resolved = notification.notifier.eResource.resolve(old_uri_fragment)
        except AttributeError:
            logger.debug("Resolving of old URI fragment fails, Ignoring for now:", notification=notification)
            return
        if not isinstance(resolved, f.eType):
            # TODO: the way pyEcore deletes objects with references in non-deterministic, because it uses a unordered set()
            # for storing the list of references of an object. That's why the order of notification differs among different
            # runs. Our code should deal with it (as the order shouldn't matter) but when pyEcore unlinks an object from
            # the tree, cross-references (such as connectedTo and carrier) do not have eContainer() information anymore
            # and eURIFragment() will return "/" in that case, which is wrong.
            # The above check removes these faulty cross-reference notifications, as they are (hopefully) captered by the
            # deepcopy_eobject_change in the x-refs.
            #
            # @see https://365tno.sharepoint.com/:p:/r/teams/T94910/TeamDocuments/Team/Design/ProjectManager/Non-determinisme%20in%20notification%20generation%20of%20PyEcore.pptx?d=w9fc13e3db82246119c7b02b7ed3b3513&csf=1&web=1&e=R07dvF
            # @see undo_pyecore_patch.py to make sure notifications are send before the actual removal.
            #
            # check if old_uri_fragment is valid, as sometimes an event comes too late and
            # old uri_fragment is "/" instead of the correct one.
            # logger.debug(f"!!!!!!!!!!!!!!! missing container information, should be handled previously..., {f.eType.eClass} <-> {notification.notifier.eResource.resolve(old_uri_fragment).eClass}")
            return
        # else:
        #     pass

        if notification.feature.containment:
            if notification.old is not None:  # delete actual value, so we need to store this value and xrefs.
                change = ep.Delete(
                    ownerFragment=owner_fragment,
                    feature=feature_name,
                    objectValue=previous_value,
                    objectFragment=old_uri_fragment,
                )
        else:  # remove a reference
            change = ep.Remove(ownerFragment=owner_fragment, feature=feature_name, objectFragment=old_uri_fragment)
            # TODO check if this is true:
            # if we remove a reference, we don't need to do a deepcopy and
            # we don't need to add x-refs
            prev_value_x_refs = []
            value_x_refs = []

    elif (
        notification.kind == Kind.REMOVE_MANY
    ):  # remove eobject from collection, only .old is available as previous value
        f = notification.feature
        if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
            # bi-directional references generate 2 notifications, we can ignore the opposite
            logger.debug("  \\ -- f.eOpposite and f.eOposite.containment", feature_name=f.name)
        owner_fragment = notification.notifier.eURIFragment()
        if notification.feature.containment:
            if notification.old is not None:  # delete actual value, so we need to store this value and xrefs.
                for obj in notification.old:
                    copy, xrefs = deepcopy_eobject_change(value)
                    change = ep.Delete(
                        ownerFragment=owner_fragment,
                        feature=feature_name,
                        objectValue=copy,
                        objectFragment=obj.eURIFragment(),
                    )
                    filtered,_ = filterDoubleConnectedTo(xrefs)
                    change.previousValue_xrefs.extend(filtered)
                    # manually add multiple changes to the stack
                    stack.push(change)
                    change = None
        else:  # remove a reference
            for obj in notification.old:
                change = ep.Remove(
                    ownerFragment=owner_fragment, feature=feature_name, objectFragment=obj.eURIFragment()
                )
                stack.push(change)
                change = None
    else:
        logger.warning("Not converted notification: ", notification=notification)

    # add possible xrefs from a deepcopy
    if change:
        if len(value_x_refs) > 0:
            total_list = []
            total_list.extend(change.objectValue_xrefs)
            total_list.extend(value_x_refs)
            cleaned_change_list, _ = filterDoubleConnectedTo(total_list)
            # logger.debug(
            #     f"------ Adding cross-references of size {len(cleaned_change_list)}, "
            #     f"(removed {len(total_list) - len(cleaned_change_list)} duplicates)"
            # )
            change.objectValue_xrefs.clear()
            change.objectValue_xrefs.extend(cleaned_change_list)
        if len(prev_value_x_refs) > 0:
            cleaned_change_list, _ = filterDoubleConnectedTo(prev_value_x_refs)
            # logger.debug(
            #     f"------ Adding cross-references of size {len(cleaned_change_list)}, "
            #     f"(removed {len(prev_value_x_refs) - len(cleaned_change_list)} duplicates)"
            # )
            change.previousValue_xrefs.extend(cleaned_change_list)
        stack.push(change)

    if len(stack.post_process_list) > 0:
        if notification not in stack.post_process_list:
            for n in list(stack.post_process_list):
                convertNotificationToChange(stack, n)
                stack.post_process_list.remove(n)
            if len(stack.post_process_list) == 0:
                logger.debug("convertNotificationToChange() ****** Emptied post_proces_list")

    # logger.debug("**** exit convertNotificationToChange ****")


def updateResourceUUIDdict(notification: Notification):
    """
    Updates the UUID dict of the resource beloning to this notification
    Parameters
    ----------
    notification
    """
    f: EStructuralFeature = notification.feature
    value = notification.new
    if notification.kind == Kind.SET:
        if isinstance(f, EAttribute) and f.name == "id":
            owner = notification.notifier
            resource: XMLResource = owner.eResource
            resource.uuid_dict[value] = owner
            #logger.debug(f"Updating UUID dict for {owner}.id={value}")
    elif notification.kind == Kind.ADD:
        if isinstance(f, EReference) and f.containment and isinstance(value, EObject):
            # whole object is added: iterate though contents and add all ids
            if hasattr(value, "id"):
                value.eResource.uuid_dict[value.id] = value
                #logger.debug(f"|Updating UUID dict for {value}.id={value.id}")
            for obj in value.eAllContents():
                if hasattr(obj, "id"):
                    obj.eResource.uuid_dict[obj.id] = obj
                    #logger.debug(f"|-Updating UUID dict for {obj}.id={obj.id}")

    elif notification.kind == Kind.UNSET:
        if notification.old is not None and isinstance(f, EAttribute) and f.name == "id":
            owner = notification.notifier
            resource: XMLResource = owner.eResource
            save_delete_dict_key_with_warning(resource.uuid_dict, notification.old.id)
            #logger.debug(f"Updating UUID dict, remove {owner}.id={notification.old.id}")

    elif notification.kind == Kind.REMOVE:
        prev_values = notification.old
        if isinstance(f, EReference) and f.containment and isinstance(prev_values, EObject):
            # whole object is removed: iterate though contents and remove all ids
            resource = prev_values.eResource
            if not resource:
                resource = notification.notifier.eResource
            if not resource:
                logger.warning(f"Can't update uuid_dict as no resource available: {notification}")
                return
            if hasattr(prev_values, "id") and prev_values.id is not None:
                save_delete_dict_key_with_warning(resource.uuid_dict, prev_values.id)
                #logger.debug(f"|Updating UUID dict, remove {prev_values}.id={prev_values.id}")
            for obj in prev_values.eAllContents():
                if hasattr(obj, "id") and obj.id is not None:
                    save_delete_dict_key_with_warning(resource.uuid_dict, obj.id)
                    #logger.debug(f"|-Updating UUID dict, remove {obj}.id={obj.id}")
    elif notification.kind == Kind.REMOVE_MANY:
        prev_values = notification.old
        if isinstance(f, EReference) and f.containment and isinstance(prev_values, list) and len(prev_values) > 0:
            # whole object is removed: iterate though contents and remove all ids
            resource = prev_values[0].eResource
            if not resource:
                resource = notification.notifier.eResource
            if not resource:
                logger.warning(f"Can't update uuid_dict as no resource available: {notification}")
                return
            for prev_value in prev_values:
                if hasattr(prev_value, "id") and prev_value.id is not None:
                    save_delete_dict_key_with_warning(resource.uuid_dict, prev_value.id)
                    #logger.debug(f"|Updating UUID dict, remove_many {prev_value}.id={prev_value.id}")
                for obj in prev_value.eAllContents():
                    if hasattr(obj, "id") and obj.id is not None:
                        save_delete_dict_key_with_warning(resource.uuid_dict, obj.id)
                        #logger.debug(f"|\\-Updating UUID dict, remove_many {obj}.id={obj.id}")
    else:
        logger.warning(f"Warning: updateResourceUUIDdict() unsupported notification {notification.kind}")


def save_delete_dict_key_with_warning(d: dict, key: Any):
    try:
        del d[key]
    except NameError:
        logger.warn(f"IGNORE: AutoUpdateUUID work in progress: updateResourceUUIDdict(): can't delete {key} from {d}")
    except KeyError:
        logger.warn(f"IGNORE: AutoUpdateUUID work in progress: updateResourceUUIDdict(): can't delete {key} from {d}")


# observe every change in the model, but this works for *all* EObjects in memory... so this is not very handy.
# so this is currently not used, as pyEcore has been changed to emit notifications at the resource level
# def monitor_esdl_changes(command_stack: UndoRedoCommandStack):
#     observer = EObserver(notifyChanged=lambda x: handleNotification(command_stack, x))
#     old_init = EObject.__init__
#
#     def new_init(self, **kwargs):
#         observer.observe(self)
#         old_init(self, **kwargs)
#
#     setattr(EObject, '__init__', new_init)


class ResourceObserver(EObserver):
    def __init__(self, changes_stack: UndoRedoCommandStack):
        super().__init__()
        self.stack = changes_stack

    def notifyChanged(self, notification):
        convertNotificationToChange(self.stack, notification)
        updateResourceUUIDdict(notification)


@dataclass
class Tracker:
    resource: Resource
    stack: UndoRedoCommandStack
    observer: ResourceObserver

    def __repr__(self):
        return f"Tracker(resource={self.resource.uri.plain}, stack={self.stack}, observer={self.observer})"


class ChangeTracker:
    def __init__(self, change_handler=None):
        """

        Parameters
        ----------
        change_handler - a function that is called when notifications are
        generated when changing the monitored resource (by using new_tracker())

        """
        self.trackers = []
        self.change_handler = change_handler

    def new_tracker(self, variant: ep.Variant, eobj: EObject = None, resource: Resource = None) -> Tracker:
        """
        Creates a new UndoRedoCommandStack and ResourceObserver and stores
        changes in the variant supplied.

        Either a EObject or a resource should be supplied as object to be monitored
        for changes.

        Parameters
        ----------
        variant - the variant in which all changes are stored
        eobj - the EObject that is being monitored for changes
        resource - the Resource that is monitored

        Returns
        -------
        the change tracker data structure that is created for this.

        """
        logger.info("Creating new ChangeTracker for variant ", variant_name=variant.name, resource=resource, eobj=eobj)
        if eobj:
            resource = eobj.eResource
        elif resource:
            pass
        else:
            raise Exception("Can't create new tracker: Resource is None")

        logger.debug("undo.py: Tracking changes for resource with URI {}".format(resource.uri.plain))
        stack = UndoRedoCommandStack(variant=variant, resource=resource, change_handler=self.change_handler)
        ro = ResourceObserver(changes_stack=stack)
        ro.observe(resource)
        tracker: Tracker = Tracker(resource, stack, ro)
        self.trackers.append(tracker)
        return tracker

    def get_tracker(self, eobj: EObject = None, resource: Resource = None) -> Optional[Tracker]:
        """
        Returns the CommandStack for the resource of eobj or the resource given by the resource parameter
        One of the parameters is required.

        :eobj: an EObject (any class in the ESDL)
        :resource: the resource used to store the ESDL
        """
        if resource is None and eobj is not None:
            resource = eobj.eResource
        if resource is None:
            raise ValueError("Can't find stack for the resource of {} (of type {})".format(eobj, eobj.eClass.name))
        for t in self.trackers:
            if t.resource == resource:
                return t
        return None

    def get_tracker_stack(self, eobj: EObject = None, resource: Resource = None) -> UndoRedoCommandStack:
        """
        Returns the CommandStack for the resource of eobj or the resource given by the resource parameter
        One of the parameters is required.

        :eobj: an EObject (any class in the ESDL)
        :resource: the resource used to store the ESDL
        """
        tracker = self.get_tracker(eobj, resource)
        if tracker:
            return tracker.stack
        raise ValueError("Can't find stack belonging to resource {} and object {}".format(resource.uri.plain, eobj))

    def delete(self, stack:UndoRedoCommandStack = None, resource:XMLResource = None, tracker:Tracker = None):
        """
        Deletes this tracker and removes the listening of changes of this resource
        Use or `stack` or `resource` or `tracker` as parameter
        """
        if tracker:
            logger.debug(f"Removing tracker {tracker}")
            self.trackers.remove(tracker)
            return

        for t in list(self.trackers):
            t: Tracker = t
            if (stack is not None and t.stack is stack) or (resource is not None and t.resource is resource):
                logger.debug(f"Removing tracker {t}")
                del t.stack
                t.resource.listeners.remove(t.observer)
                del t.observer
                del t.resource # needed?
                self.trackers.remove(t)


    def reset(self):
        """
        Resets the Tracker and removes everything.
        -------
        """
        for t in list(self.trackers):
            t: Tracker
            # make sure all references to stack items are removed.
            t.stack.stack.clear()
            t.resource = None
            t.observer = None
        self.trackers.clear()
