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
import {useWmsLayers, showLayer} from "@/composables/wmsLayers";
import {useEsdlAreas} from "@/composables/esdlAreas";
import {useEsdlBuildings} from "./esdlBuildings";
import {useEsdlLayers} from "@/composables/esdlLayers";
import {displayNotification, NotificationType} from "@/utils/notification";

const { clearWmsLayers } = useWmsLayers();
const { addAreaContextMenuItem, totalEntriesAndAreas, esdlAreasDict,
    removeAreaContextMenuItem, saveAreaContextMenuState, restoreAreaContextMenuState } = useEsdlAreas();
const { addBuildingContextMenuItem, removeBuildingContextMenuItem } = useEsdlBuildings();

/**
 * @typedef {Object} ActivityContextMenuService
 * @property {string} id - The service ID.
 * @property {string} location - The location where to add the service. Can be map, area, or building.
 * @property {string} icon - The icon for the service.
 */

/**
 * @typedef {Object} ActivityContextMenuJsFunction
 * @property {string} title - The label of the context menu.
 * @property {string} location - The location where to add the service.
 * @property {string} icon - The icon for the context menu.
 * @property {string} js_function - The JS function to activate. Must be available on window\!
 */

/**
 * @typedef {Object} ActivityContext
 * @property {string} activity_id - The unique identifier for the activity context.
 * @property {string} name - The name of the activity context.
 * @property {string|null} workflow - The workflow to activate.
 * @property {boolean|null} is_global - If true, the context is shown to all users.
 * @property {boolean|null} clear_area_context_menu - If true, all existing options will be removed (and restored later)
 * @property {string|null} js_function - The JS function to execute when the context is activated.
 * @property {string[]|null} wms_layers - The WMS layers to activate.
 * @property {string[]|null} disable_esdl_layers - The ESDL layers to disable when activating this context.
 * @property {ActivityContextMenuService[]|null} context_menu_services - The services to add to context menus.
 * @property {ActivityContextMenuJsFunction[]|null} context_menu_js_functions - The JS functions to add to the context menu.
 * @property {string|null} toast_text - Text to show in an alert when activating this context.
 */

// The active activity context is the context that is currently active in the map.
/** @type {import('vue').Ref<ActivityContext>} */
const activeActivityContext = ref({});

// Track the services that are enabled in the context menu's so we can remove them when the context is cleared.
const enabledAreaContextMenus = ref([]);
const enabledMapContextMenus = ref([]);
const enabledBuildingContextMenus = ref([]);

watch(totalEntriesAndAreas, () => {
    addContextMenuJsFunctions(activeActivityContext.value); // trigger only on structural change
});

/**
 * Add the context menu js functions that are part of the context to the context menus.
 * @param activityContext
 */
function addContextMenuJsFunctions(activityContext) {
    const contextMenuJsFunctions = activityContext.context_menu_js_functions;
    if (contextMenuJsFunctions) {
        for (const contextMenuJsFunction of contextMenuJsFunctions) {
            if (contextMenuJsFunction.location === "area") {
                if (activityContext.clear_area_context_menu) {
                    saveAreaContextMenuState();
                }
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
                    for (const [, esdlAreas] of Object.entries(esdlAreasDict.value)) {
                        for (const esdlArea of esdlAreas) {
                            window.add_service_to_area_contextmenu(esdlArea.layer, foundService, foundServiceIdx, contextMenuService.icon)
                        }
                    }
                    enabledAreaContextMenus.value.push(foundService.name);
                } else if (contextMenuService.location === "map") {
                    console.debug("Service " + foundService.name + " is added to the map context menu");
                    foundService.location = "map_context_menu"
                    enabledMapContextMenus.value.push(foundService.id);
                } else if (contextMenuService.location === "building") {
                    addBuildingContextMenuItem(foundService['name'], window.resource_uri + 'icons/service.png', function () {
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
const {hideEsdlLayerAllEsdls, showEsdlLayerAllEsdls} = useEsdlLayers();

    /**
     * Activate the given activity context. This will update the activeActivityContext and show the WMS layers
     * that are part of the activity context. It will also add the services that are part of the context to the
     * context menus.
     * @param {ActivityContext} activityContext
     */
    function activateActivityContext(activityContext) {
        if (activeActivityContext.value) {
            clearActivityContext();
        }
        activeActivityContext.value = activityContext;

        // Enable the workflow if it is part of the activity context.
        if (activityContext.workflow) {
            for (let i=0; i < window.esdl_services_information.length; i++) {
                if (window.esdl_services_information[i].name === activityContext.workflow) {
                    window.show_service_settings(i)
                }
            }
        }

        if (activityContext.js_function) {
            // Call the js function that is part of the activity context.
            window[activityContext.js_function]()
        }

        // Clear the WMS layers and add the layers from the activity context.
        if (activityContext.wms_layers !== undefined) {
            // clearWmsLayers()
            for (const layer of activityContext.wms_layers) {
                try {
                    showLayer(layer)
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
            for (const esdlLayer of disableEsdlLayers) {
                console.debug("Disabling ESDL layer: " + esdlLayer);
                hideEsdlLayerAllEsdls(esdlLayer);
            }
        }

        addContextMenuJsFunctions(activityContext)
        addContextMenuServices(activityContext)

        if (activityContext.toast_text) {
            displayNotification(NotificationType.INFO, activityContext.toast_text);
        }

    }

    /**
     * Clear the active activity context. This will remove all the context services and context menu items that were
     * added by the active activity context.
     */
    function clearActivityContext() {
        console.debug("Clearing activity context")
        const activityContext = activeActivityContext.value;
        if (activityContext.wms_layers) {
            // Only clear if we added something.
            // TODO: Only clear those that were added.
            clearWmsLayers()
        }

        // Enable the ESDL layers that were disabled when activating the context.
        const disableEsdlLayers = activityContext.disable_esdl_layers;
        if (disableEsdlLayers) {
            for (const esdlLayer of disableEsdlLayers) {
                showEsdlLayerAllEsdls(esdlLayer);
            }
        }

        for (const name of enabledAreaContextMenus.value) {
            removeAreaContextMenuItem(name);

            if (activityContext.clear_area_context_menu) {
                restoreAreaContextMenuState();
            }
        }
        for (const id of enabledMapContextMenus.value) {
            let [foundService,] = findServiceById(id);
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
