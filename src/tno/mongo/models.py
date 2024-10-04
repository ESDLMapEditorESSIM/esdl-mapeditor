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
