/**
 * A composable for managing items currently visible.
 *
 */
import {ref, toValue} from "vue";
import {useWmsLayers} from "./wmsLayers";

const {getWmsLayerList} = useWmsLayers()
const globalVisibleLayerList = ref([]);

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
            element => element.id === id
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
    }

    return {
        getVisibleLayerList,
        removeFromVisibleLayerList,
        addToVisibleLayerList,
        updateDisplayOrderVisibleLayers,
        layerIsVisible
    }
}
