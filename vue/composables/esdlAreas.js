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
                        const callback_info = {
                            id: window.get_area_id_from_mapeditor_id(id),
                            lat: e.latlng.lat.toString(),
                            lng: e.latlng.lng.toString(),
                        };
                        console.log(callback_info);
                        // Pass the id of the area and the mouse coordinates to the onclick function.
                        onclick(e, callback_info);
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
