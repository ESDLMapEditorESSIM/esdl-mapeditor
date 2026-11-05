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

from typing import Any, Dict

from extensions.settings_storage import SettingType

removed_wms_layer_ids = {"LianderHS", "LianderMS", "PICO_Hoogspanningsnet_2018", "TEO"}
default_wms_layers: Dict[str, Dict[str, Any]] = {
    "AHN2_5m": {
        "description": "AHN Maaiveld (DTM)",
        "url": "https://service.pdok.nl/rws/ahn/wms/v1_0?",
        "layer_name": "dtm_05m",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": '<a href="https://www.ahn.nl/">AHN</a> | <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>',
        "tile_options": {"maxZoom": 25},
    },
    "AHN_DSM": {
        "description": "AHN Oppervlak (DSM)",
        "url": "https://service.pdok.nl/rws/ahn/wms/v1_0?",
        "layer_name": "dsm_05m",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": '<a href="https://www.ahn.nl/">AHN</a> | <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0</a>',
        "tile_options": {"maxZoom": 25},
    },
    **{
        layer_id: {
            "type": "WMTS",
            "description": description,
            "url": f"https://service.pdok.nl/hwh/{service}/wmts/v1_0/{layer_name}/EPSG:3857/{{z}}/{{x}}/{{y}}.jpeg",
            "layer_name": layer_name,
            "setting_type": SettingType.SYSTEM.value,
            "layer_ref": None,
            "visible": False,
            "attribution": '&copy; <a href="https://www.beeldmateriaal.nl/">Beeldmateriaal Nederland</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>',
            "tile_options": {"maxZoom": 25, "maxNativeZoom": 21},
        }
        for layer_id, description, service, layer_name in [
            ("PDOK_Luchtfoto_Zomer", "PDOK Luchtfoto zomer (25cm)", "luchtfotorgb", "Actueel_ortho25"),
            ("PDOK_Infrarood", "PDOK Infrarood (8cm)", "luchtfotocir", "Actueel_orthoHRIR"),
            ("PDOK_Infrarood_Zomer", "PDOK Infrarood zomer (25cm)", "luchtfotocir", "Actueel_ortho25IR"),
        ]
    },
    **{
        f"PDOK_Luchtfoto_{year}": {
            "type": "WMTS",
            "description": f"PDOK Luchtfoto {year}",
            "url": f"https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/{layer_name}/EPSG:3857/{{z}}/{{x}}/{{y}}.jpeg",
            "layer_name": layer_name,
            "setting_type": SettingType.SYSTEM.value,
            "layer_ref": None,
            "visible": False,
            "attribution": '&copy; <a href="https://www.beeldmateriaal.nl/">Beeldmateriaal Nederland</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>',
            "tile_options": {"maxZoom": 25, "maxNativeZoom": 21},
        }
        for year, layer_name in [
            (2025, "2025_orthoHR"),
            (2024, "2024_orthoHR"),
            (2023, "2023_orthoHR"),
            (2022, "2022_orthoHR"),
            (2021, "2021_orthoHR"),
            (2020, "2020_ortho25"),
            (2019, "2019_ortho25"),
            (2018, "2018_ortho25"),
            (2017, "2017_ortho25"),
            (2016, "2016_ortho25"),
        ]
    },
    "NASA_Blue_Marble": {
        "description": "NASA Blue Marble",
        "url": "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?",
        "layer_name": "BlueMarble_ShadedRelief",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": 'Imagery: <a href="https://www.earthdata.nasa.gov/centers/gibs-daac">NASA EOSDIS GIBS</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 8},
    },
    "NASA_Black_Marble": {
        "description": "NASA Black Marble (2016)",
        "url": "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?time=2016-01-01",
        "layer_name": "VIIRS_Black_Marble",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": 'Imagery: <a href="https://www.earthdata.nasa.gov/centers/gibs-daac">NASA EOSDIS GIBS</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 8},
    },
    "NASA_MODIS_Terra_TrueColor": {
        "description": "NASA MODIS Terra true colour (latest)",
        "url": "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?",
        "layer_name": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": 'Imagery: <a href="https://www.earthdata.nasa.gov/centers/gibs-daac">NASA EOSDIS GIBS</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 9},
    },
    "NASA_MODIS_Terra_SurfaceTemperature": {
        "description": "NASA MODIS Terra surface temperature (latest)",
        "url": "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?",
        "layer_name": "MODIS_Terra_Land_Surface_Temp_Day",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": 'Imagery: <a href="https://www.earthdata.nasa.gov/centers/gibs-daac">NASA EOSDIS GIBS</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 7},
    },
    "ESA_WorldCover_2021": {
        "type": "WMTS",
        "description": "ESA WorldCover land cover (2021)",
        "url": "https://wmts.terrascope.be/?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&LAYER=esa-worldcover-map-10m-2021-v2_map&STYLE=default&FORMAT=image/png&TIME=2021-01-01&TILEMATRIXSET=EPSG:3857&TILEMATRIX={z}&TILECOL={x}&TILEROW={y}",
        "layer_name": "esa-worldcover-map-10m-2021-v2_map",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "min_zoom_level": 6,
        "attribution": '&copy; <a href="https://esa-worldcover.org/en/data-access">ESA WorldCover project 2021</a> / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 14, "bounds": [[-60, -180], [83, 180]], "noWrap": True},
    },
    "ESA_Sentinel_RGB_2021": {
        "type": "WMTS",
        "description": "ESA Sentinel RGB composite (2021)",
        "url": "https://wmts.terrascope.be/?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&LAYER=esa-worldcover-s2rgbnir-10m-2021-v2_tcc&STYLE=default&FORMAT=image/png&TIME=2021-01-01&TILEMATRIXSET=EPSG:3857&TILEMATRIX={z}&TILECOL={x}&TILEROW={y}",
        "layer_name": "esa-worldcover-s2rgbnir-10m-2021-v2_tcc",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "min_zoom_level": 8,
        "attribution": '&copy; <a href="https://esa-worldcover.org/en/data-access">ESA WorldCover project 2021</a> / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 14, "bounds": [[-60, -180], [83, 180]], "noWrap": True},
    },
    "ESA_NDVI_2021": {
        "type": "WMTS",
        "description": "ESA NDVI composite (2021)",
        "url": "https://wmts.terrascope.be/?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&LAYER=esa-worldcover-ndvi-10m-2021-v2_ndvi&STYLE=default&FORMAT=image/png&TIME=2021-01-01&TILEMATRIXSET=EPSG:3857&TILEMATRIX={z}&TILECOL={x}&TILEROW={y}",
        "layer_name": "esa-worldcover-ndvi-10m-2021-v2_ndvi",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "min_zoom_level": 8,
        "attribution": '&copy; <a href="https://esa-worldcover.org/en/data-access">ESA WorldCover project 2021</a> / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>',
        "tile_options": {"maxZoom": 25, "maxNativeZoom": 14, "bounds": [[-60, -180], [83, 180]], "noWrap": True},
    },
    "CORINE_2018": {
        "description": "EU CORINE land cover (2018)",
        "url": "https://image.discomap.eea.europa.eu/arcgis/services/Corine/CLC2018_WM/MapServer/WMSServer?",
        "layer_name": "12",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": '<a href="https://land.copernicus.eu/en/products/corine-land-cover/clc2018">Copernicus Land Monitoring Service / European Environment Agency, CORINE Land Cover 2018</a>',
        "tile_options": {"maxZoom": 25},
    },
    "RVO_Restwarmte": {
        "description": "Restwarmte (RVO: ligging industrie)",
        "url": "https://service.pdok.nl/rvo/restwarmte/wms/v1_0?",
        "layer_name": "liggingindustrieco2",
        "setting_type": SettingType.SYSTEM.value,
        "layer_ref": None,
        "visible": False,
        "attribution": "",
    },
    "LT_WarmteBronnen_ECW": {
        "description": "LT_WarmteBronnen_ECW",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "LT_WarmteBronnen_ECW",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "WarmteNetten": {
        "description": "WarmteNetten",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "WarmteNetten",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "GasLeidingenEnexis": {
        "description": "GasLeidingenEnexis",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "GasLeidingenEnexis2020_v2",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "GasLeidingenStedin": {
        "description": "GasLeidingenStedin",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "GasLeidingenStedin",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "CO2EmissieBedrijven": {
        "description": "CO2EmissieBedrijven",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "CO2EmissieBedrijven",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "AardwarmteKrijtJura": {
        "description": "AardwarmteKrijtJura",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "AardwarmteKrijtJura",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    # "AardwarmteTriasMap": {
    #     "description": "AardwarmteTriasMap",
    #     "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "AardwarmteTriasMap",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # },
    "AardwarmteRotliegend": {
        "description": "AardwarmteRotliegend",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "AardwarmteRotliegend",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "CondensWarmte": {
        "description": "Potentieel Restwarmte uit koelinstallaties voor MT warmtenetten",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "CondensWarmte",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    "DataCentraWarmte": {
        "description": "Potentieel Restwarmte uit DataCentra voor LT warmtenetten",
        "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
        "layer_name": "DataCentraWarmte",
        "setting_type": SettingType.SYSTEM.value,
        "legend_url": "",
        "layer_ref": None,
        "visible": False,
        "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>',
    },
    # "gs_warm": {
    #     "description": "Potentieel warmte uit vertikale gesloten WKO (warmte koude opslag)",
    #     "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "gs_warm",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # },
    # "gs_koud": {
    #     "description": "Potentieel koude uit vertikale gesloten WKO (warmte koude opslag)",
    #     "url": "https://www.warmteatlas.nl/geoserver/WarmteAtlas/wms?",
    #     "layer_name": "gs_koud",
    #     "legend_url": "",
    #     "layer_ref": None,
    #     "visible": False,
    #     "attribution": 'Mapdata  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> &copy; <a href="http://www.warmteatlas.nl">WarmteAtlas RVO</a>'
    # }
}


default_wms_layer_groups: Dict[str, Dict[str, Any]] = {
    group_id: {
        "description": description,
        "setting_type": SettingType.SYSTEM.value,
        "project_name": SettingType.SYSTEM.value,
        "is_root": False,
        "opened": False,
        "child_ids": child_ids,
    }
    for group_id, description, child_ids in [
        ("system_ahn_group", "AHN", ["AHN2_5m", "AHN_DSM"]),
        (
            "system_pdok_aerial_group",
            "PDOK luchtfoto’s",
            ["PDOK_Infrarood", "PDOK_Infrarood_Zomer", "PDOK_Luchtfoto_Zomer", "system_pdok_history_group"],
        ),
        ("system_pdok_history_group", "Historisch", [f"PDOK_Luchtfoto_{year}" for year in range(2025, 2015, -1)]),
        (
            "system_nasa_group",
            "NASA",
            [
                "NASA_Blue_Marble",
                "NASA_Black_Marble",
                "NASA_MODIS_Terra_TrueColor",
                "NASA_MODIS_Terra_SurfaceTemperature",
            ],
        ),
        ("system_esa_group", "ESA", ["ESA_WorldCover_2021", "ESA_Sentinel_RGB_2021", "ESA_NDVI_2021"]),
        (
            "system_warmteatlas_group",
            "WarmteAtlas",
            [
                "LT_WarmteBronnen_ECW",
                "WarmteNetten",
                "GasLeidingenEnexis",
                "GasLeidingenStedin",
                "CO2EmissieBedrijven",
                "AardwarmteKrijtJura",
                "AardwarmteRotliegend",
                "CondensWarmte",
                "DataCentraWarmte",
            ],
        ),
    ]
}

grouped_layer_ids = {child_id for group in default_wms_layer_groups.values() for child_id in group["child_ids"]}
default_wms_layer_groups["standard_root_group"] = {
    "description": "Standard Layers",
    "setting_type": SettingType.SYSTEM.value,
    "project_name": SettingType.SYSTEM.value,
    "is_root": True,
    "child_ids": [
        "system_ahn_group",
        "system_pdok_aerial_group",
        "system_nasa_group",
        "system_esa_group",
        "system_warmteatlas_group",
    ]
    + [layer_id for layer_id in default_wms_layers if layer_id not in grouped_layer_ids],
}
