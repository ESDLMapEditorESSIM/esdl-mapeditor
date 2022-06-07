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
import os

import tempfile
from flask_executor import Executor
from typing import Dict, List, Optional, TypedDict, Union

from influxdb import InfluxDBClient
from flask import Flask, jsonify, request
from flask_socketio import SocketIO

from extensions.essim import (
    essim_esdl_contents_to_esdl_string,
    retrieve_simulation_from_essim,
)
from esdl import esdl
from extensions.dice_workflow.export_essim import export_energy_system_simulation
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger
from src.settings import essim_config

logger = get_logger(__name__)


KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7

DICE_ESSIM_EXPORTS = "dice_essim_exports"


class DiceESSIMExport(TypedDict):
    simulation_id: str
    finished: bool
    file_paths: Optional[dict[str, str]]


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
            buildings = _get_buildings_in_active_es()
            building_dicts: List[Dict] = []
            for building in buildings:
                kpi_dict = _building_kpis_to_dict(building)
                kpis_value_dict: Dict[str, Union[int, float, str]] = {}
                for kpi_name, kpi in kpi_dict.items():
                    kpis_value_dict[kpi_name] = kpi.value
                building_dict = dict(
                    id=building.id,
                    name=building.name,
                    kpis=kpis_value_dict,
                )
                building_dicts.append(building_dict)

            return jsonify(building_dicts), 200

        @self.flask_app.route("/dice_workflow/export_essim", methods=["GET", "POST"])
        def export_essim():
            if request.method == "GET":
                # Retrieve previously performed exports.
                essim_exports: dict[
                    str, DiceESSIMExport
                ] = self.settings_storage.get_current_user(DICE_ESSIM_EXPORTS)
                finished_essim_exports = [
                    dict(id=essim_export["simulation_id"])
                    for essim_export in essim_exports.values()
                    if essim_export["finished"]
                ]
                return jsonify(finished_essim_exports)
            else:
                # Start new ESSIM export.
                export_json: ExportEssimDict = request.json
                # ESSIM simulation ID. We also use this as process id for the download process..
                simulation_id = export_json["simulation_id"]

                self.settings_storage.del_current_user(DICE_ESSIM_EXPORTS)
                try:
                    user_processes: dict[
                        str, DiceESSIMExport
                    ] = self.settings_storage.get_current_user(DICE_ESSIM_EXPORTS)
                except KeyError:
                    user_processes = dict()

                # Create long process entry in the mongo db.
                essim_export: DiceESSIMExport = dict(
                    simulation_id=simulation_id, finished=False
                )
                user_processes[simulation_id] = essim_export
                self.settings_storage.set_current_user(
                    DICE_ESSIM_EXPORTS, user_processes
                )

                # Start job to generate the export.
                self.executor.submit(
                    _export_energy_system_simulation_task,
                    simulation_id,
                    export_json.get("networks"),
                    self.settings_storage,
                )
                return jsonify({}), 202

        @self.flask_app.route(
            "/dice_workflow/export_essim/<simulation_id>/download", methods=["POST"]
        )
        def export_essim_download(simulation_id: str):
            essim_export: DiceESSIMExport = self.settings_storage.get_current_user(
                DICE_ESSIM_EXPORTS
            ).get(simulation_id)
            if essim_export is None or not essim_export["finished"]:
                return jsonify({}), 404
            logger.info(essim_export)
            file_paths = essim_export["file_paths"]
            return jsonify({})

        @self.flask_app.route(
            "/dice_workflow/export_essim/<simulation_id>", methods=["GET"]
        )
        def export_essim_progress(simulation_id: str):
            essim_export: DiceESSIMExport = self.settings_storage.get_current_user(
                DICE_ESSIM_EXPORTS
            ).get(simulation_id)
            if essim_export is None:
                return dict(progress=0, message="Export not yet started")
            if essim_export["finished"]:
                return dict(progress=100, message="Simulation complete")
            return dict(progress=10, message="Exporting data")


def _export_energy_system_simulation_task(
    simulation_id: str,
    networks: Optional[list[str]],
    settings_storage: SettingsStorage,
):
    """
    A background task to export the energy system simulation results.
    """
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
        result = retrieve_simulation_from_essim(simulation_id)
        esdl_string = essim_esdl_contents_to_esdl_string(result["esdlContents"])
        es, _ = esh.load_external_string(esdl_string, name=f"essim_{simulation_id}")

        results = export_energy_system_simulation(
            influx_client, simulation_id, es, networks
        )
        influx_client.close()
        logger.info("Finished exporting ESSIM, saving result to files")

        # zip_filename = "ESSIM-export-{simulation_id}"
        # zip_file_obj = tempfile.mkstemp()
        # with zipfile.ZipFile(, "w") as zip_object:
        #     file_paths: dict[str, str] = dict()

        file_paths: dict[str, str] = dict()
        dir_path = tempfile.mkdtemp(prefix=f"ESSIM-export-{simulation_id}")
        for filename, df in results.items():
            path = os.path.join(dir_path, filename)
            file_paths[filename] = path
            df.to_excel(path)

        # Find the long process and finalize it.
        user_processes: dict[str, DiceESSIMExport] = settings_storage.get_current_user(
            DICE_ESSIM_EXPORTS
        )
        essim_export = user_processes.get(simulation_id)
        essim_export["finished"] = True
        essim_export["file_paths"] = file_paths
        user_processes[simulation_id] = essim_export
        settings_storage.set_current_user(DICE_ESSIM_EXPORTS, user_processes)
        logger.info("Finished generating ESSIM export")
    except Exception:
        logger.exception("Exception generating ESSIM export")


class ExportEssimDict(TypedDict):
    simulation_id: str
    es_id: Optional[str]
    networks: Optional[list[str]]


def _get_buildings_in_active_es() -> List[esdl.AbstractBuilding]:
    """
    Retrieve all buildings in the active energy system.
    """
    active_es_id = get_session("active_es_id")
    esh = get_handler()
    es = esh.get_energy_system(es_id=active_es_id)
    area = es.instance[0].area
    buildings: List[esdl.AbstractBuilding] = []
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            buildings.append(asset)
    return buildings


def _building_kpis_to_dict(building: esdl.AbstractBuilding) -> Dict[str, esdl.KPI]:
    """
    Find all KPIs of a building, and returns it as a dict, indexed by the name.
    """
    kpis: Dict[str, esdl.KPI] = {}
    if building.KPIs is not None:
        for kpi in building.KPIs.kpi:
            kpis[kpi.name] = kpi
    return kpis
