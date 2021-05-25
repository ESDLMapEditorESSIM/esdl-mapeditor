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
                    else:
                        profile_type = profile.profileType.name
                    database = profile.database
                    multiplier = profile.multiplier
                    measurement = profile.measurement
                    profiles = Profiles.get_instance().get_profiles()['profiles']
                    for pkey in profiles:
                        p = profiles[pkey]
                        if p['database'] == database and p['measurement'] == measurement and p['field'] == field:
                            profile_name = p['profile_uiname']
                    if profile_name == None:
                        profile_name = profile.field + " (Multiplier: " + str(multiplier) + " - Type: " + profile_type + ")"

                    embedUrl = create_panel(profile_name, "", profile.host+':'+str(profile.port),
                                        profile.database, profile.measurement, profile.field, profile.filters, qau,
                                        "sum", profile.startDate, profile.endDate)
                    if embedUrl:
                        return embedUrl
                else:
                    send_alert('ProfileType other than InfluxDBProfile not supported yet')
                    return None