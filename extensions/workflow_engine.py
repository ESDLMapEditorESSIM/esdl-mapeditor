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
from __future__ import annotations
import base64
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime

from flask import Flask
from flask_socketio import SocketIO, emit

import time
import requests
import uuid

from extensions.external_models.external_models_storage import (
    ExternalModelsStorage,
    STATUS,
    OUTPUT_ESDL,
    LAST_UPDATED_TO_EXTERNAL_MODEL_AT,
    PROGRESS_FRACTION,
    MODEL_SPECIFIC_OUTPUT,
)
from src.tno.shared.util import get_nested_dict_value, parse_url_string_with_parameters
from extensions.session_manager import get_session, get_all_session_ids_for_user
from src.esdl_services import ESDLServices
import src.log as log

logger = log.get_logger(__name__)


DEFAULT_RETRY_INTERVAL_SECONDS = 10
DEFAULT_MAXIMUM_WAIT_SECONDS = 3600


@dataclass
class SequenceData:
    id: str
    run_name: str
    user_email: str
    main_service_config: dict
    run_id: str | None = None
    model_job_id: str | None = None
    steps_progress: list[StepProgress] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class StepProgress:
    name: str
    status: str
    progress_fraction: float
    message: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class WorkflowStep:
    def __init__(
        self,
        socketio: SocketIO,
        sequence_data: SequenceData,
        step_config,
        models_storage: ExternalModelsStorage,
    ):
        self.socketio = socketio
        self.sequence_data = sequence_data
        self.step_config = step_config
        self.models_storage = models_storage

    def run(self) -> bool:
        step_progress = StepProgress(name=self.step_config.get("monitor_name"), status="STARTED", progress_fraction=0)
        self.sequence_data.steps_progress.append(step_progress)
        # self.sequence_data.steps_progress.append(step_progress)

        retry_interval_seconds = self.step_config.get("retry_interval_seconds")
        if not retry_interval_seconds:
            retry_interval_seconds = DEFAULT_RETRY_INTERVAL_SECONDS
        maximum_wait_seconds = self.step_config.get("maximum_wait_seconds")
        if not maximum_wait_seconds:
            maximum_wait_seconds = DEFAULT_MAXIMUM_WAIT_SECONDS

        nr_of_retries = 0
        while True:
            updated_values = dict(model_specific_output=dict())
            if "queries" in self.step_config:
                for query_config in self.step_config["queries"]:
                    self.update_values_from_query(updated_values, query_config)
            if updated_values[STATUS] is None:
                return False
            updated_values[LAST_UPDATED_TO_EXTERNAL_MODEL_AT] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # update mongodb
            updated_model_run = self.models_storage.update_model_run(self.sequence_data.run_id, updated_values)

            if updated_model_run:
                step_progress.status = updated_model_run[STATUS]
                step_progress.progress_fraction = updated_model_run[PROGRESS_FRACTION]

                # send to frontend
                connected_user_client_ids = get_all_session_ids_for_user(self.sequence_data.user_email)
                if len(connected_user_client_ids) > 0:
                    for client_id in connected_user_client_ids:
                        self.socketio.emit(
                            "wfe_sequence_progress",
                            {
                                "wfe_sequence_id": self.sequence_data.id,
                                "run_name": self.sequence_data.run_name,
                                "steps_progress": [pr.as_dict() for pr in self.sequence_data.steps_progress],
                            },
                            namespace="/esdl",
                        )
                        self.socketio.emit(
                            "wfe_update_model_run",
                            updated_model_run,
                            namespace="/esdl",
                            room=client_id,
                        )

                # check if workflow step finished
                completed_statuses = self.step_config.get("completed_statuses")
                if not completed_statuses or updated_values[STATUS] in completed_statuses:
                    logger.info(
                        f"Workflow engine sequence for user '{self.sequence_data.user_email}' completed:"
                        f" sequence '{self.sequence_data.run_id}'."
                    )
                    return True
                elif nr_of_retries * retry_interval_seconds > maximum_wait_seconds:
                    logger.error(
                        f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated: maximum wait"
                        f" time '{maximum_wait_seconds}' exceeded for step '{self.step_config}'."
                    )
                    return False
                else:
                    nr_of_retries += 1
                    time.sleep(retry_interval_seconds)
            else:
                logger.error(
                    f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated:"
                    f" model run '{self.sequence_data.run_id}' could not be found."
                )
                return False

    def update_values_from_query(self, updated_values: dict, query_config: dict):
        url = parse_url_string_with_parameters(query_config["url"], self.sequence_data.as_dict())
        try:
            resp = requests.get(url)

            if resp.status_code == 200:
                resp_json = resp.json()
                for key, model_key in query_config["response_mapping"].items():
                    resp_value = get_nested_dict_value(resp_json, model_key)
                    if resp_value:
                        updated_values[key] = self.parse_response_key(key, resp_value, query_config)
                for key, model_key in query_config["model_specific_response_mapping"].items():
                    resp_value = get_nested_dict_value(resp_json, model_key)
                    if resp_value:
                        updated_values[MODEL_SPECIFIC_OUTPUT][key] = self.parse_response_key(
                            key, resp_value, query_config
                        )
        except Exception as e:
            logger.warning(f"Error while getting external model run results: {str(e)}")

    @staticmethod
    def parse_response_key(key, value, query_config):
        if key == STATUS:
            for status, model_status_values in query_config["status_mapping"].items():
                if value in model_status_values:
                    return status
            logger.error(f"Status '{value}' not found in status mapping '{query_config['status_mapping']}'")
            return None
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
            try:
                float_value = float(value)
                if float_value > 1:
                    float_value /= 100
                return round(float_value, 2)
            except ValueError:
                return value
        else:
            return value


class WorkflowEngine:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        external_models_storage: ExternalModelsStorage,
        esdl_services: ESDLServices,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.external_models_storage = external_models_storage
        self.esdl_services = esdl_services

        self.register()

    def register(self):
        logger.info("Registering WorkflowEngine extension")

        @self.socketio.on("wfe_initialize_sequence", namespace="/esdl")
        def wfe_initialize_sequence(init_data) -> str | None:
            logger.info(f"Initializing external models sequence: {init_data}")

            # create sequence data
            user_email = get_session("user-email")
            role = get_session("user-role")
            services_list = self.esdl_services.get_user_services_list(user_email, role)
            main_service_config = None
            for config_service in services_list:
                if config_service["id"] == init_data["main_service_id"]:
                    main_service_config = config_service
                    break
            if not main_service_config:
                logger.error(f"Service id '{init_data['service_id']}' not found in services list.")
                return None
            sequence_id = str(uuid.uuid4())
            if "run_name_key" in init_data:
                run_name = get_nested_dict_value(init_data, init_data["run_name_key"])
            else:
                run_name = sequence_id
            sequence_data = SequenceData(
                id=sequence_id,
                user_email=user_email,
                main_service_config=main_service_config,
                run_name=run_name,
            )

            # run initial workflow step inside request context to enable for instance selected ESDL loading
            if init_data["type"] == "esdl_service":
                esdl_service_ok, esdl_service_result = self.esdl_services.call_esdl_service(init_data)
                if esdl_service_ok:
                    emit(
                        "wfe_update_model_run",
                        esdl_service_result["model_run_doc"],
                        namespace="/esdl",
                    )
                    sequence_data.run_id = esdl_service_result["model_run_doc"]["run_id"]
                    sequence_data.model_job_id = esdl_service_result["model_run_doc"]["model_job_id"]
                else:
                    logger.error(f"Error running esdl service with data: '{init_data}")
                    return None
            else:
                logger.error(f"Type '{init_data['type']}' not implemented for the workflow engine.")
                return None

            # run subsequent steps on new thread outside request context (will continue when user disconnects)
            if "workflow_engine_next_step" in init_data:
                t = threading.Thread(
                    target=self.run_sequence, args=(sequence_data, init_data["workflow_engine_next_step"])
                )
                t.daemon = True
                t.start()

            return sequence_id

    def run_sequence(self, sequence_data: SequenceData, first_step):
        logger.info(f"Running workflow sequence for run '{sequence_data.run_name}")

        next_step = first_step
        while next_step:
            step_config = self.get_workflow_step_config(sequence_data.main_service_config, next_step)
            logger.info(f"Running workflow engine step '{step_config['reference']}' for run '{sequence_data.run_name}")
            step = WorkflowStep(
                socketio=self.socketio,
                sequence_data=sequence_data,
                step_config=step_config,
                models_storage=self.external_models_storage,
            )
            run_succeeded = step.run()
            logger.info(f"Workflow engine step '{step_config['reference']}' finished for run '{sequence_data.run_name}")
            if run_succeeded and "workflow_engine_next_step" in step_config:
                next_step = step_config["workflow_engine_next_step"]
            else:
                next_step = None
        logger.info(f"External Models sequence finished for run '{sequence_data.run_name}")

    @staticmethod
    def get_workflow_step_config(service_config, identifier):
        if isinstance(identifier, str):
            for step_index, step in enumerate(service_config["workflow"]):
                if step["reference"] == identifier:
                    return step
        return service_config["workflow"][identifier]
