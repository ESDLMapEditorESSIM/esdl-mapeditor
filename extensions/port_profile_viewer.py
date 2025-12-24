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
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math
import re

from esdl import esdl
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager
# TODO: phase out panel service
from extensions.panel_service import get_panel_service_datasource, create_panel_multiple
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler, get_session
from src.esdl_helper import get_port_profile_info
from extensions.profiles import Profiles
import src.log as log

logger = log.get_logger(__name__)

DEFAULT_PROFILE_AGGREGATION_METHOD = "sum"


def send_alert(message):
    print(message)
    emit("alert", message, namespace="/esdl")

@dataclass
class AssetsProfilesRequest:
    es_id: str
    asset_ids: List[str]

@dataclass
class ProfileTracesRequest:
    es_id: str
    profile_ids: List[str]
    dt_range: Optional[List[str]] = None
    max_datapoints: Optional[int] = None
    """If specified, downsample profile data to approximately the given value."""

class ProfileNotFoundError(Exception):
    pass

class ProfileRetrievalError(Exception):
    pass

class InfluxDBProfileLoadError(Exception):
    pass


class PortProfileViewer:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info("Registering PortProfileViewer extension")
            
        @self.socketio.on("port_profile_viewer/assets_profiles", namespace="/esdl")
        def _get_assets_profiles(params: dict):
            req = AssetsProfilesRequest(**params)
            return PortProfileViewer.get_assets_profiles(req.es_id, req.asset_ids)
        
        @self.socketio.on("port_profile_viewer/profile_traces", namespace="/esdl")
        def _get_profile_traces_from_profile_ids(params: dict):
            req = ProfileTracesRequest(**params)
            return self.get_profile_traces_from_profile_ids(req)

        @self.socketio.on("show_multiple_profiles", namespace="/esdl")
        def show_multiple_profiles(profile_id_list):
            esh = get_handler()
            active_es_id = get_session("active_es_id")

            profiles_list = list()
            for profile_id in profile_id_list:
                profile = esh.get_by_id(active_es_id, profile_id)
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
            esh = get_handler()
            active_es_id = get_session("active_es_id")
            es = esh.get_energy_system(active_es_id)
            area = es.instance[0].area
            profile = esh.get_by_id(active_es_id, profile_id)

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
    def get_assets_profiles(es_id: str, asset_ids: List[str]) -> list:
        """
        Returns a list of dictionaries with asset and associated profiles information.

        Example:
        [
            {
                "asset_id": "asset123",
                "asset_name": "Consumer",
                "profiles": [
                    {"id": "profile456", "name": "Heat flow [W]"},
                    ...
                ]
            },
            ...
        ]
        """
        assets_profiles = []
        for asset_id in asset_ids:
            asset_name, profiles = PortProfileViewer.get_asset_profiles(es_id, asset_id)
            assets_profiles.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "profiles": profiles
                }
            )

        return assets_profiles
    
    @staticmethod
    def get_asset_profiles(es_id: str, asset_id: str):
        esh = get_handler()
        asset: esdl.Asset = esh.get_by_id(es_id, asset_id)

        port_profile_info: list = get_port_profile_info(asset, only_if_profile=True, only_of_type="InfluxDBProfile")

        profiles = []
        for port in port_profile_info:
            for p in port.get("profiles", []):
                profile_id = p.get("id")
                profile_name = p.get("uiname")
                profile_qau = p.get("type")
                profiles.append(
                    {
                        "id": profile_id,
                        "name": f"{profile_name} [{profile_qau.split(' ')[-1]}]"
                    }
                )

        return asset.name, profiles

    def get_profile_traces_from_profile_ids(self, req: ProfileTracesRequest) -> Dict[str, List[Dict[str, Any]]]:
        """Return a dictionary with profile traces for plotly visualization or error messages."""

        results = {"traces": [], "errors": []}

        for profile_id in req.profile_ids:
            try:
                trace = self.get_profile_trace(req.es_id, profile_id, req.dt_range, req.max_datapoints)
                results["traces"].append({
                    "profile_id": profile_id,
                    "trace": trace
                })
            except Exception as e:
                results["errors"].append({
                    "profile_id": profile_id,
                    "error": str(e)
                })

        return results

    def get_profile_trace(
            self,
            es_id: str,
            profile_id: str,
            dt_range: Optional[List[str]],
            max_datapoints: Optional[int]
        ):
        """
        Return profile trace for plotly visualization.

        TODO: move to esdl/profiles/influxdbprofilemanager.py?
        """

        esh = get_handler()
        dt_str_format = '%Y-%m-%d %H:%M:%S'

        profiles_settings = Profiles.get_instance().get_profiles_settings()

        try:
            profile: esdl.InfluxDBProfile = esh.get_by_id(es_id, profile_id)
            if not profile:
                raise ProfileNotFoundError(f"Profile with ID {profile_id} (ESDL ID {es_id}) not found.")
            
            influxdb_settings = InfluxDBProfileManager.get_profile_influxdb_settings(profile, profiles_settings)
        except Exception as e:
            raise ProfileRetrievalError(f"Failed to retrieve profile {profile_id}: {e}") from e

        query_filters = self._parse_profile_filters(profile.filters)

        try:
            start_date, end_date = self._resolve_date_range(dt_range, profile, dt_str_format)
        except ValueError as e:
            raise ValueError(f"Invalid datetime range format: {e}")

        groupby_interval_sec = self._calculate_groupby_interval(start_date, end_date, max_datapoints)

        try:
            prof_manager = InfluxDBProfileManager(influxdb_settings)
            prof_manager.load_influxdb(
                measurement=profile.measurement,
                fields=[profile.field],
                from_datetime=start_date,
                to_datetime=end_date,
                filters=query_filters,
                groupby_interval_sec=groupby_interval_sec
            )
            # profile_data_list: a list of lists, with each list structure to be [datetime, field value, ...]
            datetime_profile = prof_manager.profile_data_list
        except Exception as e:
            raise InfluxDBProfileLoadError(f"Failed to load profile data for {profile_id}: {e}") from e

        datetimes, values = [], []
        for d in datetime_profile:
            # skip when value is None (this can occur when downsampling is applied)
            if d[1] is None:
                continue

            date: datetime = d[0]
            value = d[1] * profile.multiplier

            datetimes.append(date.strftime(dt_str_format))
            values.append(value)

        trace_name = PortProfileViewer.get_profile_asset_name(profile)
        profile_qau = PortProfileViewer.get_profile_qau_string(profile)

        trace = {
            "name": trace_name,
            "x": datetimes,
            "y": values,
            "legendgroup": profile.field,
            "legendgrouptitle": {"text": profile.field},
            "subplotgroup": profile_qau
        }

        return trace
    
    @staticmethod
    def get_profile_qau_string(profile):
        qau = profile.profileQuantityAndUnit
        if qau and isinstance(qau, esdl.QuantityAndUnitReference):
            qau = qau.reference
        if qau:
            return qau_to_string(qau)

        return "Unknown"
    
    @staticmethod
    def get_profile_asset_name(profile):
        profile_container = profile.eContainer().eContainer()
        if isinstance(profile_container, esdl.EnergyAsset):
            return str(profile_container.name)

        return "Unknown"
    
    def _parse_profile_filters(self, filters: Optional[str]) -> List[Dict[str, str]]:
        """A helper function"""

        if not filters:
            return []
        if "AND" in filters:
            matches = re.findall(r"(\w+)='([^']*)'", filters)
        else:
            matches = re.findall(r'"(\w+)"=\'([^\']+)\'', filters)
        return [{"tag": k, "value": v} for k, v in matches]
    
    def _resolve_date_range(self, dt_range: Optional[List[str]], profile, fmt: str) -> Tuple[datetime, datetime]:
        """A helper function"""

        if dt_range:
            return datetime.strptime(dt_range[0], fmt), datetime.strptime(dt_range[1], fmt)
        return profile.startDate, profile.endDate
    
    def _calculate_groupby_interval(self, start: datetime, end: datetime, max_points: Optional[int]) -> Optional[int]:
        """A helper function"""

        if not max_points:
            return None
        time_delta_sec = (end - start).total_seconds()
        # To round to common (readable) interval: 1s, 30s, 1m, 30m, 1h, 6h, 12h, 1d
        common_intervals = [1, 30, 60, 1800, 3600, 21600, 43200, 86400]
        interval_sec = math.ceil(time_delta_sec / max_points)
        return min(common_intervals, key=lambda x: abs(x - interval_sec))