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

from flask import Flask
from flask_socketio import SocketIO

from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
import src.log as log

logger = log.get_logger(__name__)

LAYERS_SETTING = 'layers'
LAYERS_GROUP_SETTING = 'layer_groups'


class WMSLayers:
    def __init__(self, flask_app: Flask, socket: SocketIO, settings_storage: SettingsStorage):
        self.flask_app = flask_app
        self.socketio = socket
        self.settings_storage = settings_storage
        self.register()

        # add initial layers when not in the system settings
        if not self.settings_storage.has_system(LAYERS_SETTING):
            self.settings_storage.set_system(LAYERS_SETTING, default_wms_layers)
        else:
            logger.info('Found WMS layers in System Settings')

        if not self.settings_storage.has_system(LAYERS_GROUP_SETTING):
            self.settings_storage.set_system(LAYERS_GROUP_SETTING, default_system_wms_layer_groups)

    def register(self):
        logger.info('Registering WMS layer extension')

        @self.socketio.on('get_wms_layer', namespace='/esdl')
        def _get_wms_layer(params):
            return self.get_wms_layer(params['id'])

        @self.socketio.on('get_wms_layer_group', namespace='/esdl')
        def _get_wms_layer_group(params):
            return self.get_wms_layer_group(params['id'])

        @self.socketio.on('save_wms_layer', namespace='/esdl')
        def _save_wms_layer(params):
            self.save_wms_layer(params['id'], params['lyr_info'])
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

        @self.socketio.on('add_wms_layer', namespace='/esdl')
        def _add_wms_layer(params):
            logger.info(params)
            layer_id = params['id']
            parent_group_id = params['parent_group_id']

            layer = {
                "description": params['description'],
                "url": params['url'],
                "layer_name": params['name'],
                "setting_type": params['setting_type'],
                "project_name": params['project_name'],
                "legend_url": params['legend_url'],
                "layer_ref": None,
                "visible": False
            }

            self.add_wms_layer(layer_id, layer, parent_group_id)
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

    def add_wms_layer_group(self, layer_group_id: str, layer_group: dict, parent_group_id: str = None,
                            position: str = None):
        setting_type = SettingType(layer_group['setting_type'])
        identifier = self._get_identifier(setting_type, layer_group['project_name'])

        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_GROUP_SETTING):
            layer_groups = self.settings_storage.get(setting_type, identifier, LAYERS_GROUP_SETTING)
        else:
            layer_groups = dict()

        layer_groups[layer_group_id] = layer_group
        self.settings_storage.set(setting_type, identifier, LAYERS_GROUP_SETTING, layer_groups)
        if parent_group_id:
            self.add_child_to_layer_group(parent_group_id, layer_group_id, position)

    def get_wms_layer_group(self, group_id: str):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        group = self.get_layers()[LAYERS_GROUP_SETTING][group_id]
        return group

    def add_child_to_layer_group(self, group_id: str, child_id: str, position: int = None):
        group = self.get_wms_layer_group(group_id)
        if isinstance(position, int):
            group["child_ids"].insert(position, child_id)
        else:
            group["child_ids"].append(child_id)
        self.add_wms_layer_group(group_id, group)

    def remove_child_from_layer_group(self, group_id: str, child_id: str):
        group = self.get_wms_layer_group(group_id)
        if child_id in group['child_ids']:
            group['child_ids'].remove(child_id)
        self.add_wms_layer_group(group_id, group)

    def update_item_setting_type_project(self, item_id: str, parent_id: str):
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
            items = self.settings_storage.get(parent_setting_type, parent_identifier, item_setting)
            item['setting_type'] = parent_group['setting_type']
            item['project_name'] = parent_group['project_name']
            items[item_id] = item
            self.settings_storage.set(parent_setting_type, parent_identifier, item_setting, items)

        if 'child_ids' in item and item['child_ids']:
            for child_id in item['child_ids']:
                self.update_item_setting_type_project(child_id, item_id)

    def move_wms_item(self, item_id: str, old_parent_id: str, new_parent_id: str, position: id):
        self.remove_child_from_layer_group(old_parent_id, item_id)
        self.add_child_to_layer_group(new_parent_id, item_id, position)
        self.update_item_setting_type_project(item_id, new_parent_id)

    def copy_wms_item_and_children(self, item_id: str, new_parent_id: str, position: id):
        all_layers = self.get_layers()
        new_item_id = str(uuid4())
        new_parent_group = all_layers[LAYERS_GROUP_SETTING][new_parent_id]
        if item_id in all_layers[LAYERS_SETTING]:
            layer = all_layers[LAYERS_SETTING][item_id]
            new_layer = {
                "description": layer['description'],
                "url": layer['url'],
                "layer_name": layer['layer_name'],
                "setting_type": new_parent_group['setting_type'],
                "project_name": new_parent_group['project_name'],
                "legend_url": layer['legend_url'],
                "layer_ref": None,
                "visible": False
            }
            self.add_wms_layer(new_item_id, new_layer, new_parent_id, position)
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
        group = self.get_wms_layer_group(group_id)
        group["description"] = group_name
        self.add_wms_layer_group(group_id, group)

    def add_wms_layer(self, layer_id: str, layer: dict, parent_group_id: str = None, position: str = None):
        setting_type = SettingType(layer['setting_type'])
        project_name = layer['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        layer['visible'] = False  # make sure we don't save the visibility
        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
        else:
            layers = dict()
        layers[layer_id] = layer
        self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)

        if parent_group_id:
            self.add_child_to_layer_group(parent_group_id, layer_id, position)

    def get_wms_layer(self, layer_id: str):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        layer = self.get_layers()[LAYERS_SETTING][layer_id]
        return layer

    def save_wms_layer(self, layer_id: str, lyr_info: dict):
        layer = self.get_wms_layer(layer_id)

        layer["description"] = lyr_info["description"]
        layer["url"] = lyr_info["url"]
        layer["layer_name"] = lyr_info["layer_name"]
        layer["legend_url"] = lyr_info["legend_url"]
        layer["attribution"] = lyr_info["attribution"]

        self.add_wms_layer(layer_id, layer)

    def remove_wms_layer(self, layer_id: str, parent_id: str):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        if layer_id not in self.get_layers()[LAYERS_SETTING]:
            return False
        layer = self.get_layers()[LAYERS_SETTING][layer_id]
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
        # gets the default list and adds the user layers
        all_layers = dict()
        if self.settings_storage.has_system(LAYERS_SETTING):
            all_layers.update(self.settings_storage.get_system(LAYERS_SETTING))

        user = get_session('user-email')
        user_group = get_session('user-group')
        mapeditor_role = get_session('user-mapeditor-role')
        if user is not None and self.settings_storage.has_user(user, LAYERS_SETTING):
            # add user layers if available
            all_layers.update(self.settings_storage.get_user(user, LAYERS_SETTING))

        # TODO this should be done in __init__ but then 'user = get_session('user-email')' does not work yet
        if user is not None and not self.settings_storage.has_user(user, LAYERS_GROUP_SETTING):
            # add user default user group_layers if not present
            self.settings_storage.set_user(user, LAYERS_GROUP_SETTING, default_user_wms_layer_groups)

        all_layer_groups = dict()
        if user is not None:
            all_layer_groups.update(self.settings_storage.get_system(LAYERS_GROUP_SETTING))
            all_layer_groups.update(self.settings_storage.get_user(user, LAYERS_GROUP_SETTING))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, LAYERS_SETTING):
                    # add project layers if available
                    all_layers.update(self.settings_storage.get_project(identifier, LAYERS_SETTING))
                if not self.settings_storage.has_project(identifier, LAYERS_GROUP_SETTING):
                    # add root project group if not present
                    default_project_group = dict()
                    default_project_group[identifier] = {
                        "setting_type": SettingType.PROJECT.value,
                        "project_name": identifier,
                        "description": "Project Layers for " + group,
                        "parent_group_id": "root",
                        "child_ids": []}
                    self.settings_storage.set_project(identifier, LAYERS_GROUP_SETTING, default_project_group)
                # add project group layers
                all_layer_groups.update(self.settings_storage.get_project(identifier, LAYERS_GROUP_SETTING))

        # generate message
        message = {
            LAYERS_SETTING: all_layers,
            LAYERS_GROUP_SETTING: all_layer_groups
        }
        # message = copy.deepcopy(default_wms_layer_groups)
        # possible_groups = message["layer_groups"]
        # if enough rights, mark Standard layers and layer groups editable
        for layer in message[LAYERS_SETTING].values():
            if 'mapeditor-admin' in mapeditor_role:
                layer['readonly'] = False
            else:
                layer['readonly'] = layer['setting_type'] == SettingType.SYSTEM.value
        for layer_group in message[LAYERS_GROUP_SETTING].values():
            if 'mapeditor-admin' in mapeditor_role:
                layer_group['readonly'] = False
            else:
                layer_group['readonly'] = layer_group['setting_type'] == SettingType.SYSTEM.value
        # possible_groups.extend(self._create_group_layers_for_projects(user_group))
        # logger.debug(message)
        return message


default_system_wms_layer_groups = {
    "standard_layers": {
        "setting_type": SettingType.SYSTEM.value,
        "project_name": SettingType.SYSTEM.value,
        "description": "Standard Layers",
        "parent_group_id": "root",
        "child_ids": [
            "AHN2_5m", "RVO_Restwarmte", "LianderHS", "LianderMS", "LT_WarmteBronnen_ECW", "WarmteNetten",
            "GasLeidingenEnexis", "GasLeidingenStedin", "CO2EmissieBedrijven", "AardwarmteKrijtJura",
            "AardwarmteRotliegend", "CondensWarmte", "DataCentraWarmte", "PICO_Hoogspanningsnet_2018", "TEO"
        ]},
}

default_user_wms_layer_groups = {
    "personal_layers": {
        "setting_type": SettingType.USER.value,
        "project_name": SettingType.USER.value,
        "description": "Personal Layers",
        "parent_group_id": "root",
        "child_ids": []},
}

default_wms_layers = {
    "AHN2_5m": {
        "description": "AHN2 5 meter",
        "url": "http://geodata.nationaalgeoregister.nl/ahn2/wms?",
        "layer_name": "ahn2_5m",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": ''
    },
    "RVO_Restwarmte": {
        "description": "Restwarmte (RVO: ligging industrie)",
        "url": "https://geodata.nationaalgeoregister.nl/restwarmte/wms?",
        "layer_name": "liggingindustrieco2",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": ''
    },
    "LianderHS": {
        "description": "Liander hoogspanningskabels",
        "url": "https://geodata.nationaalgeoregister.nl/liander/elektriciteitsnetten/v1/wms?",
        "layer_name": "hoogspanningskabels",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": ''
    },
    "LianderMS": {
        "description": "Liander middenspanningskabels",
        "url": "https://geodata.nationaalgeoregister.nl/liander/elektriciteitsnetten/v1/wms?",
        "layer_name": "middenspanningskabels",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": ''
    },
    "LT_WarmteBronnen_ECW": {
        "description": "LT_WarmteBronnen_ECW",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "LT_WarmteBronnen_ECW",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "WarmteNetten": {
        "description": "WarmteNetten",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "WarmteNetten",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "GasLeidingenEnexis": {
        "description": "GasLeidingenEnexis",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "GasLeidingenEnexis",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "GasLeidingenStedin": {
        "description": "GasLeidingenStedin",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "GasLeidingenStedin",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "CO2EmissieBedrijven": {
        "description": "CO2EmissieBedrijven",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "CO2EmissieBedrijven",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "AardwarmteKrijtJura": {
        "description": "AardwarmteKrijtJura",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "AardwarmteKrijtJura",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    # "AardwarmteTriasMap": {
    #     "description": "AardwarmteTriasMap",
    #     "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "AardwarmteTriasMap",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # },
    "AardwarmteRotliegend": {
        "description": "AardwarmteRotliegend",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "AardwarmteRotliegend",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "CondensWarmte": {
        "description": "Potentieel Restwarmte uit koelinstallaties voor MT warmtenetten",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "CondensWarmte",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    "DataCentraWarmte": {
        "description": "Potentieel Restwarmte uit DataCentra voor LT warmtenetten",
        "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "DataCentraWarmte",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    },
    # "gs_warm": {
    #     "description": "Potentieel warmte uit vertikale gesloten WKO (warmte koude opslag)",
    #     "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "gs_warm",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # },
    # "gs_koud": {
    #     "description": "Potentieel koude uit vertikale gesloten WKO (warmte koude opslag)",
    #     "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "gs_koud",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # }
    "PICO_Hoogspanningsnet_2018": {
        "description": "PICO Hoogspanningsnet 2018",
        "url": "https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=120&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs",
        "layer_name": "Hoogspanningsnet_2018",
        "setting_type": SettingType.PROJECT.value,
        "project_name": "MCS",
        "legend_url": "https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=96&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs&request=GetLegendGraphic&service=WMS&itemFONTSIZE=7&format=png&layertitle=false&layer=Hoogspanningsnet_2018",
        "layer_ref": None,
        "visible": False,
        "attribution": 'PICO'
    },
    "TEO": {
        "description": "Thermische energie uit oppervlaktewater",
        "url": "https://stowa.geoapps.nl/proxy?auth=null&path=https://geosrv02a.geoapps.nl/geoserver/b8e2d7c2645c48359cc2994f45f10940/wms?",
        "layer_name": "a3643e0e53fa4174a4ead41f56659a6e",
        "setting_type": SettingType.PROJECT.value,
        "project_name": "MCS",
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Stowa'
    }
}

# zie https://stowa.geoapps.nl/Overzichtskaart voor meer TEO/TEA kaartlagen
# TEA - economische potentie - direct - RWZI: https://stowa.geoapps.nl/proxy?auth=null&path=https://geosrv02c.geoapps.nl/geoserver/b8e2d7c2645c48359cc2994f45f10940/wms?
# LAYERS=2bd449fcb6e74f81af1ccdba770c1b0a
# TEA - economische potentie - direct - Leidingen: https://stowa.geoapps.nl/proxy?auth=null&path=https://geosrv02c.geoapps.nl/geoserver/b8e2d7c2645c48359cc2994f45f10940/wms?
# LAYERS=d21caa0e2cfb4d638aa74b23f5b2b34f
# TEA - economische potentie - direct - Gemalen: https://stowa.geoapps.nl/proxy?auth=null&path=https://geosrv02e.geoapps.nl/geoserver/b8e2d7c2645c48359cc2994f45f10940/wms?
# LAYERS=88c739dc2cac4ab2a0740af5b5513965


"""
PICO Hoogspanningsnet 2018
https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=120&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs
Hoogspanningsnet_2018
https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=96&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs&request=GetLegendGraphic&service=WMS&itemFONTSIZE=7&format=png&layertitle=false&layer=Hoogspanningsnet_2018
"""
