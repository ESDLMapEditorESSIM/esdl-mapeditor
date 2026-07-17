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
import json

from pika import BasicProperties
from pika.exchange_type import ExchangeType
from pika.spec import Basic

from threading import Thread

from src.app import socketio
from src.log import get_logger
from src import settings
from src.tno.envsettings import EnvSettings
from src.tno.live_model_interface.shared.config import AMQP_URL
from src.tno.live_model_interface.shared.consumer import RabbitMQConsumerConfig, ReconnectingConsumer

logger = get_logger(__name__)


def on_result_message(channel, basic_deliver: Basic.Deliver, properties: BasicProperties, body):
    """
    The handler for all results message.

    TODO: This was built for proof of concept. Do we still need it?
    """
    message = json.loads(body.decode("utf-8"))
    logger.debug("Result message received", message=message)
    if "user_email" in message:
        del message["user_email"]
    # TODO: Send message to only the user.
    exclude_sessions = []
    socketio.emit(
        "results.asset.positioning",
        message,
        skip_sid=exclude_sessions,
        namespace="/esdl",
    )


def start_rmq_thread():
    """Start the RabbitMQ thread."""
    if not settings.USE_RABBITMQ:
        logger.warning(
            "RabbitMQ disabled; skipping live_model_interface results listener",
            reason=settings.RABBITMQ_DISABLED_REASON,
        )
        return
    logger.info("Starting RabbitMQ thread for live_model_interface listener")
    thread = RMQThread()
    thread.start()


class RMQThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        consumer_config = RabbitMQConsumerConfig(
            amqp_url=AMQP_URL,
            exchange=EnvSettings.rabbitmq_exchange(),
            exchange_type=ExchangeType.topic,
            queue=EnvSettings.rabbitmq_queue(),
            routing_keys=["results.#"],
            on_start_consuming_callback=None,
            on_message=on_result_message,
            durable_queue=True,
        )

        consumer = ReconnectingConsumer(consumer_config)
        consumer.run()


# def setup_rabbitmq():
#     connection = pika.BlockingConnection(parameters=PIKA_CONNECTION_PARAMETERS)
#     channel = connection.channel()
#     channel.exchange_declare(exchange="mapeditor", exchange_type="topic")
#     result = channel.queue_declare("", auto_delete=True)
#     queue_name = result.method.queue
#     channel.queue_bind(
#         exchange="mapeditor", queue=queue_name, routing_key="mapeditor.frontend"
#     )
#     # logger.info("Emitting")
#     # socketio.emit("live_model_interface.frontend", {"data": "Hello"}, namespace="/esdl")
#     channel.basic_consume(queue=queue_name, on_message_callback=on_message)
#     return channel
#
#
# if __name__ == "__main__":
#     rabbitmq_channel = setup_rabbitmq()
#     try:
#         rabbitmq_channel.start_consuming()
#     except KeyboardInterrupt:
#         rabbitmq_channel.stop_consuming()
#         rabbitmq_channel.connection.close()
