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
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler
from xmldiff import main
import src.log as log

logger = log.get_logger(__name__)


class ESDLCompare:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self):
        logger.info('Registering ESDL Compare extension')

        @self.socketio.on('esdl_compare', namespace='/esdl')
        def compare(esdls):
            with self.flask_app.app_context():
                esh = get_handler()

                es_id1 = esdls['esdl1']
                es_id2 = esdls['esdl2']

                es1_str = esh.to_string(es_id1).encode()    # convert string to bytes
                es2_str = esh.to_string(es_id2).encode()    # convert string to bytes

                logger.info("Comparing EnergySystems with id {} and {}".format(es_id1, es_id2))
                results = main.diff_texts(es1_str, es2_str)

                emit('esdl_compare_window', results, namespace='/esdl')
