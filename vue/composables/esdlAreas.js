import {computed, ref} from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";
import {layerHasContextMenuItem} from "../utils/utils";

/**
 * @typedef {Object} EsdlArea
 * @property {Object} feature
 * @property {Object} layer
 */

// The esdlAreas object is a dictionary with the layer id as key and an array of areas as value.
// The areas are objects with a feature and a layer property.
// The reason that the areas are stored in an array is that the area ID is not unique.
const esdlAreasDict = ref({});

/**
 * Add an area to the esdlAreasDict. The esdlAreasDict is a dictionary with the layer id as key and an array of areas as value.
 * The areas are objects with a feature and a layer property.
 * @param id
 * @param feature
 * @param layer
 */
const addEsdlArea = (id, feature, layer) => {
    if (!esdlAreasDict.value[id]) {
        esdlAreasDict.value[id] = [];
    }
    esdlAreasDict.value[id].push({feature: feature, layer: layer})
}

/**
 * The total number of entries and areas in the esdlAreasDict.
 * @type {import('vue').ComputedRef<number>}
 */
const totalEntriesAndAreas = computed(() => {
    return Object.values(esdlAreasDict.value).reduce(
        (acc, areas) => acc + areas.length,
        Object.keys(esdlAreasDict.value).length
    );
});

export function useEsdlAreas() {
    PubSubManager.subscribe(MessageNames.ADD_AREA_TO_LAYER, (name, message) => {
        addEsdlArea(message.id, message.feature, message.layer);
    })

    /**
     * Add context menu items to all known areas.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     * @param {*} allow_multiple
     */
    const addAreaContextMenuItem = (text, icon, onclick, allow_multiple) => {
        for (const [id, esdlAreas] of Object.entries(esdlAreasDict.value)) {
            for (const esdlArea of esdlAreas) {
                const layer = esdlArea.layer;
                if (!layerHasContextMenuItem(layer, text)) {
                    layer.options.contextmenuItems.push({
                        text: text,
                        icon: icon,
                        callback: function (e) {
                            const callback_info = {
                                id: window.get_area_id_from_mapeditor_id(id),
                                lat: e.latlng.lat.toString(),
                                lng: e.latlng.lng.toString(),
                            };
                            // Pass the id of the area and the mouse coordinates to the onclick function.
                            onclick(e, callback_info);
                        },
                        extra_options: {
                            allow_multiple: allow_multiple,
                        }
                    });
                }
            }
        }
    }

    /**
     * Remove context menu items in all areas by text.
     * @param {*} text 
     */
    const removeAreaContextMenuItem = (text) => {
        for (const [, esdlAreas] of Object.entries(esdlAreasDict.value)) {
            for (const esdlArea of esdlAreas) {
                const layer = esdlArea.layer;
                layer.options.contextmenuItems = layer.options.contextmenuItems.filter(function (contextmenuItem) {
                    return contextmenuItem.text != text;
                });
            }
        }
    }

    const saveAreaContextMenuState = () => {
        console.log("save");
        for (const [, esdlAreas] of Object.entries(esdlAreasDict.value)) {
            for (const esdlArea of esdlAreas) {
                const layer = esdlArea.layer;
                // somehow this function is called twice, for now solve it like this
                if ((layer.backupContextMenuItems === null) || (layer.backupContextMenuItems === undefined)) {
                    layer.backupContextMenuItems = [...layer.options.contextmenuItems];
                    layer.options.contextmenuItems = [];
                }
            }
        }
    }

    const restoreAreaContextMenuState = () => {
        console.log("restore");
        for (const [, esdlAreas] of Object.entries(esdlAreasDict.value)) {
            for (const esdlArea of esdlAreas) {
                const layer = esdlArea.layer;
                if ((layer.backupContextMenuItems !== null) && (layer.backupContextMenuItems !== undefined)) {
                    layer.options.contextmenuItems = [...layer.backupContextMenuItems];
                    layer.backupContextMenuItems = null;
                }
            }
        }
    }

    return {
        addAreaContextMenuItem,
        esdlAreasDict,
        totalEntriesAndAreas,
        removeAreaContextMenuItem,
        saveAreaContextMenuState,
        restoreAreaContextMenuState
    }
}
