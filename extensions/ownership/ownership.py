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

import json
from dataclasses import asdict
from uuid import uuid4

from flask import Flask, request
from flask_socketio import SocketIO

import esdl
from extensions.ownership.ownership_messages import PartiesListResponse, EnhancedJSONEncoder, Party
from extensions.session_manager import get_handler, get_session
from extensions.settings_storage import SettingsStorage
import src.settings as settings
import src.log as log


logger = log.get_logger(__name__)


class Ownership:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage

        self.register()

    def register(self):
        logger.info('Registering Ownership extension')

        @self.flask_app.route('/ownership/parties', methods=['GET'])
        def ownership_parties():
            esh = get_handler()
            active_es_id = get_session('active_es_id')
            es = esh.get_energy_system(active_es_id)

            parties_list = list()
            parties = es.parties
            if parties:
                for party in parties.party:
                    p = Party(
                        id=party.id,
                        name=party.name,
                        short_name=party.shortName,
                    )
                    parties_list.append(p)

            return asdict(PartiesListResponse(parties=parties_list)), 200

        @self.flask_app.route('/ownership/parties', methods=['POST'])
        def ownership_add_party():
            party_info = request.get_json(silent=True)
            self.add_party(party_info)

        @self.flask_app.route('/ownership/parties/<int:party_id>', methods=['DELETE'])
        def ownership_remove_party(party_id):
            pass

    def add_party(self, party_info):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        es = esh.get_energy_system(active_es_id)

        parties = es.parties
        if not parties:
            # If there is no Parties collection in the EnergySystem yet, create one
            parties = es.parties = esdl.Parties()

        if 'id' in party_info:
            party_id = party_info['id']
            if party_id == '':
                party_id = str(uuid4())
        else:
            party_id = str(uuid4())

        party = esdl.Party(
            id = party_id,
            name = party_info['name'],
            shortName = party_info['short_name'],
        )

        parties.party.append(party)

    def delete_party(self, party_id):
        esh = get_handler()
        active_es_id = get_session('active_es_id')
        es = esh.get_energy_system(active_es_id)

        parties = es.parties
        if parties:
            for party in list(parties.party):
                if party.id == party_id:
                    parties.remove(party)
                    return {}, 204
