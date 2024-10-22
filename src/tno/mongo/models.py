import json
from dataclasses import dataclass
from typing import TypedDict

from bson import ObjectId, json_util


class ActivityContextMenuService(TypedDict):
    """
    A service to add to a context menu.
    """
    # The service ID.
    id: str
    # The location where to add the service. Can be map, area, or building.
    location: str
    icon: str


class ActivityContextMenuJsFunction(TypedDict):
    """
    A JS function to add to the context menu.
    """
    # The label of the context menu.
    title: str
    # The location where to add the service.
    location: str
    icon: str
    # The JS function to activate. Must be available on window!
    js_function: str


@dataclass
class ActivityContext:
    """
    Stored in MongoDB
    """
    activity_id: str
    name: str
    # The workflow to activate.
    workflow: str | None
    # If a context is global, it is shown to all users.
    is_global: bool | None
    # Js function to execute when the context is activated.
    js_function: str | None
    # WMS layers to activate.
    wms_layers: list[str] | None
    # The ESDL layers to disable when activating this context.
    disable_esdl_layers: list[str] | None
    # The services to add to context menus.
    context_menu_services: list[ActivityContextMenuService] | None
    context_menu_js_functions: list[ActivityContextMenuJsFunction] | None
    # Text to show in an alert when activating this context.
    toast_text: str | None
    # _id: ObjectId | None = None

    def to_json(self):
        return json_util.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        return ActivityContext(**json_util.loads(json_str))


class LiveModelInterface(TypedDict):
    lmi_id: str
    name: str
    description: str
    enabled: bool
    can_be_disabled: bool

class ApplicationContext(TypedDict):
    """
    Stored in MongoDB
    """
    application_id: str
    name: str
    # The live model interfaces to activate.
    live_model_interfaces: list[LiveModelInterface]
    # If a context is global, it is shown to all users.
    is_global: bool | None
