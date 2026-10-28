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
import traceback

from flask import Flask, request, session
from flask_executor import Executor
from flask_socketio import SocketIO, emit

import src.log as log
from esdl.processing.string_uri import StringURI
from esdl.project import Variant
from esdl.project.ProjectManager import ProjectManager, load_external_string
from extensions.prompt_manager import PromptManager
from extensions.session_manager import set_session, get_project_manager, set_project_manager, del_session, get_session
from src.process_es_area_bld import call_process_energy_system
from src.tno.live_model_interface.api import send_add_variant_and_esdl_message_to_lmi, send_project_manager_to_lmi_async
from src.tno.projects.core import init_mapeditor_change_handlers
from src.tno.projects.emits import emit_active_esdl_project
from src.tno.projects.duplicate_detection import (
    DuplicateChoice,
    DuplicatePrompt,
    find_duplicate_variant_collection,
    generate_renamed_esdl_string,
    next_available_name,
)

logger = log.get_logger(__name__)

ESDL_DUPLICATE_IMPORT_FILE = "esdl_duplicate_import_file"


def add_esdl_to_project(pm, filename, file) -> Variant | None:
    try:
        uri = StringURI(filename, file)
        variant, parse_info = pm.add_energy_system(uri)
        if len(parse_info) > 0:
            info = ""
            for line in parse_info:
                info += line + "\n"
            logger.warning("Warnings while opening {}:\n\n{}".format(filename, info))
        return variant
    except Exception as e:
        logger.exception(f"Error opening {filename}")
        logger.warning("Error opening {}. Exception is: {}".format(filename, e))
        raise e


def clear_mapeditor_ui():
    del_session("shape_dictionary")
    del_session("conn_list")
    del_session("asset_list")
    del_session("building_list")
    del_session("area_bld_list")

    es_info_list = {}
    set_session("es_info_list", es_info_list)
    emit('clear_ui')
    emit('clear_esdl_layer_list')


def handle_esdl_duplicate_import_file(choice_key: str, context: dict):
    """Apply user choice for duplicate file-import prompts."""
    pm = get_project_manager()
    files = context.get("files", [])
    conflict_index = context.get("conflict_index")

    if choice_key == DuplicateChoice.CANCEL:
        return

    if conflict_index is None or conflict_index >= len(files):
        logger.warning("Invalid conflict index in prompt context")
        return

    conflict_file = files[conflict_index]
    conflict_filename = conflict_file["filename"]
    conflict_esdl_string = conflict_file["esdl_string"]
    temp_es, _ = load_external_string(esdl_string=conflict_esdl_string, name=conflict_filename)

    if choice_key == DuplicateChoice.OVERWRITE:
        duplicate_vc, _, _, _ = find_duplicate_variant_collection(pm, temp_es.id, temp_es.name)
        if duplicate_vc:
            pm.delete_variant(duplicate_vc)
    elif choice_key == DuplicateChoice.RENAME:
        new_name = next_available_name(pm, temp_es.name)
        conflict_file["esdl_string"] = generate_renamed_esdl_string(
            conflict_esdl_string,
            conflict_filename,
            new_name=new_name,
        )

    added_variants = []
    for entry in files:
        variant = add_esdl_to_project(pm, entry["filename"], entry["esdl_string"])
        added_variants.append(variant)

    last_variant = added_variants[-1] if added_variants else None
    if last_variant is not None:
        pm.set_active_variant(last_variant)
        send_add_variant_and_esdl_message_to_lmi(last_variant)

    send_project_manager_to_lmi_async(only_send_for_client_id=context.get("client_id"))
    clear_mapeditor_ui()
    emit_active_esdl_project()
    call_process_energy_system.submit()


PromptManager.register_handler(ESDL_DUPLICATE_IMPORT_FILE, handle_esdl_duplicate_import_file)


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
                with self.flask_app.app_context():
                    # Set max to 20 MB.
                    request.max_form_memory_size = 20 * 1024 * 1024
                    is_import = request.values.get("is_import", 'true') == 'true'
                    if is_import:
                        pm = get_project_manager()
                    else:
                        pm = ProjectManager(create_empty_variant=False)

                    added_variants = []
                    files = []
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
                            files.append({"filename": filename, "esdl_string": esdl_str})

                    if is_import:
                        for idx, entry in enumerate(files):
                            temp_es, parse_info = load_external_string(
                                esdl_string=entry["esdl_string"], name=entry["filename"]
                            )
                            duplicate_vc, match_id, match_name, matched_es = find_duplicate_variant_collection(
                                pm, temp_es.id, temp_es.name
                            )
                            if duplicate_vc:
                                user_email = get_session("user-email")
                                details = "\n".join(parse_info) if parse_info else None
                                PromptManager.get_instance().send(DuplicatePrompt(
                                    user_email=user_email,
                                    continuation_id=ESDL_DUPLICATE_IMPORT_FILE,
                                    match_id=match_id,
                                    match_name=match_name,
                                    matched_es=matched_es,
                                    context={
                                        "files": files,
                                        "conflict_index": idx,
                                        "client_id": session.get("client_id"),
                                    },
                                    details=details,
                                ))
                                return {'status': 'pending_prompt'}, 202

                    for entry in files:
                        variant = add_esdl_to_project(pm, entry["filename"], entry["esdl_string"])
                        added_variants.append(variant)
                        # emit_active_esdl_project() # cant do emit here, because it is not socket io request

                    client_id = session["client_id"]
                    if not is_import:
                        # Now overwrite the project manager. We do this at the end to prevent the project manager from being
                        # overwritten with an incomplete project manager in case of an error.
                        set_project_manager(pm)
                        init_mapeditor_change_handlers(pm, client_id)
                    send_project_manager_to_lmi_async(only_send_for_client_id=client_id)
                    last_variant = added_variants[-1]
                    if last_variant is not None:
                        pm.set_active_variant(last_variant)
                        # Ewoud: Not sure if this is necessary, as we already send the whole project manager
                        send_add_variant_and_esdl_message_to_lmi(last_variant)


                    return {'message': 'all ESDL(s) received'}, 201
            except Exception as e:
                logger.exception("Error processing ESDL file(s)", exception=e)
                PromptManager.get_instance().send_error(
                    user_email=get_session("user-email"),
                    title="Error loading ESDL",
                    exception=e,
                    details=traceback.format_exc(),
                )
                return {'status': 'error_prompt_sent'}, 200


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
        clear_mapeditor_ui()
