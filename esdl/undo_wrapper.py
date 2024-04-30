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

from functools import wraps

from contextlib import contextmanager
from flask_socketio import emit
from extensions.session_manager import get_project_manager
from src.tno.undoredo.types import serialize_command_stack


def undo_record_changes(label: str):
    """
     Wraps undo_record_changes, such that changes are automatically recorded
     In a seperate file to avoid cyclic imports.
     Label is required.
    """
    def internal_recording(fn):
        @wraps(fn)
        def wrapped_record_changes(*args, **kwargs):
            pm = get_project_manager()
            # active_es_id = get_session('active_es_id')
            # stack = pm.get_undo_redo_stack(es_id=active_es_id)
            stack = pm.get_undo_redo_stack()
            stack.start_recording(label=label)
            result = fn(*args, **kwargs)
            stack.stop_recording()
            emit('update_undo_redo_stack', serialize_command_stack(stack))
            return result
        return wrapped_record_changes
    return internal_recording


@contextmanager
def undo_record_changes_context(label: str, combine_commands=True):
    """
    Context manager for recording changes. Example usage:

    with undo_record_changes_context("My label"):
        # do stuff

    :param label:
    :param combine_commands:
    :return:
    """
    pm = get_project_manager()
    stack = pm.get_undo_redo_stack()
    stack.start_recording(label=label, combineCommands=combine_commands)
    try:
        yield
    finally:
        stack.stop_recording()
