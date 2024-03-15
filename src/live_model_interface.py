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

from flask import session, request
from pika import BasicProperties
from pika.exchange_type import ExchangeType
from pika.spec import Basic

from threading import Thread

from pyecore.resources import ResourceSet

from esdl.processing.string_uri import StringURI
from extensions.session_manager import get_project_manager, get_project_manager_with_client_id, managed_sessions
from src.app import socketio
from src.log import get_logger
from src.tno.envsettings import EnvSettings
from src.tno.events.config import AMQP_URL
from src.tno.events.consumer import RabbitMQConsumerConfig, ReconnectingConsumer
from src.process_es_area_bld import call_process_energy_system

logger = get_logger(__name__)

# TODO: Find better way to get app here? import directly results in cyclic import error
local_app = None


def on_live_model_interface_message(channel, basic_deliver: Basic.Deliver, properties: BasicProperties, body):
    """
    The handler for all results message.
    """
    message = json.loads(body.decode("utf-8"))
    logger.debug("Result message received", message=message)
    del message["user_email"]
    client_id = message['client_id']

    uri = StringURI('hlc.json', message['high_level_change'])
    # user_email = msg['user_email']
    external_rset = ResourceSet()
    external_resource = external_rset.create_resource(uri)
    external_resource.load()
    hlc = external_resource.contents[0]

    pm = get_project_manager_with_client_id(client_id)
    es = pm.get_active_energy_system()
    tracker = pm.active_tracker
    tracker.stack.start_recording(label=hlc.label)
    for change in hlc.change:
        pm.processChange(change, es.eResource)
    tracker.stack.stop_recording(call_change_handler=False)

    global local_app

    # create request context (and session?)...
    with local_app.test_request_context():
        session['client_id'] = client_id
        request.sid = managed_sessions[client_id]['socketio_sid']
        request.namespace = '/esdl'

        # refresh the changes, now done by reparsing the whole energysystem... could be done smarter
        call_process_energy_system.submit(force_update_es_id=es.id, zoom=False)  # run in seperate thread


def start_live_model_interface_thread(app):
    global local_app
    local_app = app

    """Start the RabbitMQ thread."""
    logger.info("Starting RabbitMQ thread for events listener")
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
            queue="mapeditor.esdl",
            routing_key="mapeditor.esdl.#",
            on_message=on_live_model_interface_message,
        )

        consumer = ReconnectingConsumer(consumer_config)
        consumer.run()
