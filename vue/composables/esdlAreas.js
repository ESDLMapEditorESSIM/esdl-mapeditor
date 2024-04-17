import { ref } from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";

const esdlAreas = ref({});

PubSubManager.subscribe(MessageNames.ADD_AREA_TO_LAYER, (name, message) => {
    esdlAreas.value[message.id] = {feature: message.feature, layer: message.layer}
})

export function useEsdlAreas() {
    /**
     * Add context menu items to all known items.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addAreaContextMenuItem = (text, icon, onclick) => {
        if (!hasAreaContextMenuItem(text)) {
            for (const [id, esdlArea] of Object.entries(esdlAreas.value)) {
                const layer = esdlArea.layer;
                layer.options.contextmenuItems.push({
                    text: text,
                    icon: icon,
                    callback: function (e) {
                        onclick(e);
                    },
                });
            }
        }
    }

    /**
     * 
     * @param {*} text 
     */
    const hasAreaContextMenuItem = (text) => {
        for (const [, esdlArea] of Object.entries(esdlAreas.value)) {
            const layer = esdlArea.layer;
            const result = layer.options.contextmenuItems.filter(function(contextmenuItem) { 
                return contextmenuItem.text == text;
            });
            return result.length > 0;
        }
    }

    /**
     * Remove context menu items by text.
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
