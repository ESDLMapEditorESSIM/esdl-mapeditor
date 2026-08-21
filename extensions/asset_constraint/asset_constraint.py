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
from typing import List
from uuid import uuid4

import esdl
from extensions.asset_constraint.asset_constraint_message import (
    ConstraintType,
    RangeMsg,
    ProfileConstraintMsg,
    RangedConstraintMsg,
    PipeDiameterConstraintMsg,
)
from extensions.profiles import Profiles
from extensions.session_manager import get_project_manager, get_session
from esdl.processing.ESDLEcore import get_asset_attributes, get_asset_references

import src.log as log


logger = log.get_logger(__name__)


class AssetConstraint:
    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.register()

    def register(self):
        logger.info("Registering AssetConstraint extension")

        @self.flask_app.route(
            "/asset_constraint/<string:constraint_type>", methods=["GET"]
        )
        def _get_new_empty_constraint(constraint_type: str):
            return self.get_new_empty_constraint(constraint_type)

        @self.flask_app.route(
            "/asset_constraint/<string:es_id>/<string:asset_id>", methods=["GET"]
        )
        def _get_asset_constraint(es_id: str, asset_id: str):
            return self.get_asset_constraint(es_id, asset_id)

        @self.flask_app.route(
            "/asset_constraint/<string:es_id>/<string:asset_id>", methods=["POST"]
        )
        def _set_asset_constraint(es_id: str, asset_id: str) -> Response:
            asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg | PipeDiameterConstraintMsg] = (
                request.get_json()
            )
            try:
                self.set_asset_constraint(es_id, asset_id, asset_constraints)
                return Response("Success", 200)
            except Exception as e:
                return Response(f"Error: {e}", 500)

    def get_new_empty_constraint(self, constraint_type: str) -> dict:
        """
        Create and return a new empty ESDL constraint object of the requested type,
        including its attribute and reference metadata.

        Parameters
        ----------
        constraint_type : str
            The name of the ESDL constraint class to instantiate.

        Returns
        -------
        dict
            A dictionary containing:
            - "attrs": list of attribute definitions for the new constraint
            - "refs": list of reference definitions for the new constraint
        """
        if constraint_type == esdl.ProfileConstraint.__name__:
            constraint = esdl.ProfileConstraint()
        elif constraint_type == esdl.RangedConstraint.__name__:
            constraint = esdl.RangedConstraint()
        elif constraint_type == esdl.PipeDiameterConstraint.__name__:
            constraint = esdl.PipeDiameterConstraint()
        else:
            err = f"Unsupport constraint type {constraint_type}"
            logger.error(err)
            raise ValueError(err)

        if constraint:
            constraint.id = str(uuid4())

        attrs = get_asset_attributes(constraint)
        refs = get_asset_references(constraint)

        return {
            "attrs": attrs,
            "refs": refs
        }

    # All supported constraint types
    ALL_CONSTRAINT_TYPES = [ct.value for ct in ConstraintType]

    # Default attribute references applicable to most asset types
    DEFAULT_ATTRIBUTE_REFERENCES = ['power', 'capacity', 'volume', 'aggregationCount', 'diameter']

    MODEL_CONTEXT_CONFIG = {
        "CHESS": {
            "constraint_types": {
                "HeatProducer": [ConstraintType.RANGED.value, ConstraintType.PROFILE.value],
                "ResidualHeatSource": [ConstraintType.RANGED.value, ConstraintType.PROFILE.value],
                "HeatPump": [ConstraintType.RANGED.value],
                "GasHeater": [ConstraintType.RANGED.value],
                "ElectricBoiler": [ConstraintType.RANGED.value],
                "GeothermalSource": [ConstraintType.RANGED.value],
                "HeatStorage": [ConstraintType.RANGED.value],
                "ATES": [ConstraintType.RANGED.value],
                "HeatExchange": [ConstraintType.RANGED.value],
                "Pipe": [ConstraintType.PIPEDIAMETER.value],
            },
            "attribute_references": {
                "HeatProducer": ["power"],
                "ResidualHeatSource": ["power"],
                "HeatPump": ["power"],
                "GasHeater": ["power"],
                "ElectricBoiler": ["power"],
                "GeothermalSource": ["aggregationCount"],
                "HeatStorage": ["volume"],
                "ATES": ["aggregationCount"],
                "HeatExchange": ["capacity"],
                "Pipe": ["diameter"],
            },
            "disabled_fields": {
                "_default": ["range.min_value", "range.mid_value", "minimum"],
            },
            "notification": {
                "state_is_OPTIONAL": "This asset state is OPTIONAL. Please define a constraint to specify its operational bounds.",
                "state_is_ENABLED": "This asset state is ENABLED. Defined constraints won't be used and can be removed."
            }
        }
    }

    def get_asset_constraint(
        self, es_id: str, asset_id: str
    ) -> dict:
        """
        Get constraints for the asset along with available options for the UI.
        """

        pm = get_project_manager()
        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)
        asset_state = asset.state if asset and asset.eIsSet('state') else None
        asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg | PipeDiameterConstraintMsg] = []

        asset_type = ''
        if asset:
            asset_type = asset.eClass.name
            constraints = asset.constraint
            for c in constraints:
                if isinstance(c, esdl.ProfileConstraint):
                    constraint_msg = self._get_profile_constraint_msg(c)
                elif isinstance(c, esdl.RangedConstraint):
                    constraint_msg = self._get_ranged_constraint_msg(c)
                elif isinstance(c, esdl.PipeDiameterConstraint):
                    constraint_msg = self._get_pipediameter_constraint_msg(c)
                else:
                    raise ValueError("Unsupported constraint class")

                asset_constraints.append(constraint_msg)

        model_context = get_session('mapeditor_model_context')
        context_config = self.MODEL_CONTEXT_CONFIG.get(model_context) if model_context else None

        return {
            'constraints': asset_constraints,
            'available_constraint_types': self._derive_available_constraint_types(asset_type, context_config),
            'available_attribute_references': self._derive_attribute_reference(asset_type, context_config),
            'disabled_fields': self._derive_disabled_fields(asset_type, context_config),
            'notification': self._derive_notification(asset_type, asset_state, asset_constraints, context_config),
        }

    def _derive_available_constraint_types(self, asset_type: str, context_config: dict | None) -> List[str]:
        if context_config:
            return context_config.get("constraint_types", {}).get(asset_type, self.ALL_CONSTRAINT_TYPES)
        return self.ALL_CONSTRAINT_TYPES

    def _derive_attribute_reference(self, asset_type: str, context_config: dict | None) -> List[str]:
        if context_config:
            return context_config.get("attribute_references", {}).get(asset_type, self.DEFAULT_ATTRIBUTE_REFERENCES)
        return self.DEFAULT_ATTRIBUTE_REFERENCES

    def _derive_disabled_fields(self, asset_type: str, context_config: dict | None) -> List[str]:
        if context_config:
            disabled = context_config.get("disabled_fields", {})
            return disabled.get(asset_type, disabled.get("_default", []))
        return []

    def _derive_notification(self, asset_type: str, asset_state, asset_constraints: list, context_config: dict | None) -> str | None:
        if not context_config:
            return None
        if asset_type not in context_config.get("constraint_types", {}):
            return None
        notifications = context_config.get('notification', {})
        if asset_state == esdl.AssetStateEnum.OPTIONAL and len(asset_constraints) == 0:
            return notifications.get('state_is_OPTIONAL')
        if asset_state == esdl.AssetStateEnum.ENABLED and len(asset_constraints) > 0:
            return notifications.get('state_is_ENABLED')
        return None

    def _get_profile_constraint_msg(
        self, constraint: esdl.ProfileConstraint
    ) -> ProfileConstraintMsg:
        """
        Parse an esdl ProfileConstraint instance into a ProfileConstraintMsg
        """

        max_profile_info = None
        if constraint.maximum and isinstance(constraint.maximum, esdl.GenericProfile):
            max_profile_info = Profiles.serialize_esdl_profile(constraint.maximum)

        min_profile_info = None
        if constraint.minimum and isinstance(constraint.minimum, esdl.GenericProfile):
            min_profile_info = Profiles.serialize_esdl_profile(constraint.minimum)

        profile_constraint_msg = ProfileConstraintMsg(
            id=constraint.id,
            name=constraint.name,
            description=constraint.description,
            attributeReference=constraint.attributeReference,
            type=ConstraintType.PROFILE.value,
            maximum=max_profile_info,
            minimum=min_profile_info,
        )

        return profile_constraint_msg

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

    def _get_pipediameter_constraint_msg(
        self, constraint: esdl.PipeDiameterConstraint
    ) -> PipeDiameterConstraintMsg:
        msg = PipeDiameterConstraintMsg(
            type=ConstraintType.PIPEDIAMETER.value,
            id=constraint.id,
            name=constraint.name,
            description=constraint.description,
            attributeReference=constraint.attributeReference,
            maximum=getattr(constraint.maximum, "name", None),
            minimum=getattr(constraint.minimum, "name", None)
        )

        return msg

    def set_asset_constraint(
        self,
        es_id: str,
        asset_id: str,
        asset_constraints: List[ProfileConstraintMsg | RangedConstraintMsg | PipeDiameterConstraintMsg],
    ):
        """
        Set asset constraint from the given list of asset_constraints.
        """

        pm = get_project_manager()
        asset: esdl.Asset = pm.get_by_id(es_id, asset_id)

        new_constraints: List[esdl.ProfileConstraint | esdl.RangedConstraint | esdl.PipeDiameterConstraint] = []
        for c in asset_constraints:
            if c["type"] == ConstraintType.PROFILE.value:
                esdl_constraint = self._handle_profile_constraint(es_id, c)
            elif c["type"] == ConstraintType.RANGED.value:
                esdl_constraint = self._handle_ranged_constraint(c)
            elif c["type"] == ConstraintType.PIPEDIAMETER.value:
                esdl_constraint = self._handle_pipediameter_constraint(c)
            else:
                raise ValueError(f"Unsupported constraint type: {c['type']}")
            new_constraints.append(esdl_constraint)

        asset.constraint.clear()
        asset.constraint.extend(new_constraints)

    def _handle_profile_constraint(
        self, es_id: str, constraintMsg: ProfileConstraintMsg
    ) -> esdl.ProfileConstraint:
        c = esdl.ProfileConstraint(
            id=constraintMsg.get("id") or str(uuid4()),
            name=constraintMsg["name"],
            description=constraintMsg.get("description"),
            attributeReference=constraintMsg.get("attributeReference"),
        )

        maximum_profile = constraintMsg["maximum"]
        minimum_profile = constraintMsg["minimum"]

        if maximum_profile:
            c.maximum = Profiles.construct_esdl_profile_instance(es_id=es_id,
                                                                 profile_class=maximum_profile["profileClass"],
                                                                 profile_obj=maximum_profile["profileObj"])
        if minimum_profile:
            c.minimum = Profiles.construct_esdl_profile_instance(es_id=es_id,
                                                                 profile_class=minimum_profile["profileClass"],
                                                                 profile_obj=minimum_profile["profileObj"])

        return c

    def _handle_ranged_constraint(
        self, constraintMsg: RangedConstraintMsg
    ) -> esdl.RangedConstraint:
        c = esdl.RangedConstraint(
            id=constraintMsg.get("id") or str(uuid4()),
            name=constraintMsg["name"],
            description=constraintMsg.get("description"),
            attributeReference=constraintMsg.get("attributeReference"),
            range=esdl.Range(
                id=constraintMsg["range"].get("id") or str(uuid4()),
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

    def _handle_pipediameter_constraint(
        self, constraintMsg: PipeDiameterConstraintMsg
    ) -> esdl.PipeDiameterConstraint:
        c = esdl.PipeDiameterConstraint(
            id=constraintMsg.get("id") or str(uuid4()),
            name=constraintMsg["name"],
            description=constraintMsg.get("description"),
            attributeReference=constraintMsg.get("attributeReference"),
            maximum=esdl.PipeDiameterEnum.from_string(constraintMsg.get("maximum")),
            minimum=esdl.PipeDiameterEnum.from_string(constraintMsg.get("minimum"))
        )

        return c
