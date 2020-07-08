from extensions.settings_storage import SettingType, SettingsStorage
from extensions.session_manager import get_session
import copy

LAYERS_SETTING = 'layers'

class WMSLayers:
    def __init__(self, settings_storage: SettingsStorage):
        self.settings_storage = settings_storage
        # add initial layers when not in the system settings
        if not self.settings_storage.has_system(LAYERS_SETTING):
            self.settings_storage.set_system(LAYERS_SETTING, default_wms_layers)
        else:
            print('No need to update default list, already in User Settings')

    def add_wms_layer(self, layer_id, layer):
        setting_type = SettingType(layer['setting_type'])
        project_name = layer['project_name']
        identifier = self._get_identifier(setting_type, project_name)
        if identifier is not None and self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
        else:
            layers = dict()
        layers[layer_id] = layer
        self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)

    def remove_wms_layer(self, layer_id):
        # as we only have an ID, we don't know if it is a user, project or system layer
        # get the whole list, so we can find out the setting_type
        layer = self.get_layers()[LAYERS_SETTING][layer_id]
        setting_type = SettingType(layer['setting_type'])
        identifier = self._get_identifier(setting_type, layer['project_name'])
        if identifier is None:
            return
        if self.settings_storage.has(setting_type, identifier, LAYERS_SETTING):
            # update layer dict
            layers = self.settings_storage.get(setting_type, identifier, LAYERS_SETTING)
            print('Deleting layer {}'.format(layers[layer_id]))
            del(layers[layer_id])
            self.settings_storage.set(setting_type, identifier, LAYERS_SETTING, layers)

    def _get_identifier(self, setting_type: SettingType, project_name=None):
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
        role = get_session('user-role')
        mapeditor_role = get_session('user-mapeditor-role')
        print('User: ', user)
        print('Groups: ', user_group)
        print('Roles: ', role)
        print('Mapeditor roles: ', mapeditor_role)
        if user is not None and self.settings_storage.has_user(user, LAYERS_SETTING):
            # add user layers if available
            all_layers.update(self.settings_storage.get_user(user, LAYERS_SETTING))

        if user_group is not None:
            for group in user_group:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                if self.settings_storage.has_project(identifier, LAYERS_SETTING):
                    # add project layers if available
                    all_layers.update(self.settings_storage.get_project(identifier, LAYERS_SETTING))

        # generate message
        message = copy.deepcopy(default_wms_layer_groups)
        possible_groups = message["groups"]
        # if enough rights, mark Standard layers editable
        if 'mapeditor-admin' in mapeditor_role:
            for g in possible_groups:
                if g['setting_type'] == SettingType.SYSTEM.value:
                    g['readonly'] = False
        possible_groups.extend(self._create_group_layers_for_projects(user_group))
        message[LAYERS_SETTING] = all_layers
        print(message)
        return message

    def _create_group_layers_for_projects(self, groups):
        project_list = list()
        if groups is not None:
            for group in groups:
                identifier = self._get_identifier(SettingType.PROJECT, group)
                json = {"setting_type": SettingType.PROJECT.value, "project_name": identifier, "name": "Project Layers for " + group, "readonly": False}
                project_list.append(json)
        return project_list


default_wms_layer_groups = {
    "groups": [
        {"setting_type": SettingType.USER.value, "project_name": SettingType.USER.value, "name": "Personal Layers", "readonly": False},
        {"setting_type": SettingType.SYSTEM.value, "project_name": SettingType.SYSTEM.value, "name": "Standard Layers", "readonly": True}
    ]
}

#{"id": SettingType.PROJECT.value, "name": "Project Layers"},

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
    "PICO Hoogspanningsnet 2018": {
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