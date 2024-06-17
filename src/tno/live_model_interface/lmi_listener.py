#  This work is based on original code developed and copyrighted by TNO 2023.
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
import json
import uuid
from datetime import datetime, timezone

from flask import session, request
from pika import BasicProperties
from pika.exchange_type import ExchangeType
from pika.spec import Basic

from threading import Thread

from pyecore.resources import ResourceSet

from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonResource
from esdlproject.ProjectManager import ProjectManager
from esdlproject.change_handler import applyChange
from extensions.session_manager import get_project_manager_with_client_id, managed_sessions, PM_KEY
from src.log import get_logger
from src.tno.envsettings import EnvSettings
from src.tno.live_model_interface.shared.config import AMQP_URL, RABBITMQ_APP_ID
from src.tno.live_model_interface.shared.consumer import RabbitMQConsumerConfig, ReconnectingConsumer
from src.process_es_area_bld import call_process_energy_system
from src.tno.live_model_interface.shared.message_types import HighLevelChangeMessage, LmiMessage, NewESDLMessage, \
    ProjectManagerMessage
from src.tno.live_model_interface.shared.publisher import send_rabbitmq_message

logger = get_logger(__name__)

# TODO: Find better way to get app here? import directly results in cyclic import error
local_app = None

LAST_PM_REFRESH_SENT: datetime | None = None
"""The last time we sent a project manager refresh. This is used to prevent sending a PM refresh for an old message."""


def on_high_level_change(message: HighLevelChangeMessage):
    """
    Handle a high level change message from the live model interface.
    """
    logger.debug("High level change received", message=message)
    client_id = message['client_id']

    uri = StringURI('hlc.json', message['high_level_change'])
    logger.info(f"Received HighLevelChange from Live model: {message['high_level_change']}")
    external_rset = ResourceSet()
    external_rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)
    external_resource = external_rset.create_resource(uri)
    external_resource.load()
    hlc = external_resource.contents[0]
    try:
        pm = get_project_manager_with_client_id(client_id)
    except KeyError as e:
        logger.warn(f"Ignoring received message due to: {str(e)}")
        return
    es = pm.get_active_energy_system()
    tracker = pm.active_tracker
    tracker.stack.start_recording(label=hlc.label)
    for change in hlc.change:
        applyChange(change, es.eResource)
    tracker.stack.stop_recording(call_change_handler=False)

    global local_app

    # create request context (and session?)...
    with local_app.test_request_context():
        session['client_id'] = client_id
        request.sid = managed_sessions[client_id]['socketio_sid']
        request.namespace = '/esdl'

        # refresh the changes, now done by reparsing the whole energysystem... could be done smarter
        call_process_energy_system.submit(force_update_es_id=es.id, zoom=False)  # run in seperate thread


def on_pm_refresh_request(message: LmiMessage):
    """
    Handle an Project Manager refresh request from the live model interface.
    :param message:
    :return:
    """
    global LAST_PM_REFRESH_SENT
    timestamp = message['timestamp']
    if LAST_PM_REFRESH_SENT is not None and LAST_PM_REFRESH_SENT >= timestamp:
        logger.info("Ignoring PM refresh request, because the last refresh was already sent.")
        return
    sessions = managed_sessions
    for client_id, session_data in sessions.items():
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


message_handlers = {
    "lmi.esdl.high_level_change": on_high_level_change,
    "lmi.pm.refresh": on_pm_refresh_request,
}


def on_live_model_interface_message(channel, basic_deliver: Basic.Deliver, properties: BasicProperties, body):
    """
    The handler for all results message. This function will be called when a message is received from the RabbitMQ
    queue. The message will be parsed and the result will be sent to the client.

    We should avoid unhandled exceptions, because RabbitMQ will keep retrying to deliver the message, causing an
    infinite loop of exceptions.
    """
    try:
        if properties.app_id == RABBITMQ_APP_ID:
            logger.debug("Ignoring message from myself")
            return
        # Get the routing key.
        routing_key = basic_deliver.routing_key
        logger.info(
            "Received message",
            delivery_tag=basic_deliver.delivery_tag,
            routing_key=routing_key,
            app_id=properties.app_id,
            body=body[:150],
        )
        message = json.loads(body.decode("utf-8"))

        # Call the appropriate message handler.
        if routing_key in message_handlers:
            message_handlers[routing_key](message)
        else:
            logger.warn(f"No handler found for message with routing key {routing_key}")
    except Exception:
        logger.exception("Failed to process live model interface message")


def start_live_model_interface_thread(app):
    global local_app
    local_app = app

    """Start the RabbitMQ thread."""
    logger.info("Starting RabbitMQ thread for live_model_interface listener")
    thread = LiveModelInterfaceThread()
    thread.start()


class LiveModelInterfaceThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        consumer_config = RabbitMQConsumerConfig(
            amqp_url=AMQP_URL,
            exchange=EnvSettings.rabbitmq_exchange(),
            exchange_type=ExchangeType.topic,
            queue=EnvSettings.rabbitmq_queue(),
            routing_keys=["lmi.#"],
            on_message=on_live_model_interface_message,
        )

        consumer = ReconnectingConsumer(consumer_config)
        consumer.run()
