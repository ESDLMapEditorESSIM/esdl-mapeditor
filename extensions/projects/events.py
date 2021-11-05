import base64

# from app import send_alert
from uuid import uuid4

from esdl.resources.xmlresource import XMLResource

from esdl.esdl_handler import StringURI
from extensions.projects.types import serialize_project
from extensions.session_manager import get_handler

from src import socketio
import src.log as log
from variation import Project

logger = log.get_logger(__name__)


@socketio.on('load_energy_project', namespace='/esdl')
def load_energy_project(message):
    base64_file = message['base64_file']
    file_content = base64.urlsafe_b64decode(base64_file.split(',')[1]).decode('utf-8')
    filename = message['filename']
    uri = StringURI(filename + '.project', file_content)
    esh = get_handler()
    rset = esh.rset

    try:
        project_resource = rset.get_resource(uri)
        project: Project = project_resource.contents[0]
        variant_names = [v.name for v in project.variants]
        print(f'Loaded project {project.name}, containing {len(project.variants)} variants: {variant_names}')
        return serialize_project(project)
    except Exception as e:
        logger.error("Error loading {}: {}".format(filename, e))
        # send_alert('Error interpreting ESDL from file - Exception: ' + str(e))


@socketio.on('activate_project_variant', namespace='/esdl')
def activate_project_variant(message):
    logger.info(message)
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
        logger.info(variant)
        if variant.name == requested_variant_name:
            found_variant = variant
            break
    if found_variant is None:
        return

    snapshot = base_variant.snapshot
    logger.info(snapshot)
    # TODO: This can probably be done nicer than first writing to string.
    # Now using the add_from_string so that it gets properly added to the resource set.
    uri = StringURI('to_string_' + str(uuid4()) + '.esdl')
    resource = XMLResource(uri)
    resource.append(snapshot)
    resource.save()
    esh.add_from_string(found_variant.name, uri.getvalue())
