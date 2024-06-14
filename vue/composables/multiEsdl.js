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

/*
This file is a wrapper around the multi_esdl.js in the legacy codebase.
 */

import {computed, ref} from "vue";

const esdlList = computed(() => window.esdl_list);

export function useMultiEsdl() {
    /**
     * Return whether or not any of the layers of the ESDL is shown on the map.
     * @param es_id
     * @returns {boolean}
     */
    function isEsdlShownOnMap(es_id) {
        const esdlListValue = esdlList.value;
        if (es_id in esdlListValue) {
            const es = esdlListValue[es_id];
            for (const layerName of Object.keys(es.layers)) {
                if (window.map.hasLayer(esdlListValue[es_id].layers[layerName])) {
                    return true;
                }
            }
        }
        return false;
    }

    function showEsdlLayerOnMap(es_id, layer_name) {
        window.show_esdl_layer_on_map(es_id, layer_name);
        window.set_leaflet_sizes();
    }

    function hideEsdlLayerFromMap(es_id, layer_name) {
        window.hide_esdl_layer_from_map(es_id, layer_name);
        //window.set_leaflet_sizes();
    }


    return {
        isEsdlShownOnMap,
        showEsdlLayerOnMap,
        hideEsdlLayerFromMap,
        esdlList,
    }
}
