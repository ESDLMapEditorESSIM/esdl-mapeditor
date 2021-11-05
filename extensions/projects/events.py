import base64

# from app import send_alert
from esdl.esdl_handler import StringURI
from extensions.session_manager import get_handler

from src import socketio
import src.log as log
from variation import Project

logger = log.get_logger(__name__)


@socketio.on('load_energy_project', namespace='/esdl')
def load_energy_project(message):
    logger.info(message)
    base64_file = message['base64_file']
    file_content = base64.urlsafe_b64decode(base64_file.split(',')[1]).decode('utf-8')
    logger.info(file_content)
    filename = message['filename']
    logger.info(filename)
    uri = StringURI(filename + '.project', file_content)
    esh = get_handler()
    rset = esh.rset

    try:
        project_resource = rset.get_resource(uri)
        project: Project = project_resource.contents[0]
        variant_names = [v.name for v in project.variants]
        print(f'Loaded project {project.name}, containing {len(project.variants)} variants: {variant_names}')
        return variant_names
    except Exception as e:
        logger.error("Error loading {}: {}".format(filename, e))
        # send_alert('Error interpreting ESDL from file - Exception: ' + str(e))

