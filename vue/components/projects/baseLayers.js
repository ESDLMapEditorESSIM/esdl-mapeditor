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


export const baseLayerDefinitions = [
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
        label: 'Google Streets',
        layer: L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
            attribution: 'Google'
        }),
        enabled: false,
    },
    {
        label: 'Google Satellite',
        layer: L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
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

/**
 * Return base layer definition by label.
 * @param label
 * @returns {{label: string, layer}|{label: string, layer}|{label: string, layer}|{label: string, layer: *}|null}
 */
export function getBaseLayerByLabel(label) {
    for (const baseLayer of baseLayerDefinitions) {
        if (baseLayer.label === label) {
            return baseLayer;
        }
    }
    return null;
}

export function addBaseLayerToMap(baseLayer) {
    if (!map.hasLayer(baseLayer.layer)) {
        map.addLayer(baseLayer.layer);
        baseLayer.enabled = true;
    }
}

export function removeBaseLayerFromMap(baseLayer) {
    if (map.hasLayer(baseLayer.layer)) {
        map.removeLayer(baseLayer.layer);
        baseLayer.enabled = false;
    }
}
