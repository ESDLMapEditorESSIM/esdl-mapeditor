#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-1.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from extensions.session_manager import get_project_manager
from src import socketio
from src.log import get_logger
from src.tno.undoredo.types import serialize_command_stack

logger = get_logger(__name__)


@socketio.on('get_undo_redo_stack', namespace='/esdl')
def get_undo_redo_stack(_):
    """
    Return the undo redo stack for the currently activate energy system.
    """
    pm = get_project_manager()
    undo_redo_stack = pm.get_undo_redo_stack()
    serialized_stack = serialize_command_stack(undo_redo_stack)
    return serialized_stack

