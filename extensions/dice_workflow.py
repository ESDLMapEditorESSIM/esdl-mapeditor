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

from esdl import esdl
from extensions.dice_workflow_utils.export_essim import export_energy_system_simulation
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger
from src.settings import essim_config

logger = get_logger(__name__)


KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7


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
        self.settings_storage = SettingsStorage
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

        @self.flask_app.route("/dice_workflow/export_essim", methods=["POST"])
        def export_essim():
            export_json: ExportEssimDict = request.json
            active_es_id = get_session("active_es_id")
            es_id = export_json.get("es_id", None)
            if es_id is None:
                es_id = active_es_id
            else:
                esh = get_handler()
                es = esh.get_energy_system(es_id=es_id)
                if es is None:
                    return (
                        jsonify(
                            dict(
                                message=f"Energy system with ID {es_id} not found. Please make sure to upload the energy system for which this ESSIM run was performed."
                            )
                        ),
                        400,
                    )

            simulation_id = export_json["simulation_id"]

            # Start job to generate the export.
            self.executor.submit(
                _export_energy_system_simulation_task,
                es_id,
                simulation_id,
                export_json.get("networks"),
            )
            return jsonify({}), 202


def _export_energy_system_simulation_task(
    es_id: str, simulation_id: str, networks: Optional[list[str]]
):
    """
    A background task to export the energy system simulation results.
    """
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
    es = esh.get_energy_system(es_id=es_id)

    results = export_energy_system_simulation(
        influx_client, simulation_id, es, networks
    )
    logger.info(results)

    dir_path = tempfile.mkdtemp(prefix=f"ESSIM-{simulation_id}-")
    for filename, df in dir_path.values():
        path = (os.path.join(dir_path, filename),)
        df.to_excel(path)
    logger.info("Finished generating energy system simulation results")
    influx_client.close()


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
