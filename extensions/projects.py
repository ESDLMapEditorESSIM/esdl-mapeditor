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

from flask import Blueprint, jsonify, request

from esdl.esdl_handler import StringURI
from esdlproject import ESDLProject
from esdlproject.variant_api import create_new_variant
from extensions.session_manager import get_project_manager, set_session
from src.app import executor, socketio
import src.log as log
from src.process_es_area_bld import call_process_energy_system, process_energy_system
from src.tno.projects.emits import emit_active_esdl_project
from src.tno.projects.types import serialize_esdl_project
from src.tno.undoredo.emits import emit_update_undo_redo_stack

logger = log.get_logger(__name__)

projects = Blueprint('projects', __name__, url_prefix='/projects')


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
    filename = request.json['filename']
    pm = get_project_manager()
    uri = StringURI(filename + '.project', file_content)
    pm.load(uri)
    set_session("es_info_list", {})
    return jsonify(serialize_esdl_project(pm, pm.project))


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
    Create a brand new energy project.
    """
    pm = get_project_manager()
    pm.init_empty_project()
    set_session("es_info_list", {})
    emit_update_undo_redo_stack(pm.active_tracker.stack)
    return serialize_esdl_project(pm, pm.project)


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
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message['id'])
    if variant:
        pm.set_active_variant(variant)
        es = pm.get_active_energy_system()
        set_session('active_es_id', es.id)
        executor.submit(process_energy_system)
        emit_active_esdl_project()
        emit_update_undo_redo_stack(pm.active_tracker.stack)
    else:
        logger.warning("No variant with given ID found!", variant_id=message["id"])


@socketio.on('create_base_variant', namespace='/esdl')
def create_base_variant():
    pm = get_project_manager()
    pm.create_new_variant_collection()
    emit_active_esdl_project()


class DeleteBaseVariantRequest(TypedDict):
    id: str


@socketio.on('delete_base_variant', namespace='/esdl')
def delete_base_variant(message: DeleteBaseVariantRequest):
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message['id'])
    if base_variant is not None:
        pm.delete_variant(base_variant)
        emit_active_esdl_project()


class RenameBaseVariantRequest(TypedDict):
    id: str
    name: str


@socketio.on("rename_base_variant", namespace="/esdl")
def rename_project(message: RenameBaseVariantRequest):
    """
    Load energy project from file.
    """
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message["id"])
    base_variant.name = message["name"]


class CreateVariantRequest(TypedDict):
    base_variant_id: str


@socketio.on('create_variant', namespace='/esdl')
def create_variant(message: CreateVariantRequest):
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message['base_variant_id'])
    create_new_variant(base_variant)
    emit_active_esdl_project()


class CreateChildVariantRequest(TypedDict):
    parent_variant_id: str


@socketio.on('create_child_variant', namespace='/esdl')
def create_child_variant(message: CreateChildVariantRequest):
    pm = get_project_manager()
    parent_variant = pm.get_variant_by_id(message['parent_variant_id'])
    create_new_variant(parent_variant)
    emit_active_esdl_project()


class DeleteVariantRequest(TypedDict):
    id: str


@socketio.on('delete_variant', namespace='/esdl')
def delete_base_variant(message: DeleteVariantRequest):
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message['id'])
    if variant is not None:
        pm.delete_variant(variant)

    emit_active_esdl_project()


class RenameVariantRequest(TypedDict):
    id: str
    name: str


@socketio.on("rename_variant", namespace="/esdl")
def rename_project(message: RenameVariantRequest):
    """
    Rename energy project.
    """
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message["id"])
    variant.name = message["name"]

