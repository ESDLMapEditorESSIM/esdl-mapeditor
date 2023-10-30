/**
 * A composable for managing items currently visible.
 *
 */
import {ref, toValue} from "vue";
import {useVisibleLayers} from "./visibleLayers";

const {getVisibleLayerList, addToVisibleLayerList, removeFromVisibleLayerList} = useVisibleLayers();

const L = window.L;
const map = window.map;
let socket = null;

const globalWmsLayerList = ref([]);
// retrieve wms layers info
(async () => { // wait for socket to be defined
    while (window.socket === undefined)
        await new Promise(resolve => setTimeout(resolve, 10));
    socket = window.socket;
    socket.on('wms_layer_list', function (wmsLayerList) {
        console.log('getting wms layer list');
        globalWmsLayerList.value = wmsLayerList;
        console.log(wmsLayerList)
        for (const key in globalWmsLayerList.value['layers']) {
            const layer_info = globalWmsLayerList.value['layers'][key];
            layer_info.id = key;
            layer_info.layer_ref = L.tileLayer.wms(layer_info.url, {
                layers: layer_info.layer_name,
                format: 'image/png',
                transparent: true,
                attribution: layer_info.attribution
            });
            if (layer_info.visible) {
                layer_info.layer_ref.addTo(map);
                layer_info.layer_ref.bringToFront();
            }
        }
    });
})();

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
            visible: true
        };
        socket.emit('add_wms_layer', wmsLayer);
        addChildToGroup(groupId, layerId);

        globalWmsLayerList.value['layers'][layerId] = wmsLayer;

        globalWmsLayerList.value['layers'][layerId].layer_ref = L.tileLayer.wms(layerUrl, {
            layers: layerName,
            format: 'image/png',
            transparent: true
        });
        showWmsLayer(layerId);
        for (const visibleLayer of getVisibleLayerList()) {
            globalWmsLayerList.value['layers'][visibleLayer.id].visible = true;
        }
    };

    function updateLayer(layerId, layerDescr, layerUrl, layerName, legendUrl, layerattr) {
        socket.emit('save_wms_layer', {
            id: layerId,
            lyr_info: {
                description: layerDescr,
                url: layerUrl,
                layer_name: layerName,
                legend_url: legendUrl,
                attribution: layerattr
            }
        });

        hideWmsLayer(layerId);

        globalWmsLayerList.value['layers'][layerId].layer_ref = L.tileLayer.wms(layerUrl, {
            layers: layerName,
            format: 'image/png',
            transparent: true
        });
        globalWmsLayerList.value['layers'][layerId].description = layerDescr;
        globalWmsLayerList.value['layers'][layerId].url = layerUrl;
        globalWmsLayerList.value['layers'][layerId].layer_name = layerName;
        globalWmsLayerList.value['layers'][layerId].legend_url = legendUrl;
        globalWmsLayerList.value['layers'][layerId].layer_attr = layerattr;

        showWmsLayer(layerId);
        for (const visibleLayer of getVisibleLayerList()) {
            globalWmsLayerList.value['layers'][visibleLayer.id].visible = true;
        }
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
        console.log('hide', globalWmsLayerList.value['layers'][layerId].description)
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        globalWmsLayerList.value['layers'][layerId].visible = false;
        if (globalWmsLayerList.value['layers'][layerId].legend_url !== "") {
            removeWmsLegend();
        }
        removeFromVisibleLayerList(layerId);
    };

    const removeWmsLayer = (layerId) => {
        socket.emit('remove_wms_layer', {id: layerId});
        map.removeLayer(globalWmsLayerList.value['layers'][layerId].layer_ref);
        delete globalWmsLayerList.value['layers'][layerId];
        removeFromVisibleLayerList(layerId);
    }

    const addWmsLayerGroup = (parentId) => {
        const groupId = window.uuidv4();
        const layerGroup = {
            'id': groupId,
            'description': 'new folder',
            'setting_type': 'user',
            'parent_group_id': parentId,
        };
        socket.emit('add_wms_layer_group', layerGroup);
        globalWmsLayerList.value['layer_groups'][groupId] = layerGroup;
        addChildToGroup(parentId, groupId);
    }

    const renameWmsLayerGroup = (groupId, name) => {
        socket.emit('rename_layer_group', {group_id: groupId, group_name: name});
    }

    const removeWmsLayerGroup = (groupId) => {
        socket.emit('remove_wms_layer_group', {id: groupId});
        delete globalWmsLayerList.value['layer_groups'][groupId];
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

const addChildToGroup = (groupId, childId) => {
    socket.emit('add_child_to_layer_group', {group_id: groupId, child_id: childId});
    globalWmsLayerList.value['layer_groups'][groupId]['child_ids'].push(childId);
}
