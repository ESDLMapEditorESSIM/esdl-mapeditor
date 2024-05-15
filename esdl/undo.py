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
from collections import UserList
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Any

from pyecore.notification import EObserver, Notification, Kind
from pyecore.ecore import EObject, EStructuralFeature, EReference, EAttribute, EClass
from pyecore.resources import Resource
from pyecore.commands import Command, AbstractCommand

from dataclasses import dataclass

from esdl.resources.xmlresource import XMLResource
from esdl.undo_pyecore_extensions import deepcopy_with_xrefs, Set, Add, Delete, Remove
from esdl.undo_pyecore_patch import patch_notification_system
from esdlproject.actions import LabelledAction
import src.log as log

patch_notification_system()  # patch pyecores notification system, so notification are always send

logger = log.get_logger(__name__)


class UndoRedoCommandStack:
    """
    Creates a undo and redo command stack for ESDL documents
    Default maximum length of the stack is 100 (Labelled)Actions or Commands
    Use -1 to create an unlimited stack.
    change_handler is a call back function that receives a LabeledAction when a new change is generated
    """
    def __init__(self, max_stack_length: int = 100, change_handler=None):
        # The actual changes. Right now it is a list of pyEcore commands.
        self.stack = []
        # The location in the stack where the last currently active change is stored.
        self.stack_index = -1
        self._recording = False
        self._combine_commands = True
        self._compound = None
        self.max_stack_length = max_stack_length
        self.last_changed: datetime = datetime.min
        self.change_handler = change_handler

    @property
    def top(self) -> LabelledAction | Command | None:
        """
        Returns the element at the top of the stack. Returns None if the stack is empty or the stack index is out of
        bounds.
        """
        if self.stack_index < 0:
            return None
        try:
            return self.stack[self.stack_index]
        except IndexError:
            return None

    @property
    def next_top(self) -> LabelledAction | Command | None:
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

    def start_recording(self, combine_commands: bool = True, label: str = None):
        """
        Starts recording of changes in the loaded ESDL model

        :param bool combine_commands: collect all actions into one single LabelledAction (default = True)
        :param label: name of the label of the action that is recorded.
        """
        print(f"=== start recording: {label} =====================================")
        self._recording = True
        self._combine_commands = combine_commands
        if combine_commands:
            # TODO: Replace by HighLevelChange. However we do need the variant then.
            self._compound = LabelledAction(label=label)
            # self._compound = HighLevelChange(label=label)

    def is_recording(self):
        return self._recording

    @contextmanager
    def pause_recording(self):
        """
        Temporarily pause recording of changes.
        """
        self._recording = False
        try:
            yield
        finally:
            self._recording = True

    def stop_recording(self, call_change_handler: bool = True):
        """
        Stops recording of changes in a resource and stops putting them on the stack.
        Parameters
        ----------
        call_change_handler if True the change_handler configured when creating this Stack
                            will be called. This is set to False if you dont want to react
                            on changes, e.g. when replaying changes to a resource.
        """
        print("=== stop recording =====================================")
        self._combine_commands = False
        if self._compound is not None and len(self._compound) > 0:
            self.push(self._compound)

            # Notify listeners in ProjectManger of this change
            print('undo.py stop recording: self._compound:', self._compound)
            print('undo.py stop recording: self.top:', self.top)
            if self.change_handler and call_change_handler:
                print("Propagating changes to change handler")
                self.change_handler(self.top)

            self._compound = None
        self._recording = False

    def add_undo_step(self, label=None):
        """
        TODO: Is this used? If so, what for?
        """
        if self._compound is not None:
            self._combine_commands = False
            self.push(self._compound)
            self._combine_commands = True
        self._compound = LabelledAction(label)

    def push(self, *commands):
        """
        Pushes a command or a list of commands to the stack. If the stack is full, the oldest command is removed.

        If _combineCommands is True, the commands are added to the compound. The compound is added to the stack when
        stop_recording() is called. This is used to combine multiple commands into one action.
        """
        if self._combine_commands:
            # the connectedTo relation between ports will be only recorded once, as undoing 2x this 'Add' command
            # gives problems
            if len(commands) == 1 and len(self._compound) > 0:
                if commands[-1].feature.name == 'connectedTo' and self._compound[-1].feature.name == 'connectedTo' and \
                        commands[-1].owner == self._compound[-1].value:  # p1.connectedTo[0] = p2 p1 == owner, value = p2
                    print('Ignore 2nd connectedTo', commands)
                    # todo add check if notifier is same as old
                    return  # ignore 2nd controlStrategy/energyAsset bi-directional relation
                # elif commands[-1].feature.name == 'controlStrategy' and self._compound[-1].feature.name == 'energyAsset' and \
                #     commands[-1].owner == self._compound[-1].value:
                #     print('Ignore ControlStrategy bi-directional relation')
            # only adding multiple commands to the compound
            print("Adding combined command {} to action '{}'".format(commands, self._compound.label))
            self._compound.extend(commands)
            return
        if not self._recording:
            print('Undo-redo: Ignoring command NOT RECORDING', commands)
            return

        for command in commands:
            if not isinstance(command, LabelledAction):
                # Check if the command is executed. We don't check this for LabelledAction, I don't know why.
                if command.can_execute:
                    # Set _executed to True to activate correct behaviour in PyEcore code, such that undo works
                    command._executed = True
                else:
                    raise ValueError('Cannot execute command {}'.format(command))

            index = self.stack_index + 1
            self.stack[index:index] = [command]
            self.stack_index = index
            self.last_changed = datetime.now()
            print(f"Pushed {command} to the stack")

        # make sure the stack length is not larger than its max length
        if self.max_stack_length > 0:
            while len(self.stack) > self.max_stack_length and len(self.stack) > 1:
                self.stack.pop(0)
                self.stack_index = self.stack_index - 1

    def can_redo(self):
        return self.next_top is not None

    def redo(self):
        if self._combine_commands is True:
            print("Cannot redo while recording combined commands")
            return

        print('Redo', self.next_top)
        if self.next_top is None:
            return

        # suppress generated notifications for redo
        with self.pause_recording():
            # TODO: following code is not necessary with updateResourceUUIDdict() now in place
            # check if that is true
            for command in self.next_top:
                c: AbstractCommand = command
                if isinstance(c, Delete) or isinstance(c, Remove):
                    value = c.value
                    if isinstance(c, Delete):
                        value = c.owner
                    if c.feature.name != "connectedTo" and isinstance(value, EObject) and hasattr(value, 'id') and value.id is not None:
                        resource = value.eResource
                        # do removing from uuid_dict before removing it from the eResource
                        if value.id in resource.uuid_dict:
                            print("Redo: remove from to uuid_dict", value.id, value)
                            try:
                                del resource.uuid_dict[value.id]
                            except KeyError:
                                pass

            self.next_top.redo()
            self.stack_index += 1

    def can_undo(self):
        return self.top is not None

    def undo(self):
        if self._combine_commands is True:
            print("Cannot undo while recording combined commands")
            return

        # Suppress generated notification for undo
        with self.pause_recording():
            action = self.top
            self.last_changed = datetime.now()
            print('Undo', action)
            if self.top.can_undo:
                self.top.undo()
                self.stack_index -= 1

            # TODO: following code is not necessary with updateResourceUUIDdict() now in place
            # check if that is true
            for command in action:
                c: AbstractCommand = command
                if isinstance(c, Delete) or isinstance(c, Remove):
                    value = c.value
                    if isinstance(c, Delete):
                        value = c.owner
                    # ignore connected to, since Ports are handled, so id's are already in uuid_dict
                    if c.feature.name != "connectedTo" and isinstance(value, EObject) and hasattr(value, 'id') and value.id is not None:
                        resource = value.eResource
                        print("Undo: adding to uuid_dict", value.id, value)
                        resource.uuid_dict[value.id] = value

    def update_label(self, new_label: str) -> None:
        if self._compound:
            self._compound.label = new_label


def handleNotification(stack: UndoRedoCommandStack, notification: Notification):
    """
    Handles a notification from the pyEcore framework and creates a command for the UndoRedoCommandStack.

    :param stack: the UndoRedoCommandStack
    :param notification: the notification to handle

    :return: None
    """
    if notification.notifier.eResource is None:  # if the object has not been added to a resource, ignore it.
        print('=== handleNotification ====== !!! No eResource for', notification)
        return
    if not stack.is_recording():  # ignore all notifications when not recording
        #print('Ignoring ', notification)
        return
    print(f"=== handleNotification ====== len(stack): {len(stack.stack)}, {notification} =============================")
    if notification.old is None and notification.new is None:
        print('\ -- Ignoring (change=None)', notification)
        return
    print('Handling', notification)
    if notification.kind == Kind.SET:  # EValue.set()
        f: EStructuralFeature = notification.feature
        if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
            print("  \ -- Ignoring opposite setters for", f.name)
            return
        value = notification.new
        previous_value = notification.old
        if isinstance(value, EObject):
            # disable handling of events during deepcopy() in code below
            with stack.pause_recording():
                value = notification.new.deepcopy() if notification.new else None
                previous_value = notification.old.deepcopy() if notification.old else None
        setNotification = Set(owner=notification.notifier, feature=notification.feature,
                              value=value)
        setNotification.previous_value = previous_value
        setNotification._executed = True
        if isinstance(f, EReference): # store uri fragment, because we deepcopy, so that info is gone
            setNotification.valueURIFragment = notification.new.eURIFragment()
        stack.push(setNotification)
    elif notification.kind == Kind.UNSET: # remove reference
        if notification.old is not None:
            f: EStructuralFeature = notification.feature
            if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
                print("  \ -- Ignoring opposite unset for ", f.name)
                return
            if isinstance(f, EAttribute) or not f.containment:
                # disable handling of events during deepcopy() in code below
                with stack.pause_recording():
                    value = notification.new.deepcopy() if notification.new else None
                    previous_value = notification.old.deepcopy() if notification.old else None
                unsetNotification = Set(owner=notification.notifier, feature=notification.feature, value=value)
                unsetNotification.previous_value = previous_value
                unsetNotification.can_execute  # calls a property in notification, although it is a function... horrible python
                print("\ -- [(Un)Set], not delete")
            else:
                unsetNotification = Delete(owner=notification.old)
                unsetNotification.feature = notification.feature
                #unsetNotification.references = {notification.feature: notification.old}
                #unsetNotification.previous_value = notification.new
                #unsetNotification.value = notification.old
                unsetNotification.can_execute  # record all changes
                #unsetNotification.ownerURIFragment = notification.old.eURIFragment()
                print("\ -- [Delete] ", "\n \ -- inv_refs:", unsetNotification.inverse_references, "\n \ --refs:", unsetNotification.references)
            unsetNotification._executed = True
            stack.push(unsetNotification)
    elif notification.kind == Kind.ADD: # add an item to a collection
        # make sure we get the current EObject /as is/ to make sure that later on we don't work with an updated
        # version
        with stack.pause_recording():
            #value = notification.new.deepcopy() if notification.new else None
            #previous_value = notification.old.deepcopy() if notification.old else None
            value, xrefs = deepcopy_with_xrefs(notification.new) if notification.new else (None, [])
            previous_value, pref_xrefs = deepcopy_with_xrefs(notification.old) if notification.old else (None, [])
        addNotification = Add(owner=notification.notifier, feature=notification.feature, value=value)
        addNotification.valueURIFragment = notification.new.eURIFragment()
        addNotification.previous_value = previous_value
        addNotification.index = notification.notifier.eGet(notification.feature).index(notification.new)
        addNotification._collection = notification.notifier.eGet(notification.feature)
        addNotification.deepcopy = True
        if notification.new and notification.new.eContainer():
            addNotification.testURIFragment = notification.new.eContainer().eURIFragment() + \
                                              '/@' + notification.new.eContainmentFeature().name + \
                                              '.' + str(addNotification.index)
        else:
            addNotification.testURIFragment = None
        addNotification._executed = True
        stack.push(addNotification)
        for command in xrefs:
            stack.push(command)
    elif notification.kind == Kind.REMOVE: # remove eobject from collection
        if notification.old is not None:
            # disable handling of events during deepcopy() in code below
            with stack.pause_recording():
                #value = notification.old.deepcopy()
                #previous_value = notification.new.deepcopy() if notification.new else None
                value, xrefs = deepcopy_with_xrefs(notification.old) if notification.old else (None, [])
                previous_value, pref_xrefs = deepcopy_with_xrefs(notification.new) if notification.new else (None, [])
            removeNotification = Remove(owner=notification.notifier, feature=notification.feature, value=value, index=None)
            removeNotification.previous_value = previous_value
            removeNotification.deepcopy = True
            #removeNotification.value = notification.old
            if notification.feature.many:
                removeNotification._collection = notification.notifier.eGet(notification.feature)
                print("\ -- [Remove] collection of {} has length {}".format(notification.feature.name, len(removeNotification._collection)))
                try:
                    removeNotification.index = notification.notifier.eGet(notification.feature).index(notification.old)
                    print(" \ -- [Remove] found index in collection ", removeNotification.index)
                except KeyError:
                    removeNotification.index = 0
                # old.eURIFragment() does not work as it is removed from the tree, but in our patching we still have
                # a reference to the container and we can build up this reference manually
                removeNotification.refURIFragment = notification.old.eContainer().eURIFragment() + '/@' + notification.old.eContainmentFeature().name + '.' + str(removeNotification.index)
            else:
                removeNotification.refURIFragment = notification.old.eContainer().eURIFragment() + '/@' + notification.old.eContainmentFeature().name
            removeNotification._executed = True
            try:
                ownerFragment = notification.notifier.eURIFragment()
                removeNotification.ownerFragment = ownerFragment
                stack.push(removeNotification)
                for command in xrefs:
                    stack.push(command)
            except KeyError:
                print("***************************************************** Not adding this remove, as the owner has been removed from the tree already")
                pass #ignore this notification, as owner is not part of the tree anymore


            #removeNotification.refURIFragment = notification.old.eURIFragment()
    # elif notification.kind == Kind.REMOVE_MANY: # delete containment relation / object
    #     # check if this works at all...
    #     deleteNotification = Delete(owner=notification.notifier)
    #     deleteNotification._executed = True
    #     stack.push(deleteNotification)
    else:
        print("Not handled notification: ", notification)
    print("**** exit handleNotification ****")


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
        if isinstance(f, EAttribute) and f.iD is True and f.name == 'id':
            owner = notification.notifier
            resource: XMLResource = owner.eResource
            resource.uuid_dict[value] = owner
            print(f"Updating UUID dict for {owner}.id={value}")
    elif notification.kind == Kind.ADD:
        if isinstance(f, EReference) and f.containment and isinstance(value, EObject):
            # whole object is added: iterate though contents and add all ids
            if hasattr(value, 'id'):
                value.eResource.uuid_dict[value.id] = value
                print(f"|Updating UUID dict for {value}.id={value.id}")
            for obj in value.eAllContents():
                if hasattr(obj, 'id'):
                    obj.eResource.uuid_dict[obj.id] = obj
                    print(f"|-Updating UUID dict for {obj}.id={obj.id}")

    elif notification.kind == Kind.UNSET:
        if notification.old is not None and isinstance(f, EAttribute) and f.iD is True and f.name == 'id':
            owner = notification.notifier
            resource:XMLResource = owner.eResource
            save_delete_dict_key_with_warning(resource.uuid_dict, notification.old.id)
            print(f"Updating UUID dict, remove {owner}.id={notification.old.id}")

    elif notification.kind == Kind.REMOVE:
        prev_value = notification.old
        if isinstance(f, EReference) and f.containment and isinstance(prev_value, EObject):
            # whole object is removed: iterate though contents and remove all ids
            if hasattr(prev_value, 'id'):
                save_delete_dict_key_with_warning(prev_value.eResource.uuid_dict, prev_value.id)
                print(f"|Updating UUID dict, remove {prev_value}.id={prev_value.id}")
            for obj in prev_value.eAllContents():
                if hasattr(obj, 'id'):
                    save_delete_dict_key_with_warning(obj.eResource.uuid_dict, obj.id)
                    print(f"|-Updating UUID dict, remove {obj}.id={obj.id}")
    else:
        print(f"Warning: updateResourceUUIDdict() unsupported notification {notification.kind}")


def save_delete_dict_key_with_warning(d: dict, key: Any):
    try:
        del d[key]
    except NameError:
        logger.warn(f"IGNORE: AutoUpdateUUID work in progress: updateResourceUUIDdict(): can't delete {key} from {d}")


# observe every change in the model, but this works for *all* EObjects in memory... so this is not very handy.
# so this is currently not used, as pyEcore has been changed to emit notifications at the resource level
def monitor_esdl_changes(command_stack: UndoRedoCommandStack):
    observer = EObserver(notifyChanged=lambda x: handleNotification(command_stack, x))
    old_init = EObject.__init__

    def new_init(self, **kwargs):
        observer.observe(self)
        old_init(self, **kwargs)

    setattr(EObject, '__init__', new_init)


class ResourceObserver(EObserver):
    def __init__(self, command_stack: UndoRedoCommandStack):
        self.stack = command_stack

    def notifyChanged(self, notification):
        handleNotification(self.stack, notification)
        updateResourceUUIDdict(notification)


@dataclass
class Tracker:
    resource: Resource
    stack: UndoRedoCommandStack
    observer: ResourceObserver


class ChangeTracker:
    def __init__(self, change_handler = None):
        self.trackers = []
        self.change_handler = change_handler

    def new_tracker(self, eobj: EObject = None, resource: Resource = None) -> Tracker:
        if eobj:
            resource = eobj.eResource
        elif resource:
            pass
        else:
            raise Exception("Can't create new tracker: Resource is None")

        print("undo.py: Tracking changes for resource with URI {}".format(resource.uri.plain))
        stack = UndoRedoCommandStack(change_handler=self.change_handler)
        ro = ResourceObserver(command_stack=stack)
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
            raise Exception("Can't find stack for the resource of {} (of type {})".format(eobj, eobj.eClass.name))
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

    def delete(self, stack):
        """
        Deletes this stack and removes the listening of changes of this resource
        """
        for t in self.trackers:
            t: Tracker = t
            if t.stack is stack:
                del t.stack
                t.resource.listeners.remove(t.observer)
                del t.observer
                #del t.resource # needed?

    def reset(self):
        """
        Resets the Tracker and removes everything.
        -------

        """
        for t in list(self.trackers):
            t:Tracker
            # make sure all references to stack items are removed.
            t.stack.stack.clear()
            t.resource = None
            t.observer = None
        self.trackers.clear()
