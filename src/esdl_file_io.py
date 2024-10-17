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
from datetime import datetime, timezone
from typing import List

from flask import Flask, request
from flask_executor import Executor
from flask_socketio import SocketIO, emit

import src.log as log
from esdl.processing.string_uri import StringURI
from esdlproject import Variant
from extensions.session_manager import set_session, get_project_manager
from src.process_es_area_bld import process_energy_system
from src.tno.live_model_interface.api import send_add_variant_and_esdl_message_to_lmi
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
            try:
                #with self.flask_app.request_context():
                # len(request.values) seems to be a multiple of 2
                added_variants = []
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

                        variant = self.add_esdl_to_project(filename, esdl_str)
                        added_variants.append(variant)
                        #emit_active_esdl_project() # cant do emit here, because it is not socket io request
                # Now clear current loaded variants. We do this at the end to not destroy the current project if something goes wrong.
                self.clear_current_loaded_variants(exclude_variant_ids=[v.id for v in added_variants])
                # TODO send clear loaded variants message to LMI
                return {'message': 'all ESDL(s) received'}, 201
            except Exception:
                logger.exception("Error processing ESDL file(s)")
                return {'message': 'Error processing ESDL file(s)'}, 500


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

    def clear_current_loaded_variants(self, exclude_variant_ids: list[str] = None):
        if exclude_variant_ids is None:
            exclude_variant_ids = []
        pm = get_project_manager()
        for vc in list(pm.project.variantCollection):
            variants: list[Variant] = []
            pm.get_variant_list(vc.variant, variants)
            variants.reverse()  # go from tail to root
            for v in variants:
                if v.id in exclude_variant_ids:
                    continue
                es = pm.get_variant_snapshot(v)
                if es is not None: # no snapshot yet available
                    stack = pm.get_undo_redo_stack(es)
                    if stack.last_changed > datetime.min.replace(tzinfo=timezone.utc):
                        # warn for unsaved changes
                        self.send_alert(f"{v.name} contains unsaved changes")
                        return

                pm.delete_variant(v)
            #pm.delete_variant(vc)

    def add_esdl_to_project(self, filename, file) -> Variant | None:
        pm = get_project_manager()

        try:
            uri = StringURI(filename, file)
            variant, parse_info = pm.add_energy_system(uri) #add_from_string(esdl_string=file, name=filename)
            pm.set_active_variant(variant)
            send_add_variant_and_esdl_message_to_lmi(variant)
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                self.send_alert("Warnings while opening {}:\n\n{}".format(filename, info))
            return variant
        except Exception as e:
            logger.exception(f"Error opening {filename}")
            self.send_alert("Error opening {}. Exception is: {}".format(filename, e))
            return None

    @staticmethod
    def call_process_energy_system():
        process_energy_system(force_update_es_id=None, zoom=True)
