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
from esdl import esdl
from extensions.panel_service import get_panel_service_datasource, create_panel_multiple
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_project_manager, get_session
from src.esdl_helper import get_port_profile_info
from esdl.processing import ESDLQuantityAndUnits
from extensions.profiles import Profiles
import src.log as log

logger = log.get_logger(__name__)

DEFAULT_PROFILE_AGGREGATION_METHOD = "sum"


def send_alert(message):
    print(message)
    emit("alert", message, namespace="/esdl")


class PortProfileViewer:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info("Registering PortProfileViewer extension")

        @self.socketio.on("port_profile_viewer_request_asset", namespace="/esdl")
        def port_profile_viewer_request_asset(asset_id_list):
            with self.flask_app.app_context():
                return PortProfileViewer.get_port_profile_info_multiple_assets(asset_id_list)

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
                if Profiles.check_if_profiles_have_same_host_port_database(profiles_list):
                    # Determine some parameters based on first profile
                    profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(
                        profiles_list[0]
                    )
                    datasource = self.find_datasource(profiles_list[0])

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
                    logger.info("Not all profiles use same host, port, database")
                    return None

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
                    if Profiles.check_if_profiles_have_same_host_port_database(similar_profiles_list):
                        # Determine some parameters based on first profile
                        profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(profile)
                        datasource = Profiles.get_instance().find_datasource(profile)

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
                        logger.info("Not all profiles use same host, port, database")
                        return None

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
            profile_type = ESDLQuantityAndUnits.qau_to_string(qau)
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
    def get_port_profile_info_multiple_assets(asset_id_list):
        """
        Get port profile information in case multiple assets are selected
        """
        pm = get_project_manager()
        active_es_id = get_session("active_es_id")

        port_profile_info_per_asset = list()
        for asset_id in asset_id_list:
            asset = pm.get_by_id(active_es_id, asset_id)
            port_profile_info = get_port_profile_info(asset, only_if_profile=True, only_of_type="InfluxDBProfile")
            port_profile_info_per_asset.append(port_profile_info)

        units_found = {"InPort": list(), "OutPort": list()}
        print(port_profile_info_per_asset)

        # TODO: this only works properly for assets with single In/OutPorts of the same type (so not for assets that
        #  have two InPorts both with "Energy in kWh" as the QaU)
        asset_port_profile_info_first_asset = port_profile_info_per_asset[0]
        for port_profile_info in asset_port_profile_info_first_asset:
            # Find port type (InPort / OutPort) as it's not stored as part of the port_profile_info
            port_id = port_profile_info["port_id"]
            port = pm.get_by_id(active_es_id, port_id)
            port_type = port.eClass.name

            for profile in port_profile_info["profiles"]:
                # Check if other assets have same profile
                all_assets_have_same_profile = True
                all_assets_have_same_profile_name = True
                similar_profile_list = [profile["id"]]
                for other_asset in port_profile_info_per_asset[1:]:
                    for oa_port_profile_info in other_asset:
                        oa_port_id = oa_port_profile_info["port_id"]
                        oa_port = pm.get_by_id(active_es_id, oa_port_id)
                        oa_port_type = oa_port.eClass.name

                        if oa_port_type == port_type:
                            same_profile_found = False
                            same_profile_name_found = False
                            for oa_profile in oa_port_profile_info["profiles"]:
                                # Check for similar QaU
                                if profile["type"] == oa_profile["type"]:
                                    same_profile_found = True
                                    similar_profile_list.append(oa_profile["id"])
                                # Check for similar UI Name
                                if profile["uiname"] == oa_profile["uiname"]:
                                    same_profile_name_found = True

                            if not same_profile_found:
                                all_assets_have_same_profile = False
                                break

                            if not same_profile_name_found:
                                all_assets_have_same_profile_name = False

                if all_assets_have_same_profile:
                    final_profile_info = {"type": profile["type"], "id_list": similar_profile_list}

                    if all_assets_have_same_profile_name:
                        final_profile_info["uiname"] = profile["uiname"]
                    else:
                        final_profile_info["uiname"] = ""

                    units_found[port_type].append(final_profile_info)

        result = list()
        for pt in ["InPort", "OutPort"]:
            for p in units_found[pt]:
                p["port_type"] = pt
                result.append(p)

        return result
