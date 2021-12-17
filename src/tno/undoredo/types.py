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

from typing import Optional, TypedDict

from esdl.undo import UndoRedoCommandStack


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


def serialize_command_stack(command_stack: UndoRedoCommandStack) -> UndoRedoSerializedStack:
    """
    Return the stack in a format that can be serialized and sent as JSON to the frontend.
    """
    stack = []
    for entry in command_stack.stack:
        commands: list[UndoRedoCommandDict] = [{
            'id': command.value.id if hasattr(command.value, "id") else None,
            'name': command.value.name if hasattr(command.value, "name") else None,
            'type': command.__class__.__name__,
        } for command in entry.data if command.value is not None]
        # To find the kind of action the user did, we look at the last command in the set.
        # For a delete, we first remove everything that is attached and the last action is to remove what
        # the user wanted gone. For an add, we just add.
        entry_type = ""
        if commands:
            entry_type = commands[-1]['type']
        dict_entry: UndoRedoStackEntryDict = {
            'label': entry.label,
            'type': entry_type,
            'commands': commands,
        }
        stack.append(dict_entry)
    return dict(
        stack_index=command_stack.stack_index,
        stack=stack,
    )

