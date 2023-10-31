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
const treeId = "layer_tree"
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);

const globalWmsLayerList = ref([]);
// retrieve wms layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    socket.on('wms_layer_list', updateGlobalWmsLayerList);
})();

const updateGlobalWmsLayerList = (wmsLayerList, visibleId) => {
    console.log('getting wms layer list');
    globalWmsLayerList.value = wmsLayerList;
    for (const key in globalWmsLayerList.value['layers']) {
        const layer_info = globalWmsLayerList.value['layers'][key];
        layer_info.id = key;
        layer_info.layer_ref = L.tileLayer.wms(layer_info.url, {
            layers: layer_info.layer_name, format: 'image/png', transparent: true, attribution: layer_info.attribution
        });
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
}

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
            console.log(allLayers)
            console.log(layerId)
            allLayers['layers'][layerId].visible = true;
            console.log(allLayers)
            updateGlobalWmsLayerList(allLayers, layerId);
            showWmsLayer(layerId);
        });

    };

    function updateLayer(layerId, layerDescr, layerUrl, layerName, legendUrl, layerattr) {
        hideWmsLayer(layerId);
        // addToVisibleLayerList(layerId); // make sure that the layer is checked
        socket.emit('save_wms_layer', {
            id: layerId, lyr_info: {
                description: layerDescr,
                url: layerUrl,
                layer_name: layerName,
                legend_url: legendUrl,
                attribution: layerattr
            }
        }, (allLayers) => {
            console.log(allLayers)
            allLayers['layers'][layerId].visible = true;
            updateGlobalWmsLayerList(allLayers);
            showWmsLayer(layerId);
        });
    }

    const showWmsLayer = (layerId) => {
        globalWmsLayerList.value['layers'][layerId].layer_ref.addTo(map);
        globalWmsLayerList.value['layers'][layerId].layer_ref.bringToFront();
        if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
            showWmsLegend(globalWmsLayerList.value['layers'][layerId].legend_url);
        }
        addToVisibleLayerList(globalWmsLayerList.value['layers'][layerId], 0);
    };

    const hideWmsLayer = (layerId) => {
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        // globalWmsLayerList.value['layers'][layerId].visible = false;
        if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
            removeWmsLegend();
        }
        removeFromVisibleLayerList(layerId);
    };

    const removeWmsLayer = (layerId, parentId) => {
        socket.emit('remove_wms_layer', {id: layerId, parent_id: parentId}, updateGlobalWmsLayerList);
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        removeFromVisibleLayerList(layerId);
    }

    const addWmsLayerGroup = (parentId) => {
        const groupId = window.uuidv4();
        const layerGroup = {
            'id': groupId, 'description': 'new folder', 'setting_type': 'user', 'parent_group_id': parentId,
        };
        socket.emit('add_wms_layer_group', layerGroup);
        // globalWmsLayerList.value['layer_groups'][groupId] = layerGroup;
        // globalWmsLayerList.value['layer_groups'][parentId]['child_ids'].push(groupId);
        getTree().create_node(parentId, {
            id: groupId,
            text: 'new folder',
            setting_type: 'user',
            type: 'wms_layer_folder',
            state: { opened: true},
        });
    }

    const renameWmsLayerGroup = (groupId, name) => {
        socket.emit('rename_layer_group', {group_id: groupId, group_name: name}, updateGlobalWmsLayerList);
    }

    const removeWmsLayerGroup = (groupId, parentId) => {
        socket.emit('remove_wms_layer_group', {id: groupId, parent_id: parentId}, updateGlobalWmsLayerList);
    }

    const moveWmsItem = (itemId, oldParentId, newParentId) => {
        socket.emit('move_wms_item', {
            item_id: itemId, old_parent_id: oldParentId, new_parent_id: newParentId
        });
    }

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
        moveWmsItem
    };
}

const createWmsLayerLegend = (url) => {
    let legend_div = L.DomUtil.create('div', 'info legend');
    legend_div.oncontextmenu = L.DomEvent.stopPropagation;
    let legend_title_div = L.DomUtil.create('div', 'legend_title', legend_div);
    legend_title_div.innerHTML += 'Legend';

    const LegendPicture_div = L.DomUtil.create('div', 'info legend', legend_div);
    LegendPicture_div.innerHTML = '<img src="' + url + '" alt="wms legend">'
    return legend_div;
}

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
}

const removeWmsLegend = () => {
    if (wmsLegend) {
        map.removeControl(wmsLegend);
    }
}
