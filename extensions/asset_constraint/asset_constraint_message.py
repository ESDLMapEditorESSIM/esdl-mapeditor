from enum import Enum
from typing import TypedDict, Literal, List, Optional


class ConstraintType(Enum):
    PROFILE = "Profile constraint"
    RANGED = "Ranged constraint"


class ProfileClass(Enum):
    INFLUXDB = "InfluxDBProfile"


class InfluxDBProfileMsg(TypedDict):
    id: str
    name: Optional[str]
    displayed_name: str
    profile_class: Literal[ProfileClass.INFLUXDB]
    multiplier: float
    qau_description: str


class ConstraintBase(TypedDict):
    id: str
    name: str
    description: Optional[str]
    attributeReference: Optional[str]


class ProfileConstraintMsg(ConstraintBase):
    type: Literal[ConstraintType.PROFILE]
    maximum: Optional[InfluxDBProfileMsg]
    minimum: Optional[InfluxDBProfileMsg]


class RangeMsg(TypedDict):
    id: str
    name: str
    min_value: Optional[float]
    mid_value: Optional[float]
    max_value: Optional[float]


class RangedConstraintMsg(ConstraintBase):
    type: Literal[ConstraintType.RANGED]
    range: RangeMsg
