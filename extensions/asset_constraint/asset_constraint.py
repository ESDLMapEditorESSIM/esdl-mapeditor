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

from flask import Flask, request, Response
from typing import List, Optional

import esdl
from extensions.asset_constraint.asset_constraint_message import (
    ConstraintType,
    ProfileClass,
    InfluxDBProfileMsg,
    RangeMsg,
    ProfileConstraintMsg,
    RangedConstraintMsg,
)
from extensions.profiles import Profiles
from esdl.processing import ESDLQuantityAndUnits
import src.esdl_config as esdl_config
from extensions.session_manager import get_project_manager
from src.esdl_helper import generate_profile_info

import src.log as log


logger = log.get_logger(__name__)


class AssetConstraint:
    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info("Registering AssetConstraint extension")

        @self.flask_app.route(
            "/asset_constraint/<string:es_id>/<string:asset_id>", methods=["GET"]
        )
        def _get_asset_constraint(es_id: str, asset_id: str):
            return self.get_asset_constraint(es_id, asset_id)

        @self.flask_app.route(
            "/asset_constraint/<string:es_id>/<string:asset_id>", methods=["POST"]
        )
        def _set_asset_constraint(es_id: str, asset_id: str) -> Response:
            asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg] = (
                request.get_json()
            )
            try:
                self.set_asset_constraint(es_id, asset_id, asset_constraints)
                return Response("Success", 200)
            except Exception as e:
                return Response(f"Error: {e}", 500)

    def get_asset_constraint(
        self, es_id: str, asset_id: str
    ) -> List[ProfileConstraintMsg | RangedConstraintMsg]:
        """
        Get and return a list of ProfileConstraint or RangedConstraint of the asset.
        """

        pm = get_project_manager()
        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)
        asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg] = []

        if asset:
            constraints = asset.constraint
            for c in constraints:
                if isinstance(c, esdl.ProfileConstraint):
                    constraint_msg = self._get_profile_constraint_msg(c)
                elif isinstance(c, esdl.RangedConstraint):
                    constraint_msg = self._get_ranged_constraint_msg(c)
                else:
                    raise ValueError("Unsupported constraint class")

                asset_constraints.append(constraint_msg)

        return asset_constraints

    def _get_profile_constraint_msg(
        self, constraint: esdl.ProfileConstraint
    ) -> ProfileConstraintMsg:
        """
        Parse an esdl ProfileConstraint instance into a ProfileConstraintMsg
        """

        max_profile_msg = None
        if constraint.maximum and isinstance(constraint.maximum, esdl.InfluxDBProfile):
            max_profile_msg = self._get_influxdb_profile_msg(constraint.maximum)

        min_profile_msg = None
        if constraint.minimum and isinstance(constraint.minimum, esdl.InfluxDBProfile):
            min_profile_msg = self._get_influxdb_profile_msg(constraint.minimum)

        profile_constraint_msg = ProfileConstraintMsg(
            id=constraint.id,
            name=constraint.name,
            description=constraint.description,
            attributeReference=constraint.attributeReference,
            type=ConstraintType.PROFILE.value,
            maximum=max_profile_msg,
            minimum=min_profile_msg,
        )

        return profile_constraint_msg

    def _get_influxdb_profile_msg(
        self, minmax_profile: esdl.InfluxDBProfile
    ) -> InfluxDBProfileMsg:
        profile_info = generate_profile_info([minmax_profile])[0]
        influxdb_profile_msg = InfluxDBProfileMsg(
            id=minmax_profile.id,
            name=minmax_profile.name,
            displayed_name=profile_info["uiname"],
            profile_class=ProfileClass.INFLUXDB.value,
            multiplier=minmax_profile.multiplier,
            qau_description=profile_info["type"],
        )
        return influxdb_profile_msg

    def _get_ranged_constraint_msg(
        self, constraint: esdl.RangedConstraint
    ) -> RangedConstraintMsg:
        """
        Parse an esdl RangedConstraint instance into a RangedConstraintMsg
        """

        range_msg = None
        if constraint.range and isinstance(constraint.range, esdl.Range):
            range_msg = RangeMsg(
                id=constraint.range.id,
                name=constraint.range.name,
                min_value=constraint.range.minValue if constraint.range.eIsSet('minValue') else None,
                mid_value=constraint.range.midValue if constraint.range.eIsSet('midValue') else None,
                max_value=constraint.range.maxValue if constraint.range.eIsSet('maxValue') else None,
            )

        ranged_constraint_msg = RangedConstraintMsg(
            id=constraint.id,
            name=constraint.name,
            description=constraint.description,
            attributeReference=constraint.attributeReference,
            type=ConstraintType.RANGED.value,
            range=range_msg,
        )

        return ranged_constraint_msg

    def set_asset_constraint(
        self,
        es_id: str,
        asset_id: str,
        asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg],
    ):
        """
        Set asset constraint from the given list of asset_constraints.
        """

        pm = get_project_manager()
        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)

        new_constraints: List[esdl.ProfileConstraint | esdl.RangedConstraint] = []
        for c in asset_constraints:
            if c["type"] == ConstraintType.PROFILE.value:
                esdl_constraint = self._handle_profile_constraint(es_id, c)
            elif c["type"] == ConstraintType.RANGED.value:
                esdl_constraint = self._handle_ranged_constraint(c)
            else:
                raise ValueError(f"Unsupported constraint type: {c['type']}")
            new_constraints.append(esdl_constraint)

        asset.constraint.clear()
        asset.constraint = new_constraints

    def _handle_profile_constraint(
        self, es_id: str, constraintMsg: ProfileConstraintMsg
    ) -> esdl.ProfileConstraint:
        c = esdl.ProfileConstraint(
            id=constraintMsg["id"],
            name=constraintMsg["name"],
            description=constraintMsg.get("description"),
            attributeReference=constraintMsg.get("attributeReference"),
        )

        if constraintMsg["maximum"]:
            c.maximum = self._handle_influxdb_profile(es_id, constraintMsg["maximum"])
        if constraintMsg["minimum"]:
            c.minimum = self._handle_influxdb_profile(es_id, constraintMsg["minimum"])

        return c

    def _handle_influxdb_profile(
        self, es_id: str, profileMsg: InfluxDBProfileMsg
    ) -> Optional[esdl.InfluxDBProfile]:
        id = profileMsg["id"]
        profile_uiname = profileMsg["displayed_name"]
        multiplier = profileMsg["multiplier"]
        predefined_qau_name = profileMsg["qau_description"]

        pm = get_project_manager()
        esdl_profile = Profiles.get_instance().create_esdl_influxdb_profile(
            profile_uiname, multiplier
        )
        esdl_profile.id = id

        for pqau in esdl_config.esdl_config["predefined_quantity_and_units"]:
            if pqau["description"].lower() == predefined_qau_name.lower():
                predefined_qau_id = pqau["id"]
                try:
                    # check if predefined qau is already present in the ESDL
                    qau = pm.get_by_id(es_id, predefined_qau_id)
                except KeyError:
                    qau = ESDLQuantityAndUnits.build_qau_from_dict(pqau)
                    esi_qau = ESDLQuantityAndUnits.get_or_create_esi_qau(pm, es_id)
                    esi_qau.quantityAndUnit.append(qau)
                    pm.add_object_to_dict(es_id, qau)
                break

        # make a reference instead of a direct link
        qau_ref = esdl.QuantityAndUnitReference(reference=qau)
        esdl_profile.profileQuantityAndUnit = qau_ref

        return esdl_profile

    def _handle_ranged_constraint(
        self, constraintMsg: RangedConstraintMsg
    ) -> esdl.RangedConstraint:
        c = esdl.RangedConstraint(
            id=constraintMsg["id"],
            name=constraintMsg["name"],
            description=constraintMsg.get("description"),
            attributeReference=constraintMsg.get("attributeReference"),
            range=esdl.Range(
                id=constraintMsg["range"]["id"],
                name=constraintMsg["range"]["name"],
            ),
        )

        if constraintMsg["range"]["min_value"] is not None:
            c.range.minValue = float(constraintMsg["range"]["min_value"])
        if constraintMsg["range"]["mid_value"] is not None:
            c.range.midValue = float(constraintMsg["range"]["mid_value"])
        if constraintMsg["range"]["max_value"] is not None:
            c.range.maxValue = float(constraintMsg["range"]["max_value"])

        return c
