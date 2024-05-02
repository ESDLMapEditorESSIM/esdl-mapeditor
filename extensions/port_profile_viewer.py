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
from extensions.session_manager import get_handler, get_session
from extensions.profiles import create_panel
from src.esdl_helper import get_port_profile_info
from esdl.processing import ESDLQuantityAndUnits
from extensions.profiles import Profiles
import src.log as log

logger = log.get_logger(__name__)

DEFAULT_PROFILE_AGGREGATION_METHOD = "sum"

def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class PortProfileViewer:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info("Registering PortProfileViewer extension")

        @self.socketio.on('port_profile_viewer_request_asset', namespace='/esdl')
        def port_profile_viewer_request_asset(id):
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')
                asset = esh.get_by_id(active_es_id, id)
                return get_port_profile_info(asset)

        @self.socketio.on('get_profile_panel', namespace='/esdl')
        def get_profile_panel(profile_id):
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            profile = esh.get_by_id(active_es_id, profile_id)

            if profile:
                profile_class = type(profile).__name__

                if profile_class == "InfluxDBProfile":
                    profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(profile)
                    profile_name = PortProfileViewer.determine_profile_name(profile, profile_type)
                    datasource = self.find_datasource(profile)

                    embed_url = create_panel(
                        graph_title=profile_name,
                        axis_title="",
                        host=profile.host+':'+str(profile.port),
                        database=profile.database,
                        measurement=profile.measurement,
                        field=profile.field,
                        filters=profile.filters,
                        qau=profile.profileQuantityAndUnit,
                        prof_aggr_type=aggr_method,
                        start_datetime=profile.startDate,
                        end_datetime=profile.endDate,
                        datasource=datasource
                    )
                    if embed_url:
                        return embed_url
                    else:
                        return None
                else:
                    send_alert('ProfileType other than InfluxDBProfile not supported yet')
                    return None

        @self.socketio.on('show_similar_profiles', namespace='/esdl')
        def show_similar_profiles(profile_id):
            esh = get_handler()
            active_es_id = get_session('active_es_id')
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
                            if isinstance(obj2, type(profile)) and obj2.field == profile_field:
                                similar_profiles_list.append(obj2)

                if similar_profiles_list:
                    # Check if all profiles use same host / port / database
                    if PortProfileViewer.check_if_profiles_have_same_host_port_database(similar_profiles_list):
                        # Determine some parameters based on first profile
                        profile_type, aggr_method = PortProfileViewer.determine_profile_type_and_aggr_method(profile)
                        datasource = self.find_datasource(profile)
                        alias = PortProfileViewer.determine_profile_alias(profile)

                        # Create a list with appropriate info for all datasets to be visualized
                        dataset_info_list = list()
                        for p in similar_profiles_list:
                            dataset_info_list.append({
                                "measurement": p.measurement,
                                "field": p.field,
                                "prof_aggr_type": aggr_method,
                                "alias": alias,
                                "filters": p.filters
                            })

                        embed_url = create_panel_multiple(
                            graph_title="Multiple profiles (asset type: " + type(asset).__name__ + ", field name: " +
                                profile.field + ")",
                            axis_title="",
                            host=profile.host + ':' + str(profile.port),
                            database=profile.database,
                            dataset_info=dataset_info_list,
                            qau=profile.profileQuantityAndUnit,
                            start_datetime=profile.startDate,
                            end_datetime=profile.endDate,
                            datasource=datasource
                        )
                        if embed_url:
                            return embed_url
                        else:
                            return None

                    else:
                        logger.info("Not all profiles use same host, port, database")
                        return None

            else:
                send_alert('ProfileType other than InfluxDBProfile not supported yet')
                return None

    @staticmethod
    def determine_profile_aggregation_method(qau: esdl.QuantityAndUnitType):
        # Whether to use "sum" or "mean" does not only depend on the physicalQuantity, but for now start with this list
        # and correct it when we run into problems. This is just a first 'guess' of what parameters need to be summed
        if qau.physicalQuantity in [esdl.PhysicalQuantityEnum.ENERGY, esdl.PhysicalQuantityEnum.VOLUME,
                                    esdl.PhysicalQuantityEnum.COST, esdl.PhysicalQuantityEnum.LENGTH,
                                    esdl.PhysicalQuantityEnum.DISTANCE, esdl.PhysicalQuantityEnum.WEIGHT]:
            return "sum"
        else:
            return "mean"

    def determine_database_credentials(self, host, port, database):
        # Whenever the port profile viewer is called based on information (host / database) in the ESDL InfluxDB profile
        # this functions tries to see if the credentials are stored in the profile server settings

        # Example profile server configuration in MongoDB
        #       {
        #         "name": "Standard profiles server",
        #         "host": "influxdb",
        #         "port": "8086",
        #         "username": "admin",
        #         "password": "admin",
        #         "database": "energy_profiles",
        #         "ssl_enabled": false
        #       }

        with self.flask_app.app_context():
            profiles_settings = Profiles.get_instance().get_profiles_settings()

            for prof_server in profiles_settings['profiles_servers']:
                if prof_server["host"] == host and prof_server["port"] == str(port):
                    return {
                        "username": prof_server["username"],
                        "password": prof_server["password"]
                    }

        return None

    @staticmethod
    def determine_profile_name(profile, profile_type):
        # Gives back a logical name for the profile panel
        profiles = Profiles.get_instance().get_profiles()['profiles']
        profile_name = None
        for pkey in profiles:
            p = profiles[pkey]
            if p['database'] == profile.database and p['measurement'] == profile.measurement and p['field'] == profile.field:
                profile_name = p['profile_uiname']
        if not profile_name:
            profile_name = profile.field + " (Multiplier: " + str(profile.multiplier) + " - Type: " + profile_type + ")"
        return profile_name

    @staticmethod
    def determine_profile_alias(profile):
        profile_container = profile.eContainer().eContainer()
        if isinstance(profile_container, esdl.EnergyAsset):
            alias = profile_container.name + ": " + profile.field
        else:
            alias = "Cannot determine profile name - contact me!"
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

    def find_datasource(self, profile):
        # Find out if credentials are required (these are not stored in the ESDL and must be stored as
        # an external profile server configuration)
        credentials = self.determine_database_credentials(profile.host, profile.port, profile.database)
        if credentials:
            datasource = get_panel_service_datasource(
                profile.database,
                profile.host + ':' + str(profile.port),
                credentials["username"],
                credentials["password"]
            )
        else:
            datasource = None  # Let datasource be created (or found) by the create_panel function

        return datasource

    @staticmethod
    def check_if_profiles_have_same_host_port_database(profile_list):
        used_host = None
        used_port = None
        used_database = None

        for p in profile_list:
            if used_host and p.host != used_host:
                return False
            else:
                used_host = p.host

            if used_port and p.port != used_port:
                return False
            else:
                used_port = p.port

            if used_database and p.database != used_database:
                return False
            else:
                used_database = p.database

        return True