import { ref } from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";
import {layerHasContextMenuItem} from "../utils/utils";

const esdlAreas = ref({});

PubSubManager.subscribe(MessageNames.ADD_AREA_TO_LAYER, (name, message) => {
    esdlAreas.value[message.id] = {feature: message.feature, layer: message.layer}
})

export function useEsdlAreas() {
    /**
     * Add context menu items to all known areas.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addAreaContextMenuItem = (text, icon, onclick) => {
        for (const [id, esdlArea] of Object.entries(esdlAreas.value)) {
            const layer = esdlArea.layer;
            if (!layerHasContextMenuItem(layer, text)) {
                layer.options.contextmenuItems.push({
                    text: text,
                    icon: icon,
                    callback: function (e) {
                        // Pass the id of the area to the onclick function.
                        onclick(e, id);
                    },
                });
            }
        }
    }

    /**
     * Remove context menu items in all areas by text.
     * @param {*} text 
     */
    const removeAreaContextMenuItem = (text) => {
        for (const [, esdlArea] of Object.entries(esdlAreas.value)) {
            const layer = esdlArea.layer;
            layer.options.contextmenuItems = layer.options.contextmenuItems.filter(function(contextmenuItem) { 
                return contextmenuItem.text != text;
            });
        }
    }

    return {
        addAreaContextMenuItem,
        esdlAreas: esdlAreas,
        removeAreaContextMenuItem,
    }
}
