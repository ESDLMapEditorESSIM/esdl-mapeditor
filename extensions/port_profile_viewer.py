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

from flask import Flask
from flask_socketio import SocketIO, emit

from esdl.units.parser import qau_to_string

from dataclasses import dataclass
from typing import List

from esdl import esdl
# TODO: phase out panel service
from extensions.panel_service import get_panel_service_datasource, create_panel_multiple
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_project_manager, get_session
from src.esdl_helper import get_port_profile_info
from extensions.profiles import Profiles, ProfileTracesRequest, ProfileVizOptions, EmptyProfileWarning
import src.log as log

logger = log.get_logger(__name__)

DEFAULT_PROFILE_AGGREGATION_METHOD = "sum"


def send_alert(message):
    print(message)
    emit("alert", message, namespace="/esdl")

@dataclass
class AssetsPortsProfilesRequest:
    es_id: str
    asset_ids: List[str]


class PortProfileViewer:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info("Registering PortProfileViewer extension")

        @self.socketio.on("port_profile_viewer/assets_ports_profiles", namespace="/esdl")
        def _get_assets_ports_profiles(params: dict):
            req = AssetsPortsProfilesRequest(**params)
            return PortProfileViewer.get_assets_ports_profiles(req.es_id, req.asset_ids)


        @self.socketio.on("port_profile_viewer/profile_traces", namespace="/esdl")
        def _get_port_profile_traces_from_profile_ids(params: dict):
            req = ProfileTracesRequest(**params)
            req.viz_options = ProfileVizOptions(**req.viz_options)
            return PortProfileViewer.get_port_profile_traces_from_profile_ids(req)

        @self.socketio.on("show_multiple_profiles", namespace="/esdl")
        def show_multiple_profiles(profile_id_list):
            pm = get_project_manager()
            active_es_id = get_session("active_es_id")

            profiles_list = list()
            for profile_id in profile_id_list:
                profile = pm.get_by_id(active_es_id, profile_id)
                if isinstance(profile, esdl.InfluxDBProfile):
                    profiles_list.append(profile)

            if profiles_list:
                # Check if all profiles use same host / port / database
                try:
                    Profiles.check_if_profiles_have_same_host_port_database(profiles_list)
                except Exception as e:
                    send_alert(f"Could not retrieve data: {str(e)}")
                    return None

                # Determine some parameters based on first profile
                profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(
                    profiles_list[0]
                )
                datasource = PortProfileViewer.find_datasource(profiles_list[0])

                # Create a list with appropriate info for all datasets to be visualized
                dataset_info_list = list()
                for p in profiles_list:
                    alias = PortProfileViewer.determine_profile_alias(p)

                    dataset_info_list.append(
                        {
                            "measurement": p.measurement,
                            "field": p.field,
                            "prof_aggr_type": aggr_method,
                            "alias": alias,
                            "filters": p.filters,
                        }
                    )

                if len(profiles_list) == 1:
                    graph_name = PortProfileViewer.determine_profile_name(profiles_list[0], profile_type)
                else:
                    graph_name = "Multiple profiles (" + profile_type + ")"

                # Grafana datasources don't work anymore with host:443 as a configured host
                # needs to be https://host now
                if profile.port == 443 and not profile.host.startswith("https"):
                    host = "https://" + profile.host
                else:
                    host = profile.host + ":" + str(profile.port) if profile.port else profile.host

                embed_url = create_panel_multiple(
                    graph_title=graph_name,
                    axis_title="",
                    host=host,
                    database=profile.database,
                    dataset_info=dataset_info_list,
                    qau=profile.profileQuantityAndUnit,
                    start_datetime=profile.startDate,
                    end_datetime=profile.endDate,
                    datasource=datasource,
                )
                return embed_url


            else:
                send_alert("ProfileType other than InfluxDBProfile not supported yet")
                return None

        @self.socketio.on("show_similar_profiles", namespace="/esdl")
        def show_similar_profiles(profile_id):
            pm = get_project_manager()
            active_es_id = get_session("active_es_id")
            es = pm.get_energy_system(active_es_id)
            area = es.instance[0].area
            profile = pm.get_by_id(active_es_id, profile_id)

            if profile and isinstance(profile, esdl.InfluxDBProfile):
                profile_class = type(profile).__name__
                profile_field = profile.field
                asset = profile.eContainer().eContainer()

                similar_profiles_list = list()

                for obj in area.eAllContents():
                    if isinstance(obj, type(asset)):
                        for obj2 in obj.eAllContents():
                            # if isinstance(obj2, type(profile)) and obj2.field == profile_field:
                            if isinstance(
                                obj2, type(profile)
                            ) and PortProfileViewer.check_if_profiles_have_same_profile_qau(profile, obj2):
                                similar_profiles_list.append(obj2)

                if similar_profiles_list:
                    # Check if all profiles use same host / port / database
                    try:
                        Profiles.check_if_profiles_have_same_host_port_database(similar_profiles_list)
                    except Exception as e:
                        send_alert(f"Could not retrieve data: {str(e)}")
                        return None

                    # Determine some parameters based on first profile
                    profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(profile)
                    datasource = PortProfileViewer.find_datasource(profile)

                    # Create a list with appropriate info for all datasets to be visualized
                    dataset_info_list = list()
                    for p in similar_profiles_list:
                        alias = PortProfileViewer.determine_profile_alias(p)

                        dataset_info_list.append(
                            {
                                "measurement": p.measurement,
                                "field": p.field,
                                "prof_aggr_type": aggr_method,
                                "alias": alias,
                                "filters": p.filters,
                            }
                        )

                    # Grafana datasources don't work anymore with host:443 as a configured host
                    # needs to be https://host now
                    if profile.port == 443 and not profile.host.startswith("https"):
                        host = "https://" + profile.host
                    else:
                        host = profile.host + ":" + str(profile.port) if profile.port else profile.host

                    embed_url = create_panel_multiple(
                        graph_title="Multiple profiles (asset type: " + type(asset).__name__ + ")",
                        axis_title="",
                        host=host,
                        database=profile.database,
                        dataset_info=dataset_info_list,
                        qau=profile.profileQuantityAndUnit,
                        start_datetime=profile.startDate,
                        end_datetime=profile.endDate,
                        datasource=datasource,
                    )
                    return embed_url

            else:
                send_alert("ProfileType other than InfluxDBProfile not supported yet")
                return None

    @staticmethod
    def determine_profile_aggregation_method(qau: esdl.QuantityAndUnitType):
        # Whether to use "sum" or "mean" does not only depend on the physicalQuantity, but for now start with this list
        # and correct it when we run into problems. This is just a first 'guess' of what parameters need to be summed
        if qau.physicalQuantity in [
            esdl.PhysicalQuantityEnum.ENERGY,
            esdl.PhysicalQuantityEnum.VOLUME,
            esdl.PhysicalQuantityEnum.COST,
            esdl.PhysicalQuantityEnum.LENGTH,
            esdl.PhysicalQuantityEnum.DISTANCE,
            esdl.PhysicalQuantityEnum.WEIGHT,
        ]:
            return "sum"
        else:
            return "mean"

    @staticmethod
    def determine_profile_name(profile, profile_type):
        # Gives back a logical name for the profile panel
        profiles = Profiles.get_instance().get_profiles()["profiles"]
        profile_name = None
        for pkey in profiles:
            p = profiles[pkey]
            if (
                p["database"] == profile.database
                and p["measurement"] == profile.measurement
                and p["field"] == profile.field
            ):
                profile_name = p["profile_uiname"]
        if not profile_name:
            profile_name = profile.field + " (Multiplier: " + str(profile.multiplier) + " - Type: " + profile_type + ")"
        return profile_name

    @staticmethod
    def determine_profile_alias(profile):
        profile_container = profile.eContainer().eContainer()
        if isinstance(profile_container, esdl.EnergyAsset):
            alias = profile_container.name + ": " + profile.field
        else:
            alias = "Cannot determine profile alias - contact us!"
        return alias

    @staticmethod
    def determine_profile_type_and_aggr_method(profile):
        # Determines the profile type (can be the quantity and unit) and aggr_method (based on the quantity and unit)
        qau = profile.profileQuantityAndUnit
        if isinstance(qau, esdl.QuantityAndUnitReference):
            qau = qau.reference
        if qau:
            profile_type = qau_to_string(qau)
            aggr_method = PortProfileViewer.determine_profile_aggregation_method(qau)
        else:
            profile_type = profile.profileType.name
            aggr_method = DEFAULT_PROFILE_AGGREGATION_METHOD

        return profile_type, aggr_method

    @staticmethod
    def find_datasource(profile):
        """
        Find out if credentials are required (these are not stored in the ESDL and must be stored as
        an external profile server configuration)
        """
        credentials = Profiles.get_instance().determine_database_credentials(
            profile.host, profile.port, profile.database
        )
        if credentials:
            datasource = get_panel_service_datasource(
                profile.database,
                profile.host + ":" + str(profile.port),
                credentials["username"],
                credentials["password"],
            )
        else:
            datasource = None  # Let datasource be created (or found) by the create_panel function

        return datasource

    @staticmethod
    def check_if_profiles_have_same_profile_qau(profile1: esdl.GenericProfile, profile2: esdl.GenericProfile):
        qau1 = profile1.profileQuantityAndUnit
        if isinstance(qau1, esdl.QuantityAndUnitReference):
            qau1 = qau1.reference
        qau2 = profile2.profileQuantityAndUnit
        if isinstance(qau2, esdl.QuantityAndUnitReference):
            qau2 = qau2.reference

        if qau1.physicalQuantity != qau2.physicalQuantity:
            return False
        if qau1.unit != qau2.unit:
            return False
        if qau1.multiplier != qau2.multiplier:
            return False
        if qau1.perUnit != qau2.perUnit:
            return False
        if qau1.perMultiplier != qau2.perMultiplier:
            return False
        if qau1.perTimeUnit != qau2.perTimeUnit:
            return False

        return True

    @staticmethod
    def get_assets_ports_profiles(es_id: str, asset_ids: List[str]) -> List[dict]:
        """
        Returns a list of dictionaries with asset and associated ports profiles information.

        Example:
        [
            {
                "asset_id": "asset123",
                "asset_name": "Consumer",
                "ports_profiles": [
                    {
                        "port_id": "port123",
                        "port_name": "In",
                        "port_profiles": [
                            {
                                "id": "profile123",
                                "profileClass": "InfluxDBProfile"
                                ...
                            },
                            ...
                        ]
                    },
                    ...
                ]
            },
            ...
        ]
        """
        assets_ports_profiles = []
        for asset_id in asset_ids:
            asset_ports_profiles = Profiles.get_asset_ports_profiles(es_id=es_id, asset_id=asset_id)
            assets_ports_profiles.append(asset_ports_profiles)

        return assets_ports_profiles

    @staticmethod
    def get_port_profile_traces_from_profile_ids(req: ProfileTracesRequest) -> dict[str, list]:
        """Return a dictionary with profile traces for plotly visualization or warning/error messages."""

        results = {"traces": [], "warnings": [], "errors": []}

        for profile_id in req.profile_ids:
            try:
                trace = Profiles.get_esdl_profile_trace_from_id(req.es_id, profile_id, req.viz_options)
                
                # Enrich trace with profile metadata for legend and subplot grouping
                profile_metadata = _get_profile_metadata(req.es_id, profile_id)                
                trace["legendgroup"] = profile_metadata.get("container_name")
                trace["legendgrouptitle"] = {}
                trace["legendgrouptitle"]["text"] = profile_metadata.get("container_name")
                trace["subplotgroup"] = profile_metadata.get("profile_qau")
                # Replace trace name with displayed name
                trace["name"] = profile_metadata.get("displayed_name")

                results["traces"].append({
                    "profile_id": profile_id,
                    "trace": trace
                })
            except EmptyProfileWarning as warning:
                results["warnings"].append({
                    "profile_id": profile_id,
                    "warning": str(warning)
                })
            except Exception as e:
                results["errors"].append({
                    "profile_id": profile_id,
                    "error": str(e)
                })

        return results


def _get_profile_metadata(es_id: str, profile_id: str) -> dict:
    """A util function to get and return profile metadata in a dictionary for frontend visualization."""

    pm = get_project_manager()
    profile = pm.get_by_id(es_id, profile_id)

    container_name = None
    port_name = None
    qau_description = None
    profile_type = None

    profile_container = profile.eContainer().eContainer()
    if isinstance(profile_container, esdl.EnergyAsset):
        container_name = str(profile_container.name)

    profile_port = profile.eContainer()
    if isinstance(profile_port, esdl.Port):
        port_name = str(profile_port.name)

    if profile.profileType and profile.profileType != esdl.ProfileTypeEnum.UNDEFINED:
        profile_type = str(profile.profileType.name)

    qau = profile.profileQuantityAndUnit
    if qau and isinstance(qau, esdl.QuantityAndUnitReference):
        qau = qau.reference
    if qau:
        qau_description = qau.description if qau.description else qau_to_string(qau)

    meta_parts = [] 
    if port_name is not None:
        meta_parts.append(f"Port={port_name}")
    if profile_type is not None:
        meta_parts.append(f"profileType={profile_type}")

    meta_suffix = ""
    if meta_parts:
        meta_suffix = " (" + ", ".join(meta_parts) + ")"

    if isinstance(profile, esdl.DataTableProfile):
        profile_name = profile.columnName
    elif isinstance(profile, esdl.InfluxDBProfile):
        profile_name = profile.field
    else:
        profile_name = "Unknown"
    qau_unit = qau_description.split(" ")[-1]
    displayed_name = f"{profile_name} [{qau_unit}]{meta_suffix}"

    return {
        "displayed_name": displayed_name,
        "profile_name": profile_name,
        "profile_qau": qau_description,
        "profile_type": profile_type,
        "container_name": container_name,
        "port_name": port_name,
    }