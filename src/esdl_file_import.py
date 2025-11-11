import base64
import uuid
from typing import Dict

from flask import Flask, request
from flask_executor import Executor
from flask_socketio import SocketIO
from pyecore.resources import ResourceSet

import esdl
import src.log as log
from esdl import EnergySystem, TimeSeriesProfile, InfluxDBProfile
from esdl.processing.string_uri import StringURI
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager, ConnectionSettings
from esdlproject.ProjectManager import load_external_string
from extensions.profiles import Profiles
from extensions.session_manager import set_session, get_project_manager
from src.process_es_area_bld import process_energy_system, call_process_energy_system

logger = log.get_logger(__name__)


class ESDLFileImport:
    def __init__(self, flask_app: Flask, socket: SocketIO, executor: Executor):
        self.flask_app = flask_app
        self.socketio = socket
        self.register()
        self.executor = executor

    def register(self):
        logger.info('Registering ESDL File Import extension')

        @self.flask_app.route("/esdl_file_import", methods=['POST'])
        def esdl_file_import():
            with self.flask_app.app_context():
                pm = get_project_manager()

                filename = request.values.get('filename')

                base64_file_contents = request.values.get('file_content')
                base64_file_contents = base64_file_contents.split(',')[1]
                esdlstr_base64_bytes = base64_file_contents.encode('utf-8')
                esdlstr_bytes = base64.b64decode(esdlstr_base64_bytes)
                file_content = esdlstr_bytes.decode('utf-8')

                inline = request.values.get('inline')

                try:
                    if inline == 'true':  # silly js to python conversion
                        logger.info("Importing inline ESDL")
                        # inline_esh = EnergySystemHandler()  # TODO: or use esh.load_external_string()?
                        inline_es, parse_info = load_external_string(name=filename, esdl_string=file_content)
                        inline_es = self.convert_inline_to_influx(inline_es)
                        inline_es.name = inline_es.name.replace(" - In-line Profiles", "")

                        uri = StringURI('es_converted.esdl')
                        es_converted_resource = ResourceSet().create_resource(uri)
                        es_converted_resource.append(inline_es)
                        es_converted_resource.save(uri)
                        file_content = uri.getvalue()
                        logger.debug("Inline ESDL converted to InfluxDB profiles")

                    imported_es, parse_info = pm.add_from_string(
                        name=filename, esdl_string=file_content
                    )

                    if len(parse_info) > 0:
                        info = ''
                        for line in parse_info:
                            info += line + "\n"
                    set_session('active_es_id', imported_es.id)
                    set_session('es_filename', filename)

                    return {'message': 'ESDL imported'}, 201
                except Exception as e:
                    logger.error("Error importing {}: {}".format(filename, e))
                    # send_alert('Error interpreting ESDL from file - Exception: ' + str(e))

                return {'message': 'Error importing ESDL'}, 500


        @self.socketio.on("process_imported_energysystem", namespace='/esdl')
        def process_imported_energysystem():
            call_process_energy_system.submit()

    @staticmethod
    def convert_inline_to_influx(inline_es: EnergySystem) -> EnergySystem:
        inline_esi = inline_es.energySystemInformation

        prof_servers = Profiles.get_instance().get_profiles_settings()["profiles_servers"]
        if len(prof_servers) == 0:
            raise Exception("No profiles servers found in profiles settings.")
        prof_server = prof_servers[0]  # TODO: ugly and potentially incorrect
        influxdb_settings = ConnectionSettings(
            host=prof_server["host"],
            port=int(prof_server["port"]),
            database=prof_server["database"],
            username=prof_server["username"],
            password=prof_server["password"],
            ssl=prof_server.get("ssl_enabled", False),
            verify_ssl=prof_server.get("ssl_enabled", False),
        )

        handled_profiles: Dict[str, esdl.InfluxDBProfile] = {}

        def _create_influxdb_profile(prof: TimeSeriesProfile, multiplier: float | None = None):
            prof_manager = InfluxDBProfileManager(influxdb_settings)
            prof_manager.parse_esdl(prof)
            # profile_header[1] should now be prof.name which is a concatenation of measurement and field
            # if this profile was converted from an InfluxDBProfile to TimeSeriesProfile.
            field_name = prof_manager.profile_header[1]
            field_name_split = field_name.split("_")
            measurement = inline_esi.id.replace("-", "_")

            # If the profile is based on a default profile we don't need to save it to the database,
            # and we can create a profile directly.
            if field_name.startswith("standard_profiles_point"):
                field_name = "_".join(field_name_split[3:])
                measurement = "_".join(field_name_split[:3])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name], profile_type=prof.profileType)
            # TODO: elif field_name.startswith("standard_profiles"):
            elif field_name.startswith("bedrijfstijden_profielen"):
                field_name = "_".join(field_name_split[2:])
                measurement = "_".join(field_name_split[:2])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name], profile_type=prof.profileType)
            elif field_name.startswith("KIP_EH_profielen_point"):
                field_name = "_".join(field_name_split[4:])
                measurement = "_".join(field_name_split[:4])
                influx_profile = prof_manager.get_esdl_influxdb_profile(measurement, [field_name], profile_type=prof.profileType)
            # TODO: elif field_name.startswith("KIP_EH_profielen"):
            else:
                # If the profile is not based on a default profile we need to save it to the database
                # TODO: we could create a panel for these profiles...
                field_name = f"{(prof.id or str(uuid.uuid4()))}"
                prof_manager.profile_header[1] = field_name
                influx_profile = prof_manager.save_influxdb(
                    measurement=measurement,
                    field_names=[prof_manager.profile_header[1]],
                    profile_type=prof.profileType,
                )
            influx_profile.name = prof.name  # equal to f"{measurement}_{field_name}" for standard profiles and a UUID for custom profiles
            influx_profile.profileType = prof.profileType
            if multiplier is not None:
                influx_profile.multiplier = multiplier
            # Fix to fix temporary fix in profile manager that removes http from host
            if not influx_profile.host.startswith("http"):
                influx_profile.host = f"http://{influx_profile.host}"
            handled_profiles[prof.name] = influx_profile

        def _convert_profile_for_port(port: esdl.Port):
            port_profiles_remove = []
            port_profiles_add = []

            def add_handled_profile(handled_profile: esdl.InfluxDBProfile, multiplier: float):
                port_profiles_add.append(InfluxDBProfile(
                    id=str(uuid.uuid4()),
                    name=handled_profile.name,
                    host=handled_profile.host,
                    port=handled_profile.port,
                    database=handled_profile.database,
                    measurement=handled_profile.measurement,
                    field=handled_profile.field,
                    filters=handled_profile.filters,
                    startDate=handled_profile.startDate,
                    endDate=handled_profile.endDate,
                    multiplier=multiplier,
                    profileType=handled_profile.profileType,
                ))

            for profile in port.profile:
                if isinstance(profile, esdl.TimeSeriesProfile):
                    profile_name = profile.name

                    if profile_name not in handled_profiles:
                        _create_influxdb_profile(profile, multiplier=None)

                    handled_influx_profile = handled_profiles[profile_name]
                    assert isinstance(handled_influx_profile, esdl.InfluxDBProfile)
                    add_handled_profile(handled_influx_profile, multiplier=1.0)
                    port_profiles_remove.append(profile)
                elif isinstance(profile, esdl.ProfileReference):
                    # Reference of ProfileReference should be TimeSeriesProfile
                    if not isinstance(profile.reference, esdl.TimeSeriesProfile):
                        return

                    referenced_profile: esdl.TimeSeriesProfile = profile.reference
                    profile_name = referenced_profile.name

                    if profile_name not in handled_profiles:
                        _create_influxdb_profile(referenced_profile, profile.multiplier)

                    handled_influx_profile = handled_profiles[profile_name]
                    assert isinstance(handled_influx_profile, esdl.InfluxDBProfile)
                    add_handled_profile(handled_influx_profile, multiplier=profile.multiplier)
                    port_profiles_remove.append(profile)

            # Update port profiles after iterating to avoid changing the list while iterating
            for profile in port_profiles_add:
                port.profile.append(profile)
            for profile in port_profiles_remove:
                port.profile.remove(profile)

        def _convert_asset_profiles(asset: esdl.Asset):
            if hasattr(asset, 'port'):
                in_ports = [port for port in asset.port if isinstance(port, esdl.InPort)]
                for in_port in in_ports:
                    _convert_profile_for_port(in_port)

                out_ports = [port for port in asset.port if isinstance(port, esdl.OutPort)]
                for out_port in out_ports:
                    _convert_profile_for_port(out_port)

            if hasattr(asset, 'asset'):  # Recursively convert profiles of sub-assets
                for sub_asset in asset.asset:
                    _convert_asset_profiles(sub_asset)

        global_timeseries_profiles = [profile for profile in inline_esi.profiles.profile if isinstance(profile, esdl.TimeSeriesProfile)]
        for timeseries_profile in global_timeseries_profiles:
            if timeseries_profile.name not in handled_profiles:
                _create_influxdb_profile(timeseries_profile, multiplier=None)

        # Start conversion of the energy system
        # Convert profiles of each asset to InfluxDB profiles
        for area_asset in inline_es.instance[0].area.asset:
            _convert_asset_profiles(area_asset)
        # The TimeSeriesProfiles referenced in the assets should all be converted now, so we can remove them
        # (and for sake of completeness add InfluxDBProfiles in their place
        global_timeseries_profiles = [profile for profile in inline_esi.profiles.profile if isinstance(profile, esdl.TimeSeriesProfile)]
        for timeseries_profile in global_timeseries_profiles:
            if timeseries_profile.name not in handled_profiles:
                _create_influxdb_profile(timeseries_profile, multiplier=None)

            global_influx_profile = handled_profiles[timeseries_profile.name]
            assert isinstance(global_influx_profile, esdl.InfluxDBProfile)
            inline_esi.profiles.profile.append(global_influx_profile)
            inline_esi.profiles.profile.remove(timeseries_profile)

        return inline_es
