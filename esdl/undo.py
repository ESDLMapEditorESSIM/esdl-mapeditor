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

from pyecore.notification import EObserver, Notification, Kind
from pyecore.ecore import EObject, EStructuralFeature, EReference
from pyecore.commands import Set, Add, Delete, CommandStack, EditingDomain, Compound
from src.log import get_logger

log = get_logger(__name__)

class UndoRedoCommandStack(CommandStack):
    def __init__(self):
        self._recording = False
        self._combineCommands = True
        self.compound = None
        super().__init__()

    def start_recording(self, combineCommands=False):
        self._recording = True
        self._combineCommands = combineCommands
        if combineCommands:
            self.compound = Compound()

    def is_recording(self):
        return self._recording

    def stop_recording(self):
        self._combineCommands = False
        if len(self.compound) > 0:
            self.append(self.compound)
        self._recording = False


    def add_undo_step(self):
        if self.compound is not None:
            self._combineCommands = False
            self.append(self.compound)
            self._combineCommands = True
        self.compound = Compound()


    def append(self, *commands):
        if self._combineCommands:
            # only adding multiple commands
            print("Adding combined command {}".format(commands))
            self.compound.extend(commands)
            return
        if not self._recording:
            #print('Ignoring ', commands)
            return

        for command in commands:
            if isinstance(command, Compound):
                for cmd in command:
                    if cmd.can_execute:
                        cmd._executed = True
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
        super().redo()
        self._recording = True

    def can_undo(self):
        return len(self.stack) > 0 and self.stack_index >= 0

    def undo(self):
        if self._combineCommands is True:
            print("Cannot undo while recording combined commands")
            return
        self._recording = False # suppress generated notification for undo
        super().undo()
        self._recording = True


def handleNotification(stack: UndoRedoCommandStack, notification: Notification):
    if notification.notifier.eResource is None:  # if the object has not been added to a resource, ignore it.
        return
    if not stack.is_recording():  # ignore all notifications when not recording
        #print('Ignoring ', notification)
        return
    print('Handling', notification)
    if notification.kind == Kind.SET:
        f: EStructuralFeature = notification.feature
        if isinstance(f, EReference) and f.eOpposite and f.eOpposite.containment:
            print("Ignoring opposite setters")
            return
        setNotification = Set(owner=notification.notifier, feature=notification.feature, value=notification.new)
        setNotification.previous_value = notification.old
        stack.append(setNotification)
    if notification.kind == Kind.ADD:
        addNotification = Add(owner=notification.notifier, feature=notification.feature, value=notification.new)
        addNotification.previous_value = notification.old
        addNotification.index = notification.notifier.eGet(notification.feature).index(notification.new)
        stack.append(addNotification)

#stack = UndoRedoCommandStack()  # keep track of all undo-redo stuff using notifications


# observe every change in the model
def monitor_esdl_changes(command_stack: UndoRedoCommandStack):
    observer = EObserver(notifyChanged=lambda x: handleNotification(command_stack, x))
    old_init = EObject.__init__

    def new_init(self, **kwargs):
        observer.observe(self)
        old_init(self, **kwargs)

    setattr(EObject, '__init__', new_init)