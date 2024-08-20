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

from extensions.session_manager import get_project_manager, del_session, set_session
from src.log import get_logger
from src.tno.projects.types import serialize_esdl_project

logger = get_logger(__name__)


def emit_active_esdl_project():
    """
    Send the entire active ESDL project to the frontend.
    """
    pm = get_project_manager()
    project_data = serialize_esdl_project(pm, pm.project)
    logger.info("Active project data", project_data=project_data)
    emit('update_active_esdl_project', project_data, namespace="/esdl")


def emit_clear_ui():
    """
    Clears the UI.
    :return:
    """
    set_session("es_info_list", {})
    del_session("shape_dictionary")
    emit('clear_ui')


def emit_clear_frontend_esdls():
    """
    Clears all known ESDLs in the frontend.
    """
    emit('clear_esdl_layer_list')


# def emit_send_active_variant():
#     #call_process_energy_system.submit(filename)
#
#     del_session('store_item_metadata')
#     emit('store_item_metadata', {})
#     set_session('active_es_id', es.id)
#     set_session('es_filename', filename)