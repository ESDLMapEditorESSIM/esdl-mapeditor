import { ref } from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";

const esdlBuildings = ref({});

PubSubManager.subscribe(MessageNames.ADD_BUILDING_TO_LAYER, (name, message) => {
    esdlBuildings.value[message.id] = {feature: message.feature, layer: message.layer}
})

export function useEsdlBuildings() {
    /**
     * Add context menu items to all known items.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addBuildingContextMenuItem = (text, icon, onclick) => {
        if (!hasBuildingContextMenuItem(text)) {
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
    }

    /**
     * 
     * @param {*} text 
     */
    const hasBuildingContextMenuItem = (text) => {
        for (const [, esdlBuilding] of Object.entries(esdlBuildings.value)) {
            const layer = esdlBuilding.layer;
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
    const removeBuildingContextMenuItem = (text) => {
        console.log("Removing context menu items")
        for (const [, esdlBuilding] of Object.entries(esdlBuildings.value)) {
            const layer = esdlBuilding.layer;
            layer.options.contextmenuItems = layer.options.contextmenuItems.filter(function(contextmenuItem) { 
                return contextmenuItem.text != text;
            });
        }
    }

    return {
        addBuildingContextMenuItem,
        esdlBuildings,
        removeBuildingContextMenuItem,
    }
}
