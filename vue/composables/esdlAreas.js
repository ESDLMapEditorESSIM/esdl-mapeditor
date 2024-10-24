import { ref } from "vue";
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

PubSubManager.subscribe(MessageNames.ADD_AREA_TO_LAYER, (name, message) => {
    if (!esdlAreasDict.value[message.id]) {
        esdlAreasDict.value[message.id] = [];
    }
    esdlAreasDict.value[message.id].push({feature: message.feature, layer: message.layer})
})

export function useEsdlAreas() {
    /**
     * Add context menu items to all known areas.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addAreaContextMenuItem = (text, icon, onclick) => {
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

    return {
        addAreaContextMenuItem,
        esdlAreasDict,
        removeAreaContextMenuItem,
    }
}
