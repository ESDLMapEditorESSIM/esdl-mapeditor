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

from uuid import uuid4
from copy import deepcopy

from flask import Flask
from flask_socketio import SocketIO
import requests
from typing import Any, Dict, Optional, List, Union
from dataclasses import asdict

from xml.etree import ElementTree as ET

from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
import src.log as log
from src.roles import is_mapeditor_admin
from src.wms_layer_defaults import default_wms_layers, default_wms_layer_groups, removed_wms_layer_ids

from extensions.vue_backend.messages.map_layers_message import (WmsLayerFeatureRequestBody, 
                                                                WmsLayerRequestInfo, 
                                                                WmsLayerFeatureResp, 
                                                                LayerFeaturePropsResp,
                                                                GetCapabilitiesRequestBody,
                                                                ServiceLayerInfo,
                                                                ServiceGetCapabilitiesResp,
                                                                LayerOpacitySettingRequestBody)

logger = log.get_logger(__name__)

LAYERS_SETTING = 'layers'
LAYERS_GROUP_SETTING = 'layer_groups'
LAYER_PREFERENCES_SETTING = 'layer_preferences'


class WMSLayers:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        self.migrate_default_layers()

    def migrate_default_layers(self) -> None:
        """Remove saved built-ins once, retaining custom layers and display preferences."""
        collection = self.settings_storage.settings
        selector = {"type": SettingType.SYSTEM.value, "name": SettingsStorage.SYSTEM_NAME_IDENTIFIER}
        saved = collection.find_one(selector)
        if saved is None or saved.get("layer_defaults_version") == 1:
            return

        stored_layers = saved.get(LAYERS_SETTING, {})
        stored_groups = saved.get(LAYERS_GROUP_SETTING, {})
        preferences = deepcopy(saved.get(LAYER_PREFERENCES_SETTING, {}))
        # Drop saved standard layers, but keep opacity overrides separate from their definitions.
        layers = {}
        for layer_id, layer in stored_layers.items():
            if layer_id in default_wms_layers or layer_id in removed_wms_layer_ids:
                if "opacity" in layer:
                    preferences.setdefault(layer_id, {}).setdefault("opacity", layer["opacity"])
            else:
                layers[layer_id] = layer

        # Remove standard folders and references while leaving custom folder structure intact.
        groups = deepcopy(stored_groups)
        root_candidates = []
        for group_id, group in stored_groups.items():
            if group_id == "system_root_group" or group_id in default_wms_layer_groups:
                del groups[group_id]
                root_candidates.extend(group.get("child_ids", []))
                if "opened" in group:
                    preferences.setdefault(group_id, {}).setdefault("opened", group["opened"])
            else:
                children = []
                for child_id in group.get("child_ids", []):
                    if child_id in removed_wms_layer_ids:
                        continue
                    if child_id not in default_wms_layers and child_id not in default_wms_layer_groups:
                        children.append(child_id)
                groups[group_id]["child_ids"] = children

        referenced = set()
        for group in groups.values():
            for child_id in group["child_ids"]:
                referenced.add(child_id)

        # Reattach custom items from removed folders so they remain reachable from the system root.
        root_children = []
        for child_id in root_candidates:
            if child_id in layers or child_id in groups:
                if child_id not in referenced and child_id not in root_children:
                    root_children.append(child_id)
        for child_id in list(layers) + list(groups):
            if child_id not in referenced and child_id not in root_children:
                root_children.append(child_id)
        if root_children:
            groups["system_root_group"] = {"child_ids": root_children}

        fields = {
            LAYERS_SETTING: layers,
            LAYERS_GROUP_SETTING: groups,
            LAYER_PREFERENCES_SETTING: preferences,
            "layer_defaults_version": 1,
        }
        collection.update_one({"_id": saved["_id"]}, {"$set": fields})
        logger.info("Migrated stored standard layers to code-defined defaults")

    def check_stored_items(self, *item_ids: Optional[str]) -> None:
        """Prevent definition changes to built-in layers and folders."""
        for item_id in item_ids:
            if item_id in default_wms_layers or item_id in default_wms_layer_groups:
                raise ValueError("Built-in layers and folders are read-only")

    def register(self):
        logger.info('Registering web service layer extension')

        @self.socketio.on('get_service_layer', namespace='/esdl')
        def _get_service_layer(params):
            return self.get_service_layer(params['id'])

        @self.socketio.on('get_service_layer_group', namespace='/esdl')
        def _get_service_layer_group(params):
            return self.get_service_layer_group(params['id'])

        @self.socketio.on('save_service_layer', namespace='/esdl')
        def _save_service_layer(params):
            type = params['type']
            if type in ("WMS", "WMTS"):
                self.save_wms_layer(params['id'], params['lyr_info'])
            elif type == "WFS":
                self.save_wfs_layer(params['id'], params['lyr_info'])
            else:
                logger.error(f"Unsupported type: {type}")
            return self.get_layers()

        @self.socketio.on('add_wms_layer_group', namespace='/esdl')
        def _add_wms_layer_group(params):
            logger.info('add wms layer group')
            group_id = params['id']
            parent_group_id = params['parent_group_id']

            layer_group = {
                "description": params['description'],
                "setting_type": params['setting_type'],
                "project_name": params['project_name'],
                "child_ids": []
            }

            self.add_wms_layer_group(group_id, layer_group, parent_group_id)

            return self.get_layers()

        @self.socketio.on('rename_layer_group', namespace='/esdl')
        def _rename_layer_group(params):
            self.rename_layer_group(params['group_id'], params['group_name'])
            return self.get_layers()

        @self.socketio.on('add_service_layer', namespace='/esdl')
        def _add_service_layer(params):
            logger.info(params)
            type = params['type']
            layer_id = params['id']
            parent_group_id = params['parent_group_id']

            layer = {
                "type": params['type'],
                "description": params['description'],
                "url": params['url'],
                "layer_name": params['name'],
                "setting_type": params['setting_type'],
                "project_name": params['project_name'],
                "layer_ref": None,
                "visible": False,
                "min_zoom_level": params.get('min_zoom_level')
            }

            if type == "WMS":
                layer["legend_url"] = params.get('legend_url')
            elif type == "WFS":
                layer["style"] = params.get('style')
            else:
                logger.error(f"Unsupported type: {type}")

            self.add_layer_to_storage(layer_id, layer, parent_group_id)
            
            return self.get_layers()

        @self.socketio.on('remove_wms_layer', namespace='/esdl')
        def _remove_wms_layer(params):
            layer_id = params['id']
            parent_id = params['parent_id']
            self.remove_wms_layer(layer_id, parent_id)
            return self.get_layers()

        @self.socketio.on('remove_wms_layer_group', namespace='/esdl')
        def _remove_wms_layer_group(params):
            group_id = params['id']
            parent_id = params['parent_id']
            self.remove_wms_layer_group(group_id, parent_id)
            return self.get_layers()

        @self.socketio.on('move_wms_item', namespace='/esdl')
        def _move_wms_item(params: dict):
            item_id = params['item_id']
            old_parent_id = params['old_parent_id']
            new_parent_id = params['new_parent_id']
            position = params['position']
            self.move_wms_item(item_id, old_parent_id, new_parent_id, position)
            return self.get_layers()

        @self.socketio.on('copy_wms_item', namespace='/esdl')
        def _copy_wms_item(params: dict):
            item_id = params['item_id']
            new_parent_id = params['new_parent_id']
            position = params['position']
            self.copy_wms_item_and_children(item_id, new_parent_id, position)
            return self.get_layers()
        
        @self.socketio.on('query_wms_layer_feature', namespace='/esdl')
        def _query_wms_layer_feature(params: Dict[str, Union[Dict, List]]) -> Dict[str, Any]:
            """
            Args:
                params (Dict): A dict with structure as {ev_lat_lng: MouseEventLatLng, layers: List[WmsLayerRequestInfo]}
            """
            req = WmsLayerFeatureRequestBody(**params)
            layers_features_props: list[LayerFeaturePropsResp] = []
            for l in req.layers:
                layer = WmsLayerRequestInfo(**l)
                props = self.query_wms_layer_feature_properties(layer.url)
                layers_features_props.append(LayerFeaturePropsResp(layer.name, props))
            resp = WmsLayerFeatureResp(req.ev_lat_lng, layers_features_props)
            return asdict(resp)

        @self.socketio.on('get_service_getcapabilities', namespace='/esdl')
        def _get_service_getcapabilities(params: Dict[str, str]) -> Dict[str, Any]:
            """
            Args:
                params (Dict): A dict with structure as {url: str, service_type: str}
            """
            req = GetCapabilitiesRequestBody(**params)
            result = self.get_service_getcapabilities(req.url, req.service_type)
            return asdict(result)
        
        @self.socketio.on('save_layer_opacity_setting', namespace='/esdl')
        def _save_layer_opacity_setting(params: Dict[str, Union[str, float]]) -> Dict[str, Dict]:
            """
            Args:
                params (Dict): A dict with structure as {layer_id: str, opacity: float}
            """
            req = LayerOpacitySettingRequestBody(**params)
            self.save_layer_opacity_setting(req.layer_id, req.opacity)
            return self.get_layers()


    def query_wms_layer_feature_properties(self, url: str) -> Optional[Dict]:
        feature_props: Optional[Dict] = None
        resp = None
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            if resp.status_code == 200:
                data = resp.json()
                if 'features' in data and len(data['features']) > 0:
                    feature_props = data['features'][0]['properties']
                else:
                    feature_props = {}
        except Exception as e:
            if resp is not None:
                logger.warning(
                    "Error querying WMS layer feature: %s; HTTP %s; Content-Type: %s; response: %.1000s",
                    str(e), resp.status_code, resp.headers.get('Content-Type'), resp.text
                )
            else:
                logger.warning(f"An unexpected error occurred while querying layer feature: {str(e)}")
        return feature_props
    
    def get_service_getcapabilities(self, url: str, service_type: str = "WMS") -> ServiceGetCapabilitiesResp:
        """
        Fetches GetCapabilities for either WMS or WFS.
        
        service_type: "WMS" or "WFS"
        """
        try:
            resp = requests.get(url, params={"service": service_type, 
                                             "request": "GetCapabilities"})
            resp.raise_for_status()

            content_type = resp.headers.get('Content-Type')
            if 'xml' not in content_type:
                raise Exception(f"Expected XML response, but received {content_type}")
            
            getcapabilities_xml = resp.text
            if service_type == "WMS":
                layer_options = self.parse_wms_getcapabilities_xml(getcapabilities_xml)
            elif service_type == "WFS":
                layer_options = self.parse_wfs_getcapabilities_xml(getcapabilities_xml)
            else:
                return ServiceGetCapabilitiesResp(False, f"Unsupported service type {service_type}.")

            if len(layer_options):
                return ServiceGetCapabilitiesResp(True, layer_options)
            else:
                return ServiceGetCapabilitiesResp(False, "No layer or feature types available.")
        except Exception as e:
            logger.warning(e)
            return ServiceGetCapabilitiesResp(False, f"{str(e)}.")
        
    def parse_wms_getcapabilities_xml(self, xml_string: str) -> List[ServiceLayerInfo]:
        """
        Parses a WMS GetCapabilities XML string and extracts layer attributes.

        It returns a list of ServiceLayerInfo data class. Each ServiceLayerInfo contains
        'name', 'title', and 'legend_url' attributes. If a layer does not have a
        legend URL, the 'legend_url' will be an empty string.

        Args:
            xml_string (str): The XML string of the WMS GetCapabilities document.

        Returns:
            list: A list of ServiceLayerInfo data class, each with 'name', 'title', and 'legend_url' attributes.
        """
        namespaces = {'wms': 'http://www.opengis.net/wms', 'xlink': 'http://www.w3.org/1999/xlink'}
        root = ET.fromstring(xml_string)
        layers = root.findall(".//wms:Layer", namespaces)
        layer_options: List[ServiceLayerInfo] = []

        for layer in layers:
            layer_name_elem = layer.find("wms:Name", namespaces)
            layer_title_elem = layer.find("wms:Title", namespaces)

            if layer_name_elem is not None and layer_title_elem is not None:
                layer_name = layer_name_elem.text
                layer_title = layer_title_elem.text

                # Extract legend URL
                legend_url = ""
                styles = layer.findall("wms:Style", namespaces)
                if styles:
                    # NOTE: the current implementation default to use the first style
                    legend_url_elem = styles[0].find("wms:LegendURL", namespaces)
                    if legend_url_elem is not None:
                        online_resource = legend_url_elem.find("wms:OnlineResource", namespaces)
                        if online_resource is not None:
                            legend_url = online_resource.get(f"{{{namespaces['xlink']}}}href")

                if layer_name is not None and not any(l.name == layer_name for l in layer_options):
                    layer_info = ServiceLayerInfo(layer_name, layer_title, legend_url)
                    layer_options.append(layer_info)
                
        return layer_options
    
    def parse_wfs_getcapabilities_xml(self, xml_string: str) -> List[ServiceLayerInfo]:
        """
        Parses a WFS GetCapabilities XML string and extracts layer attributes.
        """
        root = ET.fromstring(xml_string)
        layer_options: List[ServiceLayerInfo] = []

        feature_types = root.findall(".//{*}FeatureType") 
        
        for ft in feature_types:
            name = ft.findtext("{*}Name")
            title = ft.findtext("{*}Title")
            if name and title:
                layer_options.append(ServiceLayerInfo(name, title, None))

        return layer_options
    
    def add_wms_layer_group(self, layer_group_id: str, layer_group: dict, parent_group_id: str = None,
                            position: str = None):
        setting_type = SettingType(layer_group['setting_type'])
        self.check_stored_items(layer_group_id, parent_group_id)
        identifier = self._get_identifier(setting_type, layer_group['project_name'])

        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_GROUP_SETTING):
            layer_groups = self.settings_storage.get(setting_type, identifier, LAYERS_GROUP_SETTING)
        else:
            layer_groups = dict()

        if layer_group_id == "system_root_group":
            layer_group = {
                "child_ids": [
                    child_id
                    for child_id in layer_group["child_ids"]
                    if child_id not in default_wms_layers and child_id not in default_wms_layer_groups
                ]
            }
        layer_groups[layer_group_id] = layer_group
        self.settings_storage.set(setting_type, identifier, LAYERS_GROUP_SETTING, layer_groups)
        self.add_child_to_layer_group(parent_group_id, layer_group_id, position)

    def get_service_layer_group(self, group_id: str):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        group = self.get_layers()[LAYERS_GROUP_SETTING][group_id]
        return group

    def add_child_to_layer_group(self, group_id: str, child_id: str, position: int = None):
        if group_id:
            group = self.get_service_layer_group(group_id)
            if isinstance(position, int):
                group["child_ids"].insert(position, child_id)
            else:
                group["child_ids"].append(child_id)
            self.add_wms_layer_group(group_id, group)

    def remove_child_from_layer_group(self, group_id: str, child_id: str):
        group = self.get_service_layer_group(group_id)
        if child_id in group['child_ids']:
            group['child_ids'].remove(child_id)
        self.add_wms_layer_group(group_id, group)

    def update_item_setting_type_project(self, item_id: str, parent_id: str):
        self.check_stored_items(item_id, parent_id)
        all_layers = self.get_layers()
        if item_id in all_layers[LAYERS_SETTING]:
            item = all_layers[LAYERS_SETTING][item_id]
            item_setting = LAYERS_SETTING
        else:
            item = all_layers[LAYERS_GROUP_SETTING][item_id]
            item_setting = LAYERS_GROUP_SETTING

        item_setting_type = SettingType(item['setting_type'])
        item_identifier = self._get_identifier(item_setting_type, item['project_name'])

        parent_group = all_layers[LAYERS_GROUP_SETTING][parent_id]
        parent_setting_type = SettingType(parent_group['setting_type'])
        parent_identifier = self._get_identifier(parent_setting_type, parent_group['project_name'])

        if item_identifier != parent_identifier:
            # remove item from old location
            items = self.settings_storage.get(item_setting_type, item_identifier, item_setting)
            del (items[item_id])
            self.settings_storage.set(item_setting_type, item_identifier, item_setting, items)

            # add item to new parent
            if self.settings_storage.has(parent_setting_type, parent_identifier, item_setting):
                items = self.settings_storage.get(parent_setting_type, parent_identifier, item_setting)
            else:
                items = {}
            item['setting_type'] = parent_group['setting_type']
            item['project_name'] = parent_group['project_name']
            items[item_id] = item
            self.settings_storage.set(parent_setting_type, parent_identifier, item_setting, items)

        if 'child_ids' in item and item['child_ids']:
            for child_id in item['child_ids']:
                self.update_item_setting_type_project(child_id, item_id)

    def move_wms_item(self, item_id: str, old_parent_id: str, new_parent_id: str, position: id):
        self.check_stored_items(item_id, old_parent_id, new_parent_id)
        self.remove_child_from_layer_group(old_parent_id, item_id)
        self.add_child_to_layer_group(new_parent_id, item_id, position)
        self.update_item_setting_type_project(item_id, new_parent_id)

    def copy_wms_item_and_children(self, item_id: str, new_parent_id: str, position: id):
        """Copy a layer or folder into editable storage, preserving service-specific options."""
        all_layers = self.get_layers()
        new_item_id = str(uuid4())
        new_parent_group = all_layers[LAYERS_GROUP_SETTING][new_parent_id]
        if item_id in all_layers[LAYERS_SETTING]:
            layer = all_layers[LAYERS_SETTING][item_id]
            new_layer = deepcopy(layer)
            new_layer.pop('readonly', None)
            new_layer.pop('id', None)
            new_layer.update(
                setting_type=new_parent_group['setting_type'],
                project_name=new_parent_group['project_name'],
                layer_ref=None,
                visible=False,
            )
            self.add_layer_to_storage(new_item_id, new_layer, new_parent_id, position)
        elif item_id in all_layers[LAYERS_GROUP_SETTING]:
            layer_group = all_layers[LAYERS_GROUP_SETTING][item_id]
            new_layer_group = {
                "description": layer_group['description'],
                "setting_type": new_parent_group['setting_type'],
                "project_name": new_parent_group['project_name'],
                "child_ids": []
            }
            self.add_wms_layer_group(new_item_id, new_layer_group, new_parent_id)
            for child_id in layer_group['child_ids']:
                self.copy_wms_item_and_children(child_id, new_item_id, None)

    def rename_layer_group(self, group_id: str, group_name: str):
        group = self.get_service_layer_group(group_id)
        group["description"] = group_name
        self.add_wms_layer_group(group_id, group)

    def add_layer_to_storage(self, layer_id: str, layer: dict, parent_group_id: str = None, position: str = None):
        self.check_stored_items(layer_id, parent_group_id)
        setting_type = SettingType(layer['setting_type'])
        project_name = layer.get('project_name')
        identifier = self._get_identifier(setting_type, project_name)
        layer['visible'] = False  # make sure we don't save the visibility
        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
        else:
            layers = dict()
        layers[layer_id] = layer
        self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)

        self.add_child_to_layer_group(parent_group_id, layer_id, position)

    def save_layer_opacity_setting(self, layer_id: str, opacity: float) -> None:
        """Persist built-in opacity separately from the code-defined layer."""
        if not isinstance(opacity, (int, float)) or not 0 <= opacity <= 1:
            raise ValueError('Opacity must be between 0 and 1')
        if layer_id in default_wms_layers:
            preferences = {}
            if self.settings_storage.has_system(LAYER_PREFERENCES_SETTING):
                preferences = self.settings_storage.get_system(LAYER_PREFERENCES_SETTING)
            preferences.setdefault(layer_id, {})['opacity'] = opacity
            self.settings_storage.set_system(LAYER_PREFERENCES_SETTING, preferences)
            return
        layer = self.get_service_layer(layer_id)
        layer_type = layer.get("type", "WMS")
        setting_type = SettingType(layer['setting_type'])
        project_name = layer.get('project_name')
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
            if layer_type in ("WMS", "WMTS"):
                layers[layer_id]['opacity'] = opacity
            elif layer_type == "WFS" and layer['style']:
                layers[layer_id]['style']['opacity'] = opacity
            self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)
        else:
            logger.error("Error whiling saving layer opacity setting to the settings_storage.")

    def get_service_layer(self, layer_id: str):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        layer = self.get_layers()[LAYERS_SETTING][layer_id]
        return layer

    def save_wms_layer(self, layer_id: str, lyr_info: dict):
        layer = self.get_service_layer(layer_id)

        layer["description"] = lyr_info["description"]
        layer["url"] = lyr_info["url"]
        layer["layer_name"] = lyr_info["layer_name"]
        layer["legend_url"] = lyr_info.get("legend_url")
        layer["attribution"] = lyr_info["attribution"]
        layer["min_zoom_level"] = lyr_info["min_zoom_level"]

        self.add_layer_to_storage(layer_id, layer)

    def save_wfs_layer(self, layer_id: str, lyr_info: dict):
        layer = self.get_service_layer(layer_id)

        layer["description"] = lyr_info["description"]
        layer["url"] = lyr_info["url"]
        layer["layer_name"] = lyr_info["layer_name"]
        layer["min_zoom_level"] = lyr_info["min_zoom_level"]

        self.add_layer_to_storage(layer_id, layer)

    def remove_wms_layer(self, layer_id: str, parent_id: str):
        self.check_stored_items(layer_id, parent_id)
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        if layer_id not in self.get_layers()[LAYERS_SETTING]:
            return False
        layer = self.get_service_layer(layer_id)
        setting_type = SettingType(layer['setting_type'])
        identifier = self._get_identifier(setting_type, layer['project_name'])
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            # update layers dict
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
            if layer_id in layers:
                logger.info('Deleting layer {}'.format(layers[layer_id]))
                del (layers[layer_id])
                self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)
                self.remove_child_from_layer_group(parent_id, layer_id)
                return True

    def remove_wms_layer_group(self, group_id: str, parent_id: str):
        self.check_stored_items(group_id, parent_id)
        group = self.get_layers()[LAYERS_GROUP_SETTING][group_id]

        # if group has children remove as well
        if group['child_ids']:
            self.remove_wms_layer_group_children(group_id)

        setting_type = SettingType(group['setting_type'])
        identifier = self._get_identifier(setting_type, group['project_name'])
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, LAYERS_GROUP_SETTING):
            # update layer groups dict
            groups = self.settings_storage.get(setting_type, identifier, LAYERS_GROUP_SETTING)
            logger.info('Deleting layer group {}'.format(groups[group_id]))
            del (groups[group_id])
            self.settings_storage.set(setting_type, identifier, LAYERS_GROUP_SETTING, groups)
        self.remove_child_from_layer_group(parent_id, group_id)

    def remove_wms_layer_group_children(self, group_id: str, all_layers: dict = None):
        if not all_layers:  # to avoid getting all_layers many times
            all_layers = self.get_layers()
        group = all_layers[LAYERS_GROUP_SETTING][group_id]
        for child_id in group['child_ids']:
            if not self.remove_wms_layer(child_id, group_id):
                # if not wms layer then wms_group:
                if child_id in all_layers[LAYERS_GROUP_SETTING]:
                    child_group = all_layers[LAYERS_GROUP_SETTING][child_id]
                    if child_group['child_ids']:
                        self.remove_wms_layer_group_children(child_id, all_layers)
                    self.remove_wms_layer_group(child_id, group_id)

    def _get_identifier(self, setting_type: SettingType, project_name: str = None):
        if setting_type is None:
            return
        elif setting_type == SettingType.USER:
            identifier = get_session('user-email')
        elif setting_type == SettingType.PROJECT:
            if project_name is not None:
                identifier = project_name.replace(' ', '_')
            else:
                identifier = 'unnamed project'
        elif setting_type == SettingType.SYSTEM:
            identifier = SettingsStorage.SYSTEM_NAME_IDENTIFIER
        else:
            return None
        return identifier

    def get_layers(self):
        """Combine custom layers with fresh copies of the code-defined standard tree."""
        built_in_layers = deepcopy(default_wms_layers)
        built_in_groups = deepcopy(default_wms_layer_groups)
        # gets the web service layers and group layer lists
        all_layers = dict()
        all_layer_groups = dict(built_in_groups)

        # add custom system layers and layer groups
        system_layers = {}
        system_groups = {}
        if self.settings_storage.has_system(LAYERS_SETTING):
            system_layers = self.settings_storage.get_system(LAYERS_SETTING)
        if self.settings_storage.has_system(LAYERS_GROUP_SETTING):
            system_groups = self.settings_storage.get_system(LAYERS_GROUP_SETTING)
        all_layers.update(system_layers)
        all_layer_groups.update(system_groups)
        custom_children = system_groups.get("system_root_group", {}).get("child_ids", [])
        all_layer_groups["system_root_group"] = {
            "description": "System Layers",
            "setting_type": SettingType.SYSTEM.value,
            "project_name": SettingType.SYSTEM.value,
            "is_root": True,
            "child_ids": [
                child_id
                for child_id in custom_children
                if child_id not in default_wms_layers and child_id not in default_wms_layer_groups
            ],
        }

        # add user layers and layer groups
        user = get_session('user-email')
        if user is not None:
            user_layers = dict()
            if self.settings_storage.has_user(user, LAYERS_SETTING):
                user_layers.update(self.settings_storage.get_user(user, LAYERS_SETTING))
            if not self.settings_storage.has_user(user, LAYERS_GROUP_SETTING):
                # add root group
                layer_groups = dict()
                layer_groups['user_root_group'] = {
                    "setting_type": SettingType.USER.value,
                    "project_name": SettingType.USER.value,
                    "description": "Personal Layers",
                    "is_root": True,
                    "child_ids": [layer_id for layer_id in user_layers]
                }
                self.settings_storage.set_user(user, LAYERS_GROUP_SETTING, layer_groups)
            all_layers.update(user_layers)
            all_layer_groups.update(self.settings_storage.get_user(user, LAYERS_GROUP_SETTING))

        # add project layers and layer groups
        user_group = get_session('user-group')
        if user_group is not None:
            for group in user_group:
                project_layers = dict()
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, LAYERS_SETTING):
                    project_layers.update(self.settings_storage.get_project(identifier, LAYERS_SETTING))
                if not self.settings_storage.has_project(identifier, LAYERS_GROUP_SETTING):
                    # add root group
                    layer_groups = dict()
                    key = identifier + "_root_group"
                    layer_groups[identifier + "_root_group"] = {
                        "setting_type": SettingType.PROJECT.value,
                        "project_name": identifier,
                        "description": "Project Layers for " + group,
                        "is_root": True,
                        "child_ids": [layer_id for layer_id in project_layers]
                    }
                    self.settings_storage.set_project(identifier, LAYERS_GROUP_SETTING, layer_groups)

                all_layers.update(project_layers)
                all_layer_groups.update(self.settings_storage.get_project(identifier, LAYERS_GROUP_SETTING))

        # Built-in definitions always come from code, not saved copies.
        preferences = {}
        if self.settings_storage.has_system(LAYER_PREFERENCES_SETTING):
            preferences = self.settings_storage.get_system(LAYER_PREFERENCES_SETTING)
        for layer_id, layer in built_in_layers.items():
            layer["project_name"] = SettingType.SYSTEM.value
            if "opacity" in preferences.get(layer_id, {}):
                layer["opacity"] = preferences[layer_id]["opacity"]
        for group_id, group in built_in_groups.items():
            if "opened" in preferences.get(group_id, {}):
                group["opened"] = preferences[group_id]["opened"]

        all_layers.update(built_in_layers)
        all_layer_groups.update(built_in_groups)

        # set rights
        is_admin = is_mapeditor_admin()
        for layer_id, layer in all_layers.items():
            layer["readonly"] = layer_id in default_wms_layers or (
                layer["setting_type"] == SettingType.SYSTEM.value and not is_admin
            )
        for group_id, layer_group in all_layer_groups.items():
            layer_group["readonly"] = group_id in default_wms_layer_groups or (
                layer_group["setting_type"] == SettingType.SYSTEM.value and not is_admin
            )
        return {LAYERS_SETTING: all_layers, LAYERS_GROUP_SETTING: all_layer_groups}
