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

from extensions.external_models_storage import ExternalModelsStorage, RunStatus
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

        @self.socketio.on("external_models_check_and_get_runs", namespace="/esdl")
        def external_models_check_and_get_runs(model_run_info) -> list:
            """
            Check if updated progress or new results are available and get runs for external model.

            :param model_run_info: external model data.
            """
            logger.info(f"external_models_check_and_get_runs: {model_run_info}")
            model_name = model_run_info["external_model_name"]

            user = get_session("user-email")
            user_projects = get_session("user-group")
            model_runs = self.em_storage.get_model_runs_for_current_user(user, user_projects, model_name)

            for i_run, stored_run_data in enumerate(model_runs):
                if RunStatus(stored_run_data["status"]) in [RunStatus.SUBMITTED, RunStatus.RUNNING]:
                    url = parse_url_parameters(stored_run_data["get_result_config"]["url"], stored_run_data)

                    get_result_config = stored_run_data["get_result_config"]
                    result_esdl_encoding = get_result_config.get("esdl_encoding")
                    result_status_param = get_result_config.get("status_param")
                    result_output_esdl_param = get_result_config.get("output_esdl_param")
                    result_logs_param = get_result_config.get("logs_param")
                    result_save_params = get_result_config.get("save_additional_params")
                    status_mapping = get_result_config.get("status_mapping")

                    try:
                        resp = requests.get(url)
                        if resp.status_code == 200:
                            new_run_data = resp.json()
                            updated_values = dict(model_specific_output=dict())
                            for doc_key, data_key in result_save_params.items():
                                updated_values["model_specific_output"][doc_key] = new_run_data[data_key]
                            # map external model status to mapeditor status
                            if result_status_param:
                                run_status = get_nested_dict_value(new_run_data, result_status_param)
                                for status, model_status_values in status_mapping.items():
                                    if run_status in model_status_values:
                                        updated_values["status"] = status
                                        break
                            if (
                                result_output_esdl_param
                                and result_output_esdl_param in new_run_data
                                and new_run_data[result_output_esdl_param]
                            ):
                                if result_esdl_encoding == "utf_8":
                                    output_esdl = new_run_data[result_output_esdl_param]
                                elif result_esdl_encoding == "base64_encoded":
                                    esdlstr_bytes = new_run_data[result_output_esdl_param].encode("utf-8")
                                    esdlstr_base64_bytes = base64.b64decode(esdlstr_bytes)
                                    output_esdl = esdlstr_base64_bytes.decode("utf-8")
                                else:
                                    raise NotImplementedError(
                                        f"Result ESDL encoding '{result_esdl_encoding}' is not supported"
                                    )

                                updated_values["output_esdl"] = output_esdl

                            if result_logs_param:
                                updated_values["logs"] = get_nested_dict_value(new_run_data, result_logs_param)

                            updated_values["last_update_from_external_model"] = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            model_runs[i_run] = self.em_storage.update_model_run(
                                stored_run_data["run_id"], updated_values
                            )
                    except Exception as e:
                        logger.warning(f"Error while getting external model run results: {str(e)}")
            return model_runs

        @self.socketio.on("external_models_update_run", namespace="/esdl")
        def external_models_update_run(model_run_info) -> None:
            """
            Update Model run data.

            :param model_run_info: external model data.
            """
            logger.info(f"external_models_update_run: {model_run_info}")
            run_id = model_run_info["run_id"]
            self.em_storage.update_model_run(run_id, model_run_info)

        @self.socketio.on("external_models_delete_run", namespace="/esdl")
        def external_models_delete_run(model_run_info) -> dict:
            """
            Delete Model run data.

            :param model_run_info: external model data.
            :return: Message with deleted run info.
            """
            logger.info(f"external_models_delete_run: {model_run_info}")
            run_id = model_run_info["run_id"]

            deleted_run_data = self.em_storage.delete_model_run(run_id)

            if "delete_result_url" in model_run_info:
                url = parse_url_parameters(model_run_info["delete_result_url"], deleted_run_data)
                try:
                    requests.delete(url)
                except Exception as e:
                    logger.warning(f"Error while deleting external model run results: {str(e)}")
            return {"message": f"{deleted_run_data['model_name']} run '{deleted_run_data['run_name']}' deleted ok."}

        @self.socketio.on("external_models_get_run_text", namespace="/esdl")
        def external_models_get_run_text(model_run_info):
            """
            Get model run details as text omitting certain parameters which are too long or not relevant.

            :param model_run_info: external model data.
            :return: Run details as text.
            """
            logger.info(f"external_models_get_run_text: {model_run_info}")
            run_id = model_run_info["run_id"]
            model_run_data = self.em_storage.get_model_run(run_id)

            text = f"<b>{model_run_data['model_name']}</b> run details for: <b>{model_run_data['run_name']}</b><br>"

            top_keys = ["model_name", "run_name", "status", "user", "projects", "run_id"]
            omit_keys = ["input_esdl", "output_esdl", "get_result_config"]

            for key in top_keys:
                text += f"<br>{key}: <b>{pretty_print(model_run_data[key], '&emsp;')}</b>"
            for key, value in model_run_data.items():
                if key not in top_keys + omit_keys + ["logs"]:
                    text += f"<br>{key}: <b>{pretty_print(value, '&emsp;')}</b>"
            if "logs" in model_run_data:
                logs = model_run_data["logs"].replace("\n", "<br>")
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
            run_id = model_run_info["run_id"]
            model_run_data = self.em_storage.get_model_run(run_id)

            user_projects = get_session("user-group")
            properties = {}
            required = []
            form_data = {}
            ui_elements = []

            properties["run_name"] = dict(type="string", minLength=3, title="name")
            required.append("run_name")
            form_data["run_name"] = model_run_data["run_name"]
            ui_elements.append(dict(type="Control", scope="#/properties/run_name"))

            properties["projects"] = dict(
                type="array", title="Projects", uniqueItems=True, items=dict(type="string", enum=user_projects)
            )
            form_data["projects"] = model_run_data["projects"]
            ui_elements.append(dict(type="Control", scope="#/properties/projects"))

            info_keys = ["model_name", "user", "status", "run_id", "submitted_at"]
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
    Get dictionary value from nested key in which consists of subsequent keys separated by a dot.

    :param dictionary: dictionary to get value from.
    :param nested_key: nested key which consists of subsequent keys separated by a dot.
    :return: dictionary value of the nested key .
    """
    if "." not in nested_key:
        return dictionary[nested_key]
    else:
        top_key = nested_key.split(".", 1)[0]
        new_key = nested_key.split(".", 1)[1]
        return get_nested_dict_value(dictionary[top_key], new_key)


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
