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

from extensions.data_manager import db
from src import settings
from src.log import get_logger

logger = get_logger(__name__)

class DataManager:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering DataManager extension')
        logger.info(f"Connecting to Data Manager database using: {settings.SQLALCHEMY_DATABASE_URI}")
        self.flask_app.config.update({
            "SQLALCHEMY_DATABASE_URI": settings.SQLALCHEMY_DATABASE_URI
        })
        db.init_app(self.flask_app)

        # init database

        @self.socketio.on('datamanager/query', namespace='/esdl')
        def socketio_duplicate(message):
            with self.flask_app.app_context():
                pass
