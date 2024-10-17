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
from datetime import datetime, date

import json

from pika.exchange_type import ExchangeType

import src.log as log
import pika

from src.tno.envsettings import EnvSettings
from src.tno.live_model_interface.shared.config import PIKA_CONNECTION_PARAMETERS, RABBITMQ_APP_ID
from src.tno.live_model_interface.shared.message_types import LmiMessage
from utils.utils import timed

logger = log.get_logger(__name__)


# class RabbitMQPublisher(object):
#     """This is a publisher that will handle unexpected interactions
#     with RabbitMQ such as channel and connection closures.
#     If RabbitMQ closes the connection, it will reopen it. You should
#     look at the output, as there are limited reasons why the connection may
#     be closed, which usually are tied to permission related issues or
#     socket timeouts.
#     It uses delivery confirmations and illustrates one way to keep track of
#     messages that have been sent and if they've been confirmed by RabbitMQ.
#     """
#
#     EXCHANGE = EnvSettings.rabbitmq_fanout_exchange()
#     EXCHANGE_TYPE = ExchangeType.fanout
#     PUBLISH_INTERVAL = 1
#     QUEUE = EnvSettings.rabbitmq_queue()
#     ROUTING_KEY = ""
#     APP_ID = "mapeditor"
#
#     def __init__(self, amqp_url):
#         """Setup the example publisher object, passing in the URL we will use
#         to connect to RabbitMQ.
#         :param str amqp_url: The URL for connecting to RabbitMQ
#         """
#         self._connection = None
#         self._channel = None
#
#         self._deliveries = None
#         self._acked = None
#         self._nacked = None
#         self._message_number = None
#
#         self._stopping = False
#         self._url = amqp_url
#
#     def connect(self):
#         """This method connects to RabbitMQ, returning the connection handle.
#         When the connection is established, the on_connection_open method
#         will be invoked by pika.
#         :rtype: pika.SelectConnection
#         """
#         logger.info("Connecting", url=self._url)
#         return pika.SelectConnection(
#             pika.URLParameters(self._url),
#             on_open_callback=self.on_connection_open,
#             on_open_error_callback=self.on_connection_open_error,
#             on_close_callback=self.on_connection_closed,
#         )
#
#     def on_connection_open(self, _unused_connection):
#         """This method is called by pika once the connection to RabbitMQ has
#         been established. It passes the handle to the connection object in
#         case we need it, but in this case, we'll just mark it unused.
#         :param pika.SelectConnection _unused_connection: The connection
#         """
#         logger.info("Connection opened")
#         self.open_channel()
#
#     def on_connection_open_error(self, _unused_connection, err):
#         """This method is called by pika if the connection to RabbitMQ
#         can't be established.
#         :param pika.SelectConnection _unused_connection: The connection
#         :param Exception err: The error
#         """
#         logger.error("Connection open failed, reopening in 5 seconds", error=err)
#         self._connection.ioloop.call_later(5, self._connection.ioloop.stop)
#
#     def on_connection_closed(self, _unused_connection, reason):
#         """This method is invoked by pika when the connection to RabbitMQ is
#         closed unexpectedly. Since it is unexpected, we will reconnect to
#         RabbitMQ if it disconnects.
#         :param pika.connection.Connection connection: The closed connection obj
#         :param Exception reason: exception representing reason for loss of
#             connection.
#         """
#         self._channel = None
#         if self._stopping:
#             self._connection.ioloop.stop()
#         else:
#             logger.warning("Connection closed, reopening in 5 seconds", reason=reason)
#             self._connection.ioloop.call_later(5, self._connection.ioloop.stop)
#
#     def open_channel(self):
#         """This method will open a new channel with RabbitMQ by issuing the
#         Channel.Open RPC command. When RabbitMQ confirms the channel is open
#         by sending the Channel.OpenOK RPC reply, the on_channel_open method
#         will be invoked.
#         """
#         logger.info("Creating a new channel")
#         self._connection.channel(on_open_callback=self.on_channel_open)
#
#     def on_channel_open(self, channel):
#         """This method is invoked by pika when the channel has been opened.
#         The channel object is passed in so we can make use of it.
#         Since the channel is now open, we'll declare the exchange to use.
#         :param pika.channel.Channel channel: The channel object
#         """
#         logger.info("Channel opened")
#         self._channel = channel
#         self.add_on_channel_close_callback()
#         self.setup_exchange(self.EXCHANGE)
#
#     def add_on_channel_close_callback(self):
#         """This method tells pika to call the on_channel_closed method if
#         RabbitMQ unexpectedly closes the channel.
#         """
#         logger.info("Adding channel close callback")
#         self._channel.add_on_close_callback(self.on_channel_closed)
#
#     def on_channel_closed(self, channel, reason):
#         """Invoked by pika when RabbitMQ unexpectedly closes the channel.
#         Channels are usually closed if you attempt to do something that
#         violates the protocol, such as re-declare an exchange or queue with
#         different parameters. In this case, we'll close the connection
#         to shutdown the object.
#         :param pika.channel.Channel channel: The closed channel
#         :param Exception reason: why the channel was closed
#         """
#         logger.warning("Channel was closed", channel=channel, reason=reason)
#         self._channel = None
#         if not self._stopping:
#             self._connection.close()
#
#     def setup_exchange(self, exchange_name):
#         """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
#         command. When it is complete, the on_exchange_declareok method will
#         be invoked by pika.
#         :param str|unicode exchange_name: The name of the exchange to declare
#         """
#         logger.info("Declaring exchange", exchange=exchange_name)
#         # Note: using functools.partial is not required, it is demonstrating
#         # how arbitrary data can be passed to the callback when it is called
#         cb = functools.partial(self.on_exchange_declareok, userdata=exchange_name)
#         self._channel.exchange_declare(
#             exchange=exchange_name, exchange_type=self.EXCHANGE_TYPE, callback=cb
#         )
#
#     def on_exchange_declareok(self, _unused_frame, userdata):
#         """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
#         command.
#         :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
#         :param str|unicode userdata: Extra user data (exchange name)
#         """
#         logger.info("Exchange declared", exchange=userdata)
#         self.setup_queue(self.QUEUE)
#
#     def setup_queue(self, queue_name):
#         """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
#         command. When it is complete, the on_queue_declareok method will
#         be invoked by pika.
#         :param str|unicode queue_name: The name of the queue to declare.
#         """
#         logger.info("Declaring queue", queue=queue_name)
#         self._channel.queue_declare(queue=queue_name, callback=self.on_queue_declareok)
#
#     def on_queue_declareok(self, _unused_frame):
#         """Method invoked by pika when the Queue.Declare RPC call made in
#         setup_queue has completed. In this method we will bind the queue
#         and exchange together with the routing key by issuing the Queue.Bind
#         RPC command. When this command is complete, the on_bindok method will
#         be invoked by pika.
#         :param pika.frame.Method method_frame: The Queue.DeclareOk frame
#         """
#         logger.info(
#             "Binding queue",
#             exchnage=self.EXCHANGE,
#             queue=self.QUEUE,
#             routing_key=self.ROUTING_KEY,
#         )
#         self._channel.queue_bind(
#             self.QUEUE,
#             self.EXCHANGE,
#             routing_key=self.ROUTING_KEY,
#             callback=self.on_bindok,
#         )
#
#     def on_bindok(self, _unused_frame):
#         """This method is invoked by pika when it receives the Queue.BindOk
#         response from RabbitMQ. Since we know we're now setup and bound, it's
#         time to start publishing."""
#         logger.info("Queue bound")
#
#     def on_delivery_confirmation(self, method_frame):
#         """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
#         command, passing in either a Basic.Ack or Basic.Nack frame with
#         the delivery tag of the message that was published. The delivery tag
#         is an integer counter indicating the message number that was sent
#         on the channel via Basic.Publish. Here we're just doing house keeping
#         to keep track of stats and remove message numbers that we expect
#         a delivery confirmation of from the list used to keep track of messages
#         that are pending confirmation.
#         :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame
#         """
#         confirmation_type = method_frame.method.NAME.split(".")[1].lower()
#         ack_multiple = method_frame.method.multiple
#         delivery_tag = method_frame.method.delivery_tag
#
#         logger.info(
#             "Received for delivery tag",
#             confirmation_type=confirmation_type,
#             delivery_tag=delivery_tag,
#             ack_multiple=ack_multiple,
#         )
#
#         if confirmation_type == "ack":
#             self._acked += 1
#         elif confirmation_type == "nack":
#             self._nacked += 1
#
#         del self._deliveries[delivery_tag]
#
#         if ack_multiple:
#             for tmp_tag in list(self._deliveries.keys()):
#                 if tmp_tag <= delivery_tag:
#                     self._acked += 1
#                     del self._deliveries[tmp_tag]
#         """
#         NOTE: at some point you would check self._deliveries for stale
#         entries and decide to attempt re-delivery
#         """
#
#         logger.info(
#             "Published %i messages, %i have yet to be confirmed, "
#             "%i were acked and %i were nacked",
#             self._message_number,
#             len(self._deliveries),
#             self._acked,
#             self._nacked,
#         )
#
#     def publish_message(self, message):
#         """
#         If the class is not stopping, publish a message to RabbitMQ,
#         appending a list of deliveries with the message number that was sent.
#         This list will be used to check for delivery confirmations in the
#         on_delivery_confirmations method.
#         Once the message has been sent, schedule another message to be sent.
#         The main reason I put scheduling in was just so you can get a good idea
#         of how the process is flowing by slowing down and speeding up the
#         delivery intervals by changing the PUBLISH_INTERVAL constant in the
#         class.
#         """
#         if self._channel is None or not self._channel.is_open:
#             logger.warning("Attempting to send message but channel either None or not open", channel=self._channel)
#             return
#
#         properties = pika.BasicProperties(
#             app_id=self.APP_ID, content_type="application/json"
#         )
#
#         self._channel.basic_publish(
#             self.EXCHANGE,
#             self.ROUTING_KEY,
#             json.dumps(message, ensure_ascii=False),
#             properties,
#         )
#         self._message_number += 1
#         self._deliveries[self._message_number] = True
#         logger.info("Published message", nr=self._message_number)
#
#     def stop(self):
#         """Stop the example by closing the channel and connection. We
#         set a flag here so that we stop scheduling new messages to be
#         published. The IOLoop is started because this method is
#         invoked by the Try/Catch below when KeyboardInterrupt is caught.
#         Starting the IOLoop again will allow the publisher to cleanly
#         disconnect from RabbitMQ.
#         """
#         logger.info("Stopping")
#         self._stopping = True
#         self.close_channel()
#         self.close_connection()
#
#     def close_channel(self):
#         """Invoke this command to close the channel with RabbitMQ by sending
#         the Channel.Close RPC command.
#         """
#         if self._channel is not None:
#             logger.info("Closing the channel")
#             self._channel.close()
#
#     def close_connection(self):
#         """This method closes the connection to RabbitMQ."""
#         if self._connection is not None:
#             logger.info("Closing connection")
#             self._connection.close()
#
#
# AMQP_URL = f"amqp://{EnvSettings.rabbitmq_user()}:{EnvSettings.rabbitmq_password()}@localhost:5672/%2F?connection_attempts=3&heartbeat=3600"
# rabbitmq_fanout_publisher = RabbitMQPublisher(AMQP_URL)
# rabbitmq_fanout_publisher.connect()


def get_rabbitmq_topic_channel():
    """
    Connect to RabbitMQ and return the topic channel.
    """
    connection = pika.BlockingConnection(parameters=PIKA_CONNECTION_PARAMETERS)
    channel = connection.channel()
    # I suppose we don't need to do this every time we make a connection, but I don't think it's a big deal.
    channel.exchange_declare(
        exchange=EnvSettings.rabbitmq_exchange(),
        exchange_type=ExchangeType.topic,
        durable=True,
    )
    return channel


def _json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


@timed
def send_rabbitmq_message(message: LmiMessage, routing_key, delivery_mode=None):
    """
    Publish a message on the RabbitMQ exchange, so that all queues will receive it.

    Message is send as JSON.
    """
    channel = get_rabbitmq_topic_channel()
    body = json.dumps(message, default=_json_serializer).encode()
    properties = pika.BasicProperties(app_id=RABBITMQ_APP_ID, content_type='application/json')
    if delivery_mode:
        properties.delivery_mode = delivery_mode
    channel.basic_publish(
        exchange=EnvSettings.rabbitmq_exchange(),
        routing_key=routing_key,
        body=body,
        properties=properties,
    )
    channel.close()
