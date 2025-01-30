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

from flask import Flask, request, session
from flask_executor import Executor
from flask_socketio import SocketIO, emit

import src.log as log
from esdl.processing.string_uri import StringURI
from esdlproject import Variant
from esdlproject.ProjectManager import ProjectManager
from extensions.session_manager import set_session, get_project_manager, set_project_manager, managed_sessions
from src.process_es_area_bld import process_energy_system, call_process_energy_system
from src.tno.live_model_interface.api import send_add_variant_and_esdl_message_to_lmi, send_project_manager_to_lmi_async
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
                is_import = request.values.get("is_import", True)
                if is_import:
                    pm = get_project_manager()
                else:
                    pm = ProjectManager(create_empty_variant=False)

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

                        variant = self.add_esdl_to_project(pm, filename, esdl_str)
                        added_variants.append(variant)
                        #emit_active_esdl_project() # cant do emit here, because it is not socket io request

                last_variant = added_variants[-1]
                if last_variant is not None:
                    send_add_variant_and_esdl_message_to_lmi(last_variant)
                client_id = session["client_id"]
                # Now overwrite the project manager. We do this at the end to prevent the project manager from being
                # overwritten with an incomplete project manager in case of an error.
                if is_import:
                    send_project_manager_to_lmi_async(only_send_for_client_id=client_id)
                else:
                    set_project_manager(pm)
                    send_project_manager_to_lmi_async(only_send_for_client_id=client_id)
                return {'message': 'all ESDL(s) received'}, 201
            except Exception as e:
                logger.exception("Error processing ESDL file(s)", exception=e)
                return {'message': 'Error processing ESDL file(s): ' + str(e)}, 500


        @self.socketio.on("process_loaded_energysystems", namespace='/esdl')
        def process_loaded_energysystems():
            """
            The user has loaded one or more ESDL files. Process them.

            This endpoint really only exists so that we can emit to the frontend.
            """
            with self.flask_app.app_context():
                self.clear_mapeditor_ui()
                emit_active_esdl_project()
                call_process_energy_system.submit()

    def send_alert(self, message):
        logger.warning(message)
        # emit('alert', message, namespace='/esdl')

    def clear_mapeditor_ui(self):
        es_info_list = {}
        set_session("es_info_list", es_info_list)
        emit('clear_ui')
        emit('clear_esdl_layer_list')

    def add_esdl_to_project(self, pm, filename, file) -> Variant | None:
        try:
            uri = StringURI(filename, file)
            variant, parse_info = pm.add_energy_system(uri) #add_from_string(esdl_string=file, name=filename)
            if len(parse_info) > 0:
                info = ''
                for line in parse_info:
                    info += line + "\n"
                self.send_alert("Warnings while opening {}:\n\n{}".format(filename, info))
            return variant
        except Exception as e:
            logger.exception(f"Error opening {filename}")
            self.send_alert("Error opening {}. Exception is: {}".format(filename, e))
            raise e
