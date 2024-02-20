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
import base64
from datetime import datetime
from typing import List

from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_executor import Executor

from esdl.processing.string_uri import StringURI
from esdlproject import Variant
from extensions.session_manager import set_session, get_project_manager
import src.log as log
from src.process_es_area_bld import process_energy_system
from src.tno.projects.emits import emit_active_esdl_project

logger = log.get_logger(__name__)


class ESDLFileIO:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()
        self.executor = executor

    def register(self):
        logger.info('Registering ESDL File I/O extension')

        @self.flask_app.route("/esdl_file_io", methods=['POST'])
        def esdl_file_io():
            #with self.flask_app.request_context():
            # first remove active variants
            self.clear_current_loaded_variants()
            # len(request.values) seems to be a multiple of 2
            for i in range(int(len(request.values)/2)):
                base64_file_contents = request.values.get(f'file_info[{i}][file]')
                # base64_file_contents now contains something like
                # "data:application/octet-stream;base64,PD94bWwgdmVyc..."
                # Only take the part after the comma
                base64_file_contents = base64_file_contents.split(',')[1]
                filename = request.values.get(f'file_info[{i}][filename]')

                if base64_file_contents:
                    esdlstr_base64_bytes = base64_file_contents.encode('utf-8')
                    esdlstr_bytes = base64.b64decode(esdlstr_base64_bytes)
                    esdl_str = esdlstr_bytes.decode('utf-8')

                    self.add_esdl_to_project(filename, esdl_str)
                    #emit_active_esdl_project() # cant do emit here, because it is not socket io request

            return {'message': 'all ESDL(s) received'}, 201

        @self.socketio.on("process_loaded_energysystems", namespace='/esdl')
        def process_loaded_energysystems():
            with self.flask_app.app_context():
                self.clear_mapeditor_ui()
                emit_active_esdl_project()
                self.executor.submit(self.call_process_energy_system)  # run in seperate thread

    def send_alert(self, message):
        logger.warning(message)
        # emit('alert', message, namespace='/esdl')

    def clear_mapeditor_ui(self):
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')

    def clear_current_loaded_variants(self):
        pm = get_project_manager()
        for vc in list(pm.project.variantCollection):
            variants: List[Variant] = []
            pm.get_variant_list(vc.variant, variants)
            for v in variants:
                es = pm.get_variant_snapshot(v)
                stack = pm.get_undo_redo_stack(es)
                if stack.lastChanged > datetime.min:
                    # warn for unsaved changes
                    self.send_alert(f"{v.name} contains unsaved changes")
                    return

                pm.delete_variant(v)
            #pm.delete_variant(vc)

    def add_esdl_to_project(self, filename, file):
        pm = get_project_manager()

        try:
            uri = StringURI(filename, file)
            variant, parse_info = pm.add_energy_system(uri) #add_from_string(esdl_string=file, name=filename)
            pm.set_active_variant(variant)
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                self.send_alert("Warnings while opening {}:\n\n{}".format(filename, info))
        except Exception as e:
            logger.exception(f"Error opening {filename}")
            self.send_alert("Error opening {}. Exception is: {}".format(filename, e))

    @staticmethod
    def call_process_energy_system():
        process_energy_system(force_update_es_id=None, zoom=True)
