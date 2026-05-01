from enum import Enum
from typing import TypedDict, Literal, Optional


class ConstraintType(Enum):
    PROFILE = "ProfileConstraint"
    RANGED = "RangedConstraint"
    PIPEDIAMETER = "PipeDiameterConstraint"


class ProfileClassEnum(Enum):
    """Supported profile classes for profile creation and update"""
    SINGLEVALUE = "SingleValue"
    INFLUXDBPROFILE = "InfluxDBProfile"
    DATATABLEPROFILE = "DataTableProfile"


class ProfileInfo(TypedDict):
    profileClass: ProfileClassEnum
    profileObj: dict
    """
    A dictionary contains profile data (with SingleValue or DataTableProfile-like structure)
    for instantiating an ESDL profile, or is returned as a serialized profile for the frontend application.
    """


class ConstraintBase(TypedDict):
    id: Optional[str]
    name: str
    description: Optional[str]
    attributeReference: Optional[str]


class ProfileConstraintMsg(ConstraintBase):
    type: Literal[ConstraintType.PROFILE]
    maximum: Optional[ProfileInfo]
    minimum: Optional[ProfileInfo]


class RangeMsg(TypedDict):
    id: Optional[str]
    name: str
    min_value: Optional[float]
    mid_value: Optional[float]
    max_value: Optional[float]


class RangedConstraintMsg(ConstraintBase):
    type: Literal[ConstraintType.RANGED]
    range: RangeMsg


class PipeDiameterConstraintMsg(ConstraintBase):
    type: Literal[ConstraintType.PIPEDIAMETER]
    maximum: Optional[str]
    minimum: Optional[str]