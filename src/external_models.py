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
import re
from datetime import datetime

import requests
from flask import Flask
from flask_socketio import SocketIO

from extensions.external_models_storage import ExternalModelsStorage, RunStatus, MODEL_NAME, RUN_NAME, STATUS, USER, \
    PROJECTS, RUN_ID, INPUT_ESDL, OUTPUT_ESDL, LOGS, SUBMITTED_TO_EXTERNAL_MODEL_AT
import src.log as log
from extensions.session_manager import get_session

logger = log.get_logger(__name__)


class ExternalModels:
    def __init__(self, flask_app: Flask, socket: SocketIO, external_models_storage: ExternalModelsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.em_storage = external_models_storage
        self.register()

    def register(self):
        logger.info("Registering ExternalModels")

        @self.socketio.on("get_external_model_runs_for_user", namespace="/esdl")
        def get_external_model_runs_for_user(model_run_info) -> list:
            """
            Check if updated progress or new results are available and get runs for external model.

            :param model_run_info: external model data.
            """
            logger.info(f"get_external_model_runs_for_user: {model_run_info}")
            model_name = model_run_info["external_model_name"]

            user = get_session("user-email")
            user_projects = get_session("user-group")
            model_runs = self.em_storage.get_model_runs_for_current_user(user, user_projects, model_name)

            return model_runs

        @self.socketio.on("external_models_update_run", namespace="/esdl")
        def external_models_update_run(model_run_info) -> None:
            """
            Update Model run data.

            :param model_run_info: external model data.
            """
            logger.info(f"external_models_update_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            self.em_storage.update_model_run(run_id, model_run_info)

        @self.socketio.on("external_models_delete_run", namespace="/esdl")
        def external_models_delete_run(model_run_info) -> dict:
            """
            Delete Model run data.

            :param model_run_info: external model data.
            :return: Message with deleted run info.
            """
            logger.info(f"external_models_delete_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]

            deleted_run_data = self.em_storage.delete_model_run(run_id)

            if "delete_result_url" in model_run_info:
                url = parse_url_parameters(model_run_info["delete_result_url"], deleted_run_data)
                try:
                    requests.delete(url)
                except Exception as e:
                    logger.warning(f"Error while deleting external model run results: {str(e)}")
            return {"message": f"{deleted_run_data[MODEL_NAME]} run '{deleted_run_data[RUN_NAME]}' deleted ok."}

        @self.socketio.on("external_models_get_run_text", namespace="/esdl")
        def external_models_get_run_text(model_run_info):
            """
            Get model run details as text omitting certain parameters which are too long or not relevant.

            :param model_run_info: external model data.
            :return: Run details as text.
            """
            logger.info(f"external_models_get_run_text: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            model_run_data = self.em_storage.get_model_run(run_id)

            text = f"<b>{model_run_data[MODEL_NAME]}</b> run details for: <b>{model_run_data[RUN_NAME]}</b><br>"

            top_keys = [MODEL_NAME, RUN_NAME, STATUS, USER, PROJECTS, RUN_ID]
            omit_keys = [INPUT_ESDL, OUTPUT_ESDL]

            for key in top_keys:
                text += f"<br>{key}: <b>{pretty_print(model_run_data[key], '&emsp;')}</b>"
            for key, value in model_run_data.items():
                if key not in top_keys + omit_keys + [LOGS]:
                    text += f"<br>{key}: <b>{pretty_print(value, '&emsp;')}</b>"
            if LOGS in model_run_data:
                logs = model_run_data[LOGS].replace("\n", "<br>")
                text += f"<br><br>logs:<br>{logs}<br>"

            return text

        @self.socketio.on("external_models_get_run_jsonforms", namespace="/esdl")
        def external_models_get_run_jsonforms(model_run_info) -> dict:
            """
            Get run data as jsonforms with the run name and projects as editable, and some other details as readonly.

            :param model_run_info: external model data.
            :return: Run details as jsonforms dictionary.
            """
            logger.info(f"external_models_get_run_jsonforms: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            model_run_data = self.em_storage.get_model_run(run_id)

            user_projects = get_session("user-group")
            properties = {}
            required = []
            form_data = {}
            ui_elements = []

            properties[RUN_NAME] = dict(type="string", minLength=3, title="name")
            required.append(RUN_NAME)
            form_data[RUN_NAME] = model_run_data[RUN_NAME]
            ui_elements.append(dict(type="Control", scope=f"#/properties/{RUN_NAME}"))

            properties[PROJECTS] = dict(
                type="array", title="projects", uniqueItems=True, items=dict(type="string", enum=user_projects)
            )
            form_data[PROJECTS] = model_run_data[PROJECTS]
            ui_elements.append(dict(type="Control", scope=f"#/properties/{PROJECTS}"))

            info_keys = [MODEL_NAME, USER, STATUS, RUN_ID, SUBMITTED_TO_EXTERNAL_MODEL_AT]
            for key, value in model_run_data.items():
                if key in info_keys:
                    properties[key] = dict(type="string", readOnly=True)
                    ui_elements.append(dict(type="Control", scope=f"#/properties/{key}", className=""))
                    form_data[key] = value

            return dict(
                schema=dict(
                    properties=properties,
                    required=required,
                ),
                formData=form_data,
                uischema=dict(type="VerticalLayout", elements=ui_elements),
            )


def get_nested_dict_value(dictionary: dict, nested_key: str):
    """
    Get dictionary value from a nested key, which consists of subsequent keys separated by a dot.

    :param dictionary: dictionary to get value from.
    :param nested_key: nested key which consists of subsequent keys separated by a dot.
    :return: dictionary value of the nested key .
    """
    if "." not in nested_key:
        if nested_key in dictionary:
            return dictionary[nested_key]
        else:
            return None
    else:
        top_key = nested_key.split(".", 1)[0]
        new_key = nested_key.split(".", 1)[1]
        if top_key in dictionary:
            return get_nested_dict_value(dictionary[top_key], new_key)
        else:
            return None


def parse_url_parameters(url: str, data: dict) -> str:
    """
    Parse URL parameters present in string (surrounded by `<>`).

    :param url: URL string to be parsed.
    :param data: Key-values used for the parsing.
    :return: Parsed URL string.
    """
    # put values for args in url surrounded by '< >'
    replace_args = re.findall(r"<.*?>", url)
    for replace_arg in replace_args:
        url = url.replace(replace_arg, data[replace_arg[1:-1].lower()])
    return url


def pretty_print(item_to_print: object, indent: str = "") -> str:
    """
    Pretty print for display in html.

    :param item_to_print: Item to be printed, can be dict, list or string.
    :param indent: Indent before each line.
    :return: Pretty printed text
    """
    if not item_to_print:
        return "none"
    elif isinstance(item_to_print, dict):
        pretty = ""
        for k, v in item_to_print.items():
            pretty += f"<br>{indent}{k}: "
            if isinstance(v, dict) or isinstance(v, list):
                pretty += pretty_print(v, f"{indent}&emsp;")
            else:
                pretty += str(v)
        return pretty
    elif isinstance(item_to_print, list):
        v = [str(item) for item in item_to_print]
        return ", ".join(v)
    else:
        return str(item_to_print)
