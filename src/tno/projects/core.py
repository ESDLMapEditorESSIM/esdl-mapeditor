import uuid
from datetime import datetime, timezone

from flask import session, has_request_context, request

from esdl.resources.json import JsonOptions
from esdl.undo import ChangeSource, ChangeContext
from esdl.project import HighLevelChange
from esdl.project.ProjectManager import ProjectManager, eobject_to_string, ESDLFormat
from extensions.session_manager import SESSION_MANAGER_LISTENER_ID, get_project_manager, get_session
from src import log
from src.incremental_ui.ui_change_handler import INCREMENTAL_UI_LISTENER_ID, change_handler
from src.process_es_area_bld import call_process_energy_system
from src.tno.live_model_interface.api import send_project_manager_to_lmi_async
from src.tno.live_model_interface.shared.message_types import HighLevelChangeMessage
from src.tno.live_model_interface.shared.publisher import send_rabbitmq_message
from src.tno.projects.emits import emit_clear_frontend_esdls, emit_clear_ui, emit_active_esdl_project
from src.tno.undoredo.emits import emit_update_undo_redo_stack
from extensions.session_manager import set_project_manager, set_session

logger = log.get_logger(__name__)

def create_new_project_manager(client_id=None) -> ProjectManager:
    """
    Create a new ProjectManager and set it as the active ProjectManager. This will also initialize the change handlers
    for the new ProjectManager, send the new ProjectManager to the LMI and emit the active ESDL project to the frontend.
    """
    pm = ProjectManager()
    set_project_manager(pm, client_id=client_id)
    init_mapeditor_change_handlers(pm, client_id)
    set_session("es_info_list", {}, client_id=client_id)
    if has_request_context():
        send_project_manager_to_lmi_async(only_send_for_client_id=session['client_id'])

        can_emit = hasattr(request, 'namespace')
        if can_emit:
            emit_clear_frontend_esdls()
            emit_clear_ui()
            call_process_energy_system.submit()
            emit_active_esdl_project()
            emit_update_undo_redo_stack(pm.active_tracker.stack)
    return pm


def init_mapeditor_change_handlers(pm: ProjectManager, client_id):
    """
    Makes sure this ProjectManager has the correct listeners for changes attached to it
    """
    if not pm.has_change_listener(SESSION_MANAGER_LISTENER_ID):
        pm.add_change_listener(SESSION_MANAGER_LISTENER_ID, on_change_recorded)
        logger.debug("Init PM client_id={} with listener for ESDL changes for LMI".format(client_id))
    if not pm.has_change_listener(INCREMENTAL_UI_LISTENER_ID):
        pm.add_change_listener(INCREMENTAL_UI_LISTENER_ID, change_handler)
        logger.debug("Init PM client_id={} with UI listener for ESDL changes from LMI".format(client_id))


def on_change_recorded(change: HighLevelChange, change_context: ChangeContext):
    """
    This function is called when a change is recorded on the UndoRedoCommandStack by adding this function
    as call back function to the ProjectManager's change listeners (see get_project_manager()).
    It will serialize a high level change (see ESDLProject ecore model) to send to interested live models.

    It will only react on change_sources type INTERNAL

    Parameters
    ----------
    change A HighLevelChange to be send away

    """
    # only react on change_sources type INTERNAL
    if change_context.source != ChangeSource.INTERNAL:
        return

    pm = get_project_manager()
    # pm.rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)

    # options = {'encoder': DateTimeEncoder, 'indent': 2}
    options = {JsonOptions.INDENT: 2}
    hlc_string = eobject_to_string(change, ESDLFormat.JSON, options=options)
    logger.debug(f"Sending HighLevelChange: {hlc_string[:500]}")

    # uri = StringURI("high_level_change.json")
    # resource = pm.rset.create_resource(uri)
    # resource.append(hlc)
    # options = dict()
    # options['encoder'] = DateTimeEncoder
    # resource.save(options=options)
    # hlc_string = uri.getvalue()

    user_email = get_session("user-email")
    client_id = session["client_id"]
    message = HighLevelChangeMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        user_email=user_email,
        client_id=client_id,
        variant_id=pm.get_active_variant().id,
        high_level_change=hlc_string,
    )
    # logger.debug("Sending high level change on topic events.esdl.high_level_change")
    send_rabbitmq_message(message, "events.esdl.high_level_change")

