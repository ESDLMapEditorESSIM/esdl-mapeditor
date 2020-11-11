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
from flask_executor import Executor
from flask_socketio import SocketIO, emit
from extensions.session_manager import get_handler
import src.log as log
from src.merge import ESDLMerger
from src.process_es_area_bld import process_energy_system

logger = log.get_logger(__name__)


class ESDLMerge:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.merger = ESDLMerger()
        self.register()

    def register(self):
        logger.info('Registering ESDL Merge extension')

        @self.socketio.on('esdl_merge', namespace='/esdl')
        def merge(message):
            with self.flask_app.app_context():
                esh = get_handler()

                esdl_source_id = message['esdl_source_id']
                esdl_destination_id = message['esdl_destination_id']

                es_source = esh.get_energy_system(es_id=esdl_source_id)
                es_destination = esh.get_energy_system(es_id=esdl_destination_id)

                logger.info("Merging EnergySystem with id {} into EnergySystem with id {}".format(esdl_source_id,
                                                                                                  esdl_destination_id))

                self.merger.merge(es_destination, es_source)
                self.executor.submit(process_energy_system, esh=esh, filename=None,
                                     force_update_es_id=esdl_destination_id)
