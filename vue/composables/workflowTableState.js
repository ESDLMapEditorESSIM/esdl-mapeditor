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

/**
 * Save the state of a WorkflowTable component, to avoid it being reset on every mount.
 */
import {ref} from "vue";

const selectedUserGroups = ref(["my_runs"]);

export function useWorkflowTableState() {
    /**
     * Get the reference to selected user groups list.
     */
    const getSelectedUserGroupsRef = () => selectedUserGroups;

    return {
        getSelectedUserGroupsRef,
    }
}
