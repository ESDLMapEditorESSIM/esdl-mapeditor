import copy
from typing import Dict, Optional
from uuid import uuid4

from flask import Flask, make_response, Response
from pyecore.ecore import EAttribute
from pyecore.resources import ResourceSet
from pyecore.valuecontainer import EOrderedSet

from esdl import EnergySystem, EnergySystemInformation, InfluxDBProfile, TimeSeriesProfile, Asset, InPort, OutPort, \
    Port, GenericProfile, ProfileReference
from esdl.esdl_handler import StringURI
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager, ConnectionSettings
import esdl
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

            with self.flask_app.app_context():
                try:
                    es_converted = copy_and_convert_esdl_profiles(active_es_id)
                except Exception as e:
                    logger.exception(f"Error converting ESDL to in-line profiles: {e}")
                    return make_response("Error converting ESDL to in-line profiles", 500)

            uri = StringURI('es_converted.esdl')
            es_converted_resource = ResourceSet().create_resource(uri)
            es_converted_resource.append(es_converted)
            es_converted_resource.save(uri)

            content = uri.getvalue()
            response = Response(content, direct_passthrough=True)
            response.headers.set('Content-Type', 'application/esdl+xml')
            response.headers.set('Content-Disposition', 'attachment', filename='%s' % es_converted.name)

            return response

    @staticmethod
    def convert_esdl_profiles(
        es: esdl.EnergySystem,
        profiles_settings: dict[str, object],
    ) -> esdl.EnergySystem:
        logger.info("Convert InfluxDBProfiles for the whole energy system to TimeSeriesProfiles")

        profile_mapping: dict[esdl.InfluxDBProfile, esdl.TimeSeriesProfile] = {}
        ESDL2InlineProfile.search_all_influxdb_profiles_and_create_timeseries_profiles(es, profiles_settings, profile_mapping)
        ESDL2InlineProfile.search_and_replace_all_profile_references(es, profile_mapping)
        ESDL2InlineProfile.remove_all_influxdb_profiles(profile_mapping)

        logger.info("Finished converting ESDL to in-line profiles")
        return es

    @staticmethod
    def search_all_influxdb_profiles_and_create_timeseries_profiles(es: esdl.EnergySystem, profiles_settings, profile_mapping):
        logger.info("- Search all InfluxDBProfiles and create timeseries profiles")
        for obj in es.eAllContents():
            if isinstance(obj, esdl.InfluxDBProfile):
                timeseries_profile = ESDL2InlineProfile.convert_influxdb_to_timeseries_profile(obj,
                                                                                               profiles_settings)
                container = obj.eContainer()
                containment_feature = obj.eContainmentFeature()
                attr = container.eGet(containment_feature.name)
                if isinstance(attr, EOrderedSet):
                    attr.append(timeseries_profile)
                elif isinstance(attr, EAttribute):
                    container.eSet(attr, timeseries_profile)
                else:
                    logger.error("Serious error! Not supported yet")

                profile_mapping[obj] = timeseries_profile

    @staticmethod
    def search_and_replace_all_profile_references(es, profile_mapping):
        logger.info("- Search all profile references to InfluxDBProfiles and replace it with a reference" +
                    "to the TimeSeriesProfile")
        for obj in es.eAllContents():
            if isinstance(obj, esdl.ProfileReference):
                referred_profile = obj.reference
                container = obj.eContainer()
                if referred_profile in profile_mapping:
                    # reference is to one of the InfluxDBProfiles

                    # Create a new Reference to the TimeSeriesProfile but keep the original multiplier
                    new_reference = esdl.ProfileReference(
                        reference=profile_mapping[referred_profile],
                        multiplier=obj.multiplier
                    )

                    containment_feature = obj.eContainmentFeature()
                    attr = container.eGet(containment_feature.name)
                    if isinstance(attr, EOrderedSet):
                        attr.append(new_reference)
                        attr.remove(obj)
                    elif isinstance(attr, EAttribute):
                        container.eSet(attr, new_reference)
                    else:
                        logger.error("Serious error! Not supported yet")

    @staticmethod
    def remove_all_influxdb_profiles(profile_mapping):
        logger.info("- Remove all influxdb profiles")
        for influxdb_profile in list(profile_mapping.keys()):
            container = influxdb_profile.eContainer()

            containment_feature = influxdb_profile.eContainmentFeature()
            attr = container.eGet(containment_feature.name)
            if isinstance(attr, EOrderedSet):
                # if the attribute is not of type EOrderedSet (but probably EAttribute), the profile was overwritten
                # by assigning to a new profile to the attribute
                attr.remove(influxdb_profile)

    @staticmethod
    def convert_influxdb_to_timeseries_profile(profile: esdl.InfluxDBProfile, profiles_settings: dict[str, object]) -> esdl.TimeSeriesProfile:
        influxdb_settings = None

        # Find profile server information for the InfluxDBProfile
        for prof_server in profiles_settings["profiles_servers"]:
            if prof_server["host"] in profile.host and prof_server["port"] == str(profile.port):
                influxdb_settings = ConnectionSettings(
                    host=prof_server["host"],
                    port=profile.port,
                    database=profile.database,
                    username=prof_server["username"],
                    password=prof_server["password"],
                    ssl=prof_server.get("ssl_enabled", False),
                    verify_ssl=prof_server.get("ssl_enabled", False),
                )

        if not influxdb_settings:
            logger.error(f"No InfluxDBProfile settings found for {profile.name}")
            raise Exception("No InfluxDBProfile settings found for {profile.name}")

        prof_manager = InfluxDBProfileManager(influxdb_settings)
        prof_manager.load_influxdb(
            measurement=profile.measurement,
            fields=[profile.field],
            from_datetime=profile.startDate,
            to_datetime=profile.endDate
        )
        timeseries_profile = prof_manager.get_esdl_timeseries_profile(profile_name=profile.name)
        return timeseries_profile


def copy_and_convert_esdl_profiles(
        es_id: str,
) -> EnergySystem:
    """
    Copy the active EnergySystem and convert its profiles to in-line profiles.
    """
    esh = get_handler()
    es = esh.get_energy_system(es_id=es_id)
    es_string = esh.to_string(es_id=es_id)
    es_copy, parse_info = esh.load_external_string(es_string, name=f"{es.name} - In-line Profiles")
    es_copy.name = get_session('es_filename') or (es.name or "Untitled EnergySystem") + " - In-line Profiles"
    profiles_settings = Profiles.get_instance().get_profiles_settings()
    es_converted = convert_esdl_profiles(es_copy, profiles_settings)
    return es_converted


def convert_esdl_profiles(
        es: EnergySystem,
        profiles_settings: dict[str, object],
) -> EnergySystem:
    esi: EnergySystemInformation = es.energySystemInformation

    # Remove all InfluxDBProfiles from the global profiles list
    logger.info("Removing InfluxDBProfiles from global profiles")
    global_profiles = esi.profiles.profile
    influxdb_profiles = [profile for profile in global_profiles if isinstance(profile, InfluxDBProfile)]
    for profile in influxdb_profiles:
        logger.debug(f"Removing InfluxDBProfile '{profile.name}' from global profiles")
        esi.profiles.profile.remove(profile)

    handled_profiles: dict[str, TimeSeriesProfile] = {}

    # Convert profiles for each port in each asset in each building
    for asset in es.instance[0].area.asset:
        convert_asset_profiles(asset, esi, handled_profiles, profiles_settings)
    logger.info("Finished converting ESDL to in-line profiles")
    return es


def convert_asset_profiles(asset: Asset, esi: EnergySystemInformation, handled_profiles: dict[str, TimeSeriesProfile], profiles_settings: dict[str, object]):
    """
    Convert profiles for all ports in the asset. Recursively convert profiles for all sub-assets.
    """
    ilog = logger.bind(asset_id=asset.id, asset_name=asset.name)
    ilog.debug("Converting profiles for asset")

    if hasattr(asset, 'port'):
        ilog.debug("Converting profiles for ports")
        in_ports = [port for port in asset.port if isinstance(port, InPort)]
        for in_port in in_ports:
            convert_profile_for_port(esi, in_port, handled_profiles, profiles_settings)

        out_ports = [port for port in asset.port if isinstance(port, OutPort)]
        for out_port in out_ports:
            convert_profile_for_port(esi, out_port, handled_profiles, profiles_settings)

    if hasattr(asset, 'asset'):
        ilog.debug("Recursively converting profiles for sub-assets", asset_id=asset.id, asset_name=asset.name)
        for sub_asset in asset.asset:
            convert_asset_profiles(sub_asset, esi, handled_profiles, profiles_settings)

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
                if ((prof_server["host"] == "localhost" and prof.host == "http://influxdb") or prof_server["host"] in prof.host) and prof_server["port"] == str(prof.port):
                    influxdb_settings = ConnectionSettings(
                        host=prof_server["host"],
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
            timeseries_profile.profileType = prof.profileType
            esi.profiles.profile.append(timeseries_profile)
            handled_profiles[prof.name] = timeseries_profile
            logger.info(f"Converted InfluxDBProfile '{prof.name}' to TimeSeriesProfile")

        # Replace InfluxDBProfile with ProfileReference
        reference_profile: ProfileReference = ProfileReference(
            multiplier=prof.multiplier,
            reference=handled_profiles[prof.name],
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
