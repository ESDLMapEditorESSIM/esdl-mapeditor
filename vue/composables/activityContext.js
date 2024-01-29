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

/**
 * An activity context is an activity the user is currently performing.
 */
export class ActivityContext {
    constructor(id, name, wms_layers) {
        this.id = id;
        this.name = name;
        this.wms_layers = wms_layers;
    }
}

export const ActivityContexts = Object.freeze({
    "ATES": new ActivityContext("ATES", 'Draw an ATES', ['AardwarmteRotliegend']),
    "WINDTURBINE": new ActivityContext("WINDTURBINE", 'Place a windturbine', []),
})

const activeActivityContext = ref(null);

export function useActivityContext() {
    return {
        activeActivityContext
    }
}
