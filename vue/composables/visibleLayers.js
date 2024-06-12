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
import {useWmsLayers} from "./wmsLayers";

const {getWmsLayerList} = useWmsLayers()
const globalVisibleLayerList = ref([]);

const map = window.map;
const layerTreeId = "layer_tree";
const $ = window.$;
const getLayerTree = () => $('#' + layerTreeId).jstree(true);

map.on('moveend', function () {
    for (const visibleLayer of globalVisibleLayerList.value) {
        const wms_layer = getWmsLayerList()['layers'][visibleLayer.id];
        if (wms_layer.min_zoom_level) {
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

export function useVisibleLayers() {
    /**
     * Get list of visible layers. This is a list of dictionaries with 'text' and 'type' entries.
     */
    const getVisibleLayerList = () => toValue(globalVisibleLayerList);

    /**
     * Remove visible layer by ID.
     */
    const removeFromVisibleLayerList = (id) => {
        const layerToRemove = globalVisibleLayerList.value.find(
            layer => layer.id === id
        );
        if (layerToRemove !== undefined) {
            globalVisibleLayerList.value.splice(globalVisibleLayerList.value.indexOf(layerToRemove), 1);
        }
        return layerToRemove;
    };

    /**
     * Add visible layer to the list
     */
    const addToVisibleLayerList = (layer, index) => {
        globalVisibleLayerList.value.splice(index, 0, layer);
    };

    /**
     * Update the display order of the visible layers
     */
    const updateDisplayOrderVisibleLayers = (id, newPosition) => {
        const movedlayer = removeFromVisibleLayerList(id);
        addToVisibleLayerList(movedlayer, newPosition);

        globalVisibleLayerList.value.slice().reverse().forEach(
            layer => getWmsLayerList()['layers'][layer.id].layer_ref.bringToFront()
        )
    };

    const layerIsVisible = (layerId) => {
        for (const visibleLayer of globalVisibleLayerList.value) {
            if (visibleLayer.id === layerId) {
                return true;
            }
        }
        return false;
    };

    const hideVisibleLayer = (layerId) => {
        // hide via tree action to also update parent folders three-state
        getLayerTree().uncheck_node(layerId);
    };

    const hideAllVisibleLayers = () => {
         globalVisibleLayerList.value.slice().reverse().forEach(
            layer => hideVisibleLayer(layer.id)
        )
    };

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateDisplayOrderVisibleLayers,
        layerIsVisible,
        hideVisibleLayer,
        hideAllVisibleLayers
    };
}
