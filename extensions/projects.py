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

from uuid import uuid4

from src import executor

from esdl.resources.xmlresource import XMLResource

from esdl.esdl_handler import StringURI
from flask import jsonify, request
from src.process_es_area_bld import process_energy_system
from src.tno.projects.emits import emit_active_esdl_project
from src.tno.projects.types import serialize_esdl_project
from extensions.session_manager import get_handler, get_project_manager

from src import socketio
import src.log as log
from esdlproject import ESDLProject, Variant
from flask import Blueprint

logger = log.get_logger(__name__)

projects = Blueprint('projects', __name__, url_prefix='/projects')


class DeleteBaseVariantRequest(TypedDict):
    id: str


@socketio.on('delete_base_variant', namespace='/esdl')
def delete_base_variant(message: DeleteBaseVariantRequest):
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message['id'])
    if base_variant is not None:
        pm.delete_variant(base_variant)
        emit_active_esdl_project()


class CreateVariantRequest(TypedDict):
    base_variant_id: str


@socketio.on('create_variant', namespace='/esdl')
def delete_base_variant(message: CreateVariantRequest):
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message['base_variant_id'])
    variant = Variant(name=f"Untitled variant {len(base_variant.variant) + 1}")
    base_variant.variant.append(variant)
    emit_active_esdl_project()


class DeleteVariantRequest(TypedDict):
    base_variant_id: str
    name: str


@socketio.on('delete_variant', namespace='/esdl')
def delete_base_variant(message: DeleteVariantRequest):
    pm = get_project_manager()
    variant = pm.find_variant(message['base_variant_id'], message['name'])
    if variant is not None:
        pm.delete_variant(variant)

    emit_active_esdl_project()


@projects.route("/load_energy_project", methods=["POST"])
def load_energy_project():
    """
    Load energy project from file.
    """
    base64_file = request.json['base64_file']
    file_content = base64.urlsafe_b64decode(base64_file.split(',')[1]).decode('utf-8')
    filename = request.json['filename']
    pm = get_project_manager()
    uri = StringURI(filename + '.project', file_content)
    pm.load(uri)
    return jsonify(serialize_esdl_project(pm, pm.project))


@projects.route("/save_energy_project")
def save_energy_project():
    """
    Load energy project from file.
    """
    pm = get_project_manager()
    project = pm.project
    project_as_string = pm.save()
    base64_file = base64.b64encode(project_as_string.encode()).decode()
    return jsonify(base64file=base64_file, filename=f"{project.name}.project")


@socketio.on('get_active_energy_project', namespace='/esdl')
def get_active_energy_project(_):
    pm = get_project_manager()
    project: ESDLProject = pm.project
    variant_names = [v.name for v in project.baseVariant]

    print(f'Returning project {project.name}, containing {len(project.baseVariant)} variants: {variant_names}')
    return serialize_esdl_project(pm, project)


class SetActiveVariantRequest(TypedDict):
    base_variant_id: str
    name: str


@socketio.on('set_active_variant', namespace='/esdl')
def set_active_variant(message):
    pm = get_project_manager()
    variant = pm.find_variant(message['base_variant_id'], message['name'])
    if variant:
        pm.set_active_variant(variant)
    executor.submit(process_energy_system, force_update_es_id=pm.get_active_energy_system().id)


class LoadVariantRequest(TypedDict):
    base_variant_id: str


@socketio.on('load_variant', namespace='/esdl')
def load_variant(message):
    pm = get_project_manager()
    base_variant = pm.get_base_variant_by_id(message['base_variant_id'])


@socketio.on('activate_project_variant', namespace='/esdl')
def activate_project_variant(message):
    esh = get_handler()
    energy_project = esh.get_energy_project()
    if not energy_project:
        return

    requested_variant_name = message['id']
    # Get the asked for variant.
    # TODO: Move to more generic place.
    base_variant = energy_project.variants[0]
    found_variant = None
    for variant in base_variant.variant:
        if variant.name == requested_variant_name:
            found_variant = variant
            break
    if found_variant is None:
        return

    snapshot = base_variant.snapshot
    # TODO: This can probably be done nicer than first writing to string.
    # Now using the add_from_string so that it gets properly added to the resource set.
    uri = StringURI('to_string_' + str(uuid4()) + '.esdl')
    resource = XMLResource(uri)
    resource.append(snapshot.deepcopy())
    resource.save()
    esh.add_from_string(found_variant.name, uri.getvalue())
