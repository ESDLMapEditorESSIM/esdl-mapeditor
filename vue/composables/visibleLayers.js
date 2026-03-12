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
import {constructWfsLayerUrl, useWmsLayers, updateGlobalServiceLayerList} from "./wmsLayers";

const {getWmsLayerList} = useWmsLayers();
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
 * 
 * @param {object} event Mouse click event
 */
const queryWmsLayersFeaturesOnClick = (event) => {
    const visibleLayers = useVisibleLayers().getVisibleLayerList();
    // Filter only for WMS layers
    const visibleWmsLayers = visibleLayers.filter(l => l.type === undefined || l.type === 'WMS');
    const currnetZoomLevel = map.getZoom();

    if (visibleWmsLayers.length) {
        const layersRequestInfo = visibleWmsLayers
            // Only request layer feature if the layer is within the visible zoom level.
            .filter((layer) =>
                layer.min_zoom_level === undefined ||
                currnetZoomLevel >= layer.min_zoom_level
            )
            .map((layer) => {
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

/**
 * The function can be used as an callback fn to update WFS layer features 
 * when 'moveend' event is triggered. 
 */
const updateWfsLayersOnBboxChange = async () => {
  const visibleLayers = useVisibleLayers().getVisibleLayerList();
  const bbox = map.getBounds().toBBoxString();
  const currnetZoomLevel = map.getZoom();

  // Filter only for WFS layers
  const wfsLayers = visibleLayers.filter(l => l.type !== undefined && l.type === 'WFS');

  for (const layer of wfsLayers) {
    // Only run layer feature update if the layer is within the visible zoom level.
    if (layer.min_zoom_level === undefined || currnetZoomLevel >= layer.min_zoom_level) {
        updateSingleWfsLayer(layer, bbox);
    } else {
        console.debug(`Pause WFS layer ${layer.layer_name} feature update.`);
    }
  }
};

// Update the WFS layer features based on the bounding box extent.
const updateSingleWfsLayer = async (layer, bbox) => {
  const url = constructWfsLayerUrl(layer.url, layer.layer_name, bbox);
  try {
    window.show_loader();

    const response = await fetch(url);
    const data = await response.json();

    // Clear the old data from the existing layer reference
    if (layer.layer_ref) {
      layer.layer_ref.clearLayers();
      layer.layer_ref.addData(data);
    }
  } catch (e) {
    console.error(`Failed to update BBOX for ${layer.layer_name}`, e);
  } finally {
    window.hide_loader();
  }
};

// Show or hide layer based on layer zoom level (if specified)
const updateZoomDependentLayers = () => {
  const visibleLayers = useVisibleLayers().getVisibleLayerList();
  const currnetZoomLevel = map.getZoom();

  visibleLayers.forEach(layer => {
    if (!layer.min_zoom_level) return;

    const shouldBeVisible = currnetZoomLevel >= layer.min_zoom_level;
    const isVisible = map.hasLayer(layer.layer_ref);

    if (shouldBeVisible && !isVisible) {
      layer.layer_ref.addTo(map);
    } else if (!shouldBeVisible && isVisible) {
      map.removeLayer(layer.layer_ref);
    }
  });
};

map.on("click", queryWmsLayersFeaturesOnClick);

map.on('moveend', function () {
    updateZoomDependentLayers();
    updateWfsLayersOnBboxChange();
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

    /**
     * Returns the visible layer object from a given layer Id
     * 
     * @param {string} id Layer Id
     * @returns {Object|undefined} The targeted visible layer object; If not found, undefined is returned
     */
    const getVisibleLayerById = (id) => {
        const targetedLayer = globalVisibleLayerList.value.find(layer => layer.id === id);
        return targetedLayer;
    };

    /**
     * Adjusts the opacity of the visible layer.
     * 
     * @param {string} id Layer Id
     * @param {number} opacity The desired layer opacity value between 0 and 1
     */
    const adjustVisibleLayerOpacity = (id, opacity) => {
        const targetLayer = getVisibleLayerById(id);
        const type = targetLayer.type ? targetLayer.type : "WMS";
        if (targetLayer && 0 <= opacity <= 1) {
            if (type === "WMS") {
                targetLayer.layer_ref.setOpacity(opacity);
            } else if (type === "WFS") {
                targetLayer.layer_ref.setStyle({
                    opacity: opacity,
                    fillOpacity: opacity * 0.3
                });
                // Update the stored style
                targetLayer.style.opacity = opacity;
            } else {
                console.error(`Unsupported type ${type}`);
            }
        }
    };

    /**
     * Saves the layer opacity setting to the settings_storage.
     * 
     * @param {string} id Layer Id
     */
    const saveVisibleLayerOpacitySetting = (id) => {
        const targetLayer = getVisibleLayerById(id);
        const type = targetLayer.type ? targetLayer.type : "WMS";
        if (targetLayer) {
            let opacity;
            if (type === "WMS") {
                opacity = targetLayer.layer_ref.options.opacity;
            } else if (type === "WFS") {
                opacity = targetLayer.style?.opacity !== undefined ? targetLayer.style.opacity : 1.0;
            }

            if (id && opacity) {
                const params = {layer_id: id, opacity: opacity};
                // After the "save_layer_opacity_setting" event, 
                // calling updateGlobalServiceLayerList to ensure the latest layers settings are reflected in the app.
                socket.emit("save_layer_opacity_setting", params, updateGlobalServiceLayerList);
            }
            else {
                console.error(`Error whiling saving layer opacity setting to the settings_storage with id: ${id}, opacity: ${opacity}`);
            }
        }
    };

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateDisplayOrderVisibleLayers,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers,
        getVisibleLayerById,
        adjustVisibleLayerOpacity,
        saveVisibleLayerOpacitySetting
    };
}
