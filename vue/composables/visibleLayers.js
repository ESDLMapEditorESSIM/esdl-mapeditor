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
import {computed, ref} from "vue";
import {updateGlobalWmsLayerList, useWmsLayers, WMS_LAYERS_GROUP_NAME} from "./wmsLayers";
import {useEsdlLayers} from "./esdlLayers";
import {useSocketIO} from "./socketio";

const {subscribe} = useSocketIO();

const {getWmsLayerList, hideWmsLayer, showWmsLayer} = useWmsLayers();
const {enabledEsdlIdList, hideEsdlLayerFromMap, showEsdlLayerOnMap} = useEsdlLayers();

/**
 * Debounce a function call.
 * @param func The function to debounce
 * @param wait The time in ms to wait before calling the function
 * @returns {(function(...[*]): void)|*}
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * @typedef {Object} VisibleLayer
 * @property {string} id
 * @property {boolean} visible
 * @property {string} description
 * @property {string|undefined} parent_esdl_layer
 * @property {string|undefined} es_id
 * @property {Object|undefined} es
 * @property {Object|undefined} layer_ref
 */

/**
 * @typedef {Object} VisibleLayerGroup
 * @property {string} id
 * @property {boolean | import('vue').Ref<boolean>} visible
 * @property {string} description
 * @property {VisibleLayer[]} layers
 */


// Group structure for visible layers
/** @type {import('vue').Ref<VisibleLayerGroup[]>} */
const visibleLayerGroups = ref([]);

function getLayerType(layer) {
    const wmsLayers = getWmsLayerList().layers;
    if (layer.id in wmsLayers) {
        return VisibleLayerType.WMS;
    } else if (enabledEsdlIdList.value.includes(layer.es_id)) {
        return VisibleLayerType.ESDL;
    } else {
        return VisibleLayerType.UNKNOWN;
    }
}

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
 * @typedef {Object} LayerFeatureProps
 * @property {string} name - The name of the layer.
 * @property {Object|null} feature_props - The properties of the layer feature.
 *
 * @typedef {Object} WmsLayerFeatureResponse
 * @property {Object} ev_lat_lng - The geographical LatLng property of the event location.
 * @property {LayerFeatureProps[]} layers_features_props - Array of layer feature properties.
 *
 * @param {WmsLayerFeatureResponse} resp - Response object with structure as {ev_lat_lng: event.latlng, layers_features_props: array[{name: str, feature_props: object|null }]}
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
    for (const visibleLayer of useVisibleLayers().getVisibleLayerList()) {
        const wms_layer = getWmsLayerList().layers[visibleLayer.id];
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
     * @returns {VisibleLayer[]} List of visible layers
     */
    const getVisibleLayerList = () => {
        // Get all layers from all groups.
        return visibleLayerGroups.value.reduce((acc, group) => {
            return acc.concat(group.layers);
        }, []);
    }

    /**
     * Remove visible layer by ID.
     */
    const removeFromVisibleLayerList = (id) => {
        const layerToRemove = getVisibleLayerList().find(
            layer => layer.id === id
        );
        if (layerToRemove !== undefined) {
            // Remove it from its group.
            const layerType = getLayerType(layerToRemove)
            let groupId = null;
            if (layerType === VisibleLayerType.WMS) {
                groupId = WMS_LAYERS_GROUP_NAME;
            } else if (layerType === VisibleLayerType.ESDL) {
                groupId = layerToRemove.es_id;
            }
            const layerToRemoveGroup = visibleLayerGroups.value.find(group => group.id === groupId);
            if (layerToRemoveGroup) {
                layerToRemoveGroup.layers = layerToRemoveGroup.layers.filter(layer => layer.id !== id);
            }
            // Remove group if now empty.
            if (layerToRemoveGroup && layerToRemoveGroup.layers.length === 0) {
                visibleLayerGroups.value = visibleLayerGroups.value.filter(group => group.id !== layerToRemoveGroup.id);
            }
        } else {
            console.warn(`Layer with ID ${id} not found in visible layer list.`);
        }
        return layerToRemove;
    };

    /**
     * Add a visible layer to the list.
     * @param {VisibleLayer} layer - The layer to add.
     * @param {string} groupId - The ID of the group to add the layer to.
     */
    const addToVisibleLayerList = (layer, groupId) => {
        layer.visible = true;
        // Add the layer to the group.
        const group = visibleLayerGroups.value.find(group => group.id === groupId);
        if (group) {
            // Check if the layer already exists in the group. If so, replace it. Otherwise add it.
            const existingLayerIndex = group.layers.findIndex(l => l.id === layer.id);
            if (existingLayerIndex !== -1) {
                group.layers.splice(existingLayerIndex, 1, layer);
            } else {
                group.layers.push(layer);
            }
        } else {
            console.warn(`Group with ID ${groupId} not found.`);
        }
        updateVisibleLayersOrderOnMap()
    };

    /**
     * Create a new group of visible layers.
     * @param {string} groupId - The ID of the group.
     * @param {string} description - The description of the group.
     */
    const createVisibleLayerGroup = (groupId, description = "Untitled Group") => {
        if (!visibleLayerGroups.value.find(group => group.id === groupId)) {
            /** @type {VisibleLayerGroup} */
            const group = {
                id: groupId,
                visible: computed(() => {
                    const thisGroup = visibleLayerGroups.value.find(group => group.id === groupId);
                    return thisGroup.layers.some(layer => layer.visible);
                }),
                description,
//                     description: computed(() => {
//                         return layer.es.title
//                     }),
                layers: [],
            }

            visibleLayerGroups.value.push(group);
        } else {
            console.warn(`Group with ID ${groupId} already exists.`);
        }
        updateVisibleLayersOrderOnMap();
    };

    /**
     * Remove a visible layer group by ID.
     * @param {string} groupId - The ID of the group to remove.
     */
    const removeVisibleLayerGroup = (groupId) => {
        const groupIndex = visibleLayerGroups.value.findIndex(group => group.id === groupId);
        if (groupIndex !== -1) {
            // Remove all layers in the group from the visible layer list
            visibleLayerGroups.value[groupIndex].layers.forEach(layer => {
                removeFromVisibleLayerList(layer.id);
            });
            // Remove the group from visibleLayerGroups
            visibleLayerGroups.value.splice(groupIndex, 1);
        } else {
            console.warn(`Group with ID ${groupId} not found.`);
        }
    };

    /**
     * Update the order of the groups and layers on the map.
     * @param newOrder
     */
    function updateGroupOrder(newOrder) {
        const reorderedGroups = newOrder.map(groupId => {
            return visibleLayerGroups.value.find(group => group.id === groupId);
        });
        visibleLayerGroups.value = reorderedGroups;

        updateVisibleLayersOrderOnMap();
    }

    /**
     * Update the display order of the layers within a group.
     * @param groupId
     * @param newOrder
     */
    const updateDisplayOrderVisibleLayers = (groupId, newOrder) => {
        // Find the group by groupId
        const group = visibleLayerGroups.value.find(group => group.id === groupId);
        if (!group) {
            console.error(`Group with id ${groupId} not found.`);
            return;
        }

        // Reorder the layers within the group based on the new order provided
        const reorderedLayers = newOrder.map(layerId => {
            return group.layers.find(layer => layer.id === layerId);
        });
        group.layers = reorderedLayers;
        updateVisibleLayersOrderOnMap();
    };

    const updateVisibleLayersOrderOnMap = debounce(() => {
        getVisibleLayerList().slice().reverse().forEach(layer => {
            const layerType = getLayerType(layer);
            if (layerType === VisibleLayerType.WMS) {
                getWmsLayerList().layers[layer.id].layer_ref.bringToFront();
            } else if (layerType === VisibleLayerType.ESDL) {
                layer.layer_ref.bringToFront();
            } else {
                console.error(`Unknown layer type: ${layerType}`);
            }
        });
    }, 300);

    const layerIsVisible = (layerId) => {
        for (const visibleLayer of getVisibleLayerList()) {
            if (visibleLayer.id === layerId && visibleLayer.visible) {
                return true;
            }
        }
        return false;
    };

    /**
     * Check if a layer with this layer ID exists in the visible layer list.
     * @param layerId
     */
    const layerExists = (layerId) => {
        return getVisibleLayerList().find(layer => layer.id === layerId) !== undefined;
    };

    /**
     * Hides a visible layer from the map.
     * @param layerId
     */
    const hideVisibleLayer = (layerId) => {
        const layerToHide = getVisibleLayerList().find(
            layer => layer.id === layerId
        );
        const layerType = getLayerType(layerToHide);
        if (layerType === VisibleLayerType.WMS) {
            hideWmsLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            hideEsdlLayerFromMap(layerToHide.es_id, layerToHide.description, layerToHide.parent_esdl_layer);
            // Find all other layers in the same group that has this description as parent_esdl_layer and hide them.
            const group = visibleLayerGroups.value.find(group => group.id === layerToHide.es_id);
            if (group) {
                group.layers.forEach(layer => {
                    if (layer.parent_esdl_layer === layerToHide.description) {
                        hideVisibleLayer(layer.id);
                    }
                });
            }
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
        layerToHide.visible = false;
        updateVisibleLayersOrderOnMap();
    };

    const hideAllVisibleLayers = () => {
        getVisibleLayerList().slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id)
        )
    };

    const showAllVisibleLayers = () => {
        getVisibleLayerList().slice().reverse().forEach(
            layer => showVisibleLayer(layer.id)
        )
    };

    const showVisibleLayer = (layerId) => {
        const layerToShow = getVisibleLayerList().find(
            layer => layer.id === layerId
        );
        const layerType = getLayerType(layerToShow);
        if (layerType === VisibleLayerType.WMS) {
            showWmsLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            showEsdlLayerOnMap(layerToShow.es_id, layerToShow.description, layerToShow.parent_esdl_layer);
            // Find all other layers in the same group that has this description as parent_esdl_layer and show them.
            const group = visibleLayerGroups.value.find(group => group.id === layerToShow.es_id);
            if (group) {
                group.layers.forEach(layer => {
                    if (layer.parent_esdl_layer === layerToShow.description) {
                        showVisibleLayer(layer.id);
                    }
                });
            }
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
        layerToShow.visible = true;
        updateVisibleLayersOrderOnMap();
    }

    /**
     * Returns the visible layer object from a given layer Id
     *
     * @param {string} id Layer Id
     * @returns {Object|undefined} The targeted visible layer object; If not found, undefined is returned
     */
    const getVisibleLayerById = (id) => {
        return getVisibleLayerList().find(layer => layer.id === id);
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
        createVisibleLayerGroup,
        removeVisibleLayerGroup,
        updateDisplayOrderVisibleLayers,
        getLayerType,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers,
        showAllVisibleLayers,
        showVisibleLayer,
        layerExists,
        getVisibleLayerById,
        adjustVisibleLayerOpacity,
        saveVisibleLayerOpacitySetting,
        getVisibleLayerGroups,
        toggleGroupVisibility,
    };
}
