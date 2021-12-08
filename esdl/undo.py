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
from typing import Optional, TypedDict

from pyecore.notification import EObserver, Notification, Kind
from pyecore.ecore import EObject, EStructuralFeature, EReference, EAttribute
from pyecore.resources import Resource
from pyecore.commands import Set, Add, Delete, Remove, CommandStack, Command, AbstractCommand

from dataclasses import dataclass
from esdl.undo_pyecore_patch import patch_notification_system


patch_notification_system() # patch pyecores notification system, so notification are always send


class UndoRedoCommandDict(TypedDict):
    """
    A part of a stack entry.
    """
    id: Optional[str]
    name: Optional[str]
    type: str


class UndoRedoStackEntryDict(TypedDict):
    """
    An entry in the undo redo stack.
    """
    label: str
    type: Optional[str]
    commands: list[UndoRedoCommandDict]


class UndoRedoSerializedStack(TypedDict):
    """
    An entry in the undo redo stack.
    """
    stack_index: int
    stack: list[UndoRedoStackEntryDict]


class LabelledAction(Command, UserList):
    """
     Extend the compound class with a label field
     """
    def __init__(self, label=None, *commands):
        self.label = label
        super().__init__(commands)

    @property
    def can_execute(self):
        return all(command.can_execute for command in self)

    def execute(self):
        for command in self:
            command.execute()

    @property
    def can_undo(self):
        return all(command.can_undo for command in self)

    def undo(self):
        for command in reversed(self):
            print("undo action:", command)
            command.undo()

    def redo(self):
        for command in self:
            command.redo()

    def unwrap(self):
        return self[0] if len(self) == 1 else self

    def __repr__(self):
        return '{}(label={}: {})'.format(self.__class__.__name__, self.label, self.data)


class UndoRedoCommandStack(CommandStack):
    """
    Creates a undo and redo command stack for ESDL documents
    Default maximum length of the stack is 100 (Labelled)Actions or Commands
    Use -1 to create an unlimited stack.
    """
    def __init__(self, max_stack_length: int = 100):
        self._recording = False
        self._combineCommands = True
        self.compound = None
        self.max_stack_length = max_stack_length
        super().__init__()

    def start_recording(self, combineCommands: bool = True, label: str = None):
        """
        Starts recording of changes in the loaded ESDL model

        :param bool combineCommands: collect all actions into one single LabelledAction (default = True)
        :param label: name of the label of the action that is recorded.
        """
        self._recording = True
        self._combineCommands = combineCommands
        if combineCommands:
            self.compound = LabelledAction(label=label)

    def is_recording(self):
        return self._recording

    def stop_recording(self):
        self._combineCommands = False
        if self.compound and len(self.compound) > 0:
            self.append(self.compound)
            self.compound = None
        self._recording = False

    def add_undo_step(self, label=None):
        if self.compound is not None:
            self._combineCommands = False
            self.append(self.compound)
            self._combineCommands = True
        self.compound = LabelledAction(label)

    def append(self, *commands):
        if self._combineCommands:
            # the connectedTo relation between ports will be only recorded once, as undoing 2x this 'Add' command
            # gives problems
            if len(commands) == 1 and len(self.compound) > 0 and \
                    commands[-1].feature.name == 'connectedTo' and self.compound[-1].feature.name == 'connectedTo' and \
                    commands[-1].owner == self.compound[-1].value: # p1.connectedTo[0] = p2 p1 == owner, value = p2
                print('Ignore 2nd connectedTo', commands)
                # todo add check if notifier is same as old
                return # ignore 2nd connected to relation
            # only adding multiple commands to the compound
            print("Adding combined command {} to action '{}'".format(commands, self.compound.label))
            self.compound.extend(commands)
            return
        if not self._recording:
            print('Undo-redo: Ignoring command NOT RECORDING', commands)
            return

        for command in commands:
            if isinstance(command, LabelledAction):
                self.top = command
                print("Appended {} to the stack".format(command))

            else:
                if command.can_execute:
                    # command.execute()
                    command._executed = True
                    self.top = command
                    print("Appended {} to the stack".format(command))
                else:
                    raise ValueError('Cannot execute command {}'.format(command))

        # make sure the stack length is not larger than its max length
        if self.max_stack_length > 0:
            while len(self.stack) > self.max_stack_length and len(self.stack) > 1:
                self.stack.pop(0)
                self.stack_index = self.stack_index - 1

    def can_redo(self):
        return len(self.stack) - self.stack_index > 1

    def redo(self):
        if self._combineCommands is True:
            print("Cannot redo while recording combined commands")
            return
        self._recording = False  # suppress generated notifications for redo
        action = self.peek_next_top
        print('Undo', self.peek_next_top)
        for command in action:
            c: AbstractCommand = command
            if isinstance(c, Delete) or isinstance(c, Remove):
                value = c.value
                if isinstance(c, Delete): value = c.owner
                if c.feature.name != "connectedTo" and isinstance(value, EObject) and hasattr(value, 'id') and value.id is not None:
                    resource = value.eResource
                    # do removing from uuid_dict before removing it from the eResource
                    print("Redo: remove from to uuid_dict", value.id, value)
                    if value.id in resource.uuid_dict:
                        del resource.uuid_dict[value.id]

        super().redo()
        self._recording = True

    def can_undo(self):
        return len(self.stack) > 0 and self.stack_index >= 0

    def undo(self):
        if self._combineCommands is True:
            print("Cannot undo while recording combined commands")
            return
        self._recording = False # suppress generated notification for undo
        action = self.top
        print('Undo', action)
        super().undo()
        for command in action:
            c: AbstractCommand = command
            if isinstance(c, Delete) or isinstance(c, Remove):
                value = c.value
                if isinstance(c, Delete): value = c.owner
                # ignore connected to, since Ports are handled, so id's are already in uuid_dict
                if c.feature.name != "connectedTo" and isinstance(value, EObject) and hasattr(value, 'id') and value.id is not None:
                    resource = value.eResource
                    print("Undo: adding to uuid_dict", value.id, value)
                    resource.uuid_dict[value.id] = value

        self._recording = True

    def update_label(self, new_label: str) -> None:
        if self.compound:
            self.compound.label = new_label

    def serialize(self) -> UndoRedoSerializedStack:
        """
        Return the stack in a format that can be serialized and sent as JSON to the frontend.
        """
        stack = []
        for entry in self.stack:
            commands: list[UndoRedoCommandDict] = [{
                'id': command.value.id if hasattr(command.value, "id") else None,
                'name': command.value.name if hasattr(command.value, "name") else None,
                'type': command.__class__.__name__,
            } for command in entry.data if command.value is not None]
            # To find the kind of action the user did, we look at the last command in the set.
            # For a delete, we first remove everything that is attached and the last action is to remove what
            # the user wanted gone. For an add, we just add.
            entry_type = None
            if commands:
                entry_type = commands[-1]['type']
            dict_entry: UndoRedoStackEntryDict = {
                'label': entry.label,
                'type': entry_type,
                'commands': commands,
            }
            stack.append(dict_entry)
        return dict(
            stack_index=self.stack_index,
            stack=stack,
        )


def handleNotification(stack: UndoRedoCommandStack, notification: Notification):
    if notification.notifier.eResource is None:  # if the object has not been added to a resource, ignore it.
        print('!!! No eResource for', notification)
        return
    if not stack.is_recording():  # ignore all notifications when not recording
        #print('Ignoring ', notification)
        return
    if notification.old is None and notification.new is None:
        print('\ -- Ignoring (change=None)', notification)
        return
    print('Handling', notification)
    if notification.kind == Kind.SET:  # EValue.set()
        f: EStructuralFeature = notification.feature
        if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
            print("  \ -- Ignoring opposite setters for", f.name)
            return
        setNotification = Set(owner=notification.notifier, feature=notification.feature, value=notification.new)
        setNotification.previous_value = notification.old
        setNotification._executed = True
        stack.append(setNotification)
    elif notification.kind == Kind.UNSET: # remove reference
        if notification.old is not None:
            f: EStructuralFeature = notification.feature
            if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
                print("  \ -- Ignoring opposite unset for ", f.name)
                return
            if isinstance(f, EAttribute) or not f.containment:
                unsetNotification = Set(owner=notification.notifier, feature=notification.feature, value=notification.new)
                unsetNotification.previous_value = notification.old
                unsetNotification.can_execute
                print("\ -- [(Un)Set], not delete")
            else:
                unsetNotification = Delete(owner=notification.old)
                unsetNotification.feature = notification.feature
                #unsetNotification.references = {notification.feature: notification.old}
                #unsetNotification.previous_value = notification.new
                #unsetNotification.value = notification.old
                unsetNotification.can_execute  # record all changes
                print("\ -- [Delete] ", "\n \ -- inv_refs:", unsetNotification.inverse_references, "\n \ --refs:", unsetNotification.references)
            unsetNotification._executed = True
            stack.append(unsetNotification)
    elif notification.kind == Kind.ADD: # add an item to a collection
        addNotification = Add(owner=notification.notifier, feature=notification.feature, value=notification.new)
        addNotification.previous_value = notification.old
        addNotification.index = notification.notifier.eGet(notification.feature).index(notification.new)
        addNotification._collection = notification.notifier.eGet(notification.feature)
        addNotification._executed = True
        # special case: port.connectedTo generates 2 events, but only one is needed
        #if stack.top
        stack.append(addNotification)
    elif notification.kind == Kind.REMOVE: # remove eobject from collection
        if notification.old is not None:
            removeNotification = Remove(owner=notification.notifier, feature=notification.feature, value=notification.old, index=None)
            removeNotification.previous_value = notification.new
            removeNotification.value = notification.old
            if notification.feature.many:
                removeNotification._collection = notification.notifier.eGet(notification.feature)
                print("\ -- [Remove] collection of {} has length {}".format(notification.feature.name, len(removeNotification._collection)))
                try:
                    removeNotification.index = notification.notifier.eGet(notification.feature).index(notification.old)
                    print(" \ -- [Remove] found index in collection ", removeNotification.index)
                except KeyError:
                    removeNotification.index = 0
            removeNotification._executed = True
            stack.append(removeNotification)
    # elif notification.kind == Kind.REMOVE_MANY: # delete containment relation / object
    #     # check if this works at all...
    #     deleteNotification = Delete(owner=notification.notifier)
    #     deleteNotification._executed = True
    #     stack.append(deleteNotification)
    else:
        print("Not handled notification: ", notification)



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


@dataclass
class Tracker:
    resource: Resource
    stack: UndoRedoCommandStack
    observer: ResourceObserver


class ChangeTracker:
    def __init__(self):
        self.trackers = []

    def newTracker(self, eobj: EObject = None, resource: Resource = None) -> Tracker:
        if eobj:
            resource = eobj.eResource
        elif resource:
            pass
        else:
            raise Exception("Can't create new tracker: Resource is None")

        print("Tracking changes for resource with URI {}".format(resource.uri.plain))
        stack = UndoRedoCommandStack()
        ro = ResourceObserver(command_stack=stack)
        ro.observe(resource)
        tracker: Tracker = Tracker(resource, stack, ro)
        self.trackers.append(tracker)
        return tracker

    def get_tracker_stack(self, eobj: EObject = None, resource: Resource = None) -> UndoRedoCommandStack:
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
                return t.stack
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
