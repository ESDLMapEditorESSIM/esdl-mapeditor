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
