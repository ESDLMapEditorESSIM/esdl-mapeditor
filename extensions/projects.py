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
import re
from typing import TypedDict

from flask import Blueprint, jsonify, request, session

import esdl
import src.log as log
from esdl.processing.string_uri import StringURI
from esdlproject import ESDLProject
from esdlproject.variant_api import create_new_variant
from extensions.session_manager import get_project_manager, set_session, del_session
from src.app import executor, socketio
from src.process_es_area_bld import process_energy_system
from src.tno.live_model_interface.api import send_project_manager_to_lmi_async, send_delete_variant_message_to_lmi
from src.tno.projects.core import create_new_project_manager
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
    filename: str = request.json['filename']
    pm = get_project_manager()
    if not filename.endswith(".project"):
        filename = filename + ".project"
    uri = StringURI(filename, file_content)
    project = pm.load(uri)
    if project:
        set_session("es_info_list", {})

        # Clear session variables
        del_session("shape_dictionary")
        del_session("conn_list")
        del_session("asset_list")
        del_session("area_bld_list")

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
    new_pm = create_new_project_manager()

    # Clear session variables
    del_session("shape_dictionary")
    del_session("conn_list")
    del_session("asset_list")
    del_session("area_bld_list")

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
        emit_active_esdl_project()
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
        vc_variants = []
        pm.get_variant_list(variant, vc_variants)
        # only set active variant when this is not the last variant in the list
        auto_update = len(vc_variants) > 1 or len(pm.project.variantCollection) > 1
        if variant.variantCollection:
            # if the variant is a child of a VariantCollection, delete the VariantCollection too
            pm.delete_variant(variant.variantCollection)  # this will delete all child variants too
        else:
            pm.delete_variant(variant)

    # in case the user wants to delete the last variant, initialize an empty project
    if len(pm.get_variants()) == 0:
        pm.init_empty_project()

    if not pm.get_active_variant() or auto_update:
        # if the active variant was deleted, set the parent variant as active
        if variant.parentVariant:
            logger.debug("Setting parent variant as active variant", variant_name=variant.parentVariant.name)
            pm.set_active_variant(variant.parentVariant)
        else:
            logger.debug("Selecting first variant as active variant", variant_name=variant.name)
            pm.set_active_variant(pm._select_new_active_variant())

    emit_active_esdl_project()
    # No need to process the energy system, as the set_active_variant will check for changes
    #es = pm.get_active_energy_system()
    #executor.submit(process_energy_system, force_update_es_id=es.id)
    send_delete_variant_message_to_lmi(variant)


class RenameVariantRequest(TypedDict):
    id: str
    name: str


@socketio.on("rename_variant", namespace="/esdl")
def rename_variant(message: RenameVariantRequest):
    """
    Rename variant.
    """
    pm = get_project_manager()
    variant = pm.get_variant_by_id(message["id"])
    variant.name = message["name"]
    # set InstanceDate if the new Variant name contains a year
    year_re = re.compile(r".*(20\d\d).*")
    match = year_re.match(variant.name)
    if match:
        ct = pm.get_change_tracker_for_variant(variant)
        with ct.stack.track_changes(label="Set instance year"):
            year = match.group(1)
            if variant.snapshotRef:
                instance = variant.snapshotRef.instance[0]
                instance.date = esdl.InstanceYear(year=year)

    if variant.snapshotRef:
        # don't track this change as when changing a parent variant name, this variant name will also change...
        # also rename the ESDL snapshot and give it the same name as the variant
        variant.snapshotRef.name = variant.name
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
