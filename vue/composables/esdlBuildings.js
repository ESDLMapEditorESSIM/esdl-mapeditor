import { ref } from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";

const esdlBuildings = ref({});

PubSubManager.subscribe(MessageNames.ADD_FEATURE_TO_LAYER, (name, message) => {
    esdlBuildings.value[message.id] = {feature: message.feature, layer: message.layer}
})

export function useEsdlBuildings() {
    /**
     * Add context menu items to all known items.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addContextMenuItem = (text, icon, onclick) => {
        for (const [id, esdlBuilding] of Object.entries(esdlBuildings.value)) {
            const layer = esdlBuilding.layer;
            layer.options.contextmenuItems.push({
                text: text,
                icon: icon,
                callback: function () {
                    onclick(id);
                },
            });
        }
    }

    /**
     * Remove context menu items by text.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const removeContextMenuItem = (text) => {
        for (const [, esdlBuilding] of Object.entries(esdlBuildings.value)) {
            const layer = esdlBuilding.layer;
            console.log(layer.options.contextmenuItems);
            layer.options.contextmenuItems = layer.options.contextmenuItems.filter(function(contextmenuItem) { 
                return contextmenuItem.text != text;
            });
        }
    }

    return {
        addContextMenuItem,
        esdlBuildings,
        removeContextMenuItem,
    }
}
