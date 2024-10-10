import base64
import uuid
from datetime import datetime, timezone

from flask import session

from esdlproject.ProjectManager import ProjectManager
from extensions.session_manager import get_project_manager, get_session, managed_sessions, PM_KEY
from src.tno.live_model_interface.shared.message_types import NewESDLMessage, ProjectManagerMessage, \
    ActivateDeactivateLmiMessage
from src.tno.live_model_interface.shared.publisher import send_rabbitmq_message

LAST_PM_REFRESH_SENT: datetime | None = None
"""The last time we sent a project manager refresh. This is used to prevent sending a PM refresh for an old message."""


def send_new_esdl_to_lmi():
    """
    Send "new ESDL" message to the live model interface.
    :return:
    """
    pm = get_project_manager()
    active_variant = pm.get_active_variant()
    esdlstr = pm.active_energy_system_to_string()
    esdlstr_bytes = esdlstr.encode('utf-8')
    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
    esdlstr_base64_str = esdlstr_base64_bytes.decode('utf-8')

    user_email = get_session('user-email')
    client_id = session['client_id']
    message = NewESDLMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        user_email=user_email,
        client_id=client_id,
        b64_esdl=esdlstr_base64_str,
        variant_id=active_variant.id
    )

    send_rabbitmq_message(message, "events.esdl.new")


def send_project_manager_to_lmi(only_send_for_client_id: str | None = None):
    """
    Send project managers for all users, or only for the provided users.

    :param only_send_for_client_id: If provided, only send the project manager for this client id.
    """
    global LAST_PM_REFRESH_SENT
    for client_id, session_data in managed_sessions.items():
        if only_send_for_client_id is not None and client_id != only_send_for_client_id:
            continue
        pm: ProjectManager | None = session_data.get(PM_KEY)
        if pm is None:
            continue
        project = pm.project
        project_as_string = pm.save()
        base64_file = base64.b64encode(project_as_string.encode()).decode()
        message = ProjectManagerMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            user_email=None,
            client_id=client_id,
            b64_project=base64_file,
            project_name=project.name,
        )
        send_rabbitmq_message(message, "events.pm")
    LAST_PM_REFRESH_SENT = datetime.now(timezone.utc)


def activate_live_model_interface(lmi_id: str, client_id: str):
    """
    Activate the live model interface with the given id for the given user.
    :param lmi_id:
    :param client_id:
    :return:
    """
    message = ActivateDeactivateLmiMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        client_id=client_id,
        user_email=None,
        lmi_id=lmi_id,
        activate=True
    )
    send_rabbitmq_message(message, f"{lmi_id}.activation")


def deactivate_live_model_interface(lmi_id: str, client_id: str):
    """
    Activate the live model interface with the given id for the given user.
    :param lmi_id:
    :param client_id:
    :return:
    """
    message = ActivateDeactivateLmiMessage(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        client_id=client_id,
        user_email=None,
        lmi_id=lmi_id,
        activate=False
    )
    send_rabbitmq_message(message, f"{lmi_id}.activation")
