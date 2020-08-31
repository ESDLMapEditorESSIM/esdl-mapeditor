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

from flask import Flask
from flask_socketio import SocketIO
from flask_executor import Executor
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler
import src.log as log

logger = log.get_logger(__name__)

def send_alert(message):
    print(message)
    # emit('alert', message, namespace='/esdl')


class AppSettings:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.executor = executor

        self.register()

    def register(self):
        logger.info("Registering AppSettings extension")

        @self.socketio.on('app_settings', namespace='/esdl')
        def app_settings(prmtr):
            with self.flask_app.app_context():
                esh = get_handler()
                print(prmtr)