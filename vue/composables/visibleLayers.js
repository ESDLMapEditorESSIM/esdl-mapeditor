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

/**
 * A composable for managing items currently visible.
 *
 */
import {ref, toValue} from "vue";
import {useWmsLayers} from "./wmsLayers";

const {getWmsLayerList} = useWmsLayers()
const globalVisibleLayerList = ref([]);

const map = window.map;
const layerTreeId = "layer_tree";
const $ = window.$;
const getLayerTree = () => $('#' + layerTreeId).jstree(true);

// Initialize the layer popup and specify popup options
const L = window.L;
const layersPopup = L.popup({
    autoPan: true,
    maxWidth: 400,
    maxHeight: 400
});

let socket = null;
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    socket.on("on_wms_layer_feature_resp", (resp) => {
        showWmsLayerFeaturePopup(resp);
    });
})();

/**
 * Constructs and returns a WMS layer GetFeatureInfo URL 
 * based on the mouse click event location (LatLng)
 * 
 * @param {string} wmsServiceUrl WMS service URL
 * @param {string} layerName Query layer name
 * @param {object} evLatLng Geographical LatLng property of the mouse click event
 * @returns {string} WMS GetFeatureInfo URL of the event location
 */
const constructWmsLayerGetFeatureInfoUrl = (wmsServiceUrl, layerName, evLatLng) => {
    const url = wmsServiceUrl + 
        "?service=WMS&version=1.1.1&request=GetFeatureInfo&layers=" + layerName +
        "&styles=&bbox=" + map.getBounds().toBBoxString() +
        "&height=" + map.getSize().y + "&width=" + map.getSize().x +
        "&query_layers=" + layerName +
        "&info_format=application/json&srs=EPSG:4326" +
        "&x=" + Math.round(map.latLngToContainerPoint(evLatLng).x) +
        "&y=" + Math.round(map.latLngToContainerPoint(evLatLng).y);
    return url;
};

/**
 * Based on the list of visible WMS layers and the mouse click event, 
 * constructs a query object and sends it to the backend to fetch layers features information.
 * 
 * To avoid possible CORS errors, the layer feature fetching is executed by the backend.
 * 
 * NOTE: This only works for the WMS layer at the moment. 
 * TODO: Extend this to other layer types when applicable.
 * 
 * @param {object} event Mouse click event
 */
const queryWmsLayersFeaturesOnClick = (event) => {
    const visibleLayers = useVisibleLayers().getVisibleLayerList();
    if (visibleLayers.length) {
        const layersRequestInfo = visibleLayers.map((layer) => {
            const serviceUrl = layer.url;
            const layerName = layer.layer_name;
            const getFeatureUrl = constructWmsLayerGetFeatureInfoUrl(serviceUrl, layerName, event.latlng);
            return {name: layerName, url: getFeatureUrl};
        });
        const requestBody = {
            ev_lat_lng: event.latlng,
            layers: layersRequestInfo
        };
        socket.emit("query_wms_layer_feature", requestBody);
    }
};

/**
 * Show the map popup of WMS layers features properties, 
 * when receiving the 'on_wms_layer_feature_resp' response object emitted from the backend.
 * 
 * @param {object} resp Response object with structure as {ev_lat_lng: event.latlng, layers_features_props: array[{name: str, feature_props: object|null }]}
 */
const showWmsLayerFeaturePopup = (resp) => {
    if (resp.layers_features_props.length) {
        const popupDivId = "layer-feature-popup-node";
        // Check if the popup already exists and removes it
        const existingPopupDiv = document.getElementById(popupDivId);
        if (existingPopupDiv) {
            existingPopupDiv.remove();
        }
        const popupDiv = document.createElement("div");
        popupDiv.setAttribute("id", popupDivId);
        popupDiv.classList.add("layer-feature-props-popup");

        // Updating the popup content
        resp.layers_features_props.forEach((l) => {
            const layerName = l.name;
            const layerFeatureProps = l.feature_props;

            // Layer name node
            const layerNameNode = document.createElement("h4");
            layerNameNode.innerHTML = `${layerName}`;
            popupDiv.appendChild(layerNameNode);

            if (layerFeatureProps !== null) {
                if (Object.keys(layerFeatureProps).length) {
                    // Layer feature properties node
                    Object.keys(layerFeatureProps).forEach((pName) => {
                        const propNameNode = document.createElement("p");
                        const propValueNode = document.createElement("span");
                        propNameNode.innerHTML = `${pName}: `;
                        propValueNode.innerHTML = `${layerFeatureProps[pName]}`;
                        popupDiv.appendChild(propNameNode).appendChild(propValueNode);
                    });
                } else {
                    // If the event location has no feature, remove the layerNameNode from the popup
                    popupDiv.removeChild(layerNameNode);
                }
            } else {
                console.warn(`${layerName} has null props. An error occurred while fetching ${layerName} layer feature properties.`);
                const propErrorNode = document.createElement("p");
                propErrorNode.innerHTML = `An error occurred while fetching ${layerName} layer feature properties`;
                popupDiv.appendChild(propErrorNode);
            }
        });
        
        if (popupDiv.hasChildNodes()) {
            // Set the popup content and open it
            layersPopup.setLatLng(resp.ev_lat_lng).setContent(popupDiv);
            map.openPopup(layersPopup);
        }
    }
};

map.on("click", queryWmsLayersFeaturesOnClick);

map.on('moveend', function () {
    for (const visibleLayer of globalVisibleLayerList.value) {
        const wms_layer = getWmsLayerList()['layers'][visibleLayer.id];
        if (wms_layer.min_zoom_level) {
            if (map.getZoom() >= wms_layer.min_zoom_level) {
                if (!map.hasLayer(wms_layer.layer_ref)) {
                    wms_layer.layer_ref.addTo(map);
                }
            } else {
                if (map.hasLayer(wms_layer.layer_ref)) {
                    map.removeLayer(wms_layer.layer_ref);
                }
            }
        }
    }
})

export function useVisibleLayers() {
    /**
     * Get list of visible layers. This is a list of dictionaries with 'text' and 'type' entries.
     */
    const getVisibleLayerList = () => toValue(globalVisibleLayerList);

    /**
     * Remove visible layer by ID.
     */
    const removeFromVisibleLayerList = (id) => {
        const layerToRemove = globalVisibleLayerList.value.find(
            layer => layer.id === id
        );
        if (layerToRemove !== undefined) {
            globalVisibleLayerList.value.splice(globalVisibleLayerList.value.indexOf(layerToRemove), 1);
        }
        return layerToRemove;
    };

    /**
     * Add visible layer to the list
     */
    const addToVisibleLayerList = (layer, index) => {
        globalVisibleLayerList.value.splice(index, 0, layer);
    };

    /**
     * Update the display order of the visible layers
     */
    const updateDisplayOrderVisibleLayers = (id, newPosition) => {
        const movedlayer = removeFromVisibleLayerList(id);
        addToVisibleLayerList(movedlayer, newPosition);

        globalVisibleLayerList.value.slice().reverse().forEach(
            layer => getWmsLayerList()['layers'][layer.id].layer_ref.bringToFront()
        )
    };

    const layerIsVisible = (layerId) => {
        for (const visibleLayer of globalVisibleLayerList.value) {
            if (visibleLayer.id === layerId) {
                return true;
            }
        }
        return false;
    };

    const hideVisibleLayer = (layerId) => {
        // hide via tree action to also update parent folders three-state
        getLayerTree().uncheck_node(layerId);
    };

    const hideAllVisibleLayers = () => {
         globalVisibleLayerList.value.slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id)
        )
    };

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateDisplayOrderVisibleLayers,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers
    };
}
