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

        @self.socketio.on("external_models_update_get_runs", namespace="/esdl")
        def external_models_update_get_runs(model_run_info) -> list:
            logger.info(f"external_models_update_get_runs: {model_run_info}")
            model_name = model_run_info["model_name"]
            result_save_params = model_run_info["result_save_params"]
            status_mapping = model_run_info["status_mapping"]
            get_result_url = model_run_info["get_result_url"]
            result_esdl_encoding = model_run_info["result_esdl_encoding"]

            user = get_session("user-email")
            user_projects = get_session("user-group")
            model_runs = self.em_storage.get_model_runs_for_current_user(model_name, user, user_projects)

            replace_args = re.findall(r"<.*?>", get_result_url)
            for i_run, model_run_data in enumerate(model_runs):
                if RunStatus(model_run_data["status"]) in [RunStatus.SUBMITTED, RunStatus.RUNNING]:
                    url = get_result_url
                    for replace_arg in replace_args:
                        url = url.replace(replace_arg, model_run_data[replace_arg[1:-1]])
                    try:
                        resp = requests.get(url)
                        if resp.status_code == 200:
                            run_data = resp.json()
                            updated_values = {}
                            for doc_key, data_key in result_save_params.items():
                                updated_values[doc_key] = run_data[data_key]
                            # map external model status to mapeditor status
                            if "status" in updated_values:
                                run_status = updated_values["status"]
                                for status, model_status_values in status_mapping.items():
                                    if run_status in model_status_values:
                                        updated_values["status"] = status
                                        break
                            if "output_esdl" in updated_values and result_esdl_encoding == "utf8":
                                output_esdl = updated_values["output_esdl"]
                                esdlstr_bytes = output_esdl.encode("utf-8")
                                esdlstr_base64_bytes = base64.b64encode(esdlstr_bytes)
                                updated_values["output_esdl"] = esdlstr_base64_bytes.decode("utf-8")
                            model_runs[i_run] = self.em_storage.update_model_run(
                                model_name, model_run_data["run_id"], updated_values
                            )
                    except Exception as e:
                        logger.warning(f"Error while getting external model run results: {str(e)}")
            return model_runs

        @self.socketio.on("external_models_delete_run", namespace="/esdl")
        def external_models_delete_run(model_run_info):
            logger.info(f"external_models_delete_run: {model_run_info}")
            model_name = model_run_info["model_name"]
            run_id = model_run_info["run_id"]

            model_run_data = self.em_storage.delete_model_run(model_name, run_id)

            if "delete_result_url" in model_run_info:
                delete_result_url = model_run_info["delete_result_url"]
                replace_args = re.findall(r"<.*?>", delete_result_url)
                url = delete_result_url
                for replace_arg in replace_args:
                    url = url.replace(replace_arg, model_run_data[replace_arg[1:-1]])
                try:
                    requests.delete(url)
                except Exception as e:
                    logger.warning(f"Error while deleting external model run results: {str(e)}")
            return {"message": f"{model_name} run '{model_run_data['run_name']}' deleted ok."}

        @self.socketio.on("external_models_get_run_text", namespace="/esdl")
        def external_models_get_run_text(model_run_info):
            logger.info(f"external_models_get_run_text: {model_run_info}")
            model_name = model_run_info["model_name"]
            run_id = model_run_info["run_id"]
            model_run_data = self.em_storage.get_model_run(model_name, run_id)

            text = f"<b>{model_name}</b> run details for: <b>{model_run_data['run_name']}</b><br>"

            top_keys = ["model_name", "run_name", "status", "user", "projects", "run_id"]
            omit_keys = ["input_esdl", "output_esdl"]

            for key in top_keys:
                text += f"<br>{key}: <b>{model_run_data[key]}</b>"
            for key, value in model_run_data.items():
                if key not in top_keys + omit_keys + ["logs"]:
                    text += f"<br>{key}: <b>{value}</b>"
            text += f"<br>logs:<br>{model_run_data['logs']}"

            return text

        @self.socketio.on("external_models_get_run_jsonforms", namespace="/esdl")
        def external_models_get_run_jsonforms(model_run_info):
            logger.info(f"external_models_get_run_jsonforms: {model_run_info}")
            model_name = model_run_info["model_name"]
            run_id = model_run_info["run_id"]
            model_run_data = self.em_storage.get_model_run(model_name, run_id)

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

        @self.socketio.on("external_models_save_run_jsonforms", namespace="/esdl")
        def external_models_save_run_jsonforms(model_run_info):
            logger.info(f"external_models_save_run_jsonforms: {model_run_info}")
            model_name = model_run_info["model_name"]
            run_id = model_run_info["run_id"]
            self.em_storage.update_model_run(model_name, run_id, model_run_info)
