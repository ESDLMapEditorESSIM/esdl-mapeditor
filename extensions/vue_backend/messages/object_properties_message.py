from typing import Any, Optional, TypedDict


ObjectFeature = dict[str, Any]
CategorizedObjectFeatures = dict[str, list[ObjectFeature]]


class ObjectDescription(TypedDict):
    name: Optional[str]
    doc: Optional[str]
    type: str
    id: Optional[str]
    fragment: Optional[str]


class ContainerDescription(ObjectDescription):
    container: Optional["ContainerDescription"]


class ObjectCapabilities(TypedDict):
    ports: bool
    cost_information: bool
    kpis: bool
    constraints: bool


class MultiSelectInfo(TypedDict):
    num_assets_selected: int
    selected_asset_type: Optional[str]


class RawObjectInfo(TypedDict):
    object: ObjectDescription
    attributes: list[ObjectFeature]
    references: list[ObjectFeature]
    container: Optional[ContainerDescription]


class ObjectPropertiesInfo(TypedDict):
    object: ObjectDescription
    attributes: CategorizedObjectFeatures
    references: list[ObjectFeature]
    container: Optional[ContainerDescription]
    capabilities: ObjectCapabilities
    port_profile_info: list[dict[str, Any]]
    port_connected_to_info: list[dict[str, Any]]
    cost_information: list[dict[str, Any]]
    kpi_information: list[dict[str, Any]]
    multi_select_info: Optional[MultiSelectInfo]
