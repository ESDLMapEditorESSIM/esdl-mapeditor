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
from datetime import datetime
from typing import TypedDict


class LmiMessage(TypedDict):
    # Unique identifier for the message.
    id: str
    # Timestamp when the message was sent.
    timestamp: datetime | str
    # The client_id is used to identify the client that sent the message.
    client_id: str | None
    user_email: str | None


class Point(TypedDict):
    lat: float
    lng: float


class AssetPositionMessage(LmiMessage):
    point: Point


class WindPotentialResultMessage(LmiMessage):
    wind_potential: float


class NewESDLMessage(LmiMessage):
    b64_esdl: str


class ProjectManagerMessage(LmiMessage):
    b64_project: str
    project_name: str


class HighLevelChangeMessage(LmiMessage):
    high_level_change: str
