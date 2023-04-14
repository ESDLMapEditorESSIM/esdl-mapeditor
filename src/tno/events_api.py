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
from typing import TypedDict

from flask_socketio import SocketIO

import src.log as log
from flask import Flask

from extensions.settings_storage import SettingsStorage

from src.tno.events.publisher import send_rabbitmq_fanout_message

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
            # rabbitmq_fanout_publisher.publish_message(message)
            send_rabbitmq_fanout_message(message)
