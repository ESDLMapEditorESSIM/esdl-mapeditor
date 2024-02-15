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

from extensions.session_manager import get_project_manager
from src.tno.projects.types import serialize_esdl_project


def emit_active_esdl_project():
    """
    Send the entire active ESDL project to the frontend.
    """
    pm = get_project_manager()
    project_data = serialize_esdl_project(pm, pm.project)
    print("Active project data", project_data)
    emit('update_active_esdl_project', project_data, namespace="/esdl")


def emit_clear_frontend_esdls():
    """
    Clears all known ESDLs in the frontend.
    """
    emit('clear_esdl_layer_list')
