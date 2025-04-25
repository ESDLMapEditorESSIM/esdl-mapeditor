import copy
from typing import Dict, Optional
from uuid import uuid4

from flask import Flask, make_response, Response
from pyecore.ecore import EAttribute
from pyecore.resources import ResourceSet
from pyecore.valuecontainer import EOrderedSet

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

