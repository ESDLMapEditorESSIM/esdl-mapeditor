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

from flask_socketio import emit

from src.tno.undoredo.types import serialize_command_stack


def emit_update_undo_redo_stack(stack):
    """
    Send the entire active ESDL project to the frontend.
    """
    emit('update_undo_redo_stack', serialize_command_stack(stack))
