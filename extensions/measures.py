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
import enum
from typing import Optional, TypedDict, Union

from flask import Flask, jsonify, request
from flask_socketio import SocketIO

from esdl import esdl
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
from src.log import get_logger

logger = get_logger(__name__)


KWH_TO_MJ_FACTOR = 3.6
ENERGY_GAS_MJ_PER_M3 = 31.7


class Measures:
    """
    The workflow extension contains proxy endpoints, to allow the frontend to access defined services.
    """

    def __init__(
        self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage
    ):
        self.flask_app = flask_app

        self.register()

    def register(self):
        logger.info("Registering measures extension")

        @self.flask_app.route("/measures/get_buildings")
        def get_buildings():
            buildings = _get_buildings_in_active_es()
            building_dicts: list[BuildingDict] = []
            for building in buildings:
                kpi_dict = _building_kpis_to_dict(building)
                kpis_value_dict: dict[str, Union[int, float, str]] = {}
                for kpi_name, kpi in kpi_dict.items():
                    kpis_value_dict[kpi_name] = kpi.value
                building_dict: BuildingDict = dict(
                    id=building.id,
                    name=building.name,
                    kpis=kpis_value_dict,
                )
                building_dicts.append(building_dict)

            return jsonify(building_dicts), 200

        @self.flask_app.route("/measures/apply", methods=["POST"])
        def apply_measures():
            measures_to_apply: dict[str, BuildingMeasuresDict] = request.json

            buildings = _get_buildings_in_active_es()
            for building in buildings:
                building_measures = measures_to_apply.get(building.id, None)
                if building_measures is None:
                    continue

                new_elektriciteit_warmtepomp_kwh = building_measures[
                    "pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh"
                ]
                kpi_dict = _building_kpis_to_dict(building)
                energiegebruik_warmtepomp_scenario_kpi = kpi_dict.get(
                    "pand_energiegebruik_elektriciteit_gebouw_warmtepomp_scenario_kWh"
                )
                # Calculate the difference between initial and new value, to modify the KPI.
                warmtepomp_kwh_diff = new_elektriciteit_warmtepomp_kwh - energiegebruik_warmtepomp_scenario_kpi.value
                energiegebruik_warmtepomp_scenario_kpi.value = new_elektriciteit_warmtepomp_kwh

                elektrificatie_proceswarmte_kwh = building_measures[
                    "pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh"
                ]
                elektrificatie_proceswarmte_mj = elektrificatie_proceswarmte_kwh * KWH_TO_MJ_FACTOR
                elektrificatie_proceswarmte_m3_reduction = elektrificatie_proceswarmte_mj / ENERGY_GAS_MJ_PER_M3

                _scale_building(
                    building,
                    kpi_dict,
                    EpsKPIs.pand_energiegebruik_aardgas_gebouw_huidig_m3,
                    EpsKPIs.pand_energiegebruik_aardgas_gebouw_scenario_m3,
                    EpsEnergyAssetNames.gebouwgebonden_gasgebruik,
                    building_measures[
                        "pand_energiegebruik_aardgas_gebouw_schalingsfactor"
                    ],
                )
                _scale_building(
                    building,
                    kpi_dict,
                    EpsKPIs.pand_energiegebruik_aardgas_proces_huidig_m3,
                    EpsKPIs.pand_energiegebruik_aardgas_proces_scenario_m3,
                    EpsEnergyAssetNames.procesgebonden_gasgebruik,
                    building_measures[
                        "pand_energiegebruik_aardgas_proces_schalingsfactor"
                    ],
                    -elektrificatie_proceswarmte_m3_reduction
                )
                _scale_building(
                    building,
                    kpi_dict,
                    EpsKPIs.pand_energiegebruik_elektriciteit_gebouw_huidig_kWh,
                    EpsKPIs.pand_energiegebruik_elektriciteit_gebouw_scenario_kWh,
                    EpsEnergyAssetNames.gebouwgebonden_elektriciteitsgebruik,
                    building_measures[
                        "pand_energiegebruik_elektriciteit_gebouw_schalingsfactor"
                    ],
                    warmtepomp_kwh_diff,
                )
                _scale_building(
                    building,
                    kpi_dict,
                    EpsKPIs.pand_energiegebruik_elektriciteit_proces_huidig_kWh,
                    EpsKPIs.pand_energiegebruik_elektriciteit_proces_scenario_kWh,
                    EpsEnergyAssetNames.procesgebonden_elektriciteitsgebruik,
                    building_measures[
                        "pand_energiegebruik_elektriciteit_proces_schalingsfactor"
                    ],
                    elektrificatie_proceswarmte_kwh,
                )

            return jsonify({}), 200


def _scale_building(
    building: esdl.AbstractBuilding,
    kpi_dict: dict[str, esdl.KPI],
    huidig_kpi_name: str,
    scenario_kpi_name: str,
    asset_name: str,
    scaling_factor: float,
    scenario_fixed_modification: Optional[float] = None,
):
    """
    Scale a building's profiles, based on a current and scenario KPI.
    """
    huidig_kpi = kpi_dict.get(huidig_kpi_name)
    scenario_kpi = kpi_dict.get(scenario_kpi_name)

    # Calculate the factor with which the current profile multiplier was calculated, to be able to scale it.
    current_factor = (
        scenario_kpi.value / huidig_kpi.value if huidig_kpi.value > 0 else 0
    )

    if huidig_kpi is None or scenario_kpi is None:
        logger.warning("KPI's missing. Is this a valid EPS ESDL?")
        return
    scenario_kpi.value = huidig_kpi.value * scaling_factor
    if scenario_fixed_modification:
        # Apply the fixed modification.
        scenario_kpi.value += scenario_fixed_modification
    # Calculate new scaling factor after the fixed addition.
    final_scaling_factor = (
        scenario_kpi.value / huidig_kpi.value if huidig_kpi.value > 0 else 0
    )

    energy_assets_dict = _building_energy_assets_to_dict(building)
    asset = energy_assets_dict.get(asset_name, None)
    if asset is None:
        # Nothing to scale.
        return

    for port in asset.port:
        for profile in port.profile:
            # Scale the multiplier based on the original factor, and the scaling factor (which contains any fixed modification).
            base = (
                profile.multiplier / current_factor
                if current_factor > 0
                else profile.multiplier
            )
            profile.multiplier = base * final_scaling_factor


class EpsEnergyAssetNames(str, enum.Enum):
    gebouwgebonden_elektriciteitsgebruik = "Gebouwgebonden elektriciteitsgebruik"
    procesgebonden_elektriciteitsgebruik = "Procesgebonden elektriciteitsgebruik"
    gebouwgebonden_gasgebruik = "Gebouwgebonden gasgebruik"
    procesgebonden_gasgebruik = "Procesgebonden gasgebruik"


class EpsKPIs(str, enum.Enum):
    pand_energiegebruik_aardgas_gebouw_huidig_m3 = (
        "pand_energiegebruik_aardgas_gebouw_huidig_m3"
    )
    pand_energiegebruik_aardgas_proces_huidig_m3 = (
        "pand_energiegebruik_aardgas_proces_huidig_m3"
    )
    pand_energiegebruik_elektriciteit_gebouw_huidig_kWh = (
        "pand_energiegebruik_elektriciteit_gebouw_huidig_kWh"
    )
    pand_energiegebruik_elektriciteit_proces_huidig_kWh = (
        "pand_energiegebruik_elektriciteit_proces_huidig_kWh"
    )
    pand_energiegebruik_aardgas_gebouw_scenario_m3 = (
        "pand_energiegebruik_aardgas_gebouw_scenario_m3"
    )
    pand_energiegebruik_aardgas_proces_scenario_m3 = (
        "pand_energiegebruik_aardgas_proces_scenario_m3"
    )
    pand_energiegebruik_elektriciteit_gebouw_scenario_kWh = (
        "pand_energiegebruik_elektriciteit_gebouw_scenario_kWh"
    )
    pand_energiegebruik_elektriciteit_proces_scenario_kWh = (
        "pand_energiegebruik_elektriciteit_proces_scenario_kWh"
    )


class BuildingDict(TypedDict):
    id: str
    name: str
    kpis: dict[str, Union[int, float, str]]


class BuildingMeasuresDict(TypedDict):
    pand_energiegebruik_aardgas_gebouw_schalingsfactor: float
    pand_energiegebruik_aardgas_proces_schalingsfactor: float
    pand_energiegebruik_elektriciteit_gebouw_schalingsfactor: float
    pand_energiegebruik_elektriciteit_proces_schalingsfactor: float
    pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh: float
    pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh: float


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


def _building_energy_assets_to_dict(
    building: esdl.AbstractBuilding,
) -> dict[str, esdl.EnergyAsset]:
    """
    Find all KPIs of a building, and returns it as a dict, indexed by the name.
    """
    assets: dict[str, esdl.EnergyAsset] = {}
    if building.asset is not None:
        for asset in building.asset:
            if isinstance(asset, esdl.EnergyAsset):
                assets[asset.name] = asset
    return assets


def _building_profiles(building: esdl.AbstractBuilding) -> list[esdl.ExternalProfile]:
    """
    Find all KPIs of a building, and returns it as a dict, indexed by the name.
    """
    profiles: list[esdl.ExternalProfile] = []
    if building.asset is not None:
        for asset in building.asset:
            for port in asset.port:
                if port.profile:
                    for profile in port.profile:
                        profiles.append(profile)
    return profiles
