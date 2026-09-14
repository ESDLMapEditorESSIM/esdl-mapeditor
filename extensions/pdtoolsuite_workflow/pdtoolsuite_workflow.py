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
import json

import cgi
from collections import defaultdict

import base64
from flask import Flask, jsonify, request
from flask_executor import Executor
from flask_socketio import SocketIO
import os
import requests
from typing import Dict, List, Tuple, Union, cast, Type

from esdl import esdl
from extensions.session_manager import get_project_manager
from extensions.settings_storage import SettingsStorage
from src.esdl_config import ESDL_UPLOAD_PROFILES_HOST
from src.log import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30

KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7


class PDToolsuiteWorkflow:
    """
    The P&D Toolsuite Workflow extension contains functions to retrieve specific ESDL information for the P&D Toolsuite.
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
        logger.info("Registering PDToolsuiteWorkflow extension")

        @self.flask_app.route("/pdtoolsuite_workflow/get_buildings")
        def get_buildings():
            buildings: list[esdl.GenericBuilding] = _get_buildings_in_active_es()
            building_dicts: list[dict] = []
            for building in buildings:
                kpi_dict = _building_kpis_to_dict(building)
                kpis_value_dict: dict[str, Union[int, float, str]] = {}
                for kpi_name, kpi in kpi_dict.items():
                    kpis_value_dict[kpi_name] = kpi.value
                energy_assets_type_dict = _building_energy_assets_to_type_dict(building)
                heatpumps: list[esdl.HeatPump] = cast(list[esdl.HeatPump], energy_assets_type_dict.get("HeatPump"))
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

        @self.socketio.on("get_electricity_networks_active_es", namespace="/esdl")
        def get_electricity_networks_json_forms(params):
            el_networks: list[esdl.Asset] = _get_assets_of_type_in_active_es(esdl.ElectricityNetwork)
            el_networks_options: list[dict] = []
            for el_network in el_networks:
                el_networks_dict = dict(
                    id=el_network.id,
                    title=el_network.name,
                )
                el_networks_options.append(el_networks_dict)

            return el_networks_options, 200

        @self.flask_app.route("/pdtoolsuite_workflow/mock", methods=["POST"])
        def mockdata():
            """
            Mock data for the P&D Toolsuite workflow.
            """
            data = request.data
            json_data = json.loads(data.decode("utf-8"))

            payload = dict(
                esdl=json_data["esdl"],
                business_case_excel="TmFtZSxBZ2UsQ2l0eQpBbGljZSwyNSxOZXcgWW9yawpCb2IsMzAsTG9zIEFuZ2VsZXMKQ2hhcmxpZSwzNSxDaGljYWdvCg ==",
            )

            return jsonify(payload)

        @self.flask_app.route("/pdtoolsuite_workflow/profiles/template", methods=["POST"])
        def generate_profile_template():
            url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/template"
            pm = get_project_manager()
            esdlstr = pm.energy_system_to_string(pm.get_active_energy_system().id)

            base64_es = base64.b64encode(esdlstr.encode("utf-8")).decode()
            payload = dict(
                energysystem=base64_es,
            )

            r = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            return jsonify(r.json())

        @self.flask_app.route("/pdtoolsuite_workflow/profiles/template/progress/<process_id>", methods=["GET"])
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

        @self.flask_app.route("/pdtoolsuite_workflow/profiles/upload", methods=["POST"])
        def upload_profiles():
            base64_file = request.json["base64_file"]
            profiles_upload_file = base64.b64decode(base64_file, b"-_")
            url = f"{ESDL_UPLOAD_PROFILES_HOST}/process/profile"
            pm = get_project_manager()
            esdlstr = pm.energy_system_to_string(pm.get_active_energy_system().id)
            base64_es = base64.b64encode(esdlstr.encode("utf-8")).decode()
            files = dict(energysystem=base64_es, profile_excel=profiles_upload_file)

            r = requests.post(url, files=files, timeout=DEFAULT_TIMEOUT)
            if not r.ok:
                logger.error("Error uploading profiles", status_code=r.status_code, response=r.text)
                return jsonify(dict(error="Error uploading profiles")), r.status_code
            return jsonify(r.json())

        @self.flask_app.route("/pdtoolsuite_workflow/profiles/upload/progress/<process_id>", methods=["GET"])
        def check_upload_profiles(process_id: str):
            response = _check_profiles_progress(process_id)
            if not response.get("finished", False):
                return dict(
                    progress="...",
                    message="Uploading profiles. Please don't close this screen.",
                )

            content, filename = _download_profiles_result(process_id)
            pm = get_project_manager()
            pm.add_from_string(filename, content.decode("utf-8"))
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

def _get_assets_of_type_in_active_es(asset_type: Type[esdl.Asset]) -> List[esdl.Asset]:
    """
    Retrieve all buildings in the active energy system and returns it sorted by name.
    """
    pm = get_project_manager()
    es = pm.get_active_energy_system()
    area = es.instance[0].area
    assets: List[asset_type] = []
    for asset in area.asset:
        if isinstance(asset, asset_type):
            assets.append(asset)
    assets.sort(key=lambda asset: asset.name)
    return assets


def _get_buildings_in_active_es() -> List[esdl.GenericBuilding]:
    """
    Retrieve all buildings in the active energy system and returns it sorted by name.
    """
    pm = get_project_manager()
    es = pm.get_active_energy_system()
    area = es.instance[0].area
    buildings: List[esdl.GenericBuilding] = []
    for asset in area.eAllContents():
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
