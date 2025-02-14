/*
 * This work is based on original code developed and copyrighted by TNO 2025.
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
import {ref, toValue} from "vue";

const startingBackendProcessUid = ref(null);
const ongoingBackendProcessUuids = ref([]);

(async () => { // wait for socket to be defined
    while (window.socket === undefined) await new Promise(resolve => setTimeout(resolve, 10));

    window.socket.on('backend_process_complete', (data) => {
        startingBackendProcessUid.value = null;
        if (ongoingBackendProcessUuids.value.includes(data.backend_process_id)) {
            const index = ongoingBackendProcessUuids.value.findIndex(
                uuid => uuid === data.backend_process_id
            );
            ongoingBackendProcessUuids.value.splice(index, 1);
        }
    });
})();

export function useOngoingBackendProcesses() {
    const getStartingBackendProcessId = () => {
        return toValue(startingBackendProcessUid);
    };

    const setStartingBackendProcessId = (value) => {
        startingBackendProcessUid.value = value;
    };

    const addOngoingBackendProcessId = (processId) => {
        if (!ongoingBackendProcessUuids.value.includes(processId)) {
            ongoingBackendProcessUuids.value.push(processId);
        }
    };

    const isBackendProcessIdOngoing = (processId) => {
        return ongoingBackendProcessUuids.value.includes(processId);
    };

    return {
        getStartingBackendProcessId,
        setStartingBackendProcessId,
        addOngoingBackendProcessId,
        isBackendProcessIdOngoing,
    };
}