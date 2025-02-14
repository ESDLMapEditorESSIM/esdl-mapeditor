#  This work is based on original code developed and copyrighted by TNO 2025.
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
from dataclasses import dataclass

from bson import json_util


@dataclass
class ActivityContext:
    """
    Stored in MongoDB
    """
    activity_id: str
    name: str
    workflow: str | None
    is_global: bool | None
    wms_layers: list[str]
    context_services: list[str]
    # _id: ObjectId | None = None

    def to_json(self):
        return json_util.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        return ActivityContext(**json_util.loads(json_str))
