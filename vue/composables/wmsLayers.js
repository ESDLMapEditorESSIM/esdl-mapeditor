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
import {useVisibleLayers} from "./visibleLayers";

const {addToVisibleLayerList, createVisibleLayerGroup, removeFromVisibleLayerList, layerIsVisible} = useVisibleLayers();

export const WMS_LAYERS_GROUP_NAME = 'wms_layers';

const L = window.L;
const map = window.map;
let socket = null;
const treeId = "layer_tree";
const $ = window.$;
const getTree = () => $('#' + treeId).jstree(true);

// The list of all WMS layers available for the user.
const globalWmsLayerList = ref(null);

// retrieve wms layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    socket.on('wms_layer_list', updateGlobalWmsLayerList);
})();

/**
 * Updates the global WMS layer list with the provided list of layers.
 * @param wmsLayerList
 * @param visibleId
 */
const updateGlobalWmsLayerList = (wmsLayerList, visibleId) => {
    if (globalWmsLayerList.value !== null) {
        for (const layerId in globalWmsLayerList.value['layers']) {
            if (layerId in wmsLayerList['layers']) {
                // make sure not to lose the map reference
                wmsLayerList['layers'][layerId].layer_refs = globalWmsLayerList.value['layers'][layerId].layer_refs;
            } else {
                // hide layer present in global (old) list, but not in new list from database: was deleted
                removeLayerFromMapAndVisibleLayers(layerId);
            }
        }
        for (const layerGroupId in globalWmsLayerList.value['layer_groups']) {
            if (layerGroupId in wmsLayerList['layer_groups']) {
                // make sure opened folders stay open
                if ('opened' in globalWmsLayerList.value['layer_groups'][layerGroupId]) {
                    wmsLayerList['layer_groups'][layerGroupId].opened =
                        globalWmsLayerList.value['layer_groups'][layerGroupId]['opened'];
                } else {
                    wmsLayerList['layer_groups'][layerGroupId].opened = false;
                }
            }
        }
    }

    globalWmsLayerList.value = wmsLayerList;
    for (const key in globalWmsLayerList.value['layers']) {
        const layer_info = globalWmsLayerList.value['layers'][key];
        layer_info.id = key;
        if (!layer_info.layer_refs) {
            layer_info.layer_refs = [L.tileLayer.wms(layer_info.url, {
                layers: layer_info.layer_name,
                format: 'image/png',
                transparent: true,
                opacity: 0.7,
                attribution: layer_info.attribution
            })];
        }
        layer_info.visible = layerIsVisible(layer_info.id);
        if (visibleId !== undefined) {
            if (layer_info.id === visibleId) {
                layer_info.visible = true;
            }
        }
        if (layer_info.visible) {
            layer_info.layer_refs.forEach(layerRef => {
                layerRef.addTo(map);
                layerRef.bringToFront();
            });
        }
    }
};

/**
 * Extracts and returns the base URL of the WMS service.
 *
 * @param {string} inputUrl The input WMS URL (possibly with various query parameters)
 * @returns {string|Error} The base URL of the WMS service if valid, otherwise an Error object.
 */
const getWmsServiceBaseUrl = (inputUrl) => {
    try {
        const url = new URL(inputUrl);
        return `${url.origin}${url.pathname}`;
    } catch (error) {
        return new Error(`${error}`);
    }
};


export function useWmsLayers() {
    /**
     * Get the wms layer list.
     */
    const getWmsLayerList = () => toValue(globalWmsLayerList);

    /**
     * Fetches and returns the WMS GetCapabilities response into a wmsGetCapabilitiesResp object,
     * which has a structure as {success: boolean, result: WmsServiceLayerInfo[] | string}.
     *
     * @param {string} wmsBaseUrl The base URL of the WMS service.
     * @returns {Promise<Object>} A promise that resolves to a wmsGetCapabilitiesResp object.
     * @throws {Error} Throws an error if the get_wms_getcapabilities call fails.
     */
    const getWmsGetCapabilities = async (wmsBaseUrl) => {
        const params = {
            url: wmsBaseUrl
        };
        return new Promise((resolve, reject) => {
            socket.emit('get_wms_getcapabilities', params, (wmsGetCapabilitiesResp) => {
                if (wmsGetCapabilitiesResp) {
                    resolve(wmsGetCapabilitiesResp);
                } else {
                    reject(new Error(`An unknown error occurred while fetching WMS GetCapabilities ${wmsBaseUrl}.`));
                }
            });
        });
    };

    /**
     * Add a WMS layer
     *
     * @returns {Promise<Object>} A promise of allLayers object ({layers: {}, layer_groups: {}}) that resolves if the layer is added successfully,
     *                            or rejects with an error if the addition fails.
     * @throws {Error} If the backend response indicates a failure to add the layer.
     */
    const addWmsLayer = async (layerId, layerDescr, layerUrl, layerName, legendUrl, layerAttr, minZoomLevel, projectName, settingtype, groupId) => {
        const wmsLayer = {
            id: layerId,
            description: layerDescr,
            url: layerUrl,
            name: layerName,
            setting_type: settingtype,
            project_name: projectName,
            legend_url: legendUrl,
            min_zoom_level: minZoomLevel,
            parent_group_id: groupId,
        };
        return new Promise((resolve, reject) => {
            socket.emit('add_wms_layer', wmsLayer, (allLayers) => {
                if (allLayers) {
                    resolve(allLayers);
                } else {
                    reject(new Error(`An unknown error occurred while adding the WMS layer ${layerName}.`));
                }
            });
        });
    };

    const updateLayer = (layerId, layerDescr, layerUrl, layerName, legendUrl, layerattr, minZoomLevel) => {
        deactivateWmsLayer(layerId);
        globalWmsLayerList.value['layers'][layerId].layer_refs = null; // make sure map ref gets updated in updateGlobalWmsLayerList
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
            updateGlobalWmsLayerList(allLayers, layerId);
            showWmsLayer(layerId);
        });
    };

    const showWmsLayer = (layerId) => {
        const wms_layer = globalWmsLayerList.value['layers'][layerId];
        if (!layerIsVisible(layerId)) {
            if (!wms_layer.min_zoom_level || (wms_layer.min_zoom_level && map.getZoom() >= wms_layer.min_zoom_level)) {
                wms_layer.visible = true;
                wms_layer.layer_refs.forEach(layerRef => {
                    layerRef.addTo(map);
                    layerRef.bringToFront();
                    if (wms_layer.opacity !== undefined) {
                        layerRef.setOpacity(wms_layer.opacity);
                    }
                });
            }
            if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
                showWmsLegend(wms_layer.legend_url);
            }
            createVisibleLayerGroup(WMS_LAYERS_GROUP_NAME, "WMS Layers");
            addToVisibleLayerList(wms_layer, "wms_layers");
        }
    };

    const hideWmsLayer = (layerId) => {
        removeLayerFromMap(layerId);
    };

    const deactivateWmsLayer = (layerId) => {
        removeLayerFromMapAndVisibleLayers(layerId);
    };

    const deleteWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalWmsLayerList);
        const layer = globalWmsLayerList.value['layers'][layerId];
        layer.layer_refs.forEach(layerRef => {
            map.removeLayer(layerRef);
        });
        removeFromVisibleLayerList(layerId);
    };

    const clearWmsLayers = () => {
        for (const [key,] of Object.entries(globalWmsLayerList.value['layers'])) {
            deactivateWmsLayer(key)
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
        socket.emit('rename_layer_group', {group_id: groupId, group_name: name}, updateGlobalWmsLayerList);
    };

    const removeWmsLayerGroup = (groupId, parentId) => {
        removeGroupChildrenFromMap(groupId);
        socket.emit('remove_wms_layer_group', {id: groupId, parent_id: parentId}, updateGlobalWmsLayerList);
    };

    const setWmsLayerGroupOpened = (layerGroupId, isOpen) => {
        globalWmsLayerList.value['layer_groups'][layerGroupId]['opened'] = isOpen;
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
        if (nodeId in globalWmsLayerList.value['layers']) {
            collection.push(nodeId);
        } else {
            for (const childId of globalWmsLayerList.value['layer_groups'][nodeId]['child_ids']) {
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
        if (itemId in globalWmsLayerList.value['layers']) { // for recursive call
            if (isVisible) {
                showWmsLayer(itemId);
            } else {
                deactivateWmsLayer(itemId);
            }
        } else {
            for (const childId of globalWmsLayerList.value['layer_groups'][itemId]['child_ids']) {
                setVisibilityWmsLayerGroup(childId, isVisible);
            }
        }
    };

    const moveWmsItem = (itemId, oldParentId, newParentId, position) => {
        socket.emit('move_wms_item', {
            item_id: itemId, old_parent_id: oldParentId, new_parent_id: newParentId, position: position
        }, updateGlobalWmsLayerList);
    };

    const copyWmsItem = (itemId, newParentId, position) => {
        socket.emit('copy_wms_item', {
            item_id: itemId, new_parent_id: newParentId, position: position
        }, updateGlobalWmsLayerList);
    };


    return {
        clearWmsLayers,
        getWmsLayerList,
        addWmsLayer,
        updateLayer,
        showWmsLayer,
        hideWmsLayer,
        deactivateWmsLayer,
        deleteWmsLayer,
        renameWmsLayerGroup,
        addWmsLayerGroup,
        removeWmsLayerGroup,
        setWmsLayerGroupOpened,
        getDescendantLayerNodeIds,
        setVisibilityWmsLayerGroup,
        moveWmsItem,
        copyWmsItem,
        getWmsGetCapabilities,
    };
}

const removeLayerFromMap = (layerId) => {
    const layer = globalWmsLayerList.value['layers'][layerId];
    layer.layer_refs.forEach(layer_ref => {
        map.removeLayer(layer_ref);
    });
    if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
        removeWmsLegend();
    }
    globalWmsLayerList.value['layers'][layerId].visible = false;
};

const removeLayerFromMapAndVisibleLayers = (layerId) => {
    removeLayerFromMap(layerId);
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
    const group = globalWmsLayerList.value['layer_groups'][layerGroupId];
    for (const childId of group['child_ids']) {
        if (childId in globalWmsLayerList.value['layer_groups']) {
            removeGroupChildrenFromMap(childId);
        } else if (childId in globalWmsLayerList.value['layers']) {
            const layer = globalWmsLayerList.value['layers'][childId];
            layer.layer_refs.forEach(layerRef => {
                map.removeLayer(layerRef);
            });
            removeFromVisibleLayerList(childId);
        }
    }
};

export {
    getWmsServiceBaseUrl,
    updateGlobalWmsLayerList
};