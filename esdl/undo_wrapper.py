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
import inspect
from functools import wraps

from flask_socketio import emit

from esdl.undo import ChangeContext
from extensions.session_manager import get_project_manager
from src.log import get_logger
from src.tno.undoredo.types import serialize_command_stack

logger = get_logger(__name__)


def undo_record_changes(label: str, change_context: ChangeContext = None):
    """
     Wraps undo_record_changes, such that changes are automatically recorded
     In a seperate file to avoid cyclic imports.
     Label is required.
     a UndoRedoCommandStack 'stack' parameter is injected in the function
        if that 'stack' parameter is present in the function signature
    """
    def internal_recording(fn):
        @wraps(fn)
        def wrapped_record_changes(*args, **kwargs):
            pm = get_project_manager()
            # active_es_id = get_session('active_es_id')
            # stack = pm.get_undo_redo_stack(es_id=active_es_id)
            stack = pm.get_undo_redo_stack()
            with stack.track_changes(label=label, change_context=change_context):
                if 'stack' in inspect.getfullargspec(fn).args:
                    kwargs['stack'] = stack # Optionally inject the stack into the wrapped function fn
                result = fn(*args, **kwargs)
            try:
                emit('update_undo_redo_stack', serialize_command_stack(stack))
            except Exception:
                # Notify only, don't fail the wrapped operation.
                logger.exception("Failed to serialize/emit undo/redo stack")
            return result
        return wrapped_record_changes
    return internal_recording
