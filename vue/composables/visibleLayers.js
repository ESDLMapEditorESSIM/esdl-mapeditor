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
import {computed, ref, toValue, watch} from "vue";
import {useWmsLayers, updateGlobalWmsLayerList} from "./wmsLayers";
import {useEsdlLayers} from "./esdlLayers";
import {useSocketIO} from "./socketio";
const {subscribe} = useSocketIO();

const {getWmsLayerList, hideWmsLayer, showWmsLayer} = useWmsLayers();
const {enabledEsdlIdList, hideEsdlLayerFromMap, showEsdlLayerOnMap} = useEsdlLayers();

/**
 * @typedef {Object} VisibleLayer
 * @property {string} id
 * @property {string|undefined} es_id
 * @property {description|undefined} es_id
 * @property {Object|undefined} es
 * @property {VisibleLayerType} layer_type
 * @property {boolean} visible
 * @property {Object|undefined} layer_ref
 * @property {VisibleLayer[]|undefined} layers
 */


// List of visible layers. Contains wms layers as well as energy systems.
/** @type {import('vue').Ref<VisibleLayer[]>} */
const visibleLayerList = ref([]);

// Group structure for visible layers
/** @type {import('vue').Ref<VisibleLayer[]>} */
const visibleLayerGroups = ref([]);

function getLayerType(layer) {
    const wmsLayers = getWmsLayerList()['layers'];
    if (layer.id in wmsLayers) {
        return VisibleLayerType.WMS;
    } else if (enabledEsdlIdList.value.includes(layer.es_id)) {
        return VisibleLayerType.ESDL;
    } else {
        return VisibleLayerType.UNKNOWN;
    }
}

/**
 * Groups layers by their es_id (for ESDL layers) or other group identifier.
 * This function ensures that related layers are grouped together.
 */
const groupVisibleLayers = () => {
    console.debug("Grouping visible layers");
    const grouped = {};

    const currentGroupState = visibleLayerGroups.value.reduce((acc, group, index) => {
        acc[group.id] = { order: index };
        return acc;
    }, {});

    visibleLayerList.value.forEach((layer) => {
        const layerType = getLayerType(layer);
        if (layerType === VisibleLayerType.ESDL) {
            const groupId = layer.es_id;
            if (!grouped[groupId]) {
                grouped[groupId] = {
                    id: groupId,
                    layer_type: VisibleLayerType.ESDL,
                    es: layer.es,
                    description: computed(() => {
                        return layer.es.title
                    }),
                    layers: [],
                    visible: computed(() => {
                        return grouped[groupId].layers.some(layer => layer.visible);
                    }),
                    order: currentGroupState[groupId]?.order ?? Object.keys(grouped).length
                };
            }
            grouped[groupId].layers.push(layer);
        } else if (layerType === VisibleLayerType.WMS) {
            // Group all WMS layers together.
            const wmsLayerId = "wms";
            if (!grouped[wmsLayerId]) {
                grouped[wmsLayerId] = {
                    id: layer.id,
                    layer_type: VisibleLayerType.WMS,
                    description: "WMS Layers",
                    layers: [],
                    visible: computed(() => {
                        return grouped[wmsLayerId].layers.some(layer => layer.visible);
                    }),
                    order: currentGroupState[wmsLayerId]?.order ?? Object.keys(grouped).length
                };
            }
            grouped[wmsLayerId].layers.push(layer);
        } else {
            // Unknown.
            if (!grouped[layer.id]) {
                grouped[layer.id] = {
                    id: layer.id,
                    layer_type: VisibleLayerType.UNKNOWN,
                    description: layer.id,
                    layers: [],
                    visible: computed(() => {
                        return grouped[layer.id].layers.some(layer => layer.visible);
                    }),
                    order: currentGroupState[layer.id]?.order ?? Object.keys(grouped).length
                };
            }
            grouped[layer.id].layers.push(layer);
        }
    });

    visibleLayerGroups.value = Object.values(grouped).sort((a, b) => a.order - b.order);
};

// Call groupVisibleLayers whenever the visible layers are updated
const visibleLayerListLength = computed(() => visibleLayerList.value.length);
watch(visibleLayerListLength, () => {
    groupVisibleLayers();
});

const map = window.map;

// Initialize the layer popup and specify popup options
const L = window.L;
const layersPopup = L.popup({
    autoPan: true,
    maxWidth: 400,
    maxHeight: 400
});

/**
 * @enum {string}
 */
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
        console.log("Adding layer to visible layer list", layer);
        // Check if a layer with this ID already exists in the list. If so, give a warning and do not add it.
        if (visibleLayerList.value.find(l => l.id === layer.id)) {
            console.warn(`Layer with ID ${layer.id} is already in the visible layer list. Not adding it again.`);
            return;
        }
        layer.visible = true;
        visibleLayerList.value.splice(index, 0, layer);
    };

    function updateGroupOrder(newOrder) {
        const reorderedGroups = newOrder.map(groupId => {
            return visibleLayerGroups.value.find(group => group.id === groupId);
        });
        visibleLayerGroups.value = reorderedGroups;

        visibleLayerGroups.value.slice().reverse().forEach(
            group => {
                group.layers.forEach(layer => {
                    const layerType = getLayerType(layer);
                    if (layerType === VisibleLayerType.WMS) {
                        getWmsLayerList()['layers'][layer.id].layer_ref.bringToFront();
                    } else if (layerType === VisibleLayerType.ESDL) {
                        layer.layer_ref.bringToFront();
                    } else {
                        console.error(`Unknown layer type: ${layerType}`);
                    }
                });
            }
        )
    }

    const layerIsVisible = (layerId) => {
        for (const visibleLayer of visibleLayerList.value) {
            if (visibleLayer.id === layerId && visibleLayer.visible) {
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
        const layerType = getLayerType(layerToHide);
        if (layerType === VisibleLayerType.WMS) {
            hideWmsLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            hideEsdlLayerFromMap(layerToHide.es_id, layerToHide.layer_type);
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
        layerToHide.visible = false;
    };

    const hideAllVisibleLayers = () => {
        visibleLayerList.value.slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id)
        )
    };

    const showVisibleLayer = (layerId) => {
        const layerToShow = visibleLayerList.value.find(
            layer => layer.id === layerId
        );
        const layerType = getLayerType(layerToShow);
        if (layerType === VisibleLayerType.WMS) {
            showWmsLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            showEsdlLayerOnMap(layerToShow.es_id, layerToShow.layer_type);
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
        layerToShow.visible = true;
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

    /**
     * Get the list of visible layer groups. This includes grouped layers for ESDL.
     */
    const getVisibleLayerGroups = () => {
        return visibleLayerGroups.value;
    };

    /**
     * Show or hide an entire group of layers by its group id.
     */
    const toggleGroupVisibility = (groupId) => {
        const group = visibleLayerGroups.value.find((group) => group.id === groupId);
        if (group) {
            const isGroupVisible = group.visible;
            group.layers.forEach((layer) => {
                if (isGroupVisible) {
                    hideVisibleLayer(layer.id);
                } else {
                    showVisibleLayer(layer.id);
                }
            });
        } else {
            console.warn(`Group with id ${groupId} not found.`);
        }
    };

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateGroupOrder,
        getLayerType,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers,
        showVisibleLayer,
        getVisibleLayerById,
        adjustVisibleLayerOpacity,
        saveVisibleLayerOpacitySetting,
        getVisibleLayerGroups,
        toggleGroupVisibility,
    };
}
