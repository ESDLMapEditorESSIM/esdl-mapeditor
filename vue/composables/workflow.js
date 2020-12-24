import { ref } from "vue";

export const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    FORM: 'form',
    MULTI_SELECT_QUERY: 'multi-select-query',
    SELECT_QUERY: 'select-query',
    // TODO: Rename?
    ESDL_SERVICE: 'service',
    DOWNLOAD_FILE: 'download_file',
    UPLOAD_FILE: 'upload_file',
    GET_DATA: 'get_data',
    HTTP_POST: 'http_post',
    // Call a global JS function.
    CALL_JS_FUNCTION: 'call_js_function',
    PROGRESS: 'progress',
    // Custom component.
    CUSTOM: 'custom',
});

// The currently active workflow.
export const currentWorkflow = ref(null);

export function useWorkflow() {
    /**
     * Start a brand new workflow.
     * 
     * @param {*} service_index 
     * @param {*} service 
     */
    const startNewWorkflow = (service_index, service) => {
        currentWorkflow.value = new Workflow(service_index, service);
        return currentWorkflow;
    }

    /**
     * Get the current workflow state.
     */
    const getState = () => {
        return currentWorkflow.value.state;
    }

    /**
     * Get values from the state.
     * 
     * @param {*} to_obtain_params An object mapping a key (what it should be in the
     * result) to a value (the name in the state).
     */
    const getFromState = (to_obtain_params) => {
        const state = getState();
        const params = {};
        for (const [key, value] of Object.entries(to_obtain_params)) {
            params[key] = state[value];
        }
        return params;
    }

    /**
     * Go to the next workflow step.
     */
    const goToNextStep = () => {
        currentWorkflow.value.doNext();
    }

    /**
     * Go to the next workflow step.
     */
    const goToPreviousStep = () => {
        currentWorkflow.value.doPrevious();
    }

    /**
     * Go to the given workflow step.
     */
    const goToStep = (stepIdx) => {
        currentWorkflow.value.doNext(stepIdx);
    }

    return {
        currentWorkflow,
        goToStep,
        goToNextStep,
        goToPreviousStep,
        getState,
        getFromState,
        startNewWorkflow,
    }
}

export class Workflow {
    constructor(service_index, service) {
        // The array index in the list sent from the server.
        this.service_index = service_index;
        this.service = service;
        this.workflowStep = service.workflow[0];
        this.step_idx = 0;
        this.state = {};
    }

    /**
     * Go to the next step.
     */
    doNext(stepIdx = null) {
        if (stepIdx === null) {
            this.stepIdx = this.workflowStep.next_step;
        } else {
            this.stepIdx = stepIdx
        }
        if (this.stepIdx >= 0) {
            this.workflowStep = this.service.workflow[this.stepIdx];
        }
    }

    /**
     * Go to the previous step.
     */
    doPrevious() {
        this.stepIdx = this.workflowStep.previous_step;
        this.workflowStep = this.service.workflow[this.stepIdx];
    }
}