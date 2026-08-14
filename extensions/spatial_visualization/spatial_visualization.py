import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

from flask import Flask
from flask_socketio import SocketIO
from pyecore.ecore import EAttribute, EReference

import esdl
import esdl.processing.ESDLEcore as ESDLEcore
import src.log as log
from extensions.session_manager import get_project_manager, get_session
from extensions.settings_storage import SettingsStorage

logger = log.get_logger(__name__)

LAYER_VISUALIZATION_SETTINGS = "LAYER_VISUALIZATION"

def _walk(obj, steps: List[dict], pattern: List[dict]) -> Iterator[Any]:
    """Yield every object reached from obj by following steps, filtered by the parallel pattern.

    A many-reference fans out when its step carries no key_value (collect) and narrows to the
    single matching child when it does (select).
    """
    if not steps:
        yield obj
        return

    step, matcher = steps[0], pattern[0]
    feature = obj.eClass.findEStructuralFeature(step["ref"])
    if not isinstance(feature, EReference):
        return

    value = obj.eGet(feature)
    if value is None:
        return

    allowed = matcher.get("types")
    key_attr = matcher.get("key")
    wanted = step.get("key_value")

    for child in (list(value) if feature.many else [value]):
        if child is None:
            continue
        if allowed and child.eClass.name not in allowed:
            continue
        if key_attr is not None and wanted is not None and getattr(child, key_attr, None) != wanted:
            continue
        yield from _walk(child, steps[1:], pattern[1:])


def _build_path(ref_group: str, steps: List[dict], attr: Optional[str]) -> str:
    return json.dumps({"ref_group": ref_group, "steps": steps, "attr": attr}, sort_keys=True)


def _parse_path(path: str):
    if not path:
        return None, [], None
    data = json.loads(path)
    return data.get("ref_group"), data.get("steps") or [], data.get("attr")


@dataclass()
class RefFieldSchemaRequest:
    es_id: str
    object_ids: List[str]

@dataclass()
class RefFieldValuesRequest:
    es_id: str
    object_ids: List[str]
    path: str
class SpatialVisualization:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

    def register(self):
        logger.info("Registering SpatialVisualization extension")

        @self.socketio.on("spatial_visualization/object_fields", namespace="/esdl")
        def _get_esdl_object_fields(params: Dict):
            return self.get_esdl_object_attributes(params["es_id"], params["object_id"])

        @self.socketio.on("spatial_visualization/ref_field_schema", namespace="/esdl")
        def _get_ref_field_schema(params: Dict) -> dict:
            req = RefFieldSchemaRequest(**params)
            return self.get_ref_schema(req.es_id, req.object_ids)

        @self.socketio.on("spatial_visualization/ref_field_values", namespace="/esdl")
        def _get_ref_field_values(params: Dict) -> dict:
            req = RefFieldValuesRequest(**params)
            return self.get_ref_field_values(req.es_id, req.object_ids, req.path)

        @self.socketio.on("spatial_visualization/get_layer_styles", namespace="/esdl")
        def _get_layer_styles():
            return self.get_layer_styles()

        @self.socketio.on("spatial_visualization/save_layer_styles", namespace="/esdl")
        def _save_layer_styles(params: Dict):
            if not isinstance(params, dict) or not isinstance(params.get('styles'), list):
                logger.error(f"Invalid request body for save_layer_styles: {params}")
                return None
            return self.save_layer_styles(params['styles'])
    
    def get_layer_styles(self) -> Optional[List[dict]]:
        """
        Fetches the saved layer styles for the currently logged in user.

        :return: The list of saved layer styles, or None if they could not be fetched.
        """
        user = get_session('user-email')
        if user is None:
            logger.warning("No active user session found; cannot fetch layer styles.")
            return None

        try:
            styles: List[dict] = []
            if self.settings_storage.has_user(user, LAYER_VISUALIZATION_SETTINGS):
                user_settings = self.settings_storage.get_user(user, LAYER_VISUALIZATION_SETTINGS)
                if user_settings and user_settings.get('layer_styles') is not None:
                    styles = user_settings.get('layer_styles')
            return styles
        except Exception as e:
            logger.error(f"An error occurred while fetching layer styles for {user}: {e}")
            return None

    def save_layer_styles(self, styles: List[dict]) -> Optional[List[dict]]:
        """
        Saves the given list of layer styles for the currently logged in user.

        :param styles: The full list of layer styles to persist.

        :return: The persisted list of layer styles, or None if they could not be saved.
        """
        user = get_session('user-email')
        if user is None:
            logger.warning("No active user session found; cannot save layer styles.")
            return None

        try:
            self.settings_storage.set_user(user, LAYER_VISUALIZATION_SETTINGS, {"layer_styles": styles})
            return styles
        except Exception as e:
            logger.error(f"An error occurred while saving layer styles for {user}: {e}")
            return None

    def _get_attributes(self, obj) -> list:
        return [
            {'name': a['name'], 'type': a['type'], 'value': a['value']}
            for a in ESDLEcore.get_asset_attributes(obj)
        ]

    def get_esdl_object_attributes(self, es_id: str, object_id: str):
        pm = get_project_manager()
        try:
            obj: esdl.EObject = pm.get_by_id(es_id, object_id)
            attributes = self._get_attributes(obj)
            return attributes
        except KeyError:
            logger.error(f"Error getting object with ES id {es_id} and object id: {object_id}")
            return []

    def _objects_by_id(self, es_id: str, object_ids: List[str]) -> Dict[str, Any]:
        """Map each requested id to its ESDL object, skipping ids that are not in the model."""
        pm = get_project_manager()
        resource = pm.get_energy_system_resource_by_id(es_id)
        if resource is None:
            logger.error(f"Cannot find energy system resource for {es_id}")
            return {}
        uuid_dict = resource.uuid_dict
        return {oid: uuid_dict[oid] for oid in object_ids if oid in uuid_dict}

    def get_ref_schema(self, es_id: str, object_ids: List[str]) -> dict:
        """
        Return a reference field schema as a tree (dict) for the given ESDL objects 
        that can be displayed in frontend dropdown menu.
        """
        objects = self._objects_by_id(es_id, object_ids)
        if not objects:
            return {"ref": {}}

        ref_schema: Dict[str, Any] = {
            "costInformation": {},
            "KPIs": {},
        }

        for schema in ref_schema.keys():
            if schema == "costInformation":
                ref_schema[schema] = self._collect_cost_info_schema(objects.values())
            if schema == "KPIs":
                ref_schema[schema] = self._collect_kpi_schema(objects.values())

        return {"ref": ref_schema}

    def _collect_cost_info_schema(self, objects) -> dict:
        """Walk costInformation on each object and return {c_ref_name: [{attr, attrType}]} merged over all objects."""
        supported_types = ["SingleValue"]
        query_attrs = ["value"]
        result: Dict[str, list] = {}

        for obj in objects:
            containment_refs = []
            if obj.eClass.findEStructuralFeature("costInformation") is None:
                continue  # e.g. esdl.Area has no costInformation reference
            ref_cost_info = obj.eGet("costInformation")
            if ref_cost_info is None:
                continue

            for f in sorted(ref_cost_info.eClass.eAllStructuralFeatures(), key=lambda x: x.name):
                if isinstance(f, EReference) and not f.many and f.containment and not (f.eOpposite and f.eOpposite.containment):
                    containment_refs.append(f)

            for c_ref in containment_refs:
                c_ref_obj = ref_cost_info.eGet(c_ref)
                if c_ref_obj is None:
                    continue

                for child in (list(c_ref_obj) if c_ref.many else [c_ref_obj]):
                    if child is None:
                        continue
                    # The declared eType is often abstract, so filter on the child's real class.
                    if supported_types and child.eClass.name not in supported_types:
                        continue

                    collected_attrs = []
                    for attr in sorted(child.eClass.eAllStructuralFeatures(), key=lambda x: x.name):
                        if isinstance(attr, EAttribute) and (attr.name in query_attrs):
                            # Only record attrs present on at least one instance; unset means the path doesn't exist in this model.
                            if child.eIsSet(attr.name):
                                collected_attrs.append({
                                    "attr": attr.name,
                                    "attrType": attr.eType.name,
                                    # Path token used to fetch the value of this attr on any object.
                                    "path": _build_path("cost_information", [{"ref": "costInformation"}, {"ref": c_ref.name}], attr.name),
                                })
                    if c_ref.name not in result:
                        result[c_ref.name] = []
                    # Merge attrs seen on any object; different objects may have different subsets set.
                    existing = {a["attr"] for a in result[c_ref.name]}
                    for a in collected_attrs:
                        if a["attr"] not in existing:
                            result[c_ref.name].append(a)

        return result

    def _collect_kpi_schema(self, objects) -> dict:
        """
        Walk KPIs on each object and return {path_key: {ecoreType}} for each supported KPI found across all objects.
        
        TODO: return KPI unit in schema?
        """
        result: Dict[str, dict] = {}

        for obj in objects:
            ref_kpis = obj.eGet("KPIs")
            if ref_kpis is None:
                continue
            for kpi in ref_kpis.kpi:
                if kpi is None:
                    continue
                path = json.dumps({"type": kpi.eClass.name, "name": kpi.name}, sort_keys=True)
                if path in result:
                    continue
                if isinstance(kpi, esdl.DistributionKPI):
                    result[path] = {"ecoreType": "distribution"}
                elif isinstance(kpi, esdl.IntKPI):
                    result[path] = {"ecoreType": "EInt"}
                elif isinstance(kpi, esdl.DoubleKPI):
                    result[path] = {"ecoreType": "EDouble"}
                elif isinstance(kpi, esdl.StringKPI):
                    result[path] = {"ecoreType": "EString"}

        return result

    def get_ref_field_values(self, es_id: str, object_ids: List[str], path: str) -> dict:
        """Map of { objectId: { value, type } | None } for the ref field identified by `path`."""
        ref_group, steps, attr = _parse_path(path)
        if not steps or not attr:
            # Path is not a standard ref trail; try routing it as a KPI.
            try:
                kpi_info = json.loads(path)
                kpi_cls = esdl.getEClassifier(kpi_info.get("type"))
                if kpi_cls is not None:
                    if issubclass(kpi_cls, esdl.DistributionKPI):
                        return self._get_distribution_kpi_values(es_id, object_ids, kpi_info["name"])
                    if issubclass(kpi_cls, (esdl.IntKPI, esdl.DoubleKPI, esdl.StringKPI)):
                        return self._get_scalar_kpi_values(es_id, object_ids, kpi_info["name"])
            except (json.JSONDecodeError, KeyError):
                pass
            return {}

        # Steps already encode the exact trail; empty matchers means no type filtering.
        matchers = [{} for _ in steps]
        result: Dict[str, Any] = {oid: None for oid in object_ids}

        for object_id, obj in self._objects_by_id(es_id, object_ids).items():
            for leaf in _walk(obj, steps, matchers):
                feature = leaf.eClass.findEStructuralFeature(attr)
                if not isinstance(feature, EAttribute) or not leaf.eIsSet(attr):
                    continue
                raw = leaf.eGet(feature)
                result[object_id] = {
                    "value": feature.eType.to_string(raw) if raw is not None else None,
                    "type": feature.eType.name,
                }
                break

        return result

    def _get_scalar_kpi_values(self, es_id: str, object_ids: List[str], kpi_name: str) -> dict:
        """Map of { objectId: { value, type: EcoreTypeName } | None } for IntKPI, DoubleKPI, or StringKPI."""
        result: Dict[str, Any] = {oid: None for oid in object_ids}

        for object_id, obj in self._objects_by_id(es_id, object_ids).items():
            ref_kpis = obj.eGet("KPIs")
            if ref_kpis is None:
                continue
            for kpi in ref_kpis.kpi:
                if kpi is None or kpi.name != kpi_name:
                    continue
                if isinstance(kpi, esdl.IntKPI):
                    ecore_type, raw = "EInt", kpi.value
                elif isinstance(kpi, esdl.DoubleKPI):
                    ecore_type, raw = "EDouble", kpi.value
                elif isinstance(kpi, esdl.StringKPI):
                    ecore_type, raw = "EString", kpi.value
                else:
                    break
                result[object_id] = {
                    "value": str(raw) if raw is not None else None,
                    "type": ecore_type,
                }
                break

        return result

    def _get_distribution_kpi_values(self, es_id: str, object_ids: List[str], kpi_name: str) -> dict:
        """Map of { objectId: { value: [{label, value}], type: 'distribution' } | None } for a DistributionKPI."""
        result: Dict[str, Any] = {oid: None for oid in object_ids}

        for object_id, obj in self._objects_by_id(es_id, object_ids).items():
            ref_kpis = obj.eGet("KPIs")
            if ref_kpis is None:
                continue
            for kpi in ref_kpis.kpi:
                if kpi is None or kpi.name != kpi_name:
                    continue
                if not isinstance(kpi, esdl.DistributionKPI):
                    break
                dist = kpi.distribution
                if isinstance(dist, esdl.StringLabelDistribution):
                    items = [{"label": si.label, "value": si.value} for si in dist.stringItem]
                    result[object_id] = {"value": items, "type": "distribution"}
                break

        return result

