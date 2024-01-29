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
                    profile_name = None
                    qau = profile.profileQuantityAndUnit
                    if isinstance(qau, esdl.QuantityAndUnitReference):
                        qau = qau.reference
                    if qau:
                        profile_type = ESDLQuantityAndUnits.qau_to_string(qau)
                        aggr_method = PortProfileViewer.determine_profile_aggregation_method(qau)
                    else:
                        profile_type = profile.profileType.name
                        aggr_method = DEFAULT_PROFILE_AGGREGATION_METHOD
                    database = profile.database
                    multiplier = profile.multiplier
                    measurement = profile.measurement
                    field = profile.field
                    profiles = Profiles.get_instance().get_profiles()['profiles']
                    for pkey in profiles:
                        p = profiles[pkey]
                        if p['database'] == database and p['measurement'] == measurement and p['field'] == field:
                            profile_name = p['profile_uiname']
                    if not profile_name:
                        profile_name = profile.field + " (Multiplier: " + str(multiplier) + " - Type: " + profile_type + ")"

                    embedUrl = create_panel(
                        graph_title=profile_name,
                        axis_title="",
                        host=profile.host+':'+str(profile.port),
                        database=profile.database,
                        measurement=profile.measurement,
                        field=profile.field,
                        filters=profile.filters,
                        qau=qau,
                        prof_aggr_type=aggr_method,
                        start_datetime=profile.startDate,
                        end_datetime=profile.endDate
                    )
                    if embedUrl:
                        return embedUrl
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
