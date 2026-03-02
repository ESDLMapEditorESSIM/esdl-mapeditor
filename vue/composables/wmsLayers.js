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
import {ref, toValue} from "vue";
import {useVisibleLayers} from "./visibleLayers";

const {addToVisibleLayerList, removeFromVisibleLayerList, layerIsVisible} = useVisibleLayers();

const L = window.L;
const map = window.map;
let socket = null;
const treeId = "layer_tree";
const $ = window.$;
const getTree = () => $('#' + treeId).jstree(true);

const globalServiceLayerList = ref(null);

// retrieve service layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    // TODO: rename wms_layer_list
    socket.on('wms_layer_list', updateGlobalServiceLayerList);
})();

const updateGlobalServiceLayerList = async (layerList, visibleId) => {
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
                layer_info.layer_ref = L.tileLayer.wms(layer_info.url, {
                    layers: layer_info.layer_name,
                    format: 'image/png',
                    transparent: true,
                    attribution: layer_info.attribution || ''
                });
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
                console.error(`Unsupport layer type: ${layer_info.type}`);
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
        }
    }
};

/**
 * Extracts and returns the base URL of the WMS/WFS service.
 * 
 * @param {string} inputUrl The input WMS/WFS URL (possibly with various query parameters)
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

        if (type === 'WMS' && globalServiceLayerList.value['layers'][layerId].legend_url !== "") {
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

        addToVisibleLayerList(layer, 0);
    }
}

const hideLayer = (layerId) => {
    removeLayerFromMapAndVisibleLayers(layerId);
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
 * Load WFS layer features on the map.
 */
const loadWfsLayer = async (layerName, url, style) => {
  window.show_loader();
  try {
    const response = await fetch(url);
    const data = await response.json();

    return L.geoJSON(data, {
      style: () => (style),
      // TODO: show more attributes
      onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Layer:</b> ${layerName}<br><b>ID:</b> ${feature.id}`);
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

    const updateLayer = (layerId, layerDescr, layerUrl, layerName, legendUrl, layerattr, minZoomLevel) => {
        removeLayerFromMapAndVisibleLayers(layerId);
        globalServiceLayerList.value['layers'][layerId].layer_ref = null; // make sure map ref gets updated in updateGlobalServiceLayerList
        socket.emit('save_wms_layer', {
            id: layerId,
            lyr_info: {
                description: layerDescr,
                url: layerUrl,
                layer_name: layerName,
                legend_url: legendUrl,
                attribution: layerattr,
                min_zoom_level: minZoomLevel,
            }
        }, (allLayers) => {
            allLayers['layers'][layerId].visible = true;
            updateGlobalServiceLayerList(allLayers, layerId);
            showLayer(layerId);
        });
    };

    const removeWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalServiceLayerList);
        map.removeLayer(globalServiceLayerList.value['layers'][layerId].layer_ref);
        removeFromVisibleLayerList(layerId);
    };

    const clearWmsLayers = () => {
        for (const [key, value] of Object.entries(globalServiceLayerList.value['layers'])) {
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
        socket.emit('add_wms_layer_group', layerGroup);
        // Create node programmatically to enable entering into edit name mode
        getTree().create_node(parentId, {
            id: groupId,
            text: 'new folder',
            setting_type: setting_type,
            project_name: project_name,
            type: 'wms_layer_folder',
            state: {opened: false},
        });
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
        updateLayer,
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
    map.removeLayer(globalServiceLayerList.value['layers'][layerId].layer_ref);
    if (globalServiceLayerList.value['layers'][layerId].legend_url !== "") {
        removeWmsLegend();
    }
    globalServiceLayerList.value['layers'][layerId].visible = false;
    removeFromVisibleLayerList(layerId);
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
            map.removeLayer(globalServiceLayerList.value['layers'][childId].layer_ref);
            removeFromVisibleLayerList(childId);
        }
    }
};

export {
    getServiceBaseUrl,
    getServiceGetCapabilities,
    addServiceLayer,
    updateGlobalServiceLayerList,
    constructWfsLayerUrl,
    showLayer,
    hideLayer
};