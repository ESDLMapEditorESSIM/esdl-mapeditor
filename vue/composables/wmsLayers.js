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

    const addWmsLayer = (layer_descr, layer_url, layer_name, legend_url, layer_attr, project_name, setting_type) => {
        /**
         * Add wms layer
         */
        const layer_id = window.uuidv4();

        socket.emit('add_wms_layer', {
            id: layer_id,
            descr: layer_descr,
            url: layer_url,
            name: layer_name,
            setting_type: setting_type,
            project_name: project_name,
            legend_url: legend_url,
            visible: true
        });

        globalWmsLayerList.value['layers'][layer_id] = {
            id: layer_id,
            description: layer_descr,
            url: layer_url,
            legend_url: legend_url,
            layer_name: layer_name,
            setting_type: setting_type,
            project_name: project_name
        };

        globalWmsLayerList.value['layers'][layer_id].layer_ref = L.tileLayer.wms(layer_url, {
            layers: layer_name,
            format: 'image/png',
            transparent: true
        });
        showWmsLayer(layer_id);
        for (const visibleLayer of getVisibleLayerList()) {
            globalWmsLayerList.value['layers'][visibleLayer.id].visible = true;
        }
    };

    function updateLayer(layer_id, layer_descr, layer_url, layer_name, legend_url, layer_attr) {
        socket.emit('save_wms_layer', {
            id: layer_id,
            lyr_info: {
                description: layer_descr,
                url: layer_url,
                layer_name: layer_name,
                legend_url: legend_url,
                attribution: layer_attr
            }
        });

        hideWmsLayer(layer_id);

        globalWmsLayerList.value['layers'][layer_id].layer_ref = L.tileLayer.wms(layer_url, {
            layers: layer_name,
            format: 'image/png',
            transparent: true
        });
        globalWmsLayerList.value['layers'][layer_id].description = layer_descr;
        globalWmsLayerList.value['layers'][layer_id].url = layer_url;
        globalWmsLayerList.value['layers'][layer_id].layer_name = layer_name;
        globalWmsLayerList.value['layers'][layer_id].legend_url = legend_url;
        globalWmsLayerList.value['layers'][layer_id].layer_attr = layer_attr;

        showWmsLayer(layer_id);
        for (const visibleLayer of getVisibleLayerList()) {
            globalWmsLayerList.value['layers'][visibleLayer.id].visible = true;
        }
    }

    const showWmsLayer = (layer_id) => {
        console.log(globalWmsLayerList.value['layers'][layer_id].layer_ref.addTo(map))
        globalWmsLayerList.value['layers'][layer_id].layer_ref.bringToFront();
        if (globalWmsLayerList.value['layers'][layer_id].legend_url !== "") {
            showWmsLegend(globalWmsLayerList.value['layers'][layer_id].legend_url);
        }
        addToVisibleLayerList(globalWmsLayerList.value['layers'][layer_id], 0);
    };

    const hideWmsLayer = (layer_id) => {
        console.log('hide', globalWmsLayerList.value['layers'][layer_id].description)
        map.removeLayer(globalWmsLayerList.value['layers'][layer_id].layer_ref);
        globalWmsLayerList.value['layers'][layer_id].visible = false;
        if (globalWmsLayerList.value['layers'][layer_id].legend_url !== "") {
            removeWmsLegend();
        }
        removeFromVisibleLayerList(layer_id);
    };

    const removeWmsLayer = (layer_id) => {
        socket.emit('remove_wms_layer', {id: layer_id});
        map.removeLayer(globalWmsLayerList.value['layers'][layer_id].layer_ref);
        delete globalWmsLayerList.value['layers'][layer_id];
        removeFromVisibleLayerList(layer_id);
    }

    return {
        getWmsLayerList,
        addWmsLayer,
        updateLayer,
        showWmsLayer,
        hideWmsLayer,
        removeWmsLayer,
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
