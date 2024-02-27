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

const activeModelContext = ref('standard')
const visibleModelContext = ref(false)
const modelContexts = ref([])

export function useModelContext() {
    function activateModelContext(activityContext) {
        activeModelContext.value = activityContext
    }

    const fetchModelContexts = () => {
        window.socket.emit('model_contexts_get_mode_info', function (res) {
            console.log("MODEL CONTEXT HI")
            console.log(res)
            activeModelContext.value = res['current_mode']
            modelContexts.value = res['possible_modes']
        });
    }

    const showModelContexts = () => {
        visibleModelContext.value = true;
    }

    const hideModelContexts = () => {
        visibleModelContext.value = false;
    }

    return {
        activeModelContext,
        fetchModelContexts,
        modelContexts,
        visibleModelContext,
        showModelContexts,
        hideModelContexts,
    }
}
