import copy
from typing import Dict, Optional
from uuid import uuid4

from flask import Flask, make_response, Response
from pyecore.resources import ResourceSet

from esdl.esdl_handler import StringURI
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager, ConnectionSettings
from esdl.esdl import Building, EnergySystemInformation, Port, OutPort, InPort, EnergySystem, InfluxDBProfile, \
    TimeSeriesProfile, ProfileReference, GenericProfile
from extensions.profiles import Profiles
from extensions.session_manager import get_session, get_handler
import src.log as log

logger = log.get_logger(__name__)

class ESDL2InlineProfile:

    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info('Registering ESDL2InlineProfile extension')

        @self.flask_app.route('/esdl2inlineprofile')
        def export_to_profile_reference():
            active_es_id = get_session('active_es_id')
            esh = get_handler()
            es = esh.get_energy_system(es_id=active_es_id)

            # Create copy of energy system so we do not convert the original
            es_copy = copy.deepcopy(es)
            es_copy.name = get_session('es_filename') or (es.name or "Untitled EnergySystem") + " - In-line Profiles"
            es_copy.id = str(uuid4())

            with self.flask_app.app_context():
                profiles_settings = Profiles.get_instance().get_profiles_settings()
                try:
                    es_converted = self.convert_esdl_profiles(es_copy, profiles_settings)
                except Exception as e:
                    logger.error(f"Error converting ESDL to in-line profiles: {e}")
                    return make_response("Error converting ESDL to in-line profiles", 500)

            uri = StringURI('es_converted.esdl')
            es_converted_resource = ResourceSet().create_resource(uri)
            es_converted_resource.append(es_converted)
            es_converted_resource.save(uri)

            content = uri.getvalue()
            headers = dict()
            headers['Content-Disposition'] = 'attachment; filename="{}"'.format(es_converted.name)
            headers['Content-Length'] = len(content)
            return Response(content, mimetype='application/esdl+xml', direct_passthrough=True, headers=headers)

    @staticmethod
    def convert_esdl_profiles(
        es: EnergySystem,
        profiles_settings: Dict[str, object],
    ) -> EnergySystem:
        esi: EnergySystemInformation = es.energySystemInformation

        # Remove all InfluxDBProfiles from the global profiles list
        # TODO: for some reason not all global (InfluxDBProfile) profiles are found and thus not removed
        logger.info("Removing InfluxDBProfiles from global profiles")
        global_profiles = esi.profiles.profile
        for profile in global_profiles:
            logger.debug(f"Checking profile '{profile.name}' with type '{type(profile)}'")
            if isinstance(profile, InfluxDBProfile):
                logger.debug(f"Removing InfluxDBProfile '{profile.name}' from global profiles")
                esi.profiles.profile.remove(profile)

        handled_profiles: Dict[str, TimeSeriesProfile] = {}

        # Convert profiles for each port in each asset in each building
        for building in es.instance[0].area.asset:
            if not isinstance(building, Building):
                continue

            logger.info(f"Converting profiles for building '{building.name}'")

            for asset in building.asset:
                logger.debug(f"Converting profiles for asset '{asset.name}'")

                in_port: Optional[InPort] = next((
                    port
                    for port
                    in asset.port
                    if isinstance(port, InPort) and port.name == "In"
                ), None)

                if in_port is not None:
                    ESDL2InlineProfile.convert_profile_for_port(esi, in_port, handled_profiles, profiles_settings)

                out_port: Optional[OutPort] = next((
                    port
                    for port
                    in asset.port
                    if isinstance(port, OutPort) and port.name == "Out"
                ), None)

                if out_port is not None:
                    ESDL2InlineProfile.convert_profile_for_port(esi, out_port, handled_profiles, profiles_settings)

            # TODO: other ports in building?

        # TODO: convert profiles for assets not in building?

        logger.info("Finished converting ESDL to in-line profiles")
        return es

    @staticmethod
    def convert_profile_for_port(
        esi: EnergySystemInformation,
        port: Port,
        handled_profiles: Dict[str, GenericProfile],
        profiles_settings: Dict[str, object],
    ):
        def convert_influx_profile(prof: InfluxDBProfile):
            # Create TimeSeriesProfile for the profile of the port in global profiles if it does not exist yet
            if prof.name not in handled_profiles:
                influxdb_settings = None
                for prof_server in profiles_settings["profiles_servers"]:
                    if prof_server["host"] in prof.host and prof_server["port"] == str(prof.port):
                        influxdb_settings = ConnectionSettings(
                            host=prof.host,
                            port=prof.port,
                            database=prof.database,
                            username=prof_server["username"],
                            password=prof_server["password"],
                            ssl=prof_server.get("ssl_enabled", False),
                            verify_ssl=prof_server.get("ssl_enabled", False),
                        )
                if influxdb_settings is None:
                    logger.error(f"Could not find InfluxDB settings for profile '{prof.name}'")
                    raise Exception(f"Could not find InfluxDB settings for profile '{prof.name}'")

                prof_manager = InfluxDBProfileManager(influxdb_settings)
                prof_manager.load_influxdb(
                    measurement=prof.measurement,
                    fields=[prof.field],
                    from_datetime=prof.startDate,
                    to_datetime=prof.endDate
                )
                timeseries_profile = prof_manager.get_esdl_timeseries_profile()
                timeseries_profile.name = prof.name
                esi.profiles.profile.append(timeseries_profile)
                handled_profiles[prof.name] = timeseries_profile
                logger.info(f"Converted InfluxDBProfile '{prof.name}' to TimeSeriesProfile")

            # Replace InfluxDBProfile with ProfileReference
            reference_profile: ProfileReference = ProfileReference(
                multiplier=prof.multiplier,
                reference=handled_profiles[prof.name]
            )
            port.profile.append(reference_profile)
            port.profile.remove(prof)

        for profile in port.profile:  # Eagerly convert only the first profile found
            if isinstance(profile, InfluxDBProfile):
                convert_influx_profile(profile)
                logger.debug(f"Converted InfluxDBProfile '{profile.name}' to ProfileReference for port '{port.name}'")
                return
            else:
                # TODO: Warning? Error? Or just Info?
                logger.warning(f"Found a profile which is not an InfluxDBProfile for port '{port.name}'")
