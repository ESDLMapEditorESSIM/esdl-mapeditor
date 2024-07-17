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

const {addToVisibleLayerList, removeFromVisibleLayerList, layerIsVisible} = useVisibleLayers();

const L = window.L;
const map = window.map;
let socket = null;
const treeId = "layer_tree";
const $ = window.$;
const getTree = () => $('#' + treeId).jstree(true);

const globalWmsLayerList = ref(null);
// retrieve wms layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    socket.on('wms_layer_list', updateGlobalWmsLayerList);
})();

const updateGlobalWmsLayerList = (wmsLayerList, visibleId) => {
    if (globalWmsLayerList.value !== null) {
        for (const layerId in globalWmsLayerList.value['layers']) {
            if (layerId in wmsLayerList['layers']) {
                // make sure not to lose the map reference
                wmsLayerList['layers'][layerId].layer_ref = globalWmsLayerList.value['layers'][layerId].layer_ref;
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
        if (!layer_info.layer_ref) {
            layer_info.layer_ref = L.tileLayer.wms(layer_info.url, {
                layers: layer_info.layer_name,
                format: 'image/png',
                transparent: true,
                attribution: layer_info.attribution
            });
        }
        layer_info.visible = layerIsVisible(layer_info.id);
        if (visibleId !== undefined) {
            if (layer_info.id === visibleId) {
                layer_info.visible = true;
            }
        }
        if (layer_info.visible) {
            layer_info.layer_ref.addTo(map);
            layer_info.layer_ref.bringToFront();
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

/**
 * Parses a WMS GetCapabilities XML string and extracts layer information. 
 * 
 * It returns an array of layerInfo objects. Each layerInfo object contains the
 * `name`, `title`, and `legendUrl` properties. If a layer does not have a
 * legend URL, the `legendUrl` will be an empty string.
 * 
 * @param {string} xmlString The XML string of the WMS GetCapabilities document.
 * @returns {Array<Object>} An array of layerInfo objects, each with `name`,
 *                         `title`, and `legendUrl` properties.
 */
const parseXML = (xmlString) => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "text/xml");
    const layers = xmlDoc.getElementsByTagName("Layer");
    let layerOptions = [];
    Array.from(layers).forEach((layer) => {
        const layerName = layer.getElementsByTagName("Name")[0]?.textContent;
        const layerTitle = layer.getElementsByTagName("Title")[0]?.textContent;
        
        // Extract legend URL
        let legendUrl = null;
        const styles = layer.getElementsByTagName("Style");
        if (styles.length > 0) {
            // NOTE: the current implementation default to use the first style
            const legendURL = styles[0].getElementsByTagName("LegendURL");
            if (legendURL.length > 0) {
                const onlineResource = legendURL[0].getElementsByTagName("OnlineResource")[0];
                legendUrl = onlineResource?.getAttribute("xlink:href");
            }
        }

        // To avoid possible duplicates being added to the layerOptions
        if (layerName && !layerOptions.map((l) => l.name).includes(layerName)) {
            const layerInfo = {
                name: layerName,
                title: layerTitle,
                legendUrl: legendUrl || "",
            };
            layerOptions.push(layerInfo);
        }
    });
    return layerOptions;
};

export function useWmsLayers() {
    /**
     * Get the wms layer list.
     */
    const getWmsLayerList = () => toValue(globalWmsLayerList);

    /**
     * Fetches and returns the WMS GetCapabilities document as an array of layerInfo objects.
     * 
     * @param {string} wmsBaseUrl The base URL of the WMS service.
     * @returns {Promise<Array<Object>>} A promise that resolves to an array of layerInfo objects.
     * @throws {Error} Throws an error if the fetch operation fails or returns a non-OK status.
     */
    const getWmsGetCapabilities = async (wmsBaseUrl) => {
        const url = `${wmsBaseUrl}?service=WMS&request=GetCapabilities`;
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`[${resp.statusText}] Error fetching WMS GetCapabilities.`);
        } else {
            const wmsCapabilitiesXML = await resp.text();
            const layerOptions = parseXML(wmsCapabilitiesXML);
            return layerOptions;
        }
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
        removeLayerFromMapAndVisibleLayers(layerId);
        globalWmsLayerList.value['layers'][layerId].layer_ref = null; // make sure map ref gets updated in updateGlobalWmsLayerList
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
                wms_layer.layer_ref.addTo(map);
                wms_layer.layer_ref.bringToFront();
                wms_layer.visible = true;
            }
            if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
                showWmsLegend(wms_layer.legend_url);
            }
            addToVisibleLayerList(wms_layer, 0);
        }
    };

    const hideWmsLayer = (layerId) => {
        removeLayerFromMapAndVisibleLayers(layerId);
    };

    const removeWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalWmsLayerList);
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        removeFromVisibleLayerList(layerId);
    };

    const clearWmsLayers = () => {
        for (const [key, value] of Object.entries(globalWmsLayerList.value['layers'])) {
            hideWmsLayer(key)
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

    const setVisibilityWmsLayerGroup = (itemId, isVisible) => {
        if (itemId in globalWmsLayerList.value['layers']) { // for recursive call
            if (isVisible) {
                showWmsLayer(itemId);
            } else {
                hideWmsLayer(itemId);
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
        removeWmsLayer,
        renameWmsLayerGroup,
        addWmsLayerGroup,
        removeWmsLayerGroup,
        setWmsLayerGroupOpened,
        setVisibilityWmsLayerGroup: setVisibilityWmsLayerGroup,
        moveWmsItem,
        copyWmsItem,
        getWmsGetCapabilities,
    };
}

const removeLayerFromMapAndVisibleLayers = (layerId) => {
    map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
    if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
        removeWmsLegend();
    }
    globalWmsLayerList.value['layers'][layerId].visible = false;
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
            map.removeLayer(globalWmsLayerList.value['layers'][childId].layer_ref);
            removeFromVisibleLayerList(childId);
        }
    }
};

export {
    getWmsServiceBaseUrl,
    updateGlobalWmsLayerList
};