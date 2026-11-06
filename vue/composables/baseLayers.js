/*
 * This work is based on original code developed and copyrighted by TNO 2020.
 * Subsequent contributions are licensed to you by the developers of such code and are
 * made available to the Project under one or several contributor license agreements.
 *
 * This work is licensed to you under the Apache License, Version 2.0.
 * You may obtain a copy of the license at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Contributors:
 *     TNO         - Initial implementation
 * Manager:
 *     TNO
 */

const L = window.L;
const map = window.map;

const baseLayerDefinitions = [
    {
        label: 'OpenStreetMap',
        layer: window.osm,
        // Enable when layer control is phased out.
        // layer: L.tileLayer(location.protocol + '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        //     maxZoom: 25,
        //     maxNativeZoom: 19,
        //     attribution: '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        // }),
        enabled: true,
    },
    {
        label: 'OpenTopoMap',
        layer: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)'
        }),
        enabled: false,
    },
    {
        label: 'BRT Standaard',
        layer: L.tileLayer('https://service.pdok.nl/kadaster/brt-achtergrondkaart/wmts/v2_0/standaard/EPSG:3857/{z}/{x}/{y}.png', {
            maxZoom: 25,
            maxNativeZoom: 19,
            attribution: '&copy; <a href="https://www.kadaster.nl/">Kadaster</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
        }),
        enabled: false,
    },
    {
        label: 'BRT Grijs',
        layer: L.tileLayer('https://service.pdok.nl/kadaster/brt-achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png', {
            maxZoom: 25,
            maxNativeZoom: 19,
            attribution: '&copy; <a href="https://www.kadaster.nl/">Kadaster</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
        }),
        enabled: false,
    },
    {
        label: 'BRT Pastel',
        layer: L.tileLayer('https://service.pdok.nl/kadaster/brt-achtergrondkaart/wmts/v2_0/pastel/EPSG:3857/{z}/{x}/{y}.png', {
            maxZoom: 25,
            maxNativeZoom: 19,
            attribution: '&copy; <a href="https://www.kadaster.nl/">Kadaster</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
        }),
        enabled: false,
    },
    {
        label: 'TOP raster',
        layer: L.tileLayer.wms('https://service.pdok.nl/kadaster/brt-topraster/wms/v1_0', {
            layers: 'top1000raster,top500raster,top250raster,top100raster,top50raster,top25raster',
            format: 'image/png',
            minZoom: 8,
            maxZoom: 25,
            maxNativeZoom: 16,
            bounds: [[50.2129, 2.52713], [55.7212, 7.37403]],
            noWrap: true,
            attribution: '&copy; <a href="https://www.kadaster.nl/">Kadaster, Basisregistratie Topografie (BRT)</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
        }),
        enabled: false,
    },
    {
        label: 'PDOK Luchtfoto',
        layer: L.tileLayer('https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/Actueel_orthoHR/EPSG:3857/{z}/{x}/{y}.jpeg', {
            maxZoom: 25,
            maxNativeZoom: 21,
            attribution: '&copy; <a href="https://www.beeldmateriaal.nl/">Beeldmateriaal Nederland</a> | <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>'
        }),
        enabled: false,
    },
    {
        label: 'Google Streets',
        layer: L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            attribution: 'Google'
        }),
        enabled: false,
    },
    {
        label: 'Google Satellite',
        layer: L.tileLayer('https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            attribution: 'Google'
        }),
        enabled: false,
    },
    {
        label: 'No map',
        layer: L.imageOverlay('', [[50.803721015, 3.31497114423], [53.5104033474, 7.09205325687]]),
        enabled: false,
    }
];

// Enable when layer_control.js is phased out.
// addBaseLayerToMap(baseLayerDefinitions[0]);

export function useBaseLayers() {
    /**
     * Return base layer definition by label.
     * @param label
     * @returns {{label: string, layer}|{label: string, layer}|{label: string, layer}|{label: string, layer: *}|null}
     */
    function getBaseLayerByLabel(label) {
        for (const baseLayer of baseLayerDefinitions) {
            if (baseLayer.label === label) {
                return baseLayer;
            }
        }
        return null;
    }

    function showBaseLayer(baseLayer) {
        if (!map.hasLayer(baseLayer.layer)) {
            map.addLayer(baseLayer.layer);
            baseLayer.enabled = true;
        }
    }

    function hideBaseLayer(baseLayer) {
        if (map.hasLayer(baseLayer.layer)) {
            map.removeLayer(baseLayer.layer);
            baseLayer.enabled = false;
        }
    }

    return {
        getBaseLayerByLabel,
        showBaseLayer,
        hideBaseLayer,
        baseLayerDefinitions,
    }
}
