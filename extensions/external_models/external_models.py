import requests
from flask import Flask
from flask_socketio import SocketIO

from src import log
from extensions.session_manager import get_session
from extensions.external_models.external_models_storage import (
    ExternalModelsStorage,
    MODEL_NAME,
    RUN_NAME,
    STATUS,
    USER,
    PROJECTS,
    RUN_ID,
    INPUT_ESDL,
    OUTPUT_ESDL,
    LOGS,
    SUBMITTED_TO_EXTERNAL_MODEL_AT,
)
from src.tno.shared.util import pretty_print_html, parse_url_string_with_parameters

logger = log.get_logger(__name__)


class ExternalModels:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        external_models_storage: ExternalModelsStorage,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.external_models_storage = external_models_storage

        self.register()

    def register(self):
        logger.info("Registering ExternalModelsService extension")

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
            model_runs = self.external_models_storage.get_model_runs_for_current_user(user, user_projects, model_name)

            return model_runs

        @self.socketio.on("external_models_update_run", namespace="/esdl")
        def external_models_update_run(model_run_info) -> None:
            """
            Update Model run data.

            :param model_run_info: external model data.
            """
            logger.info(f"external_models_update_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            self.external_models_storage.update_model_run(run_id, model_run_info)

        @self.socketio.on("external_models_delete_run", namespace="/esdl")
        def external_models_delete_run(model_run_info) -> dict:
            """
            Delete Model run data.

            :param model_run_info: external model data.
            :return: Message with deleted run info.
            """
            logger.info(f"external_models_delete_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]

            deleted_run_data = self.external_models_storage.delete_model_run(run_id)

            delete_result_url = model_run_info.get("delete_result_url")
            if deleted_run_data:
                url = parse_url_string_with_parameters(delete_result_url, deleted_run_data)
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
            model_run_data = self.external_models_storage.get_model_run(run_id)

            text = f"<b>{model_run_data[MODEL_NAME]}</b> run details for: <b>{model_run_data[RUN_NAME]}</b><br>"

            top_keys = [MODEL_NAME, RUN_NAME, STATUS, USER, PROJECTS, RUN_ID]
            omit_keys = [INPUT_ESDL, OUTPUT_ESDL]

            for key in top_keys:
                text += f"<br>{key}: <b>{pretty_print_html(model_run_data[key], '&emsp;')}</b>"
            for key, value in model_run_data.items():
                if key not in top_keys + omit_keys + [LOGS]:
                    text += f"<br>{key}: <b>{pretty_print_html(value, '&emsp;')}</b>"
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
            model_run_data = self.external_models_storage.get_model_run(run_id)

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


