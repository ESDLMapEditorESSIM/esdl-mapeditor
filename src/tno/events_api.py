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

import pika
from typing import TypedDict

from flask_socketio import SocketIO

import src.log as log
from flask import Flask

from extensions.settings_storage import SettingsStorage
from src.tno.envsettings import EnvSettings

from src.tno.events.publisher import rabbitmq_publisher

logger = log.get_logger(__name__)


class Point(TypedDict):
    lat: float
    lng: float


class MousePositionMessage(TypedDict):
    point: Point


class EventsAPI:
    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info("Registering EventsAPI")

        @self.socketio.on("events.mouse.positioning", namespace="/esdl")
        def mouse_positioning(message: MousePositionMessage):
            logger.info("Positioning mouse", message=message)
            # rabbitmq_publisher.publish_message(message)
            pika_credentials = pika.PlainCredentials(EnvSettings.rabbitmq_user(), EnvSettings.rabbitmq_password())
            pika_connection_parameters = pika.ConnectionParameters(credentials=pika_credentials)
            connection = pika.BlockingConnection(parameters=pika_connection_parameters)
            channel = connection.channel()
            channel.queue_declare(queue=EnvSettings.rabbitmq_queue())
            channel.basic_publish(exchange="", routing_key=EnvSettings.rabbitmq_queue(), body=json.dumps(message))
