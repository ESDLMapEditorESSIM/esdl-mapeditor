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

from dataclasses import asdict
from uuid import uuid4
from typing import List, Optional

from flask import Flask, request, jsonify, Response

import esdl
from extensions.ownership.ownership_messages import (
    Assignment,
    OwnershipAsset,
    GetAssetsResp,
    OwnershipParty,
    GetPartiesResp,
)
from extensions.session_manager import get_session, get_project_manager
import src.log as log


logger = log.get_logger(__name__)


class Ownership:
    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info("Registering Ownership extension")

        @self.flask_app.route("/ownership/<string:es_id>/parties", methods=["GET"])
        def _ownership_get_parties(es_id: str) -> Response:
            parties: List[OwnershipParty] = self.get_parties_list(es_id)
            return jsonify(asdict(GetPartiesResp(parties))), 200

        @self.flask_app.route("/ownership/<string:es_id>/assets", methods=["GET"])
        def _ownership_get_assets(es_id: str) -> Response:
            assets: List[OwnershipAsset] = self.get_esdl_assets(es_id)
            return jsonify(asdict(GetAssetsResp(assets))), 200

        @self.flask_app.route("/ownership/<string:es_id>/parties", methods=["POST"])
        def _ownership_add_party(es_id: str) -> Response:
            try:
                party_info: OwnershipParty = request.get_json()
                self.add_party(es_id, party_info)
                return (
                    jsonify({"message": "Successfully added a new ownership party."}),
                    200,
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route(
            "/ownership/<string:es_id>/parties/<string:party_id>", methods=["DELETE"]
        )
        def _ownership_remove_party(es_id: str, party_id: str) -> Response:
            try:
                self.remove_party(es_id, party_id)
                return "", 204
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route(
            "/ownership/<string:es_id>/assignment/<string:party_id>", methods=["POST"]
        )
        def _ownership_assignment(es_id: str, party_id: str) -> Response:
            try:
                assignment: Assignment = request.get_json()
                if not assignment:
                    return jsonify({"error": "Invalid input"}), 400

                self.assign_ownership(es_id, party_id, assignment)
                return jsonify({"message": "Ownership assignment successful."}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def get_es(self, es_id: str) -> esdl.EnergySystem:
        pm = get_project_manager()
        es = pm.get_energy_system_by_id(es_id)

        if es is None:
            raise ValueError(f"EnergySystem with id {es_id} can't be found.")

        return es

    def add_party(self, es_id: str, party_info: OwnershipParty) -> None:
        es = self.get_es(es_id)

        if es.parties is None:
            # If there is no Parties collection in the EnergySystem yet, create one
            es.parties = esdl.Parties()

        party_id = party_info["id"]
        if party_id == "":
            party_id = str(uuid4())

        for p in es.parties.party:
            if p.name == party_info["name"]:
                raise ValueError("Party name must be unique.")

        party = esdl.Party(
            id=party_id,
            name=party_info["name"],
            shortName=(
                party_info["short_name"] if party_info["short_name"] != "" else None
            ),
        )

        es.parties.party.append(party)

    def remove_party(self, es_id: str, party_id: str) -> None:
        es = self.get_es(es_id)
        parties = es.parties

        if parties:
            for p in parties.party:
                p: esdl.Party
                if p.id == party_id:
                    # This ensures the reference party of asset.isOwnedby is also cleaned up.
                    p.delete(recursive=True)

    def get_parties_list(self, es_id: str) -> List[OwnershipParty]:
        es = self.get_es(es_id)
        parties = es.parties

        parties_list: List[OwnershipParty] = []
        if parties:
            for p in parties.party:
                p: esdl.Party
                party = OwnershipParty(
                    id=p.id,
                    name=p.name,
                    short_name=p.shortName,
                )
                parties_list.append(party)
        return parties_list

    def get_esdl_assets(self, es_id: str) -> List[OwnershipAsset]:
        es = self.get_es(es_id)
        top_area = es.instance[0].area

        assets_list: List[OwnershipAsset] = []
        for eobj in top_area.eAllContents():
            if isinstance(eobj, esdl.Asset):
                if eobj.isOwnedBy is not None:
                    party = OwnershipParty(
                        id=eobj.isOwnedBy.id,
                        name=eobj.isOwnedBy.name,
                        short_name=eobj.isOwnedBy.shortName,
                    )
                else:
                    party = None

                assets_list.append(
                    OwnershipAsset(id=eobj.id, name=eobj.name, is_owned_by=party)
                )
        return assets_list

    def assign_ownership(
        self, es_id: str, party_id: str, assignment: Assignment
    ) -> None:
        try:
            for a_id in assignment["assigned_asset_ids"]:
                self.assign_asset_ownership(es_id, a_id, party_id)

            for a_id in assignment["revoked_asset_ids"]:
                self.assign_asset_ownership(es_id, a_id, None)
        except Exception as e:
            raise Exception(f"Error in assigning ownership: {str(e)}")

    def assign_asset_ownership(
            self, es_id: str, asset_id: str, party_id: Optional[str]
    ) -> None:
        pm = get_project_manager()
        es = pm.get_active_energy_system()

        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)

        if party_id is not None:
            party: esdl.Party = [p for p in es.parties.party if p.id == party_id][0]
        else:
            party = None

        asset.isOwnedBy = party
