import { PubSubManager, MessageNames } from "../bridge.js";
import {layerHasContextMenuItem} from "../utils/utils";

const buildingContextMenuItems = new Map();

const addContextMenuItemToLayer = (layer, id, esId, text, icon, onclick) => {
    if (layerHasContextMenuItem(layer, text)) {
        return;
    }

    layer.options.contextmenuItems.push({
        text: text,
        icon: icon,
        callback: function (event) {
            onclick(id, esId, event);
        },
    });
}

const removeContextMenuItemFromLayer = (layer, text) => {
    layer.options.contextmenuItems = layer.options.contextmenuItems.filter(function(contextmenuItem) {
        return contextmenuItem.text != text;
    });
}

const visitBuildingLayers = (layer, callback) => {
    if (!layer) {
        return;
    }

    if (layer.mapeditor_layer_type === 'building') {
        callback(layer, layer.id, layer.esid);
    }

    if (typeof layer.eachLayer === 'function') {
        layer.eachLayer((childLayer) => visitBuildingLayers(childLayer, callback));
    }
}

const forEachBuildingLayer = (callback) => {
    for (const es of Object.values(window.esdl_list)) {
        visitBuildingLayers(es.layers.esdl_layer, callback);
        visitBuildingLayers(es.layers.bld_layer, callback);
    }
}

PubSubManager.subscribe(MessageNames.ADD_BUILDING_TO_LAYER, (name, message) => {
    for (const [text, item] of buildingContextMenuItems) {
        addContextMenuItemToLayer(
            message.layer,
            message.id,
            message.es_id,
            text,
            item.icon,
            item.onclick,
        );
    }
})

export function useEsdlBuildings() {
    /**
     * Add a context menu item to all known buildings.
     * @param {*} text
     * @param {*} icon
     * @param {*} onclick
     */
    const addBuildingContextMenuItem = (text, icon, onclick) => {
        buildingContextMenuItems.set(text, {icon: icon, onclick: onclick});
        forEachBuildingLayer((layer, id, esId) => {
            addContextMenuItemToLayer(layer, id, esId, text, icon, onclick);
        });
    }

    /**
     * Remove a context menu item from all known buildings by text.
     * @param {*} text
     */
    const removeBuildingContextMenuItem = (text) => {
        buildingContextMenuItems.delete(text);
        forEachBuildingLayer((layer) => {
            removeContextMenuItemFromLayer(layer, text);
        });
    }

    return {
        addBuildingContextMenuItem,
        removeBuildingContextMenuItem,
    }
}
