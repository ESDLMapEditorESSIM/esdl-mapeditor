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

from extensions.session_manager import get_handler, get_session


def undo_record_changes(label: str):
    """
     Wraps undo_record_changes, such that changes are automatically recorded
     In a seperate file to avoid cyclic imports
     Label is required
    """
    def internal_recording(fn):
        @wraps(fn)
        def wrapped_record_changes(*args, **kwargs):
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            stack = esh.get_undo_redo_stack(es_id=active_es_id)
            stack.start_recording(label=label)
            result = fn(*args, **kwargs)
            stack.stop_recording()
            return result
        return wrapped_record_changes
    return internal_recording
