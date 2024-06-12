/*
 * This work is based on original code developed and copyrighted by TNO 2020.
 * Subsequent contributions are licensed to you by the developers of such code and are
 * made available to the Project under one or several contributor license agreements.
 *
 * This work is licensed to you under the Apache License, Version 2.0.
 * You may obtain a copy of the license at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Contributors:
 *     TNO         - Initial implementation
 * Manager:
 *     TNO
 */

import {ref, watch} from "vue";
import {useWmsLayers} from "@/composables/wmsLayers";
import {useEsdlAreas} from "@/composables/esdlAreas";
import {useEsdlBuildings} from "./esdlBuildings";
import { useToast } from "vue-toastification";

const { clearWmsLayers, showWmsLayer } = useWmsLayers();
const { addAreaContextMenuItem, esdlAreas, removeAreaContextMenuItem } = useEsdlAreas();
const { addBuildingContextMenuItem, removeBuildingContextMenuItem } = useEsdlBuildings();

// The active activity context is the context that is currently active in the map.
const activeActivityContext = ref({});

// Track the services that are enabled in the context menu's so we can remove them when the context is cleared.
const enabledAreaContextMenus = ref([]);
const enabledMapContextMenus = ref([]);
const enabledBuildingContextMenus = ref([]);

const toast = useToast();

watch(esdlAreas,
    (newAreas, oldAreas) => {
        addContextMenuJsFunctions(activeActivityContext.value)
    }, {deep: true}
)

/**
 * Add the context menu js functions that are part of the context to the context menus.
 * @param activityContext
 */
function addContextMenuJsFunctions(activityContext) {
    const contextMenuJsFunctions = activityContext.context_menu_js_functions;
    if (contextMenuJsFunctions) {
        for (const contextMenuJsFunction of contextMenuJsFunctions) {
            if (contextMenuJsFunction.location === "area") {
                addAreaContextMenuItem(contextMenuJsFunction.title, contextMenuJsFunction.icon, window[contextMenuJsFunction.js_function]);
                enabledAreaContextMenus.value.push(contextMenuJsFunction.title);
            } else if (contextMenuJsFunction.location === "map") {
                console.warn("Context menu js function with location 'map' is not yet supported")
            } else if (contextMenuJsFunction.location === "building") {
                console.warn("Context menu js function with location 'building' is not yet supported")
            }
        }
    }
}

/**
 * Find the service in the esdl_services_information by id.
 * @param id
 * @returns {*[]}
 */
function findServiceById(id) {
    let foundService = null;
    let foundServiceIdx = null;
    for (let i = 0; i < window.esdl_services_information.length; i++) {
        const esdlService = window.esdl_services_information[i];
        if (esdlService.id === id) {
            foundService = esdlService;
            foundServiceIdx = i;
            break
        }
    }
    return [foundService, foundServiceIdx];
}

/**
 * Add the services that are part of the context to the context menus.
 * @param activityContext
 */
function addContextMenuServices(activityContext) {
    // Add the services to the context menus.
    const contextMenuServices = activityContext.context_menu_services;
    if (contextMenuServices) {
        // For each contextService, find the corresponding service in the esdl_services_information.
        // Then update the location of the service.
        for (const contextMenuService of contextMenuServices) {
            let [foundService, foundServiceIdx] = findServiceById(contextMenuService.id);
            if (!foundService) {
                console.warn("Service with id " + contextMenuService.id + " not found in esdl_services_information");
            } else {
                if (contextMenuService.location === "area") {
                    for (const [, esdlArea] of Object.entries(esdlAreas.value)) {
                        window.add_service_to_area_contextmenu(esdlArea.layer, foundService, foundServiceIdx, contextMenuService.icon)
                    }
                    enabledAreaContextMenus.value.push(foundService.name);
                } else if (contextMenuService.location === "map") {
                    console.debug("Service " + foundService.name + " is added to the map context menu");
                    foundService.location = "map_context_menu"
                    enabledMapContextMenus.value.push(foundService.id);
                } else if (contextMenuService.location === "building") {
                    addBuildingContextMenuItem(foundService['name'], window.resource_uri + 'icons/service.png', function (e, id) {
                        window.show_service_settings(foundServiceIdx)
                    });
                    enabledBuildingContextMenus.value.push(foundService.name);
                }

            }
        }
        // Update the context menus for the services.
        window.update_map_service_contextmenus(window.esdl_services_information)
    }
}

export function useActivityContext() {
    /**
     * Activate the given activity context. This will update the activeActivityContext and show the WMS layers
     * that are part of the activity context. It will also add the services that are part of the context to the
     * context menus.
     * @param activityContext
     */
    async function activateActivityContext(activityContext) {
        if (activeActivityContext.value) {
            clearActivityContext();
        }
        activeActivityContext.value = activityContext;

        // Clear the WMS layers and add the layers from the activity context.
        if (activityContext.workflow) {
            for (let i=0; i < esdl_services_information.length; i++) {
                if (esdl_services_information[i].name === activityContext.workflow) {
                    window.show_service_settings(i)
                }
            }
        }

        if (activityContext.js_function) {
            // Call the js function that is part of the activity context.
            window[activityContext.js_function]()
        }

        // Clear the WMS layers and add the layers from the activity context.
        if (activityContext.wms_layers) {
            clearWmsLayers()
            for (const layer of activityContext.wms_layers) {
                try {
                    showWmsLayer(layer)
                } catch (e) {
                    // Check if TypeError, then the layer does not exist.
                    if (e instanceof TypeError) {
                        console.warn("WMS layer " + layer.name + " does not exist")
                    } else {
                        console.error("Error showing WMS layer " + layer.name + ": " + e)
                    }
                }
            }
        }

        const disableEsdlLayers = activityContext.disable_esdl_layers;
        if (disableEsdlLayers) {
            for (const [es_id,] of Object.entries(window.esdl_list)) {
                for (const esdlLayer of disableEsdlLayers) {
                    console.debug("Disabling ESDL layer: " + esdlLayer);
                    window.hide_esdl_layer_from_map(es_id, esdlLayer);
                }
            }
        }

        addContextMenuJsFunctions(activityContext)
        addContextMenuServices(activityContext)

        const response = await fetch(`/context/activities/${activityContext.activity_id}/activate`, {
            method: 'POST'
        })
        if (!response.ok) {
            console.error('Error activating activity context', response)
            alert('Error activating activity context. Please check the console for more information.')
            clearActivityContext();
            return
        }

        if (activityContext.toast_text) {
            toast.info(activityContext.toast_text);
        }

    }

    /**
     * Clear the active activity context. This will remove all the context services and context menu items that were
     * added by the active activity context.
     */
    function clearActivityContext() {
        const activityContext = activeActivityContext.value;
        if (activityContext.wms_layers) {
            // Only clear if we added something.
            clearWmsLayers()
        }

        const disableEsdlLayers = activityContext.disable_esdl_layers;
        if (disableEsdlLayers) {
            for (const [es_id,] of Object.entries(window.esdl_list)) {
                for (const esdlLayer of disableEsdlLayers) {
                    window.show_esdl_layer_on_map(es_id, esdlLayer);
                }
            }
        }

        for (const name of enabledAreaContextMenus.value) {
            removeAreaContextMenuItem(name)
        }
        for (const id of enabledMapContextMenus.value) {
            let [foundService, foundServiceIdx] = findServiceById(id);
            foundService.location = "hidden";
        }
        window.update_map_service_contextmenus(window.esdl_services_information)
        for (const name of enabledBuildingContextMenus.value) {
            removeBuildingContextMenuItem(name)
        }
        enabledAreaContextMenus.value = [];
        enabledMapContextMenus.value = [];
        enabledBuildingContextMenus.value = [];

        activeActivityContext.value = {};
    }

    const fetchActivityContexts = async () => {
        const response = await fetch('/context/activities')
        return await response.json()
    }

    return {
        activeActivityContext,
        activateActivityContext,
        clearActivityContext,
        fetchActivityContexts,
    }
}
