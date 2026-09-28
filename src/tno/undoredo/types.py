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
from typing import Optional, TypedDict, List

from esdl.undo import UndoRedoCommandStack
from esdlproject import HighLevelChange
from src.log import get_logger

logger = get_logger(__name__)


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
    changed_at: str
    commands: List[UndoRedoCommandDict]


class UndoRedoSerializedStack(TypedDict):
    """
    An entry in the undo redo stack.
    """
    stack_index: int
    stack: List[UndoRedoStackEntryDict]


def _get_change_object_id(command_stack: UndoRedoCommandStack, change) -> Optional[str]:
    if change.objectValue is not None and hasattr(change.objectValue, "id"):
        return change.objectValue.id
    if change.owner is not None and hasattr(change.owner, "id"):
        return change.owner.id
    if not change.ownerFragment:
        return None
    try:
        owner = command_stack.resource.resolve(change.ownerFragment)
    except (AttributeError, KeyError, IndexError, ValueError):
        return None
    if owner is not None and hasattr(owner, "id"):
        return owner.id
    return None


def serialize_command_stack(command_stack: UndoRedoCommandStack) -> UndoRedoSerializedStack:
    """
    Return the stack in a format that can be serialized and sent as JSON to the frontend.
    """
    stack = []
    for entry in command_stack.stack:
        if not isinstance(entry, HighLevelChange):
            logger.warning(f"Unknown entry in undo stack: {entry}")
            continue
        changes: List[UndoRedoCommandDict] = [{
            'id': _get_change_object_id(command_stack, change),
            'name': change.objectValue.name if hasattr(change.objectValue, "name") else None,
            'type': change.__class__.__name__,
        } for change in entry.change]
        # To find the kind of action the user did, we look at the last command in the set.
        # For a delete, we first remove everything that is attached and the last action is to remove what
        # the user wanted gone. For an add, we just add.
        entry_type = ""
        if changes:
            entry_type = changes[-1]['type']
        dict_entry: UndoRedoStackEntryDict = {
            'label': entry.label,
            'type': entry_type,
            'changed_at': entry.changedAt.isoformat(),
            'commands': changes,
        }
        stack.append(dict_entry)
    return dict(
        stack_index=command_stack.stack_index,
        stack=stack,
    )

