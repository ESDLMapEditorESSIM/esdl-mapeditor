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
import {constructWfsLayerUrl, updateGlobalServiceLayerList, useWmsLayers, WMS_LAYERS_GROUP_NAME, showLayer, hideLayer} from "./wmsLayers";
import {useEsdlLayers} from "./esdlLayers";
import {useSocketIO} from "./socketio";
import { setLeafletFeatureStyle } from "../utils/spatialVisualization";

const {socket} = useSocketIO();

const {getWmsLayerList} = useWmsLayers();
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
 * @property {string|undefined} es_layer_name
 * @property {string|undefined} es_id
 * @property {Object|undefined} es
 * @property {Object|undefined} layer_ref
 * @property {Object[]|undefined} layer_refs
 * @property {Object[]|undefined} child_layers
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

// Cache for layer order within groups.
const layerOrderCache = ref({});
const layerVisibilityCache = ref({});

/**
 * @enum {string}
 */
export const VisibleLayerType = Object.freeze({
    WMS: 'WMS',
    WFS: 'WFS',
    ESDL: 'ESDL',
    UNKNOWN: 'Unknown'
});

const serviceType = Object.freeze({
    WMS: "WMS",
    WFS: "WFS"
});

function getLayerType(layer) {
    const serviceLayers = getWmsLayerList()?.layers || {};
    if (layer && layer.id in serviceLayers) {
        return serviceLayers[layer.id].type || VisibleLayerType.WMS;
    } else if (layer && enabledEsdlIdList.value.includes(layer.es_id)) {
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
 * Constructs and returns a WMS layer GetFeatureInfo URL
 * based on the mouse click event location (LatLng)
 *
 * @param {string} wmsServiceUrl WMS service URL
 * @param {string} layerName Query layer name
 * @param {object} evLatLng Geographical LatLng property of the mouse click event
 * @returns {string} WMS GetFeatureInfo URL of the event location
 */
const constructWmsLayerGetFeatureInfoUrl = (wmsServiceUrl, layerName, evLatLng) => {
    return wmsServiceUrl +
        "?service=WMS&version=1.1.1&request=GetFeatureInfo&layers=" + layerName +
        "&styles=&bbox=" + map.getBounds().toBBoxString() +
        "&height=" + map.getSize().y + "&width=" + map.getSize().x +
        "&query_layers=" + layerName +
        "&info_format=application/json&srs=EPSG:4326" +
        "&x=" + Math.round(map.latLngToContainerPoint(evLatLng).x) +
        "&y=" + Math.round(map.latLngToContainerPoint(evLatLng).y);
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
 * @returns {Promise} Query response object with structure as Array[{name: str, feature_props: Object | null }]
 */
const queryWmsLayersFeaturesOnClick = async (event) => {
    return new Promise((resolve) => {
        const visibleLayers = useVisibleLayers().getVisibleLayerList();
        const visibleWmsLayers = visibleLayers.filter(l => getLayerType(l) === VisibleLayerType.WMS);
        const currentZoomLevel = map.getZoom();

        const layersRequestInfo = visibleWmsLayers
            // Only request layer feature if the layer is within the visible zoom level.
            .filter((layer) =>
                layer.min_zoom_level === undefined ||
                currentZoomLevel >= layer.min_zoom_level
            )
            .map((layer) => {
                const serviceUrl = layer.url;
                const layerName = layer.layer_name;
                const getFeatureUrl = constructWmsLayerGetFeatureInfoUrl(serviceUrl, layerName, event.latlng);
                return {name: layerName, url: getFeatureUrl};
            });

        if (!layersRequestInfo.length) {
            resolve([]);
            return;
        }

        const requestBody = {
            ev_lat_lng: event.latlng,
            layers: layersRequestInfo
        };
        socket.value.emit("query_wms_layer_feature", requestBody, (resp) => {
            resolve(resp.layers_features_props);
        });
    });
};

/**
 * Show the map popup of WMS or WFS layers features properties
 *
 * @param {Object} latlng a latlng object {lat: number, lng: number} for adding the popup.
 * @param {Array} layersFeatures an array of layer feature objects with structure { name: str, feature_props: Object | null }
 */
const showServiceLayerFeaturePopup = (latlng, layersFeatures) => {
    if (layersFeatures.length === 0) {
        return;
    }

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
    layersFeatures.forEach((l) => {
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
        layersPopup.setLatLng(latlng).setContent(popupDiv);
        map.openPopup(layersPopup);
    }
};

/**
 * The function can be used as an callback fn to update WFS layer features
 * when 'moveend' event is triggered.
 */
const updateWfsLayersOnBboxChange = async () => {
  const visibleLayers = useVisibleLayers().getVisibleLayerList();
  const bbox = map.getBounds().toBBoxString();
  const currentZoomLevel = map.getZoom();

  // Filter only for WFS layers
  const wfsLayers = visibleLayers.filter(l => getLayerType(l) === VisibleLayerType.WFS);

  for (const layer of wfsLayers) {
    // Only run layer feature update if the layer is within the visible zoom level.
    if (layer.min_zoom_level === undefined || currentZoomLevel >= layer.min_zoom_level) {
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
  const currentZoomLevel = map.getZoom();

  visibleLayers.forEach(layer => {
    if (!layer.min_zoom_level || !layer.layer_ref) return;

    const shouldBeVisible = currentZoomLevel >= layer.min_zoom_level;
    const isVisible = map.hasLayer(layer.layer_ref);

    if (shouldBeVisible && !isVisible) {
      layer.layer_ref.addTo(map);
    } else if (!shouldBeVisible && isVisible) {
      map.removeLayer(layer.layer_ref);
      console.debug(`The current zoom level is smaller than the defined min_zoom_level, hide layer ${layer.layer_name}.`);
    }
  });
};

map.on("click", async (event) => {
    const wmsLayersFeatures = await queryWmsLayersFeaturesOnClick(event);
    showServiceLayerFeaturePopup(event.latlng, wmsLayersFeatures);
});

map.on('moveend', function () {
    updateZoomDependentLayers();
    // NICE TO HAVE: abort WFS update (if still running) on the cursor move again.
    updateWfsLayersOnBboxChange();
})

export function useVisibleLayers() {
    /**
     * Get list of visible layers. This is a list of objects, that are either service layers or energy systems.
     * @returns {VisibleLayer[]} List of visible layers
     */
    const getVisibleLayerList = () => {
        // Get all layers from all groups.
        return visibleLayerGroups.value.reduce((acc, group) => {
            return acc.concat(group.layers);
        }, []);
    }

    /**
     * Get the list of visible layer groups. This includes grouped layers for ESDL.
     */
    const getVisibleLayerGroups = () => {
        return visibleLayerGroups.value;
    };

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
            if (layerType === VisibleLayerType.WMS || layerType === VisibleLayerType.WFS) {
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
     * @param {boolean} updateMap - Whether to update the map. Set to false if part of bulk operation.
     */
    const addToVisibleLayerList = (layer, groupId = WMS_LAYERS_GROUP_NAME, updateMap = true) => {
        if (groupId === 0) {
            groupId = WMS_LAYERS_GROUP_NAME;
        }
        if (layer.id in layerVisibilityCache.value) {
            layer.visible = layerVisibilityCache.value[layer.id];
        } else {
            layer.visible = true;
        }
        // Add the layer to the group.
        let group = visibleLayerGroups.value.find(group => group.id === groupId);
        if (!group) {
            createVisibleLayerGroup(groupId, groupId === WMS_LAYERS_GROUP_NAME ? "Service layers" : "Untitled Group", [], false);
            group = visibleLayerGroups.value.find(group => group.id === groupId);
        }
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
        if (layer.visible) {
            showVisibleLayer(layer.id, updateMap);
        }
    };

    /**
     * Create a new group of visible layers.
     * @param {string} groupId - The ID of the group.
     * @param {string} description - The description of the group.
     * @param {VisibleLayer[]} sublayers - The sublayers to add to the group.
     * @param {boolean} updateMap - Whether to update map order after creating the group.
     */
    const createVisibleLayerGroup = (groupId, description = "Untitled Group", sublayers, updateMap = true) => {
        if (!visibleLayerGroups.value.find(group => group.id === groupId)) {
            /** @type {VisibleLayerGroup} */
            const group = {
                id: groupId,
                visible: computed(() => {
                    const thisGroup = visibleLayerGroups.value.find(group => group.id === groupId);
                    return thisGroup.layers.some(layer => layer.visible);
                }),
                description,
                layers: [],
            }

            visibleLayerGroups.value.push(group);

            if (sublayers) {
                sublayers.forEach(sublayer => {
                    addToVisibleLayerList(sublayer, groupId, false);
                });
                sublayers.forEach(sublayer => {
                    if (!sublayer.visible) {
                        hideVisibleLayer(sublayer.id);
                    }
                });
            }
            if (layerOrderCache.value[groupId]) {
                console.debug(`Restoring layer order for group ${groupId}`);
                updateDisplayOrderVisibleLayers(groupId, layerOrderCache.value[groupId]);
            }
        } else {
            console.warn(`Group with ID ${groupId} already exists.`);
        }
        if (updateMap) {
            updateVisibleLayersOrderOnMap();
        }
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
        layerOrderCache.value[groupId] = newOrder;
        updateVisibleLayersOrderOnMap();
    };

    /**
     * Update the order of the visible layers on the map. This function is debounced to prevent multiple calls in a
     * short time frame. The layers are ordered in reverse order, so that the last layer in the list is on top.
     * @type {(function(...[*]): void)|*}
     */
    const updateVisibleLayersOrderOnMap = debounce(() => {
        console.debug("Updating visible layers order on map.");
        getVisibleLayerList().slice().reverse().forEach(layer => {
            const layerType = getLayerType(layer);
            if (layerType === VisibleLayerType.WMS || layerType === VisibleLayerType.WFS) {
                const serviceLayer = getWmsLayerList().layers[layer.id];
                if (serviceLayer?.layer_ref) {
                    serviceLayer.layer_ref.bringToFront();
                }
            } else if (layerType === VisibleLayerType.ESDL) {
                layer.layer_refs.forEach(layerRef => {
                    layerRef.bringToFront();
                });
            } else {
                console.error(`Unknown layer type: ${layerType}`);
            }
        });
    }, 100);

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
     * @param updateMap Whether or not to update the map directly. Set this to false if you are doing a bulk operation.
     */
    const hideVisibleLayer = (layerId, updateMap = true) => {
        const layerToHide = getVisibleLayerList().find(
            layer => layer.id === layerId
        );
        if (!layerToHide) {
            return;
        }
        const layerType = getLayerType(layerToHide);
        if (layerType === VisibleLayerType.WMS || layerType === VisibleLayerType.WFS) {
            hideLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            hideEsdlLayerFromMap(layerToHide.es_id, layerToHide.description, layerToHide.es_layer_name);
            const group = visibleLayerGroups.value.find(group => group.id === layerToHide.es_id);
            // Find all other layers in the same group that has this description as es_layer_name and hide them.
            // In that way, all layers under the same es_layer (area, kpi, etc) are hidden when one of them is hidden.
            if (group) {
                group.layers.forEach(layer => {
                    if (layer.es_layer_name === layerToHide.description) {
                        hideVisibleLayer(layer.id);
                    }
                });
            }
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }

        if (layerToHide.child_layers) {
            layerToHide.child_layers.forEach(childLayer => {
                hideVisibleLayer(childLayer.id);
            });
        }

        layerToHide.visible = false;
        layerVisibilityCache.value[layerId] = false;
        if (updateMap) {
            updateVisibleLayersOrderOnMap();
        }
    };

    const hideAllVisibleLayers = () => {
        getVisibleLayerList().slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id, false)
        )
        updateVisibleLayersOrderOnMap();
    };

    const showAllVisibleLayers = () => {
        getVisibleLayerList().slice().reverse().forEach(
            layer => showVisibleLayer(layer.id, false)
        )
        updateVisibleLayersOrderOnMap();
    };

    const showVisibleLayer = (layerId, updateMap = true) => {
        const layerToShow = getVisibleLayerList().find(
            layer => layer.id === layerId
        );
        if (!layerToShow) {
            return;
        }
        const layerType = getLayerType(layerToShow);
        if (layerType === VisibleLayerType.WMS || layerType === VisibleLayerType.WFS) {
            showLayer(layerId);
        } else if (layerType === VisibleLayerType.ESDL) {
            showEsdlLayerOnMap(layerToShow.es_id, layerToShow.description, layerToShow.es_layer_name);
            // Find all other layers in the same group that has this description as es_layer_name and hide them.
            // In that way, all layers under the same es_layer (area, kpi, etc) are hidden when one of them is hidden.
            const group = visibleLayerGroups.value.find(group => group.id === layerToShow.es_id);
            if (group) {
                group.layers.forEach(layer => {
                    if (layer.es_layer_name === layerToShow.description) {
                        if (layer.visible) {
                            showVisibleLayer(layer.id, updateMap);
                        } else {
                            hideVisibleLayer(layer.id, updateMap);
                        }
                    }
                });
            }
        } else {
            console.error(`Unknown layer type: ${layerType}`);
        }
        layerToShow.visible = true;
        layerVisibilityCache.value[layerId] = true;
        if (updateMap) {
            updateVisibleLayersOrderOnMap();
        }
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
        const type = getLayerType(targetLayer);
        if (targetLayer && opacity >= 0 && opacity <= 1) {
            if (type === serviceType.WMS) {
                targetLayer.layer_ref.setOpacity(opacity);
            } else if (type === serviceType.WFS) {
                // Update the stored style
                targetLayer.style.opacity = opacity;
                targetLayer.layer_ref.setStyle((feature) => {
                    return setLeafletFeatureStyle(feature.geometry.type, targetLayer.style);
                });
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
        const type = getLayerType(targetLayer);
        if (targetLayer) {
            let opacity;
            if (type === serviceType.WMS) {
                opacity = targetLayer.layer_ref.options.opacity;
            } else if (type === serviceType.WFS) {
                opacity = targetLayer.style?.opacity !== undefined ? targetLayer.style.opacity : 1.0;
            }

            if (id && opacity !== undefined) {
                const params = {layer_id: id, opacity: opacity};
                // After the "save_layer_opacity_setting" event,
                // calling updateGlobalServiceLayerList to ensure the latest layers settings are reflected in the app.
                socket.value.emit("save_layer_opacity_setting", params, updateGlobalServiceLayerList);
            }
            else {
                console.error(`Error whiling saving layer opacity setting to the settings_storage with id: ${id}, opacity: ${opacity}`);
            }
        }
    };

    /**
     * Show or hide an entire group of layers by its group id.
     */
    const toggleGroupVisibility = (groupId) => {
        const group = visibleLayerGroups.value.find((group) => group.id === groupId);
        if (group) {
            const isGroupVisible = group.visible?.value ?? group.visible;
            group.layers.forEach((layer) => {
                if (isGroupVisible) {
                    hideVisibleLayer(layer.id, false);
                } else {
                    showVisibleLayer(layer.id, false);
                }
            });
            updateVisibleLayersOrderOnMap();
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
        showServiceLayerFeaturePopup
    };
}
