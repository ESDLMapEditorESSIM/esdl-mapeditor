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

from pyecore.notification import EObserver, Notification, Kind
from pyecore.ecore import EObject, EStructuralFeature, EReference
from pyecore.resources import Resource
from pyecore.commands import Set, Add, Delete, Remove, CommandStack, Compound, Command, AbstractCommand
from src.log import get_logger
from dataclasses import dataclass

log = get_logger(__name__)


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
            command.undo()

    def redo(self):
        for command in self:
            command.redo()

    def unwrap(self):
        return self[0] if len(self) == 1 else self

    def __repr__(self):
        return '{}(label={}: {})'.format(self.__class__.__name__, self.label, self.data)




class UndoRedoCommandStack(CommandStack):
    def __init__(self):
        self._recording = False
        self._combineCommands = True
        self.compound = None
        super().__init__()

    def start_recording(self, combineCommands=False, label=None):
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
                    commands[-1].feature.name == 'connectedTo' and self.compound[-1].feature.name == 'connectedTo':
                print('Ignore 2nd connectedTo', commands)
                # todo add check if notifier is same as old
                return # ignore 2nd connected to relation
            # only adding multiple commands to the compound
            print("Adding combined command {} to action '{}'".format(commands, self.compound.label))
            self.compound.extend(commands)
            return
        if not self._recording:
            #print('Ignoring ', commands)
            return

        for command in commands:
            if isinstance(command, LabelledAction):
                # make sure the new subcommands are set to executed, as we don't manually execute them, but automatically
                # for cmd in command:
                #     if cmd.can_execute:
                #         cmd._executed = True
                self.top = command
                log.debug("Appended {} to the stack".format(command))

            else:
                if command.can_execute:
                    # command.execute()
                    command._executed = True
                    self.top = command
                    log.debug("Appended {} to the stack".format(command))
                else:
                    raise ValueError('Cannot execute command {}'.format(command))

    def can_redo(self):
        return len(self.stack) - self.stack_index > 1

    def redo(self):
        if self._combineCommands is True:
            print("Cannot redo while recording combined commands")
            return
        self._recording = False  # suppress generated notifications for redo
        print('Undo', self.peek_next_top)
        super().redo()
        self._recording = True

    def can_undo(self):
        return len(self.stack) > 0 and self.stack_index >= 0

    def undo(self):
        if self._combineCommands is True:
            print("Cannot undo while recording combined commands")
            return
        self._recording = False # suppress generated notification for undo
        print('Undo', self.top)
        super().undo()
        self._recording = True


def handleNotification(stack: UndoRedoCommandStack, notification: Notification):
    if notification.notifier.eResource is None:  # if the object has not been added to a resource, ignore it.
        return
    if not stack.is_recording():  # ignore all notifications when not recording
        #print('Ignoring ', notification)
        return
    if notification.old is None and notification.new is None:
        print('Ignoring (change=None)', notification)
        return
    print('Handling', notification)
    if notification.kind == Kind.SET:
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
            unsetNotification = Delete(owner=notification.notifier)
            unsetNotification.feature = notification.feature
            #unsetNotification.references = {notification.feature: notification.old}
            #unsetNotification.previous_value = notification.new
            #unsetNotification.value = notification.old
            unsetNotification._executed = True
            stack.append(unsetNotification)
    elif notification.kind == Kind.ADD:
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
                print("collection of {} is {}".format(notification.feature.name, removeNotification._collection))
                try:
                    removeNotification.index = notification.notifier.eGet(notification.feature).index(notification.old)
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

    def newTracker(self, eobj: EObject) -> Tracker:
        resource = eobj.eResource
        if resource is None:
            raise Exception("Can't create new tracker: Resource is None")
        print("Tracking changes for resource with URI {}".format(resource.uri.plain))
        stack = UndoRedoCommandStack()
        ro = ResourceObserver(command_stack=stack)
        ro.observe(resource)
        tracker: Tracker = Tracker(resource, stack, ro)
        self.trackers.append(tracker)
        return tracker

    def get_tracker_stack(self, eobj: EObject) -> UndoRedoCommandStack:
        resource = eobj.eResource
        if resource is None:
            raise Exception("Can't find stack for the resource of {} (of type {})".format(eobj, eobj.eClass.name))
        for t in self.trackers:
            if t.resource == resource:
                return t.stack
        raise ValueError("Can't find stack belonging to resource {} and object {}".format(resource.uri.plain, eobj))

    def delete(self, stack):
        for t in self.trackers:
            t: Tracker = t
            if t.stack is stack:
                del t.stack
                t.resource.listeners.remove(t.observer)
                del t.observer
                #del t.resource # needed?

