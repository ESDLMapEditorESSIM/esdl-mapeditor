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

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from extensions.settings_storage import SettingsStorage
from extensions.session_manager import get_handler, get_session
from esdl import esdl
from esdl.processing import ESDLAsset, ESDLEnergySystem
import src.settings as settings
import requests
import json
import uuid
import src.log as log

logger = log.get_logger(__name__)


def send_alert(message):
    print(message)
    emit('alert', message, namespace='/esdl')


class PICORooftopPVPotential:
    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket

        self.register()

    def register(self):
        logger.info("Registering PICORooftopPVPotential extension")

        @self.socketio.on('use_part_of_potential', namespace='/esdl')
        def use_part_of_potential(pot_id, percentage):
            """
            Use part of a SolarPotential to install a PVInstallation

            :param pot_id: id of the SolarPotential
            :param percentage: percentage (0-100) of the SolarPotential that should be installed as a PVInstallation
            :return: None
            """
            with self.flask_app.app_context():
                esh = get_handler()
                active_es_id = get_session('active_es_id')

                pot = esh.get_by_id(active_es_id, pot_id)
                pot_container = pot.eContainer()

                # Create a PVInstallation instance and attach a profile with the percentage of the potential that
                # will be 'installed'
                pv_installation = esdl.PVInstallation(id=str(uuid.uuid4()),name="PV Installation")
                pv_outport = esdl.OutPort(id=str(uuid.uuid4()), name="Out")
                pv_profile = esdl.SingleValue(id=str(uuid.uuid4()), name="PV production", value=pot.value * percentage / 100)
                # Assume kWh for now, Geodan should communicate this in the ESDL in the end
                pv_profile.profileQuantityAndUnit = esdl.QuantityAndUnitType(
                    physicalQuantity=esdl.PhysicalQuantityEnum.ENERGY,
                    unit=esdl.UnitEnum.WATTHOUR,
                    multiplier=esdl.MultiplierEnum.KILO)
                pv_outport.profile.append(pv_profile)
                pv_installation.port.append(pv_outport)

                add_to_building = False
                # Generate a location on the map for the PV Installation
                if isinstance(pot_container, esdl.AbstractBuilding):
                    # Place the Asset in the top left corner of the BuildingEditor
                    pv_geometry = esdl.Point(lon=10, lat=490, CRS="Simple")
                    pv_installation.geometry = pv_geometry
                    add_to_building = True
                else:
                    pot_geometry = pot.geometry
                    if isinstance(pot_geometry, esdl.Point):
                        # Place the Asset with a small offset from the SolarPotential marker
                        pv_geometry = esdl.Point(lon=pot_geometry.lon + 0.001, lat=pot_geometry.lat - 0.001)
                        pv_installation.geometry = pv_geometry
                    else:
                        logger.warning('Using potentials with geometry other than esdl.Point not supported yet')

                # Add the PVInstallation to the same container as the SolarPotential (Area or Building)
                pot_container.asset.append(pv_installation)
                esh.add_object_to_dict(active_es_id, pv_installation, recursive=True)

                # Adapt the potential (substract the installed value)
                pot.value = pot.value * (100-percentage) / 100

                # Emit the information to the front-end
                asset_list = []
                port_list = [{'name': pv_outport.name, 'id': pv_outport.id, 'type': type(pv_outport).__name__, 'conn_to': []}]
                capability_type = ESDLAsset.get_asset_capability_type(pv_installation)
                asset_list.append(['point', 'asset', pv_installation.name, pv_installation.id,
                                   type(pv_installation).__name__, 'e', [pv_geometry.lat, pv_geometry.lon], port_list,
                                               capability_type])
                emit('add_esdl_objects',
                     {'es_id': active_es_id, 'add_to_building': add_to_building, 'asset_pot_list': asset_list,
                      'zoom': False})