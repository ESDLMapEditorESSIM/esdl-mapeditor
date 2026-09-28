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
import time
import requests
import uuid

from flask import Flask
from flask_socketio import SocketIO, emit

from extensions.toast_notifications import ToastNotification, NotificationType, ToastNotifications
from extensions.external_models.external_models_storage import (
    ExternalModelsStorage,
    STATUS,
    LOGS,
    OUTPUT_ESDL,
    LAST_UPDATED_TO_EXTERNAL_MODEL_AT,
    PROGRESS_FRACTION,
    MODEL_SPECIFIC_OUTPUT,
    RunStatus,
)
from src.tno.shared.util import get_nested_dict_value, parse_string_with_parameters, pretty_print_html
from extensions.session_manager import get_session, get_all_session_ids_for_user
from src.esdl_services import ESDLServices
import src.log as log

logger = log.get_logger(__name__)


QUERY_POLLING_DEFAULT_RETRY_INTERVAL_SECONDS = 10
QUERY_POLLING_DEFAULT_MAXIMUM_WAIT_SECONDS = 3600
QUERY_POLLING_DEFAULT_MAX_ERRORS = 5


@dataclass
class StepProgress:
    """Workflow Engine Step Progress data."""

    name: str
    status: str | None
    progress_fraction: float | None
    message: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class SequenceData:
    """Workflow Engine Sequence data."""

    id: str
    run_name: str
    user_email: str
    main_service_config: dict
    run_id: str | None = None
    model_job_id: str | None = None
    steps_progress: list[StepProgress] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


class WorkflowStep:
    def __init__(
        self,
        socketio: SocketIO,
        sequence_data: SequenceData,
        step_config,
        models_storage: ExternalModelsStorage,
    ) -> None:
        self.socketio = socketio
        self.sequence_data = sequence_data
        self.step_config = step_config
        self.models_storage = models_storage

    def run(self) -> bool:
        """
        Run workflow step.

        :return: True if completed successfully
        """
        step_progress = StepProgress(
            name=self.step_config.get("monitor_name"), status=RunStatus.SUBMITTED.value, progress_fraction=0
        )
        self.sequence_data.steps_progress.append(step_progress)

        if "model_run_result_polling" in self.step_config["config"]:
            return self.action_model_run_result_polling(
                step_progress, self.step_config["config"]["model_run_result_polling"]
            )
        elif "model_run_show_results" in self.step_config["config"]:
            return self.action_model_run_show_results(
                step_progress, self.step_config["config"]["model_run_show_results"]
            )
        # TODO implement other actions
        else:
            logger.error(
                f"No implemented workflow engine action found for step '{self.step_config['id']}'"
                f" with config '{self.step_config['config']}'."
            )
            return False

    def action_model_run_result_polling(self, step_progress: StepProgress, config: dict) -> bool:
        retry_interval_seconds = config.get("retry_interval_seconds")
        if not retry_interval_seconds:
            retry_interval_seconds = QUERY_POLLING_DEFAULT_RETRY_INTERVAL_SECONDS
        maximum_wait_seconds = config.get("maximum_wait_seconds")
        if not maximum_wait_seconds:
            maximum_wait_seconds = QUERY_POLLING_DEFAULT_MAXIMUM_WAIT_SECONDS

        # run query(ies) until SUCCEEDED or maximum wait time reached
        nr_of_retries = 0
        nr_of_query_errors = 0
        queries_finished = []

        while True:
            updated_run_values = dict()
            queries_error_message = ""
            for query_config in config["query_list"]:
                # update values with query response
                if query_config["url"] not in queries_finished:
                    query_error_message, query_finished = self.update_values_from_query(
                        updated_run_values, query_config
                    )
                    queries_error_message += query_error_message
                    if query_finished and query_config["url"] not in queries_finished:
                        queries_finished.append(query_config["url"])

            if queries_error_message:  # allow a number of errors (temporarily unavailable api)
                nr_of_query_errors += 1
                if nr_of_query_errors <= QUERY_POLLING_DEFAULT_MAX_ERRORS:
                    time.sleep(retry_interval_seconds)
                    continue
                else:
                    updated_run_values[STATUS] = RunStatus.ERROR.value
                    current_model_run_data = self.models_storage.get_model_run(self.sequence_data.run_id)
                    run_logs = ""
                    if current_model_run_data:
                        run_logs += f"{current_model_run_data.get(LOGS, '')}\n{queries_error_message}"
                    updated_run_values[LOGS] = run_logs + f"\nError querying model for results: '{query_config['url']}'"
            elif STATUS not in updated_run_values or updated_run_values[STATUS] is None:
                logger.error(
                    f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated:"
                    f" no status was returned/configured (model run '{self.sequence_data.run_id}')."
                )
                return False

            # update run status SUCCEEDED to SUCC_PEND when not all queries finished
            step_status = updated_run_values[STATUS]
            if (
                STATUS in updated_run_values
                and updated_run_values[STATUS] == RunStatus.SUCCEEDED.value
                and len(queries_finished) < len(config["query_list"])
            ):
                updated_run_values[STATUS] = RunStatus.SUCC_PEND.value

            updated_run_values[LAST_UPDATED_TO_EXTERNAL_MODEL_AT] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # update mongodb
            updated_model_run = self.models_storage.update_model_run(self.sequence_data.run_id, updated_run_values)
            if not updated_model_run:
                logger.info(
                    f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated:"
                    f" model run '{self.sequence_data.run_id}' could not be found."
                )
                return False

            updated_model_run["is_owner"] = updated_model_run["user"] == self.sequence_data.user_email

            # emit to frontend
            step_progress.status = step_status
            step_progress.progress_fraction = updated_model_run[PROGRESS_FRACTION]
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
                        room=client_id,
                    )
                    self.socketio.emit(
                        "wfe_update_model_run",
                        updated_model_run,
                        namespace="/esdl",
                        room=client_id,
                    )

            # check if workflow step finished
            if STATUS in updated_run_values and updated_run_values[STATUS] in [
                RunStatus.CANCELLED.value,
                RunStatus.ERROR.value,
            ]:  # on error abort workflow step
                logger.warning(
                    f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated"
                    f" with status '{updated_run_values[STATUS]}': sequence '{self.sequence_data.run_id}'."
                )
                return False
            elif len(queries_finished) == len(config["query_list"]):  # all queries finished
                if STATUS in updated_run_values and updated_run_values[STATUS] in [
                    RunStatus.SUCCEEDED.value,
                    RunStatus.SUCC_PEND.value,
                    RunStatus.SUCC_WARN.value,
                    RunStatus.NEED_INPUT.value,
                ]:
                    logger.info(
                        f"Workflow engine sequence for user '{self.sequence_data.user_email}' finished"
                        f" with status '{updated_run_values[STATUS]}': sequence '{self.sequence_data.run_id}'."
                    )
                    return True
                elif STATUS not in updated_run_values:
                    logger.warning(
                        f"Workflow engine sequence for user '{self.sequence_data.user_email}' finished"
                        f" without status: sequence '{self.sequence_data.run_id}' aborted."
                    )
                    return False
                else:
                    logger.warning(
                        f"Workflow engine sequence for user '{self.sequence_data.user_email}' finished with status"
                        f" '{updated_run_values[STATUS]}': sequence '{self.sequence_data.run_id}' aborted."
                    )
                    return False
            elif nr_of_retries * retry_interval_seconds > maximum_wait_seconds:
                logger.error(
                    f"Workflow engine sequence for user '{self.sequence_data.user_email}' terminated: maximum wait"
                    f" time '{maximum_wait_seconds}' exceeded for step '{self.step_config}'."
                )
                return False
            else:
                nr_of_retries += 1
                time.sleep(retry_interval_seconds)

    def action_model_run_show_results(self, step_progress: StepProgress, config: list) -> bool:
        model_run_data = self.models_storage.get_model_run(self.sequence_data.run_id)

        text = ""
        for row_config in config:
            if "description" in row_config:
                text += f"{row_config['description']}: "
            value = pretty_print_html(get_nested_dict_value(model_run_data, row_config["value_database_key"]), "&emsp;")
            if "link_text" in row_config:
                value = f"<a href=\"{value}\" target=\"_blank\">{row_config['link_text']}</a>"
            text += f"<b>{value}</b><br>"

        step_progress.status = None
        step_progress.progress_fraction = None
        step_progress.message = text

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
                    room=client_id,
                )
        return True

    def update_values_from_query(self, updated_values: dict, query_config: dict) -> tuple[str, bool]:
        url = parse_string_with_parameters(query_config["url"], self.sequence_data.as_dict())
        error_message = ""
        query_finished = False
        try:
            resp = requests.get(url)

            if resp.status_code == 200:
                resp_json = resp.json()
                for key, model_key in query_config["response_mapping"].items():
                    resp_value = get_nested_dict_value(resp_json, model_key)
                    if resp_value:
                        updated_values[key] = self.parse_response_key(key, resp_value, query_config)
                if "model_specific_response_mapping" in query_config:
                    for key, model_key in query_config["model_specific_response_mapping"].items():
                        resp_value = get_nested_dict_value(resp_json, model_key)
                        if resp_value:
                            # nested dot notation for mongo db update
                            updated_values[f"{MODEL_SPECIFIC_OUTPUT}.{key}"] = self.parse_response_key(
                                key, resp_value, query_config
                            )
                if "status_mapping" in query_config:
                    if updated_values[STATUS] not in [RunStatus.SUBMITTED.value, RunStatus.RUNNING.value]:
                        query_finished = True
                elif "stop_query_on" in query_config:
                    key = query_config["stop_query_on"]["key"]
                    key_value = updated_values[key] if key in updated_values else None
                    condition = query_config["stop_query_on"]["condition"]
                    value = query_config["stop_query_on"]["value"]
                    if condition == "larger_than":
                        query_finished = key_value > value
                    elif condition == "larger_equal_than":
                        query_finished = key_value >= value
                    elif condition == "equal":
                        query_finished = key_value == value
                    elif condition == "not_equal":
                        query_finished = key_value != value
                    elif condition == "smaller_than":
                        query_finished = key_value < value
                    elif condition == "smaller_equal_than":
                        query_finished = key_value <= value
                    else:
                        error_message = (
                            f"Condition '{condition}' for external model query with url '{url}':" f" does not exist."
                        )
                        logger.warning(error_message)
                    if query_finished and "new_status" in query_config["stop_query_on"]:
                        updated_values[STATUS] = RunStatus(query_config["stop_query_on"]["new_status"]).value
                else:
                    error_message = (
                        f"Missing config for external model query with url '{url}':"
                        f" 'status_mapping' or 'stop_query_on' required to determine when to stop query."
                    )
                    logger.warning(error_message)
            else:
                error_message = f"Unexpected query status code '{resp.status_code}' from url '{url}'."
                logger.warning(error_message)
        except Exception as e:
            error_message = f"Error while getting external model run results: {str(e)}"
            logger.warning(error_message)
        return error_message, query_finished

    @staticmethod
    def parse_response_key(key, value, query_config) -> str | float | None:
        if key == STATUS:
            for status, model_status_values in query_config["status_mapping"].items():
                if value in model_status_values:
                    return RunStatus(status).value
            logger.error(f"Status '{value}' not found in status mapping '{query_config['status_mapping']}'")
            return None
        elif key == OUTPUT_ESDL:
            esdl_encoding = "base64_encoded" if "esdl_encoding" not in query_config else query_config["esdl_encoding"]
            if esdl_encoding == "utf_8":
                return value
            elif esdl_encoding == "base64_encoded":
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
        toast_notifications: ToastNotifications,
    ) -> None:
        self.flask_app = flask_app
        self.socketio = socket
        self.external_models_storage = external_models_storage
        self.esdl_services = esdl_services
        self.toast_notifications = toast_notifications

        self.register()

    def register(self) -> None:
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

            try:
                # run initial workflow step inside request context to enable for instance selected ESDL loading
                if init_data["type"] == "esdl_service":
                    esdl_service_ok, esdl_service_result, _ = self.esdl_services.call_esdl_service(init_data)[0]

                    if not esdl_service_ok or not isinstance(esdl_service_result, dict):
                        logger.error(f"Error running esdl service with data: '{init_data}")
                        # On failure the service result is the error message, if the service returned one.
                        description = (
                            esdl_service_result
                            if isinstance(esdl_service_result, str)
                            else "The external service could not be started"
                        )
                        self.toast_notifications.send(
                            ToastNotification(
                                title=f"An error occurred during run '{run_name}'.",
                                description=description,
                                type=NotificationType.ERROR,
                            )
                        )
                        return None

                    esdl_service_result["model_run_doc"]["is_owner"] = (
                        esdl_service_result["model_run_doc"]["user"] == user_email
                    )
                    emit(
                        "wfe_update_model_run",
                        esdl_service_result["model_run_doc"],
                        namespace="/esdl",
                    )

                    sequence_data.run_id = esdl_service_result["model_run_doc"]["run_id"]
                    sequence_data.model_job_id = esdl_service_result["model_run_doc"]["model_job_id"]
                else:
                    logger.error(f"Type '{init_data['type']}' not implemented for the workflow engine.")
                    return None

                # run subsequent steps on new thread outside request context (will continue when user disconnects)
                if "workflow_engine_next_step" in init_data:
                    t = threading.Thread(
                        target=self.run_sequence,
                        name=f"{user_email}/workflow-engine/{run_name}/{sequence_id}",
                        args=(sequence_data, init_data["workflow_engine_next_step"]),
                    )
                    t.daemon = True
                    t.start()

                self.toast_notifications.send(
                    ToastNotification(
                        title=f"Run '{run_name}' started.",
                        description="",
                        type=NotificationType.INFO,
                    )
                )
                return sequence_id
            except Exception:
                logger.exception("Error while running workflow engine.")
                self.toast_notifications.send(
                    ToastNotification(
                        title=f"Error running '{run_name}'.",
                        description="Please check the selected ESDL and model service",
                        type=NotificationType.ERROR,
                    )
                )

    def run_sequence(self, sequence_data: SequenceData, first_step) -> None:
        logger.info(f"Running workflow sequence for run '{sequence_data.run_name}'")

        next_step = first_step
        run_succeeded = False
        while next_step:
            step_config = self.get_workflow_step_config(sequence_data.main_service_config, next_step)
            logger.info(f"Running workflow engine step '{step_config['id']}' for run '{sequence_data.run_name}'")
            step = WorkflowStep(
                socketio=self.socketio,
                sequence_data=sequence_data,
                step_config=step_config,
                models_storage=self.external_models_storage,
            )
            run_succeeded = step.run()
            logger.info(f"Workflow engine step '{next_step}' finished for run '{sequence_data.run_name}'")
            if (
                run_succeeded
                and "workflow_engine" in step_config
                and "workflow_engine_next_step" in step_config["workflow_engine"]
            ):
                next_step = step_config["workflow_engine"]["workflow_engine_next_step"]
            else:
                next_step = None  # stop workflow sequence

            if (
                run_succeeded
                and "workflow_engine" in step_config
                and "frontend_next_step" in step_config["workflow_engine"]
            ):
                connected_user_client_ids = get_all_session_ids_for_user(sequence_data.user_email)
                if len(connected_user_client_ids) > 0:
                    for client_id in connected_user_client_ids:
                        self.socketio.emit(
                            "wfe_sequence_continue_frontend",
                            {
                                "wfe_sequence_id": sequence_data.id,
                                "run_name": sequence_data.run_name,
                                "next_step": step_config["workflow_engine"]["frontend_next_step"]
                            },
                            namespace="/esdl",
                            room=client_id,
                        )
                    return

        # finish workflow sequence
        logger.info(
            f"Workflow engine sequence finished for run '{sequence_data.run_name}' successfully: '{run_succeeded}'"
        )
        if run_succeeded:
            title = f"Run '{sequence_data.run_name}' succeeded."
            notification_type = NotificationType.SUCCESS
        else:
            self.external_models_storage.update_model_run(sequence_data.run_id, {STATUS: RunStatus.ERROR.value})
            title = f"Run '{sequence_data.run_name}' failed."
            notification_type = NotificationType.ERROR
        self.toast_notifications.send_from_outside_request_context(
            user_email=sequence_data.user_email,
            toast_notification=ToastNotification(
                title=title,
                description="",
                type=notification_type,
            ),
            resend_if_user_offline=True,
        )

    @staticmethod
    def get_workflow_step_config(service_config: dict, step_identifier: str | int) -> dict:
        """Get workflow step config from service config from step_identifier as reference (string) or index (int)."""
        if isinstance(step_identifier, str):
            for step_index, step in enumerate(service_config["workflow"]):
                if step["id"] == step_identifier:
                    return step
        return service_config["workflow"][step_identifier]
