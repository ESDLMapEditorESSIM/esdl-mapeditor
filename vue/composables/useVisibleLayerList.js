/**
 * A composable for managing items currently visible.
 *
 */
import {ref, toValue} from "vue";

const globalVisibleItemList = ref([]);

export function useVisibleLayerList() {
    /**
     * Get list of visible items. This is a list of dictionaries with 'text' and 'type' entries.
     */
    const getVisibleItemList = () => toValue(globalVisibleItemList);

    /**
     * Remove visible item by ID.
     */
    const removeFromVisibleItemList = (id) => {
        const itemToRemove = globalVisibleItemList.value.find(element => element.text === id);
        globalVisibleItemList.value.splice(globalVisibleItemList.value.indexOf(itemToRemove), 1);
        return itemToRemove;
    };

    /**
     * Add visible item to the list
     */
    const addToVisibleItemList = (item, index) => {
        globalVisibleItemList.value.splice(index, 0, item);
    };

    /**
     * Update the display order of the visible items
     */
    const updateDisplayOrderVisibleItems = (id, newPosition) => {
        const movedItem = removeFromVisibleItemList(id);
        addToVisibleItemList(movedItem, newPosition);

        console.log('update order')
        getVisibleItemList().slice().reverse().forEach(
            // TODO wms layer list to composable
            item => window.wms_layer_list['layers'][item.text].layer_ref.bringToFront()
        )
    };

    return {
        getVisibleItemList,
        removeFromVisibleItemList,
        addToVisibleItemList,
        updateDisplayOrderVisibleItems
    }
}
