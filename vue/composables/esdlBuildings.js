import { ref } from "vue";
import { PubSubManager, MessageNames } from "../bridge.js";
import {layerHasContextMenuItem} from "../utils/utils";

const esdlBuildings = ref({});

PubSubManager.subscribe(MessageNames.ADD_BUILDING_TO_LAYER, (name, message) => {
    esdlBuildings.value[message.id] = {feature: message.feature, layer: message.layer}
})

export function useEsdlBuildings() {
    /**
     * Add context menu items to all known buildings.
     * @param {*} text 
     * @param {*} icon 
     * @param {*} onclick 
     */
    const addBuildingContextMenuItem = (text, icon, onclick) => {
        for (const [id, esdlBuilding] of Object.entries(esdlBuildings.value)) {
            const layer = esdlBuilding.layer;
            if (!layerHasContextMenuItem(layer, text)) {
                layer.options.contextmenuItems.push({
                    text: text,
                    icon: icon,
                    callback: function (e) {
                        onclick(e, id);
                    },
                });
            }
        }
    }

    /**
     * Remove context menu items in all buildings by text.
     * @param {*} text 
     */
    const removeBuildingContextMenuItem = (text) => {
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
