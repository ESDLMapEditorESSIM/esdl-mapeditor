/**
 * Save the state of a WorkflowTableQuery component, to avoid it being reset on every mount.
 */
import {ref} from "vue";

const selectedUserGroups = ref(["my_runs"]);
const waitingRunIdsPerAction = ref({});

export function useWorkflowTableState() {
    /**
     * Get the reference to selected user groups list.
     */
    const getSelectedUserGroupsRef = () => selectedUserGroups;

    /**
     * Get the reference to a list of waiting run id's per action.
     */
    const getWaitingRunIdsPerActionRef = () => waitingRunIdsPerAction;

    return {
        getSelectedUserGroupsRef,
        getWaitingRunIdsPerActionRef,
    }
}
