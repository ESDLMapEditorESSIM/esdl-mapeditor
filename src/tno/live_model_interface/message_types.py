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
from typing import TypedDict


class Point(TypedDict):
    lat: float
    lng: float


class AssetPositionMessage(TypedDict):
    point: Point
    client_id: str
    user_email: str


class WindPotentialResultMessage(TypedDict):
    user_email: str
    client_id: str
    wind_potential: float


class NewESDLMessage(TypedDict):
    user_email: str
    client_id: str
    b64_esdl: str


class HighLevelChangeMessage(TypedDict):
    user_email: str
    client_id: str
    high_level_change: str

