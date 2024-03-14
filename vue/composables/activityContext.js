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

import {ref} from "vue";
import {useWmsLayers} from "@/composables/wmsLayers";
import {useEsdlAreas} from "@/composables/esdlAreas";

const { clearWmsLayers, showWmsLayer } = useWmsLayers();
const { esdlAreas, removeAreaContextMenuItem } = useEsdlAreas();

// The active activity context is the context that is currently active in the map.
const activeActivityContext = ref({});

// Track the services that are enabled in the area context menu so we can remove them when the context is cleared.
const enabledAreaEsdlServices = ref([]);

export function useActivityContext() {
    /**
     * Activate the given activity context. This will update the activeActivityContext and show the WMS layers
     * that are part of the activity context. It will also add the services that are part of the context to the
     * context menus.
     * @param activityContext
     */
    function activateActivityContext(activityContext) {
        activeActivityContext.value = activityContext;

        // Clear the WMS layers and add the layers from the activity context.
        if (activityContext.workflow) {
            for (let i=0; i < esdl_services_information.length; i++) {
                if (esdl_services_information[i].name === activityContext.workflow) {
                    window.show_service_settings(i)
                }
            }
        }

        // Clear the WMS layers and add the layers from the activity context.
        clearWmsLayers()
        for (const layer of activityContext.wms_layers) {
            showWmsLayer(layer)
        }

        // Add the services to the context menus.
        const contextServices = activityContext.context_services;
        if (contextServices) {
            // For each contextService, find the corresponding service in the esdl_services_information.
            // Then update the location of the service.
            for (const contextService of contextServices) {
                let foundService = null;
                let foundServiceIdx = null;
                for (let i = 0; i < esdl_services_information.length; i++) {
                    const esdlService = esdl_services_information[i];
                    if (esdlService.id === contextService.id) {
                        foundService = esdlService;
                        foundServiceIdx = i;
                        break
                    }
                }
                if (!foundService) {
                    console.warn("Service with id " + contextService.id + " not found in esdl_services_information");
                } else {
                    if (contextService.location === "area_context_menu") {
                        for (const [, esdlArea] of Object.entries(esdlAreas.value)) {
                            window.add_service_to_area_contextmenu(esdlArea.layer, foundService, foundServiceIdx)
                        }
                        enabledAreaEsdlServices.value.push(foundService);
                    } else if (contextService.location === "map_context_menu") {
                        foundService.location = contextService.location;
                    }

                }
            }
            // Update the context menus for the services.
            window.update_map_service_contextmenus(window.esdl_services_information)
        }
    }

    function clearActivityContext() {
        activeActivityContext.value = {};
        clearWmsLayers()
        for (const service of enabledAreaEsdlServices.value) {
            removeAreaContextMenuItem(service.name)
        }
        enabledAreaEsdlServices.value = [];
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
