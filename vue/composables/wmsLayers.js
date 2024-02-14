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
    console.log('getting wms layer list');
    console.log(wmsLayerList);

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

export function useWmsLayers() {
    /**
     * Get the wms layer list.
     */
    const getWmsLayerList = () => toValue(globalWmsLayerList);

    const addWmsLayer = (layerDescr, layerUrl, layerName, legendUrl, layerAttr, projectName, settingtype, groupId) => {
        /**
         * Add wms layer
         */
        const layerId = window.uuidv4();

        const wmsLayer = {
            id: layerId,
            description: layerDescr,
            url: layerUrl,
            name: layerName,
            setting_type: settingtype,
            project_name: projectName,
            legend_url: legendUrl,
            parent_group_id: groupId,
        };
        socket.emit('add_wms_layer', wmsLayer, (allLayers) => {
            allLayers['layers'][layerId].visible = true;
            updateGlobalWmsLayerList(allLayers, layerId);
            showWmsLayer(layerId);
        });
    };

    const updateLayer = (layerId, layerDescr, layerUrl, layerName, legendUrl, layerattr) => {
        removeLayerFromMapAndVisibleLayers(layerId);
        globalWmsLayerList.value['layers'][layerId].layer_ref = null; // make sure map ref gets updated in updateGlobalWmsLayerList
        socket.emit('save_wms_layer', {
            id: layerId, lyr_info: {
                description: layerDescr,
                url: layerUrl,
                layer_name: layerName,
                legend_url: legendUrl,
                attribution: layerattr
            }
        }, (allLayers) => {
            allLayers['layers'][layerId].visible = true;
            updateGlobalWmsLayerList(allLayers, layerId);
            showWmsLayer(layerId);
        });
    };

    const showWmsLayer = (layerId) => {
        globalWmsLayerList.value['layers'][layerId].layer_ref.addTo(map);
        globalWmsLayerList.value['layers'][layerId].layer_ref.bringToFront();
        if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
            showWmsLegend(globalWmsLayerList.value['layers'][layerId].legend_url);
        }
        addToVisibleLayerList(globalWmsLayerList.value['layers'][layerId], 0);
    };

    const hideWmsLayer = (layerId) => {
        removeLayerFromMapAndVisibleLayers(layerId);
    };

    const removeWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalWmsLayerList);
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        removeFromVisibleLayerList(layerId);
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

    const moveWmsItem = (itemId, oldParentId, newParentId, position) => {
        socket.emit('move_wms_item', {
            item_id: itemId, old_parent_id: oldParentId, new_parent_id: newParentId, position: position
        });
    };

    const copyWmsItem = (itemId, newParentId, position) => {
        socket.emit('copy_wms_item', {
            item_id: itemId,
            new_parent_id: newParentId,
            position: position
        }, updateGlobalWmsLayerList);
    };

    return {
        getWmsLayerList,
        addWmsLayer,
        updateLayer,
        showWmsLayer,
        hideWmsLayer,
        removeWmsLayer,
        renameWmsLayerGroup,
        addWmsLayerGroup,
        removeWmsLayerGroup,
        moveWmsItem,
        copyWmsItem
    };
}

const removeLayerFromMapAndVisibleLayers = (layerId) => {
    map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
    if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
        removeWmsLegend();
    }
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
        if (childId in globalWmsLayerList.value['layer_groups'][layerGroupId]) {
            removeGroupChildrenFromMap((childId));
        } else if (childId in globalWmsLayerList.value['layers']) {
            map.removeLayer(globalWmsLayerList.value['layers'][childId].layer_ref);
            removeFromVisibleLayerList(childId);
        }
    }
};
