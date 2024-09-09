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
import {useWmsLayers, updateGlobalWmsLayerList} from "./wmsLayers";
import {useEsdlLayers} from "./esdlLayers";
import {useSocketIO} from "./socketio";
const {subscribe} = useSocketIO();

const {getWmsLayerList} = useWmsLayers();
const {enabledEsdlIdList, hideEsdlLayerFromMap, showEsdlLayerOnMap} = useEsdlLayers();


// List of visible layers. Contains wms layers as well as energy systems.
const visibleLayerList = ref([]);

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

export const VisibleLayerType = Object.freeze({
  WMS: 'WMS',
  ESDL: 'ESDL',
  UNKNOWN: 'Unknown'
});

subscribe("on_wms_layer_feature_resp", (resp) => {
    showWmsLayerFeaturePopup(resp);
});

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

// When the map is moved, check if the WMS layer should be visible. This handler is outside the composable, because it
// needs to be registered only once, and it meant to manage global behavior that should be consistent across the entire
// application.
map.on('moveend', function () {
    for (const visibleLayer of visibleLayerList.value) {
        const wms_layer = getWmsLayerList()['layers'][visibleLayer.id];
        if (wms_layer && wms_layer.min_zoom_level) {
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


export function useVisibleLayers(map, socket) {
    const {getWmsLayerList} = useWmsLayers();

    /**
     * Get list of visible layers. This is a list of objects, that are either wms layers or energy systems.
     */
    const getVisibleLayerList = () => toValue(visibleLayerList);

    /**
     * Remove visible layer by ID.
     */
    const removeFromVisibleLayerList = (id) => {
        const layerToRemove = visibleLayerList.value.find(
            layer => layer.id === id
        );
        if (layerToRemove !== undefined) {
            visibleLayerList.value.splice(visibleLayerList.value.indexOf(layerToRemove), 1);
        }
        return layerToRemove;
    };

    /**
     * Add visible layer to the list.
     */
    const addToVisibleLayerList = (layer, index) => {
        // Check if a layer with this ID already exists in the list. If so, give a warning and do not add it.
        if (visibleLayerList.value.find(l => l.id === layer.id)) {
            console.warn(`Layer with ID ${layer.id} is already in the visible layer list. Not adding it again.`);
            return;
        }
        layer.visible = true;
        visibleLayerList.value.splice(index, 0, layer);
    };

    const getLayerType = (layer) => {
        const wmsLayers = getWmsLayerList()['layers'];
        if (layer.id in wmsLayers) {
            return VisibleLayerType.WMS;
        } else if (enabledEsdlIdList.value.includes(layer.es_id)) {
            return VisibleLayerType.ESDL;
        } else {
            return VisibleLayerType.UNKNOWN;
        }
    };

    /**
     * Update the display order of the visible layers
     */
    const updateDisplayOrderVisibleLayers = (id, newPosition) => {
        const movedLayer = removeFromVisibleLayerList(id);
        addToVisibleLayerList(movedLayer, newPosition);
        console.log(`Moved layer ${id} to position ${newPosition}`);

        visibleLayerList.value.slice().reverse().forEach(
            layer => {
                const layerType = getLayerType(layer);
                if (layerType === VisibleLayerType.WMS) {
                    getWmsLayerList()['layers'][layer.id].layer_ref.bringToFront();
                } else if (layerType === VisibleLayerType.ESDL) {
                    layer.layer_ref.bringToFront();
                } else {
                    console.error(`Unknown layer type: ${layerType}`);
                }
            }
        )
    };

    const layerIsVisible = (layerId) => {
        for (const visibleLayer of visibleLayerList.value) {
            if (visibleLayer.id === layerId) {
                return true;
            }
        }
        return false;
    };

    /**
     * Hides a visible layer from the map.
     * @param layerId
     */
    const hideVisibleLayer = (layerId) => {
        const layerToHide = visibleLayerList.value.find(
            layer => layer.id === layerId
        );
        layerToHide.visible = false;
        const layerType = getLayerType(layerToHide);
        if (layerType === VisibleLayerType.WMS) {
            // hide via tree action to also update parent folders three-state
            // TODO: Should we really remove it completely?
            getLayerTree().uncheck_node(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            hideEsdlLayerFromMap(layerToHide.es_id, layerToHide.layer_type);
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
    };

    const hideAllVisibleLayers = () => {
         visibleLayerList.value.slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id)
        )
    };

    const getVisibleLayersOfType = (layerType) => {
        return visibleLayerList.value.filter(
            layer => getLayerType(layer) === layerType
        );
    }

    /**
     * Hides all layers related to the given layer. The exact behaviour depends on the layer type.
     * @param es_id
     */
    const hideRelatedVisibleLayers = (layerId) => {
        const layerToHide = visibleLayerList.value.find(
            layer => layer.id === layerId
        );
        const layerType = getLayerType(layerToHide);
        if (layerType === VisibleLayerType.WMS) {
            // Find all WMS layers and hide them.
            const wmsLayers = getVisibleLayersOfType(VisibleLayerType.WMS);
            wmsLayers.forEach(layer => hideVisibleLayer(layer.id));
        } else if (layerType === VisibleLayerType.ESDL) {
            // Find all layers with matching es_id and hide them.
            const layersToHide = visibleLayerList.value.filter(
                layer => layer.es_id === layerToHide.es_id
            );
            layersToHide.forEach(layer => hideVisibleLayer(layer.id));
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
    };

    const showVisibleLayer = (layerId) => {
        const layerToShow = visibleLayerList.value.find(
            layer => layer.id === layerId
        );
        layerToShow.visible = true;
        const layerType = getLayerType(layerToShow);
        if (layerType === VisibleLayerType.ESDL) {
            showEsdlLayerOnMap(layerToShow.es_id, layerToShow.layer_type);
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
    }

    /**
     * Returns the visible layer object from a given layer Id
     *
     * @param {string} id Layer Id
     * @returns {Object|undefined} The targeted visible layer object; If not found, undefined is returned
     */
    const getVisibleLayerById = (id) => {
        const targetedLayer = visibleLayerList.value.find(layer => layer.id === id);
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
        if (targetLayer && 0 <= opacity <= 1) {
            targetLayer.layer_ref.setOpacity(opacity);
        }
    };

    /**
     * Saves the layer opacity setting to the settings_storage.
     *
     * @param {string} id Layer Id
     */
    const saveVisibleLayerOpacitySetting = (id) => {
        const targetLayer = getVisibleLayerById(id);
        if (targetLayer) {
            const opacity = targetLayer.layer_ref.options.opacity;
            if (id && opacity) {
                const params = {layer_id: id, opacity: opacity};
                // After the "save_wms_layer_opacity_setting" event,
                // calling updateGlobalWmsLayerList to ensure the latest layers settings are reflected in the app.
                socket.emit("save_wms_layer_opacity_setting", params, updateGlobalWmsLayerList);
            }
            else {
                console.error(`Error whiling saving WMS layer opacity setting to the settings_storage with id: ${id}, opacity: ${opacity}`);
            }
        }
    };

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateDisplayOrderVisibleLayers,
        getLayerType,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers,
        hideRelatedVisibleLayers,
        showVisibleLayer,
        getVisibleLayerById,
        adjustVisibleLayerOpacity,
        saveVisibleLayerOpacitySetting
    };
}
