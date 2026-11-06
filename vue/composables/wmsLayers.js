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

// TODO: rename file to webServicelayers.js

/**
 * A composable for managing items currently visible.
 *
 */
import {markRaw, ref, toValue} from "vue";
import { setLeafletFeatureStyle } from "../utils/layerStyle";
import {useServiceLayerFeaturePopup} from "./serviceLayerFeaturePopup";
import {useVisibleLayerState} from "./visibleLayerState";

const {
    addLayerToVisibleLayerGroup,
    layerIsVisible,
    removeLayerFromVisibleLayerGroups,
    WMS_LAYERS_GROUP_NAME
} = useVisibleLayerState();
const {showServiceLayerFeaturePopup} = useServiceLayerFeaturePopup();

export {WMS_LAYERS_GROUP_NAME};

const L = window.L;
const map = window.map;
let socket = null;
const globalServiceLayerList = ref(null);

// retrieve service layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    // TODO: rename wms_layer_list
    socket.on('wms_layer_list', updateGlobalServiceLayerList);
})();

async function updateGlobalServiceLayerList(layerList, visibleId) {
    if (globalServiceLayerList.value !== null) {
        for (const layerId in globalServiceLayerList.value['layers']) {
            if (layerId in layerList['layers']) {
                // make sure not to lose the map reference
                layerList['layers'][layerId].layer_ref = globalServiceLayerList.value['layers'][layerId].layer_ref;
            } else {
                // hide layer present in global (old) list, but not in new list from database: was deleted
                removeLayerFromMapAndVisibleLayers(layerId);
            }
        }
        for (const layerGroupId in globalServiceLayerList.value['layer_groups']) {
            if (layerGroupId in layerList['layer_groups']) {
                // make sure opened folders stay open
                if ('opened' in globalServiceLayerList.value['layer_groups'][layerGroupId]) {
                    layerList['layer_groups'][layerGroupId].opened =
                        globalServiceLayerList.value['layer_groups'][layerGroupId]['opened'];
                } else {
                    layerList['layer_groups'][layerGroupId].opened = false;
                }
            }
        }
    }

    globalServiceLayerList.value = layerList;
    for (const key in globalServiceLayerList.value['layers']) {
        const layer_info = globalServiceLayerList.value['layers'][key];
        layer_info.id = key;
        if (!layer_info.layer_ref) {
            // Create a leaflet layer reference depending on service type.
            // If type is undefined, assume WMS type and apply WMS handling for backward compatibility.
            if (layer_info.type === undefined || layer_info.type === 'WMS') {
                layer_info.layer_ref = markRaw(L.tileLayer.wms(layer_info.url, {
                    ...layer_info.tile_options,
                    minZoom: layer_info.min_zoom_level ?? 0,
                    layers: layer_info.layer_name,
                    format: 'image/png',
                    transparent: true,
                    opacity: layer_info.opacity ?? 0.7,
                    attribution: layer_info.attribution || ''
                }));
            } else if (layer_info.type === 'WMTS') {
                layer_info.layer_ref = markRaw(L.tileLayer(layer_info.url, {
                    ...layer_info.tile_options,
                    minZoom: layer_info.min_zoom_level ?? 0,
                    opacity: layer_info.opacity ?? 0.7,
                    attribution: layer_info.attribution || ''
                }));
            } else if (layer_info.type === 'WFS') {
                // Without providing a map bbox, the given url will retrieve 0 feature,
                // and only load WFS layer into layer_ref as a reference.
                // The features are only loaded when the layer is added to the map.
                const url = constructWfsLayerUrl(layer_info.url, layer_info.layer_name);
                layer_info.layer_ref = await loadWfsLayer(
                    layer_info.layer_name,
                    url,
                    layer_info.style
                );
            } else {
                console.error(`Unsupported layer type: ${layer_info.type}`);
            }
        }
        layer_info.visible = layerIsVisible(layer_info.id);
        if (visibleId !== undefined) {
            if (layer_info.id === visibleId) {
                layer_info.visible = true;
            }
        }
        if (layer_info.visible && layer_info.layer_ref) {
            layer_info.layer_ref.addTo(map);
            layer_info.layer_ref.bringToFront();
            if (layer_info.opacity !== undefined) {
                layer_info.layer_ref.setOpacity(layer_info.opacity);
            }
        }
    }
}

/**
 * Extracts and returns the base URL of the WMS/WFS service.
 *
 * @param {string} inputUrl The input WMS/WFS URL, possibly with various query parameters.
 * @returns {string|Error} The base URL of the WMS/WFS service if valid, otherwise an Error object.
 */
const getServiceBaseUrl = (inputUrl) => {
    try {
        const url = new URL(inputUrl);
        return `${url.origin}${url.pathname}`;
    } catch (error) {
        return new Error(`${error}`);
    }
};

/**
 * Fetches and returns the Service GetCapabilities response into a resp object,
 * with a structure as {success: boolean, result: ServiceLayerInfo[] | string}.
 *
 * @param {string} layerBaseUrl The base URL of the WMS/WFS service.
 * @param {string} serviceType either "WMS" or "WFS"
 * @returns {Promise<Object>} A promise that resolves to a resp GetCapabilitiesResp object.
 */
const getServiceGetCapabilities = async (layerBaseUrl, serviceType) => {
    const params = {
        url: layerBaseUrl,
        service_type: serviceType
    };
    return new Promise((resolve, reject) => {
        socket.emit('get_service_getcapabilities', params, (resp) => {
            if (resp) {
                resolve(resp);
            } else {
                reject(new Error(`An unknown error occurred while fetching ${serviceType} GetCapabilities from ${layerBaseUrl}.`));
            }
        });
    });
};

/**
 * Add a WMS/WFS layerInfo object to MongoDB
 *
 * @returns {Promise<Object>} A promise of allLayers object ({layers: {}, layer_groups: {}}) that resolves if the layer is added successfully,
 *                            or rejects with an error if the addition fails.
 * @throws {Error} If the backend response indicates a failure to add the layer.
 */
const addServiceLayer = async ({
    type,
    layerId,
    layerDescr,
    layerUrl,
    layerName,
    style,
    settingtype,
    projectName,
    legendUrl,
    layerAttr,
    minZoomLevel,
    groupId
}) => {
    const layerInfo = {
        type: type,
        id: layerId,
        description: layerDescr,
        url: layerUrl,
        name: layerName,
        setting_type: settingtype,
        project_name: projectName,
        min_zoom_level: minZoomLevel,
        parent_group_id: groupId,
    };

    if (type === 'WFS') {
        layerInfo['style'] = style;
    }
    if (type === 'WMS') {
        layerInfo['legend_url'] = legendUrl;
        layerInfo['attribution'] = layerAttr;
    }

    return new Promise((resolve, reject) => {
        socket.emit('add_service_layer', layerInfo, (allLayers) => {
            if (allLayers) {
                resolve(allLayers);
            } else {
                reject(new Error(`An unknown error occurred while adding a ${type} layer ${layerName}.`));
            }
        });
    });
};

const showLayer = async (layerId) => {
    const layer = globalServiceLayerList.value['layers'][layerId];
    const type = layer.type ? layer.type : 'WMS';

    if (!layerIsVisible(layerId)) {
        // Load WFS based on current map bbox
        if (type === 'WFS') {
            const bbox = map.getBounds().toBBoxString();
            const url = constructWfsLayerUrl(layer.url, layer.layer_name, bbox);
            layer.layer_ref = await loadWfsLayer(
                layer.layer_name,
                url,
                layer.style
            );
        }

        if (type === 'WMS' && layer.legend_url) {
            showWmsLegend(layer.legend_url);
        }

        if (!layer.min_zoom_level || (layer.min_zoom_level && map.getZoom() >= layer.min_zoom_level)) {
            layer.layer_ref.addTo(map);
            layer.layer_ref.bringToFront();
            layer.visible = true;
            if (layer.opacity !== undefined) {
                layer.layer_ref.setOpacity(layer.opacity);
            }
        }

        addLayerToVisibleLayerGroup(layer, WMS_LAYERS_GROUP_NAME);
    }
}

const hideLayer = (layerId) => {
    removeLayerFromMapAndVisibleLayers(layerId);
};

/**
 * @typedef {Object} WmsLayerInfo
 * @property {string} description
 * @property {string} url
 * @property {string} layer_name
 * @property {string} legend_url
 * @property {string} attribution
 * @property {number | null} min_zoom_level
 */

/**
 * @typedef {Object} WfsLayerInfo
 * @property {string} description
 * @property {string} url
 * @property {string} layer_name
 * @property {number | null} min_zoom_level
 */

/**
 * Update a service layer settings in MongoDB.
 *
 * @param {string} layerId
 * @param {"WMS" | "WMTS" | "WFS"} type
 * @param {WmsLayerInfo | WfsLayerInfo} layerInfo
 */
const updateServiceLayer = (layerId, type, layerInfo) => {
    removeLayerFromMapAndVisibleLayers(layerId);
    globalServiceLayerList.value['layers'][layerId].layer_ref = null; // make sure map ref gets updated in updateGlobalServiceLayerList
    socket.emit('save_service_layer', {
        id: layerId,
        type: type,
        lyr_info: layerInfo
    }, (allLayers) => {
        allLayers['layers'][layerId].visible = true;
        updateGlobalServiceLayerList(allLayers, layerId);
        showLayer(layerId);
    });
};

/**
 * Constructs and returns a WFS layer URL
 */
const constructWfsLayerUrl = (serviceUrl, layerName, bbox, version = "1.1.0") => {
  const url = new URL(serviceUrl);

  const params = {
    service: 'WFS',
    version: version,
    request: 'GetFeature',
    typeName: layerName,
    outputFormat: 'application/json',
    srsname: 'EPSG:4326',
  };

  if (bbox) {
    params.bbox = `${bbox}`;
  } else {
    params.maxFeatures = 0;
  }

  Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
  return url.toString();
}

/**
 * @typedef {Object} FeatureStyle
 * @property {string} color
 * @property {number} opacity
 * @property {number} radius
 * @property {number} weight
 * @property {boolean} stroke
 */

/**
 * Load WFS layer features on the map.
 *
 * @param {string} layerName
 * @param {string} url
 * @param {FeatureStyle} style
 * @returns
 */
const loadWfsLayer = async (layerName, url, style) => {
  window.show_loader();
  try {
    const response = await fetch(url);
    const data = await response.json();

    return L.geoJSON(data, {
      style: function (feature) {
        return setLeafletFeatureStyle(feature.geometry.type, style);
      },
      // This styles Point/MultiPoint geometry features
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, setLeafletFeatureStyle(feature.geometry.type, style));
      },
      onEachFeature: (feature, layer) => {
        // Attach a click listener directly to the feature's layer
        layer.on('click', (event) => {
            // Prevent the map.on('click') in visibleLayers.js from firing.
            L.DomEvent.stopPropagation(event);

            showServiceLayerFeaturePopup(
                event.latlng,
                [{ name: layerName, feature_props: feature.properties }]
            );
        });

        window.set_wfs_handlers(layer);
      }
    });
  } catch (error) {
    console.error(`Error loading WFS [${layerName}]:`, error);
  } finally {
    window.hide_loader();
  }
};


export function useWmsLayers() {
    // TODO: add some filtering; or remove this fn.
    /**
     * Get the wms layer list.
     */
    const getWmsLayerList = () => toValue(globalServiceLayerList);

    const removeWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalServiceLayerList);
        const layer = globalServiceLayerList.value['layers'][layerId];
        if (layer && layer.layer_ref) {
            map.removeLayer(layer.layer_ref);
        }
        removeLayerFromVisibleLayerGroups(layerId);
    };

    const clearWmsLayers = () => {
        if (!globalServiceLayerList.value) {
            return;
        }
        for (const [key,] of Object.entries(globalServiceLayerList.value['layers'])) {
            hideLayer(key)
        }
    };

    const addWmsLayerGroup = (parentId, setting_type, project_name) => {
        const groupId = window.uuidv4();
        const layerGroup = {
            'id': groupId,
            'description': 'new folder',
            'setting_type': setting_type,
            'project_name': project_name,
            'parent_group_id': parentId,
        };
        socket.emit('add_wms_layer_group', layerGroup, updateGlobalServiceLayerList);
    };

    const renameWmsLayerGroup = (groupId, name) => {
        socket.emit('rename_layer_group', {group_id: groupId, group_name: name}, updateGlobalServiceLayerList);
    };

    const removeWmsLayerGroup = (groupId, parentId) => {
        removeGroupChildrenFromMap(groupId);
        socket.emit('remove_wms_layer_group', {id: groupId, parent_id: parentId}, updateGlobalServiceLayerList);
    };

    const setWmsLayerGroupOpened = (layerGroupId, isOpen) => {
        globalServiceLayerList.value['layer_groups'][layerGroupId]['opened'] = isOpen;
    };

    /**
     * Given the nodeId string and the collection string Array, the function appends the nodeId into the collection
     * if it belongs to a 'layer' type; Otherwise, it traverses to the children of the 'layer_groups' node
     * until no child node is found.
     *
     * @param {string} nodeId jsTree node id
     * @param {string[]} collection The array for collecting nodeId of the layer type.
     */
    const collectLayerNodes = (nodeId, collection) => {
        if (nodeId in globalServiceLayerList.value['layers']) {
            collection.push(nodeId);
        } else {
            for (const childId of globalServiceLayerList.value['layer_groups'][nodeId]['child_ids']) {
                collectLayerNodes(childId, collection);
            }
        }
    };

    /**
     * Returns an array of descendant layer Ids within a node.
     *
     * @param {Object} node jsTree node object
     * @returns {string[]} An array of layer Ids within the given node.
     */
    const getDescendantLayerNodeIds = (node) => {
        const layerNodeIds = [];
        if (node.type.includes('folder')) {
            // node children element can be either layer Id or layer_group Id
            node.children.forEach((nodeId) => {
                collectLayerNodes(nodeId, layerNodeIds);
            });
        }
        return layerNodeIds;
    };

    const setVisibilityWmsLayerGroup = (itemId, isVisible) => {
        if (itemId in globalServiceLayerList.value['layers']) { // for recursive call
            if (isVisible) {
                showLayer(itemId);
            } else {
                hideLayer(itemId);
            }
        } else {
            for (const childId of globalServiceLayerList.value['layer_groups'][itemId]['child_ids']) {
                setVisibilityWmsLayerGroup(childId, isVisible);
            }
        }
    };

    const moveWmsItem = (itemId, oldParentId, newParentId, position) => {
        socket.emit('move_wms_item', {
            item_id: itemId, old_parent_id: oldParentId, new_parent_id: newParentId, position: position
        }, updateGlobalServiceLayerList);
    };

    const copyWmsItem = (itemId, newParentId, position) => {
        socket.emit('copy_wms_item', {
            item_id: itemId, new_parent_id: newParentId, position: position
        }, updateGlobalServiceLayerList);
    };

    return {
        clearWmsLayers,
        getWmsLayerList,
        removeWmsLayer,
        renameWmsLayerGroup,
        addWmsLayerGroup,
        removeWmsLayerGroup,
        setWmsLayerGroupOpened,
        getDescendantLayerNodeIds,
        setVisibilityWmsLayerGroup: setVisibilityWmsLayerGroup,
        moveWmsItem,
        copyWmsItem,
    };
}

const removeLayerFromMapAndVisibleLayers = (layerId) => {
    const layer = globalServiceLayerList.value['layers'][layerId];
    if (layer && layer.layer_ref) {
        map.removeLayer(layer.layer_ref);
    }
    if (layer && layer.legend_url) {
        removeWmsLegend();
    }
    if (layer) {
        layer.visible = false;
    }
    removeLayerFromVisibleLayerGroups(layerId);
};

const createWmsLayerLegend = (url) => {
    let legend_div = L.DomUtil.create('div', 'info legend');
    legend_div.oncontextmenu = L.DomEvent.stopPropagation;
    let legend_title_div = L.DomUtil.create('div', 'legend_title', legend_div);
    legend_title_div.innerHTML += 'Legend';

    const LegendPicture_div = L.DomUtil.create('div', 'info legend', legend_div);
    LegendPicture_div.innerHTML = '<img src="' + url + '" alt="wms legend">';
    return legend_div;
};

let wmsLegend = null;
const showWmsLegend = (url) => {
    if (wmsLegend) {
        map.removeControl(wmsLegend);
    }
    wmsLegend = L.control({position: 'bottomright'});
    wmsLegend.onAdd = function () {
        return createWmsLayerLegend(url);
    };
    wmsLegend.addTo(map);
};

const removeWmsLegend = () => {
    if (wmsLegend) {
        map.removeControl(wmsLegend);
    }
};

const removeGroupChildrenFromMap = (layerGroupId) => {
    const group = globalServiceLayerList.value['layer_groups'][layerGroupId];
    for (const childId of group['child_ids']) {
        if (childId in globalServiceLayerList.value['layer_groups']) {
            removeGroupChildrenFromMap(childId);
        } else if (childId in globalServiceLayerList.value['layers']) {
            const layer = globalServiceLayerList.value['layers'][childId];
            if (layer.layer_ref) {
                map.removeLayer(layer.layer_ref);
            }
            removeLayerFromVisibleLayerGroups(childId);
        }
    }
};

export {
    getServiceBaseUrl,
    getServiceGetCapabilities,
    addServiceLayer,
    updateServiceLayer,
    updateGlobalServiceLayerList,
    constructWfsLayerUrl,
    showLayer,
    hideLayer
};
