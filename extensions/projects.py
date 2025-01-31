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

import base64
from typing import TypedDict

from flask import Blueprint, jsonify, request, session

import src.log as log
from esdl.processing.string_uri import StringURI
from esdlproject import ESDLProject
from esdlproject.ProjectManager import ProjectManager
from esdlproject.variant_api import create_new_variant
from extensions.session_manager import get_project_manager, set_session, set_project_manager, \
    SESSION_MANAGER_LISTENER_ID, on_change_recorded
from src.app import executor, socketio
from src.incremental_ui.ui_change_handler import INCREMENTAL_UI_LISTENER_ID, change_handler
from src.process_es_area_bld import call_process_energy_system, process_energy_system
from src.tno.live_model_interface.api import send_project_manager_to_lmi_async, send_delete_variant_message_to_lmi
from src.tno.projects.emits import emit_active_esdl_project, emit_clear_frontend_esdls, emit_clear_ui
from src.tno.projects.types import serialize_esdl_project
from src.tno.undoredo.emits import emit_update_undo_redo_stack

logger = log.get_logger(__name__)

projects = Blueprint('projects', __name__, url_prefix='/projects')

def init_mapeditor_change_handlers(pm: ProjectManager):
    """
    Makes sure this ProjectManager has the correct listeners for changes attached to it
    """
    client_id = session["client_id"]
    if not pm.has_change_listener(SESSION_MANAGER_LISTENER_ID):
        pm.add_change_listener(SESSION_MANAGER_LISTENER_ID, on_change_recorded)
        logger.debug("Init PM client_id={} with listener for ESDL changes for LMI".format(client_id))
    if not pm.has_change_listener(INCREMENTAL_UI_LISTENER_ID):
        pm.add_change_listener(INCREMENTAL_UI_LISTENER_ID, change_handler)
        logger.debug("Init PM client_id={} with UI listener for ESDL changes from LMI".format(client_id))



@socketio.on('get_active_esdl_project', namespace='/esdl')
def get_active_esdl_project(_):
    pm = get_project_manager()
    project: ESDLProject = pm.project

    variant_names = [v.name for v in project.variantCollection]
    print(f'Returning project {project.name}, containing {len(project.variantCollection)} variants: {variant_names}')

    return serialize_esdl_project(pm, project)


@projects.route("/load_esdl_project", methods=["POST"])
def load_esdl_project():
    """
    Load energy project from file.
    """
    base64_file = request.json['base64_file']
    file_content = base64.urlsafe_b64decode(base64_file.split(',')[1]).decode('utf-8')
    filename: str = request.json['filename']
    pm = get_project_manager()
    if not filename.endswith(".project"):
        filename = filename + ".project"
    uri = StringURI(filename, file_content)
    project = pm.load(uri)
    if project:
        set_session("es_info_list", {})
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])
    serialized_esdl_project = serialize_esdl_project(pm, pm.project)
    return jsonify(serialized_esdl_project)


@projects.route("/save_esdl_project")
def save_esdl_project():
    """
    Generate ESDL project as file.
    """
    pm = get_project_manager()
    project = pm.project
    project_as_string = pm.save()
    base64_file = base64.b64encode(project_as_string.encode()).decode()
    return jsonify(base64file=base64_file, filename=f"{project.name}.project")


@socketio.on("new_esdl_project", namespace="/esdl")
def new_esdl_project(_):
    """
    Create a brand-new energy project.
    """
    new_pm = ProjectManager()
    set_project_manager(new_pm)
    init_mapeditor_change_handlers(new_pm)
    set_session("es_info_list", {})
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])
    emit_clear_frontend_esdls()
    emit_clear_ui()
    call_process_energy_system.submit()
    emit_active_esdl_project()
    emit_update_undo_redo_stack(new_pm.active_tracker.stack)
    return serialize_esdl_project(new_pm, new_pm.project)


class RenameEsdlProjectRequest(TypedDict):
    name: str


@socketio.on("rename_project", namespace="/esdl")
def rename_project(message: RenameEsdlProjectRequest):
    """
    Load energy project from file.
    """
    pm = get_project_manager()
    pm.project.name = message["name"]



class SetActiveVariantRequest(TypedDict):
    id: str


@socketio.on('set_active_variant', namespace='/esdl')
def set_active_variant(message: SetActiveVariantRequest):
    """
    Set the active variant for this user. Triggers a process_energy_system invocation.

    :param message: Message containing the ID of the variant to activate.
    """
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message['id'])
    if variant:
        needs_update = pm.set_active_variant(variant)
        es = pm.get_active_energy_system()
        set_session('active_es_id', es.id)
        if needs_update:
            executor.submit(process_energy_system, force_update_es_id=es.id)
        else:
            executor.submit(process_energy_system)
        emit_update_undo_redo_stack(pm.active_tracker.stack)
    else:
        logger.warning("No variant with given ID found!", variant_id=message["id"])


@socketio.on('create_variant_collection', namespace='/esdl')
def create_variant_collection():
    pm = get_project_manager()
    pm.create_empty_variant_collection()
    emit_active_esdl_project()
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])


class CreateChildVariantRequest(TypedDict):
    parent_variant_id: str


@socketio.on('create_child_variant', namespace='/esdl')
def create_child_variant(message: CreateChildVariantRequest):
    pm = get_project_manager()
    parent_variant = pm.get_variant_by_id(message['parent_variant_id'])
    create_new_variant(parent_variant)
    emit_active_esdl_project()
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])


class DeleteVariantRequest(TypedDict):
    id: str


@socketio.on('delete_variant', namespace='/esdl')
def delete_variant(message: DeleteVariantRequest):
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message['id'])
    if variant is not None:
        pm.delete_variant(variant)

    emit_active_esdl_project()
    es = pm.get_active_energy_system()
    executor.submit(process_energy_system, force_update_es_id=es.id)
    send_delete_variant_message_to_lmi(variant)


class RenameVariantRequest(TypedDict):
    id: str
    name: str


@socketio.on("rename_variant", namespace="/esdl")
def rename_variant(message: RenameVariantRequest):
    """
    Rename energy project.
    """
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message["id"])
    variant.name = message["name"]
    if variant.snapshotRef:
        variant.snapshotRef.name = f'{pm.project.name} - {variant.name}'
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])

class FlattenVariantRequest(TypedDict):
    id: str


@socketio.on('flatten_variant', namespace='/esdl')
def flatten_variant(message: FlattenVariantRequest):
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message["id"])
    flattened_variant = pm.flatten_variant(variant)
    emit_active_esdl_project()
    send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])
