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
import json
import uuid
from datetime import datetime, timezone
from threading import Thread

from flask import Flask
from pika import BasicProperties
from pika.exchange_type import ExchangeType
from pika.spec import Basic
from pyecore.resources import ResourceSet

from esdl.processing.string_uri import StringURI
from esdl.resources.json import JsonResource
from esdl.undo import ChangeSource, ChangeContext
from esdl.project.change_handler import applyChange
from esdl.project.variant_api import create_new_variant
from extensions.session_manager import get_project_manager_for_client_id, managed_sessions
from src.log import get_logger
from src import settings
from src.tno.envsettings import EnvSettings
from src.tno.live_model_interface.api import activate_live_model_interface, send_project_manager_to_lmi
from src.tno.live_model_interface.shared.config import AMQP_URL, RABBITMQ_APP_ID
from src.tno.live_model_interface.shared.consumer import RabbitMQConsumerConfig, ReconnectingConsumer
from src.tno.live_model_interface.shared.message_types import HighLevelChangeMessage, LmiMessage, NewVariantMessage
from src.tno.live_model_interface.shared.publisher import send_rabbitmq_message
from src.tno.mongo.models import ApplicationContext

logger = get_logger(__name__)

# TODO: Find better way to get app here? import directly results in cyclic import error
LOCAL_APP = None

LMI_THREAD: Thread | None = None

LAST_PM_REFRESH_SENT: datetime | None = None
"""The last time we sent a project manager refresh. This is used to prevent sending a PM refresh for an old message."""

LMI_THREAD_LAST_HEALTH_CHECKED: datetime = datetime.now(timezone.utc)


def on_high_level_change(message: HighLevelChangeMessage):
    """
    Handle a high level change message from the live model interface.
    """
    logger.debug("High level change received")
    client_id = message['client_id']

    uri = StringURI('hlc.json', message['high_level_change'])
    logger.info(f"Received HighLevelChange from Live model: {message['high_level_change'][:500]}")
    external_rset = ResourceSet()
    external_rset.resource_factory['json'] = lambda uri: JsonResource(uri, indent=2)
    external_resource = external_rset.create_resource(uri)
    external_resource.load()
    hlc = external_resource.contents[0]
    try:
        pm = get_project_manager_for_client_id(client_id)
    except KeyError as e:
        logger.warn(f"Ignoring received message due to: {str(e)}")
        return

    variant_id = message['variant_id']
    variant = pm.get_variant_by_id(variant_id)
    es = pm.get_energy_system(variant)

    # TODO: make sure we only apply changes when process energy system is not in progress
    # otherwise it might be in a non final stage when these changes are added to the energy system
    # lock = get_session("process_energysystem_lock")
    # if lock is None:
    #     lock = Lock()
    #     set_session("process_energysystem_lock", lock)
    # logger.info(f"Acquiring lock {current_thread()}, locked={lock.locked()}")
    # lock.acquire(timeout=10.0)
    # logger.info(f"Lock acquired, processing {current_thread()}")
    #tracker = pm.active_tracker
    global LOCAL_APP

    tracker = pm.get_change_tracker_for_variant(variant)
    # add more context to the changes received, for the incremental UI updates
    context = ChangeContext(source=ChangeSource.EXTERNAL, client_id=client_id, resource=es.eResource)
    with LOCAL_APP.app_context(), tracker.stack.track_changes(label=hlc.label, change_context=context):
        for change in hlc.change:
            applyChange(change, es.eResource, variant, pm.conflict_handler)
    #lock.release()
    #logger.info(f"Lock released by {current_thread()}")


    # create request context (and session?)...
    # with local_app.test_request_context():
    #     session['client_id'] = client_id
    #     request.sid = managed_sessions[client_id]['socketio_sid']
    #     request.namespace = '/esdl'
    #
    #     # refresh the changes, now done by reparsing the whole energysystem... could be done smarter
    #     call_process_energy_system.submit(force_update_es_id=es.id, zoom=False)  # run in seperate thread


def on_pm_refresh_request(message: LmiMessage):
    """
    Handle a Project Manager refresh request from the live model interface. This sends all project managers to the
    live model interface, as well as the currently active LMI's per client.
    :param message:
    :return:
    """
    global LAST_PM_REFRESH_SENT

    only_send_for_client_id = message.get("client_id")
    if only_send_for_client_id:
        send_project_manager_to_lmi(only_send_for_client_id=only_send_for_client_id)
    else:
        timestamp = message['timestamp']
        if isinstance(timestamp, str):
            # Parse the timestamp from string to datetime.
            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")
        if LAST_PM_REFRESH_SENT is not None and LAST_PM_REFRESH_SENT >= timestamp:
            logger.info("Ignoring PM refresh request, because the last refresh was already sent.")
            return
        send_project_manager_to_lmi()
        LAST_PM_REFRESH_SENT = datetime.now(timezone.utc)

    # Also send the currently active LMI's, if any.
    for client_id, session_data in managed_sessions.items():
        if only_send_for_client_id is not None and client_id != only_send_for_client_id:
            continue
        active_application_context: ApplicationContext | None = session_data.get("application_context")
        if active_application_context is not None:
            for lmi in active_application_context.get("live_model_interfaces", []):
                activate_live_model_interface(lmi["lmi_id"], client_id)


def on_new_variant(message: NewVariantMessage):
    """
    Handle a new variant message from the live model interface.
    :param message:
    :return:
    """
    client_id = message['client_id']
    variant_id = message['variant_id']
    variant_name = message['variant_name']
    try:
        pm = get_project_manager_for_client_id(client_id)
    except KeyError as e:
        logger.warn(f"Ignoring received message due to: {str(e)}")
        return
    existing_variant = pm.get_variant_by_id(variant_id)
    if existing_variant is not None:
        logger.info(f"Ignoring new variant message, because the variant already exists.")
        return

    parent_variant_id = message['parent_variant_id']
    parent_variant = pm.get_variant_by_id(parent_variant_id)
    if parent_variant is None:
        logger.warn(f"Parent variant not found. Are we out of sync?", parent_variant_id)
        return
    create_new_variant(parent_variant, variant_name=variant_name, variant_id=variant_id)


message_handlers = {
    "lmi.esdl.high_level_change": on_high_level_change,
    "lmi.pm.refresh": on_pm_refresh_request,
    "events.variant.new": on_new_variant,
}


def on_live_model_interface_message(channel, basic_deliver: Basic.Deliver, properties: BasicProperties, body):
    """
    The handler for all results message. This function will be called when a message is received from the RabbitMQ
    queue. The message will be parsed and the result will be sent to the client.

    We should avoid unhandled exceptions, because RabbitMQ will keep retrying to deliver the message, causing an
    infinite loop of exceptions.
    """
    try:
        # Get the routing key.
        routing_key = basic_deliver.routing_key
        log = logger.bind(delivery_tag=basic_deliver.delivery_tag, app_id=properties.app_id, routing_key=routing_key)
        if properties.app_id == RABBITMQ_APP_ID:
            log.debug("Ignoring message from myself")
            return

        log.info(
            "Received message",
            body=body[:150],
        )
        message = json.loads(body.decode("utf-8"))

        # Call the appropriate message handler.
        handler = message_handlers.get(routing_key)
        if handler:
            handler(message)
        else:
            log.warn(f"No handler found for message with routing key")
    except Exception:
        logger.exception("Failed to process live model interface message")


def start_live_model_interface_thread(app: Flask):
    """Start the RabbitMQ thread."""
    global LMI_THREAD
    global LOCAL_APP
    if not settings.USE_RABBITMQ:
        logger.warning("RabbitMQ disabled; skipping LMI listener thread", reason=settings.RABBITMQ_DISABLED_REASON)
        return
    # Initialize the local_app variable so we have access to the app context in the thread.
    LOCAL_APP = app

    logger.info("Starting RabbitMQ thread for lmi_listener")
    LMI_THREAD = LiveModelInterfaceThread()
    LMI_THREAD.start()
    # Send clear project manager message, to indicate live model interfaces can clear their project managers.
    clear_pm_message = dict(id=str(uuid.uuid4()), timestamp=datetime.now(timezone.utc), client_id=None, user_email=None)
    send_rabbitmq_message(clear_pm_message, "events.pm.clear")


def is_lmi_thread_alive() -> True:
    """Check if the LiveModelInterfaceThread is dead."""
    global LMI_THREAD
    global LMI_THREAD_LAST_HEALTH_CHECKED

    if not settings.USE_RABBITMQ:
        return True

    now = datetime.now(timezone.utc)
    if (now - LMI_THREAD_LAST_HEALTH_CHECKED).total_seconds() > 60:
        LMI_THREAD_LAST_HEALTH_CHECKED = now
        logger.info("Checking if LMI thread is alive")

        if LMI_THREAD is None:
            logger.warning("LMI thread has not been started")
            return False

        if not LMI_THREAD.is_alive():
            logger.warning("LMI thread is dead")
            return False

    return True


class LiveModelInterfaceThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            logger.info("Starting RabbitMQ consumer for lmi_listener")
            try:
                consumer_config = RabbitMQConsumerConfig(
                    amqp_url=AMQP_URL,
                    exchange=EnvSettings.rabbitmq_exchange(),
                    exchange_type=ExchangeType.topic,
                    queue=EnvSettings.rabbitmq_queue(),
                    routing_keys=["lmi.#"],
                    on_start_consuming_callback=None,
                    on_message=on_live_model_interface_message,
                    durable_queue=True,
                )

                consumer = ReconnectingConsumer(consumer_config)
                consumer.run()
            except Exception:
                logger.exception("RabbitMQ consumer died unexexpectedly")
