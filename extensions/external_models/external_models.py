#  This work is based on original code developed and copyrighted by TNO 2025.
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
import io
import os

import pandas as pd
import requests
from flask import Flask
from flask_socketio import SocketIO

from extensions.profiles import Profiles
from extensions.toast_notifications import (
    ToastNotification,
    NotificationType,
    ToastNotifications,
    FileDownload,
    FileDownloadType,
)
from src import log
from extensions.session_manager import get_session, get_handler
from extensions.external_models.external_models_storage import (
    ExternalModelsStorage,
    MODEL_NAME,
    RUN_NAME,
    STATUS,
    USER,
    USER_GROUP_PATHS,
    RUN_ID,
    INPUT_ESDL,
    OUTPUT_ESDL,
    LOGS,
    SUBMITTED_TO_EXTERNAL_MODEL_AT,
)
from src.tno.shared.util import pretty_print_html, parse_string_with_parameters

logger = log.get_logger(__name__)


class ExternalModels:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        external_models_storage: ExternalModelsStorage,
        toast_notifications: ToastNotifications,
    ) -> None:
        self.flask_app = flask_app
        self.socketio = socket
        self.external_models_storage = external_models_storage
        self.toast_notifications = toast_notifications

        self.register()

    def register(self) -> None:
        logger.info("Registering ExternalModelsService extension")

        @self.socketio.on("get_external_model_runs_for_user", namespace="/esdl")
        def get_external_model_runs_for_user(model_run_info: dict) -> list:
            """
            Check if updated progress or new results are available and get runs for external model.

            :param model_run_info: external model data.
            """
            logger.info(f"get_external_model_runs_for_user: {model_run_info}")
            model_name = model_run_info["external_model_name"]

            user = get_session("user-email")
            user_group_paths = get_session("user-group-path")
            model_runs = self.external_models_storage.get_model_runs_for_current_user(
                user, user_group_paths, model_name
            )

            for model_run in model_runs:
                model_run["is_owner"] = model_run["user"] == user

            return model_runs

        @self.socketio.on("external_models_update_run", namespace="/esdl")
        def external_models_update_run(model_run_info: dict) -> None:
            """
            Update Model run data.

            :param model_run_info: external model data.
            """
            logger.info(f"external_models_update_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            self.external_models_storage.update_model_run(run_id, model_run_info)

        @self.socketio.on("external_models_download_run", namespace="/esdl")
        def external_models_download_run(model_run_info: dict) -> dict:
            """
            Download Model run influxdb data.

            :param model_run_info: external model data.
            :return: Message with deleted run info.
            """
            logger.info(f"external_models_download_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            backend_process_id = model_run_info.get("backend_process_id")
            filter_on_tag = model_run_info.get("filter_on_tag")
            esdl_object_name_field = model_run_info.get("esdl_object_name_field")
            excel_sheets_per_table = model_run_info.get("excel_sheets_per_table")
            influxdb_host_override = model_run_info.get("influxdb_host_override")
            influxdb_port_override = model_run_info.get("influxdb_port_override")

            run_data = self.external_models_storage.get_model_run(run_id)

            self.toast_notifications.send(
                ToastNotification(
                    title=f"Extracting timeseries data for run: '{run_data[RUN_NAME]}'",
                    description="",
                    type=NotificationType.INFO,
                )
            )

            esdl_str = run_data.get("output_esdl")
            if not esdl_str:
                esdl_str = run_data.get("input_esdl")

            esh = get_handler()
            es, parse_info = esh.add_from_string("ext_mod_download", esdl_str)

            influxdb_client = None
            try:
                influxdb_client = Profiles.connect_to_animation_profiles_database(
                    es.id, es.id, influxdb_host_override, influxdb_port_override
                )
                # Query to get the list of measurements in the database
                measurements_query = "SHOW MEASUREMENTS"
                measurements_result = influxdb_client.query(measurements_query)

                # Extract measurement names from the query result
                measurement_names = [measurement["name"] for measurement in measurements_result.get_points()]

                # per table (measurement), extract data for specified sheets
                processed_data = {}
                for measurement_name in measurement_names:
                    for sheet_config in excel_sheets_per_table:
                        sheet_name = measurement_name + "_" + sheet_config["name_postfix"]

                        field_name_recorded_per_esdl_object = sheet_config.get("field_name_recorded_per_esdl_object")
                        field_names_unrelated_to_esdl_objects = sheet_config.get(
                            "field_names_unrelated_to_esdl_objects"
                        )

                        # set all fields to extract
                        fields = [esdl_object_name_field]
                        exclude_values: dict = sheet_config.get("exclude_values")
                        if field_name_recorded_per_esdl_object:
                            fields.append(field_name_recorded_per_esdl_object)
                        if field_names_unrelated_to_esdl_objects:
                            fields += field_names_unrelated_to_esdl_objects
                        if exclude_values:
                            fields.append(exclude_values["field_name"])

                        # Query to fetch all data from the current measurement, sheet
                        query = f'SELECT {",".join(fields)} FROM "{measurement_name}"'

                        if filter_on_tag:
                            sim_id = run_data[filter_on_tag["value_database_key"]]
                            query += f" WHERE \"{filter_on_tag['tag_name']}\"='{sim_id}'"

                        # Execute the query
                        results = influxdb_client.query(query)

                        sheet_data = []
                        new_row = None
                        for result_row in results.get_points():
                            time_in_datetime = pd.to_datetime(result_row["time"]).tz_localize(None)
                            if not new_row:  # only for first row
                                new_row = {"time": time_in_datetime}
                            elif (
                                time_in_datetime != new_row["time"]
                            ):  # create new row (assumes results rows sorted by time)
                                if new_row:
                                    sheet_data.append(new_row)
                                new_row = {"time": time_in_datetime}

                            if exclude_values:
                                if result_row[exclude_values["field_name"]] in exclude_values["values_to_exclude"]:
                                    continue  # skip result row

                            if field_name_recorded_per_esdl_object in result_row and result_row[esdl_object_name_field]:
                                esdl_object_name = result_row[esdl_object_name_field]
                                new_row[esdl_object_name] = result_row[field_name_recorded_per_esdl_object]
                            if field_names_unrelated_to_esdl_objects:
                                for field_name in field_names_unrelated_to_esdl_objects:
                                    if field_name in result_row:
                                        new_row[field_name] = result_row[field_name]
                        if new_row:  # last row has not been appended yet
                            sheet_data.append(new_row)
                        if sheet_data:
                            processed_data[sheet_name] = sheet_data

                if not processed_data:
                    raise RuntimeError("No data found.")

                # remove common starting part from sheet names
                common_name = None
                if len(processed_data) <= 1:
                    common_name = ""
                else:
                    for sheet_name in processed_data.keys():
                        if common_name:
                            common_name = os.path.commonprefix([common_name, sheet_name])
                        else:
                            common_name = sheet_name
                for sheet_name in list(processed_data.keys()):
                    processed_data[sheet_name.replace(common_name, "")] = processed_data.pop(sheet_name)

                # Create an in-memory bytes buffer for Excel file
                buffer = io.BytesIO()

                # Write the DataFrame to an Excel file in the buffer
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    # Loop through all sheets
                    for sheet_name, sheet_data in processed_data.items():
                        df = pd.DataFrame(sheet_data)
                        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])

                # Reset the buffer's position to the beginning
                buffer.seek(0)

                # Encode the buffer's content in base64
                encoded_excel = base64.b64encode(buffer.getvalue()).decode("utf-8")

                self.toast_notifications.send(
                    ToastNotification(
                        title=f"Time series data extracted, downloading: '{run_data[RUN_NAME]}.xlsx'.",
                        description="Check your browser downloads",
                        type=NotificationType.SUCCESS,
                        close_after_seconds=8,
                        file_download=FileDownload(
                            file_name=f"{run_data[RUN_NAME]}.xlsx",
                            content_b64string=encoded_excel,
                            file_type=FileDownloadType.EXCEL,
                        ),
                    )
                )
            except ConnectionError as e:
                self.toast_notifications.send(
                    ToastNotification(
                        title=f"Could not connect to the time series database: '{es.id}'.",
                        description=str(e),
                        type=NotificationType.ERROR,
                    )
                )
            except Exception as e:
                self.toast_notifications.send(
                    ToastNotification(
                        title=f"Error extracting time series data for: '{run_data[RUN_NAME]}.",
                        description=str(e),
                        type=NotificationType.ERROR,
                    )
                )
            finally:
                # Close the client connection
                if influxdb_client:
                    influxdb_client.close()

                if backend_process_id:
                    self.socketio.emit(
                        "backend_process_complete",
                        dict(backend_process_id=backend_process_id),
                        namespace="/esdl",
                    )

                return {"message": f"{run_data[MODEL_NAME]} run '{run_data[RUN_NAME]}' downloaded ok."}

        @self.socketio.on("external_models_delete_run", namespace="/esdl")
        def external_models_delete_run(model_run_info: dict) -> dict:
            """
            Delete Model run data.

            :param model_run_info: external model data.
            :return: Message with deleted run info.
            """
            logger.info(f"external_models_delete_run: {model_run_info}")
            run_id = model_run_info[RUN_ID]

            deleted_run_data = self.external_models_storage.delete_model_run(run_id)

            delete_result_url = model_run_info.get("delete_result_url")
            if deleted_run_data and delete_result_url:
                url = parse_string_with_parameters(delete_result_url, deleted_run_data)
                try:
                    requests.delete(url)
                except Exception as e:
                    logger.warning(f"Error while deleting external model run results: {str(e)}")
            return {"message": f"{deleted_run_data[MODEL_NAME]} run '{deleted_run_data[RUN_NAME]}' deleted ok."}

        @self.socketio.on("external_models_get_run_text", namespace="/esdl")
        def external_models_get_run_text(model_run_info: dict):
            """
            Get model run details as text omitting certain parameters which are too long or not relevant.

            :param model_run_info: external model data.
            :return: Run details as text.
            """
            logger.info(f"external_models_get_run_text: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            model_run_data = self.external_models_storage.get_model_run(run_id)

            text = f"<b>{model_run_data[MODEL_NAME]}</b> run details for: <b>{model_run_data[RUN_NAME]}</b><br>"

            top_keys = [MODEL_NAME, RUN_NAME, STATUS, USER, USER_GROUP_PATHS, RUN_ID]
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
        def external_models_get_run_jsonforms(model_run_info: dict) -> dict:
            """
            Get run data as jsonforms with the run name and user group paths as editable, and some other details as
            readonly.

            :param model_run_info: external model data.
            :return: Run details as jsonforms dictionary.
            """
            logger.info(f"external_models_get_run_jsonforms: {model_run_info}")
            run_id = model_run_info[RUN_ID]
            model_run_data = self.external_models_storage.get_model_run(run_id)

            user_group_paths = get_session("user-group-path")
            properties = {}
            required = []
            form_data = {}
            ui_elements = []

            properties[RUN_NAME] = dict(type="string", minLength=3, title="name")
            required.append(RUN_NAME)
            form_data[RUN_NAME] = model_run_data[RUN_NAME]
            ui_elements.append(dict(type="Control", scope=f"#/properties/{RUN_NAME}"))

            if user_group_paths:
                properties[USER_GROUP_PATHS] = dict(
                    type="array", title="user groups", uniqueItems=True, items=dict(type="string", enum=user_group_paths)
                )
                form_data[USER_GROUP_PATHS] = model_run_data[USER_GROUP_PATHS]
                ui_elements.append(dict(type="Control", scope=f"#/properties/{USER_GROUP_PATHS}"))

            info_keys = [MODEL_NAME, USER, STATUS, RUN_ID, SUBMITTED_TO_EXTERNAL_MODEL_AT]
            for key, value in model_run_data.items():
                if key in info_keys:
                    properties[key] = dict(type="string", readOnly=True)
                    ui_elements.append(dict(type="Control", scope=f"#/properties/{key}", className=""))
                    form_data[key] = value

            return dict(
                schema=dict(
                    type="object",
                    properties=properties,
                    required=required,
                ),
                formData=form_data,
                uischema=dict(type="VerticalLayout", elements=ui_elements),
            )

        @self.socketio.on("get_user_group_paths", namespace="/esdl")
        def get_user_group_paths() -> list:
            """
            Get user group paths.

            :return: list of user group paths.
            """
            return get_session("user-group-path")
