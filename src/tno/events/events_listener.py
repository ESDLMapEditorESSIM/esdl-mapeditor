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
from dataclasses import dataclass

from threading import Thread
from socketio.kombu_manager import KombuManager


from src import get_logger

from src.tno.events.config import AMQP_URL
from src.tno.events.consumer import ReconnectingConsumer

external_sio = KombuManager(AMQP_URL, write_only=True)

logger = get_logger(__name__)


def on_message(channel, method_frame, header_frame, body, app=None):
    message = body.decode("utf-8")
    logger.info("I HAVE THE MSG", message=message)
    exclude_sessions = []
    external_sio.emit("events.frontend", {"data": message}, skip_sid=exclude_sessions, namespace='/esdl')


# def start(app):
#     # app.app_context().push()
#     amqp_url = f"amqp://{EnvSettings.rabbitmq_user()}:{EnvSettings.rabbitmq_password()}@{EnvSettings.rabbitmq_host()}:{EnvSettings.rabbitmq_port()}/%2F"
#     consumer = ReconnectingConsumer(AMQP_URL, on_message)
#     consumer.run()
#
#
# def start_rmq_thread(app):
#     t = threading.Thread(target=start, daemon=True, args=(app,))
#     t.start()


def start_rmq_thread():
    """Start the RabbitMQ thread."""
    logger.info("Starting RabbitMQ thread for events listener")
    thread = RMQThread()
    thread.start()


class RMQThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        consumer = ReconnectingConsumer(AMQP_URL, on_message)
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
#     # socketio.emit("events.frontend", {"data": "Hello"}, namespace="/esdl")
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
