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
from typing import Union

from flask import Flask, jsonify
from flask_socketio import SocketIO

from esdl import esdl
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger

logger = get_logger(__name__)


KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7


class EpsWorkflow:
    """
    The EPS Workflow extension contains functions to retrieve specific ESDL information.
    """

    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage
    ):
        self.flask_app = flask_app

        self.register()

    def register(self):
        logger.info("Registering EpsWorkflow extension")

        @self.flask_app.route("/eps_workflow/get_buildings")
        def get_buildings():
            buildings = _get_buildings_in_active_es()
            building_dicts: list[dict] = []
            for building in buildings:
                kpi_dict = _building_kpis_to_dict(building)
                kpis_value_dict: dict[str, Union[int, float, str]] = {}
                for kpi_name, kpi in kpi_dict.items():
                    kpis_value_dict[kpi_name] = kpi.value
                building_dict = dict(
                    id=building.id,
                    name=building.name,
                    kpis=kpis_value_dict,
                )
                building_dicts.append(building_dict)

            return jsonify(building_dicts), 200


# class BuildingDict(TypedDict):
#     id: str
#     name: str
#     kpis: dict[str, Union[int, float, str]]
#

def _get_buildings_in_active_es() -> list[esdl.AbstractBuilding]:
    """
    Retrieve all buildings in the active energy system.
    """
    active_es_id = get_session("active_es_id")
    esh = get_handler()
    es = esh.get_energy_system(es_id=active_es_id)
    area = es.instance[0].area
    buildings: list[esdl.AbstractBuilding] = []
    for asset in area.asset:
        if isinstance(asset, esdl.AbstractBuilding):
            buildings.append(asset)
    return buildings


def _building_kpis_to_dict(building: esdl.AbstractBuilding) -> dict[str, esdl.KPI]:
    """
    Find all KPIs of a building, and returns it as a dict, indexed by the name.
    """
    kpis: dict[str, esdl.KPI] = {}
    if building.KPIs is not None:
        for kpi in building.KPIs.kpi:
            kpis[kpi.name] = kpi
    return kpis
