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
from uuid import uuid4

import cgi
from collections import defaultdict

import base64
from datetime import datetime
from flask import Flask, jsonify, request
from flask_executor import Executor
from flask_socketio import SocketIO
from influxdb import InfluxDBClient
import io
import os
import requests
import tempfile
from typing import Dict, List, Optional, Tuple, TypedDict, Union, cast
import zipfile

from esdl import esdl
from extensions.dice_workflow.export_bc import export_business_case
from extensions.dice_workflow.export_essim import export_energy_system_simulation
from extensions.essim import (
    essim_esdl_contents_to_esdl_string,
    retrieve_simulation_from_essim,
)
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.esdl_config import ESDL_UPLOAD_PROFILES_HOST
from src.log import get_logger
from src.settings import essim_config

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30

KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7

DICE_ESSIM_EXPORTS = "dice_essim_exports"


class DiceESSIMExportType:
    ICE = "ICE"
    BUSINESS_CASE = "BUSINESS_CASE"


class DiceESSIMExport(TypedDict):
    simulation_id: str
    start_date: str  # Isoformat
    export_type: str  # See DiceEssimExportType
    end_date: Optional[str]
    failed_msg: Optional[str]
    finished: bool
    file_paths: Optional[Dict[str, str]]


class DiceWorkflow:
    """
    The DICE Workflow extension contains functions to retrieve specific ESDL information.
    """

    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
        executor: Executor,
        settings_storage: SettingsStorage,
    ):
        self.flask_app = flask_app
        self.socketio = socket
        self.executor = executor
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info("Registering DiceWorkflow extension")

        @self.flask_app.route("/dice_workflow/get_buildings")
        def get_buildings():
            buildings: List[esdl.GenericBuilding] = _get_buildings_in_active_es()
            building_dicts: List[Dict] = []
            for building in buildings:
                kpi_dict = _building_kpis_to_dict(building)
                kpis_value_dict: Dict[str, Union[int, float, str]] = {}
                for kpi_name, kpi in kpi_dict.items():
                    kpis_value_dict[kpi_name] = kpi.value
                energy_assets_type_dict = _building_energy_assets_to_type_dict(building)
                heatpumps: List[esdl.HeatPump] = cast(
                    List[esdl.HeatPump], energy_assets_type_dict.get("HeatPump")
                )
                if heatpumps:
                    heatpump_efficiency = heatpumps[0].COP
                else:
                    heatpump_efficiency = None
                building_dict = dict(
                    id=building.id,
                    name=building.name,
                    address=building.address,
                    kpis=kpis_value_dict,
                    heatpump_efficiency=heatpump_efficiency,
                )
                building_dicts.append(building_dict)

            return jsonify(building_dicts), 200

        @self.flask_app.route("/dice_workflow/profiles/template", methods=["POST"])
        def generate_profile_template():
            url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/template"
            active_es_id = get_session("active_es_id")
            esh = get_handler()

            base64_es = base64.b64encode(
                esh.to_string(active_es_id).encode("utf-8")
            ).decode()
            payload = dict(
                energysystem=base64_es,
            )

            r = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            return jsonify(r.json())

        @self.flask_app.route(
            "/dice_workflow/profiles/template/progress/<process_id>", methods=["GET"]
        )
        def check_generate_profile_template(process_id: str):
            response = _check_profiles_progress(process_id)
            if not response.get("finished", False):
                return dict(
                    progress="...",
                    message="Generating profile template. Please don't close this screen.",
                )

            content, filename = _download_profiles_result(process_id)
            base64_file = base64.b64encode(content).decode()
            return (
                jsonify(
                    dict(
                        base64file=base64_file,
                        filename=filename,
                        progress=100,
                        message="Profile template complete. It should be downloaded automatically.",
                    )
                ),
                200,
            )

        @self.flask_app.route("/dice_workflow/profiles/upload", methods=["POST"])
        def upload_profiles():
            base64_file = request.json["base64_file"]
            profiles_upload_file = base64.b64decode(base64_file, b"-_")
            url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/profile"
            active_es_id = get_session("active_es_id")
            esh = get_handler()
            base64_es = base64.b64encode(
                esh.to_string(active_es_id).encode("utf-8")
            ).decode()
            files = dict(energysystem=base64_es, profile_excel=profiles_upload_file)

            r = requests.post(url, files=files, timeout=DEFAULT_TIMEOUT)
            return jsonify(r.json())

        @self.flask_app.route(
            "/dice_workflow/profiles/upload/progress/<process_id>", methods=["GET"]
        )
        def check_upload_profiles(process_id: str):
            response = _check_profiles_progress(process_id)
            if not response.get("finished", False):
                return dict(
                    progress="...",
                    message="Uploading profiles. Please don't close this screen.",
                )

            content, filename = _download_profiles_result(process_id)
            esh = get_handler()
            esh.add_from_string(filename, content.decode("utf-8"))
            return (
                jsonify(
                    dict(
                        filename=filename,
                        progress=100,
                        message="Profile upload complete.",
                    )
                ),
                200,
            )

        @self.flask_app.route("/dice_workflow/export_essim", methods=["GET", "POST"])
        def export_essim():
            if request.method == "GET":
                # Retrieve previously performed exports.
                try:
                    essim_exports: dict[
                        str, DiceESSIMExport
                    ] = self.settings_storage.get_for_current_user(DICE_ESSIM_EXPORTS)
                except KeyError:
                    essim_exports = dict()
                finished_essim_exports = []
                for essim_export in essim_exports.values():
                    if essim_export["finished"]:
                        simulation_id = essim_export["simulation_id"]
                        result = retrieve_simulation_from_essim(simulation_id)
                        export_type = essim_export.get(
                            "export_type", DiceESSIMExportType.ICE
                        )
                        if export_type == DiceESSIMExportType.BUSINESS_CASE:
                            export_type = "Business Case"
                        finished_essim_exports.append(
                            dict(
                                key=simulation_id,
                                export_type=export_type,
                                date=essim_export.get(
                                    "start_date", datetime.now().isoformat()
                                ),
                                description=result["simulationDescription"],
                            )
                        )
                return jsonify(finished_essim_exports)
            else:
                # Start new ESSIM export.
                export_json: ExportEssimDict = request.json
                # ESSIM simulation ID. We also use this as process id for the download process..
                simulation_id = export_json["simulation_id"]
                export_type = export_json["export_type"]

                self.settings_storage.del_for_current_user(DICE_ESSIM_EXPORTS)
                try:
                    user_processes: dict[
                        str, DiceESSIMExport
                    ] = self.settings_storage.get_for_current_user(DICE_ESSIM_EXPORTS)
                except KeyError:
                    user_processes = dict()

                # Create ESSIM export entry in the mongo db.
                essim_export: DiceESSIMExport = dict(
                    simulation_id=simulation_id,
                    start_date=datetime.now().isoformat(),
                    export_type=export_type,
                    end_date=None,
                    failed_msg=None,
                    finished=False,
                    file_paths=None,
                )
                user_processes[simulation_id] = essim_export
                self.settings_storage.set_for_current_user(
                    DICE_ESSIM_EXPORTS, user_processes
                )

                # Start job to generate the export.
                self.executor.submit(
                    _export_energy_system_simulation_task,
                    simulation_id,
                    export_type,
                    export_json.get("networks"),
                    self.settings_storage,
                )
                return jsonify({}), 202

        @self.flask_app.route(
            "/dice_workflow/export_essim/<simulation_id>/download", methods=["POST"]
        )
        def export_essim_download(simulation_id: str):
            essim_export: DiceESSIMExport = self.settings_storage.get_for_current_user(
                DICE_ESSIM_EXPORTS
            ).get(simulation_id)
            if essim_export is None or not essim_export["finished"]:
                return jsonify({}), 404
            file_paths = essim_export.get("file_paths", [])

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_object:
                # Add multiple files to the zip
                for file_name, file_path in file_paths.items():
                    if os.path.isfile(file_path):
                        zip_object.write(file_path, arcname=file_name)
            zip_buffer.seek(0)
            zip_filename = f"ESSIM-export-{simulation_id}.zip"

            return jsonify(
                dict(
                    filename=zip_filename,
                    base64_file=base64.b64encode(zip_buffer.read()).decode(),
                )
            )

        @self.flask_app.route(
            "/dice_workflow/export_essim/<simulation_id>", methods=["GET"]
        )
        def export_essim_progress(simulation_id: str):
            try:
                essim_export: DiceESSIMExport = (
                    self.settings_storage.get_for_current_user(DICE_ESSIM_EXPORTS).get(
                        simulation_id
                    )
                )
            except KeyError:
                return dict(progress=0, message="Export not yet started")

            if essim_export is None:
                return dict(progress=0, message="Export not yet started")
            if essim_export["failed_msg"]:
                return dict(
                    progress=100, failed=True, message=essim_export["failed_msg"]
                )
            if essim_export["finished"]:
                return dict(progress=100, message="Export complete")
            return dict(progress=10, message="Exporting data")


def _export_energy_system_simulation_task(
    simulation_id: str,
    export_type: str,
    networks: Optional[List[str]],
    settings_storage: SettingsStorage,
):
    """
    A background task to export the energy system simulation results.
    """
    user_processes: Dict[str, DiceESSIMExport] = settings_storage.get_for_current_user(
        DICE_ESSIM_EXPORTS
    )
    essim_export = user_processes.get(simulation_id)
    try:
        logger.info("Exporting energy system simulation results")

        influx_url_parts = (
            essim_config["influx_mapeditor_url"].replace("http://", "").rpartition(":")
        )
        influx_client = InfluxDBClient(influx_url_parts[0], influx_url_parts[2])

        db = influx_client.get_list_database()[-1]["name"]
        influx_client.switch_database(db)

        # if no networks are passed export all networks found in influxdb
        if not networks:
            networks = [x["name"] for x in influx_client.get_list_measurements()]

        esh = get_handler()
        # Get ESDL from ESSIM.
        essim_simulation_run = retrieve_simulation_from_essim(simulation_id)
        esdl_string = essim_esdl_contents_to_esdl_string(
            essim_simulation_run["esdlContents"]
        )
        es, _ = esh.load_external_string(esdl_string, name=f"essim_{simulation_id}")

        dir_path = tempfile.mkdtemp(
            prefix=f"ESSIM-export-{export_type}-{simulation_id}"
        )
        file_paths: Dict[str, str] = dict()

        if export_type == DiceESSIMExportType.BUSINESS_CASE:
            business_case_export_wb = export_business_case(
                influx_client, simulation_id, es
            )
            logger.info("Finished exporting business case, saving result to file")
            filename = "business_case.xlsx"
            path = os.path.join(dir_path, filename)
            file_paths[filename] = path
            business_case_export_wb.save(path)
        else:
            results = export_energy_system_simulation(
                influx_client, simulation_id, es, networks
            )
            logger.info("Finished exporting ICE, saving result to files")

            for filename, df in results.items():
                path = os.path.join(dir_path, filename)
                file_paths[filename] = path
                df.to_excel(path)

        influx_client.close()

        # Find the long process and finalize it.
        essim_export["finished"] = True
        essim_export["end_date"] = datetime.now().isoformat()
        essim_export["file_paths"] = file_paths
        logger.info("Finished generating ESSIM export")
    except Exception as e:
        essim_export["failed_msg"] = f"Error generating export"
        essim_export["finished"] = True
        logger.exception("Error generating DICE export")
    finally:
        user_processes[simulation_id] = essim_export
        settings_storage.set_for_current_user(DICE_ESSIM_EXPORTS, user_processes)


class ExportEssimDict(TypedDict):
    simulation_id: str
    export_type: str
    es_id: Optional[str]
    networks: Optional[List[str]]


def _get_buildings_in_active_es() -> List[esdl.GenericBuilding]:
    """
    Retrieve all buildings in the active energy system and returns it sorted by name.
    """
    active_es_id = get_session("active_es_id")
    esh = get_handler()
    es = esh.get_energy_system(es_id=active_es_id)
    area = es.instance[0].area
    buildings: List[esdl.GenericBuilding] = []
    for asset in area.asset:
        if isinstance(asset, esdl.GenericBuilding):
            buildings.append(asset)
    buildings.sort(key=lambda building: building.name)
    return buildings


def _building_kpis_to_dict(building: esdl.GenericBuilding) -> Dict[str, esdl.KPI]:
    """
    Find all KPIs of a building, and returns it as a dict, indexed by the name.
    """
    kpis: Dict[str, esdl.KPI] = {}
    if building.KPIs is not None:
        for kpi in building.KPIs.kpi:
            kpis[kpi.name] = kpi
    return kpis


def _building_energy_assets_to_type_dict(
    building: esdl.AbstractBuilding,
) -> Dict[str, List[esdl.EnergyAsset]]:
    """
    Find all assets of a building, and returns it as a dict, indexed by the type.
    """
    assets: Dict[str, List[esdl.EnergyAsset]] = defaultdict(list)
    if building.asset is not None:
        for asset in building.asset:
            if isinstance(asset, esdl.EnergyAsset):
                assets[type(asset).__name__].append(asset)
    return assets


def _check_profiles_progress(process_id: str) -> dict:
    """
    Check progress for the profiles operations.
    """
    url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/{process_id}/finished"
    r = requests.get(url, timeout=DEFAULT_TIMEOUT)
    logger.info("Response", json=r.json())
    return r.json()


def _download_profiles_result(process_id: str) -> Tuple[bytes, str]:
    """
    Download the result from the profiles operation.
    """
    url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/{process_id}/result"
    r = requests.get(url, timeout=DEFAULT_TIMEOUT)
    parsed_header = cgi.parse_header(r.headers["Content-Disposition"])[-1]
    filename = os.path.basename(parsed_header["filename"])
    return r.content, filename
