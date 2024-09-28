#  This work is based on original code developed and copyrighted by TNO 2024.
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
import threading
from datetime import datetime

from flask import Flask
from flask_executor import Executor
from flask_socketio import SocketIO, emit

import time
import requests
import uuid
from extensions.external_models_storage import (
    ExternalModelsStorage,
    STATUS,
    OUTPUT_ESDL,
    PROGRESS_FRACTION,
    LAST_UPDATED_TO_EXTERNAL_MODEL_AT,
)
from extensions.session_manager import get_session
from src.esdl_services import ESDLServices
from src.external_models import parse_url_parameters, get_nested_dict_value

import src.log as log

logger = log.get_logger(__name__)


# ---------------------------------------------------------------------------------------------------------------------
#  Generic functions
# ---------------------------------------------------------------------------------------------------------------------
def send_alert(message):
    print(message)
    emit("alert", message, namespace="/esdl")


UPDATE_INTERVAL_SECONDS = 5


class ExternalModelsStep:
    def __init__(self, socket: SocketIO, sequence_data: dict, step_config, models_storage: ExternalModelsStorage):
        self.socketio = socket
        self.sequence_data = sequence_data
        self.step_config = step_config
        self.models_storage = models_storage

    def run(self) -> bool:
        logger.warn("RUN EMS STEP")
        # emit('run_ems_step_STEP', {"sequence_id": self.sequence_data["id"]})

        updated_values = dict(model_specific_output=dict())
        if "queries" in self.step_config:
            self.update_values_from_queries(self.step_config["queries"], updated_values)

        updated_values[LAST_UPDATED_TO_EXTERNAL_MODEL_AT] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.models_storage.update_model_run(self.sequence_data["run_id"], updated_values)

        completed_statuses = self.step_config.get("completed_statuses")
        if not completed_statuses or updated_values[STATUS] in completed_statuses:
            return True
        else:
            return False

    def update_values_from_queries(self, queries, updated_values):
        for query_config in queries:
            url = parse_url_parameters(query_config["url"], self.sequence_data)
            try:
                resp = requests.get(url)

                if resp.status_code == 200:
                    resp_json = resp.json()
                    for key, model_key in query_config["response_mapping"].items():
                        resp_value = get_nested_dict_value(resp_json, model_key)
                        if resp_value:
                            updated_values[key] = self.parse_response_key(key, resp_value, query_config)
            except Exception as e:
                logger.warning(f"Error while getting external model run results: {str(e)}")

    @staticmethod
    def parse_response_key(key, value, query_config):
        if key == STATUS:
            for status, model_status_values in query_config["status_mapping"].items():
                if value in model_status_values:
                    return status
        elif key == OUTPUT_ESDL:
            if query_config["esdl_encoding"] == "utf_8":
                return value
            elif query_config["esdl_encoding"] == "base64_encoded":
                esdlstr_bytes = value.encode("utf-8")
                esdlstr_base64_bytes = base64.b64decode(esdlstr_bytes)
                return esdlstr_base64_bytes.decode("utf-8")
            else:
                raise NotImplementedError(f"Result ESDL encoding '{query_config['esdl_encoding']}' is not supported")
        elif key == PROGRESS_FRACTION:
            if value > 1:
                return value / 100
            else:
                return value
        else:
            return value


class ExternalModelsService:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        executor: Executor,
        models_storage: ExternalModelsStorage,
        esdl_services: ESDLServices,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.models_storage = models_storage
        self.esdl_services = esdl_services

        self.steps: list[ExternalModelsStep] = []

        self.register()
        self.run()

    def register(self):
        logger.info("Registering ExternalModelsService extension")

        @self.socketio.on("ems_initialize_sequence", namespace="/esdl")
        def ems_initialize_sequence(init_data) -> str:
            logger.info(f"Initializing external models sequence: {init_data}")
            user_email = get_session("user-email")
            role = get_session("user-role")
            services_list = self.esdl_services.get_user_services_list(user_email, role)
            main_service_config = None
            for config_service in services_list:
                if config_service["id"] == init_data["main_service_id"]:
                    main_service_config = config_service
                    break
            if not main_service_config:
                raise RuntimeError(f"Service id '{init_data['service_id']}' not found in services list.")

            esdl_service_ok, esdl_service_result = self.esdl_services.call_esdl_service(init_data)
            logger.warn(f"RUN ID, {esdl_service_result['run_id']}")

            sequence_id = str(uuid.uuid4())
            sequence_data = {
                "id": sequence_id,
                "user": user_email,
                "run_id": esdl_service_result["run_id"],
                "run_name": "run_mv",
                "model_job_id": esdl_service_result["model_job_id"],
                "main_service_config": main_service_config,
            }
            self.steps.append(
                ExternalModelsStep(
                    socket=self.socketio,
                    sequence_data=sequence_data,
                    step_config=self.get_workflow_step_config(
                        main_service_config, init_data["next_step_external_models_service"]
                    ),
                    models_storage=self.models_storage,
                )
            )
            self.socketio.emit('run_ems_step', {"sequence_id": sequence_id})

            return sequence_id

    def run(self):
        t = threading.Thread(target=self.run_steps)
        t.daemon = True
        t.start()

    def run_steps(self):
        logger.info("Running external models service")
        while True:
            for step in self.steps:
                step_completed = step.run()
                if step_completed:
                    self.remove_step_and_optionally_add_next(step)

            time.sleep(UPDATE_INTERVAL_SECONDS)

    def remove_step_and_optionally_add_next(self, step):
        logger.info(
            f"External Models step '{step.step_config['reference']}' finished for run '{step.sequence_data['run_name']}"
        )
        self.steps.remove(step)
        if "next_step_external_models_service" in step.step_config:
            logger.info(
                f"External Models step '{step.step_config['reference']}' added for run '{step.sequence_data['run_name']}"
            )
            ExternalModelsStep(
                socket=self.socketio,
                sequence_data=step.sequence_data,
                step_config=self.get_workflow_step_config(
                    step.sequence_data["main_service_config"],
                    step.step_config["next_step_external_models_service"],
                ),
                models_storage=self.models_storage,
            )
        else:
            logger.info(f"External Models sequence finished for run '{step.sequence_data['run_name']}")

    @staticmethod
    def get_workflow_step_config(service_config, identifier):
        if isinstance(identifier, str):
            for step_index, step in enumerate(service_config["workflow"]):
                if step["reference"] == identifier:
                    return step
        return service_config["workflow"][identifier]
