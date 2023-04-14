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

from extensions.session_manager import get_session
import src.log as log
from flask import Flask

from extensions.settings_storage import SettingsStorage
from src.tno.events.messages import AssetPositionMessage, Point

from src.tno.events.publisher import send_rabbitmq_message

logger = log.get_logger(__name__)


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

        @self.socketio.on("events.asset.positioning", namespace="/esdl")
        def mouse_positioning(frontend_message: MousePositionMessage):
            logger.info("Positioning asset", message=frontend_message)
            user_email = get_session('user-email')
            message: AssetPositionMessage = dict(**frontend_message, user_email=user_email)
            # rabbitmq_fanout_publisher.publish_message(message)
            send_rabbitmq_message(message, "events.asset.positioning")
