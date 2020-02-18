default_wms_layers = {
    "groups": [
        {"id": "std", "name": "Standard Layers"},
        {"id": "project", "name": "Project Layers"}
    ],
    "layers": {
        "AHN2_5m": {
            "description": "AHN2 5 meter",
            "url": "http://geodata.nationaalgeoregister.nl/ahn2/wms?",
            "layer_name": "ahn2_5m",
            "group_id": "std",
            "layer_ref": None,
            "visible": False,
            "attribution": ''
        },
        "RVO_Restwarmte": {
            "description": "Restwarmte (RVO: ligging industrie)",
            "url": "https://geodata.nationaalgeoregister.nl/restwarmte/wms?",
            "layer_name": "liggingindustrieco2",
            "group_id": "std",
            "layer_ref": None,
            "visible": False,
            "attribution": ''
        },
        "LianderHS": {
            "description": "Liander hoogspanningskabels",
            "url": "https://geodata.nationaalgeoregister.nl/liander/elektriciteitsnetten/v1/wms?",
            "layer_name": "hoogspanningskabels",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": ''
        },
        "LianderMS": {
            "description": "Liander middenspanningskabels",
            "url": "https://geodata.nationaalgeoregister.nl/liander/elektriciteitsnetten/v1/wms?",
            "layer_name": "middenspanningskabels",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": ''
        },
        "LT_WarmteBronnen_ECW": {
            "description": "LT_WarmteBronnen_ECW",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "LT_WarmteBronnen_ECW",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "WarmteNetten": {
            "description": "WarmteNetten",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "WarmteNetten",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "GasLeidingenEnexis": {
            "description": "GasLeidingenEnexis",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "GasLeidingenEnexis",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "GasLeidingenStedin": {
            "description": "GasLeidingenStedin",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "GasLeidingenStedin",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "CO2EmissieBedrijven": {
            "description": "CO2EmissieBedrijven",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "CO2EmissieBedrijven",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "AardwarmteKrijtJura": {
            "description": "AardwarmteKrijtJura",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "AardwarmteKrijtJura",
            "group_id": "std",
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
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "CondensWarmte": {
            "description": "Potentieel Restwarmte uit koelinstallaties voor MT warmtenetten",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "CondensWarmte",
            "group_id": "std",
            "legend_url": "",
            "layer_ref": None,
            "visible": False,
            "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
        },
        "DataCentraWarmte": {
            "description": "Potentieel Restwarmte uit DataCentra voor LT warmtenetten",
            "url": "https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?",
            "layer_name": "DataCentraWarmte",
            "group_id": "std",
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
            "group_id": "project",
            "legend_url": "https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=120&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs&request=GetLegendGraphic&service=WMS&itemFONTSIZE=8&format=png&layertitle=false&layer=Hoogspanningsnet_2018",
            "layer_ref": None,
            "visible": False,
            "attribution": 'PICO'
        }
    }
}

"""
PICO Hoogspanningsnet 2018
https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=120&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs
Hoogspanningsnet_2018
https://pico.geodan.nl/cgi-bin/qgis_mapserv.fcgi?DPI=120&map=/usr/lib/cgi-bin/projects/Hoogspanningsnet_2018.qgs&request=GetLegendGraphic&service=WMS&itemFONTSIZE=8&format=png&layertitle=false&layer=Hoogspanningsnet_2018
"""


class WMSLayers:

    def __init__(self):
        self.list = default_wms_layers

    def add_wms_layer(self, id, layer):
        self.list["layers"][id] = layer

    def remove_wms_layer(self, id):
        del(self.list["layers"][id])

    def get_layers(self):
        return self.list

