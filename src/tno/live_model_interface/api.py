import base64
import uuid
from datetime import datetime, timezone

from flask import session

from extensions.session_manager import get_project_manager, get_session
from src.tno.live_model_interface.shared.message_types import NewESDLMessage
from src.tno.live_model_interface.shared.publisher import send_rabbitmq_message


def send_new_esdl():
    """
    Send "new ESDL" message to the live model interface.
    :return:
    """
    pm = get_project_manager()

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
        b64_esdl=esdlstr_base64_str
    )

    send_rabbitmq_message(message, "events.esdl.new")


def send_pm_state():
    """

    :return:
    """
    pm = get_project_manager()

    esdlstr = pm.active_energy_system_to_string()
    esdlstr_bytes = esdlstr.encode('utf-8')
    esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
    esdlstr_base64_str = esdlstr_base64_bytes.decode('utf-8')

    user_email = get_session('user-email')
    client_id = session['client_id']
    message = NewESDLMessage(
        user_email=user_email,
        client_id=client_id,
        b64_esdl=esdlstr_base64_str
    )

    send_rabbitmq_message(message, "live_model_interface.esdl.new")
