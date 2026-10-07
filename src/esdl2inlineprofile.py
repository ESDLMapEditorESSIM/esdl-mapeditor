from flask import Flask, make_response, Response
from pyecore.ecore import EAttribute
from pyecore.resources import ResourceSet
from pyecore.valuecontainer import EOrderedSet

from esdl import EnergySystem, EnergySystemInformation, InfluxDBProfile, TimeSeriesProfile, Asset, InPort, OutPort, \
    Port, GenericProfile, ProfileReference
from esdl.processing.string_uri import StringURI
from esdl.profiles.influxdbprofilemanager import InfluxDBProfileManager, ConnectionSettings
import esdl
from esdlproject.ProjectManager import load_external_string
from extensions.profiles import Profiles
from extensions.session_manager import get_session, get_project_manager
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
            pm = get_project_manager()
            es = pm.get_active_energy_system()

            # Create copy of energy system so we do not convert the original
            # TODO: I don't know why copy.deepcopy(es) does not work. Maybe it works in a later version of pyesdl?
            # es_copy = copy.deepcopy(es)
            es_string = pm.energy_system_to_string(es.id)
            es_copy, parse_info = load_external_string(es_string, name=es.name or "Untitled EnergySystem")
            # es_copy.id = str(uuid4())

            with self.flask_app.app_context():
                try:
                    es_converted = self.copy_and_convert_esdl_profiles(active_es_id)
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

    def copy_and_convert_esdl_profiles(
            self,
            es_id: str,
    ) -> EnergySystem:
        """
        Copy the active EnergySystem and convert its profiles to in-line profiles.
        """
        pm = get_project_manager()
        es = pm.get_energy_system_by_id(es_id)
        es_string = pm.energy_system_to_string(es_id)
        es_copy, parse_info = load_external_string(es_string, name=es.name or "Untitled EnergySystem")
        profiles_settings = Profiles.get_instance().get_profiles_settings()
        es_converted = self.convert_esdl_profiles(es_copy, profiles_settings)
        return es_converted

    def convert_esdl_profiles(
            self,
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

        if profile.host == "https://edr-profiles.hesi.energy":
            influxdb_settings = ConnectionSettings(
                host="edr-profiles.hesi.energy",
                port=443,
                database=profile.database,
                username=None,
                password=None,
                ssl=True,
                verify_ssl=False,
            )
        else:
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
    pm = get_project_manager()
    es = pm.get_energy_system_by_id(es_id=es_id)
    es_string = pm.energy_system_to_string(es_id=es_id)
    es_copy, parse_info = load_external_string(es_string, name=es.name or "Untitled EnergySystem")
    profiles_settings = Profiles.get_instance().get_profiles_settings()
    es_converted = convert_esdl_profiles(es_copy, profiles_settings)
    return es_converted


def convert_esdl_profiles(
        es: EnergySystem,
        profiles_settings: dict[str, object],
) -> EnergySystem:
    """Convert port profiles in all areas, including building assets and measures."""
    esi: EnergySystemInformation = es.energySystemInformation

    # Remove all InfluxDBProfiles from the global profiles list
    logger.info("Removing InfluxDBProfiles from global profiles")
    global_profiles = esi.profiles.profile
    influxdb_profiles = [profile for profile in global_profiles if isinstance(profile, InfluxDBProfile)]
    for profile in influxdb_profiles:
        logger.debug(f"Removing InfluxDBProfile '{profile.name}' from global profiles")
        esi.profiles.profile.remove(profile)

    handled_profiles: dict[str, TimeSeriesProfile] = {}

    for area in es.eAllContents():
        if isinstance(area, esdl.Area):
            for asset in area.asset:
                convert_asset_profiles(asset, esi, handled_profiles, profiles_settings)
    logger.info("Finished converting ESDL to in-line profiles")
    return es


def convert_asset_profiles(asset: Asset, esi: EnergySystemInformation, handled_profiles: dict[str, TimeSeriesProfile], profiles_settings: dict[str, object]):
    """
    Convert profiles for all ports in the asset, including sub-assets and measure assets.
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

    measures = getattr(asset, "measures", None)
    if measures is not None:
        for measure in measures.measure:
            for proposed_asset in measure.asset:
                convert_asset_profiles(proposed_asset, esi, handled_profiles, profiles_settings)


def convert_profile_for_port(
        esi: EnergySystemInformation,
        port: Port,
        handled_profiles: dict[str, GenericProfile],
        profiles_settings: dict[str, object],
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
            if prof.profileQuantityAndUnit is not None:
                timeseries_profile.profileQuantityAndUnit = prof.profileQuantityAndUnit.deepcopy()
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
