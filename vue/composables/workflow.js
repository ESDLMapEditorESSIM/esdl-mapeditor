import {ref, watch} from "vue";
import {getattrd} from "../utils/utils";
import {v4 as uuidv4} from 'uuid';

export const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    FORM: 'form',
    MULTI_SELECT_QUERY: 'multi-select-query',
    SELECT_QUERY: 'select-query',
    // TODO: Rename?
    ESDL_SERVICE: 'service',
    JSON_FORM: 'json_form',
    DOWNLOAD_FILE: 'download_file',
    UPLOAD_FILE: 'upload_file',
    GET_DATA: 'get_data',
    HTTP_POST: 'http_post',
    // Call a global JS function.
    CALL_JS_FUNCTION: 'call_js_function',
    PROGRESS: 'progress',
    TEXT: 'text',
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

    const savedWorkflows = () => {
        return Object.keys(localStorage).filter((key) => key.startsWith('wf.')).map((key) => {
            const workflow = JSON.parse(localStorage.getItem(key));
            return {uuid: workflow.uuid, name: workflow.name};
        });
    }

    /**
     * Start over the current workflow.
     *
     */
    const startOver = () => {
        currentWorkflow.value = new Workflow(currentWorkflow.value.service_index, currentWorkflow.value.service);
        return currentWorkflow;
    }

    /**
     * Get the current workflow state.
     */
    const getState = () => {
        return currentWorkflow.value.state;
    }

    /**
     * Get value from the state.
     *
     * @param {*} to_obtain_field The name of the field in the state to get.
     */
    const getFromState = (to_obtain_field) => {
        const state = getState();
        return getattrd(state, to_obtain_field);
    }

    /**
     * Set name of the workflow. Used to retrieve it later.
     * @param name
     */
    const setWorkflowName = (name) => {
        currentWorkflow.value.setName(name);
    }

    const activatePersistedWorkflow = (uuid) => {
        const key = `wf.${uuid}`;
        const parsedWorkflow = JSON.parse(localStorage.getItem(key));
        const workflowObj = new Workflow(currentWorkflow.value.service_index, currentWorkflow.value.service);
        workflowObj.uuid = parsedWorkflow.uuid;
        workflowObj.workflowStep = parsedWorkflow.workflowStep;
        workflowObj.prevWorkflowSteps = parsedWorkflow.prevWorkflowSteps;
        workflowObj.state = parsedWorkflow.state;
        workflowObj.name = parsedWorkflow.name;
        workflowObj.persisted = parsedWorkflow.persisted;
        workflowObj.drive_paths = parsedWorkflow.drive_paths;
        workflowObj.restartable = parsedWorkflow.restartable;
        currentWorkflow.value = workflowObj;
        window.show_loader();
        window.socket.emit('/workflow/load', {workflow_id: currentWorkflow.value.uuid});
    }

    const persistWorkflow = (uploadEsdls) => {
        if (currentWorkflow.value.persisted) {
            const key = `wf.${currentWorkflow.value.uuid}`;
            localStorage.setItem(key, JSON.stringify(currentWorkflow.value));
            if (uploadEsdls) {
                window.show_loader();
                window.socket.emit('/workflow/persist', {workflow_id: currentWorkflow.value.uuid}, function (msg) {
                    window.hide_loader();
                    currentWorkflow.value.setDrivePaths(msg.drive_paths);
                });
            }
        }
    }

    const deletePersistedWorkflow = (uuid) => {
        const key = `wf.${uuid}`;
        localStorage.removeItem(key)
        window.show_loader();
        window.socket.emit('/workflow/delete', {workflow_id: currentWorkflow.value.uuid}, function(msg) {
            window.hide_loader();
            currentWorkflow.value.setDrivePaths([]);
        });
    }

    /**
     * Get values from the state, as a parameter mapping..
     *
     * @param {*} to_obtain_params An object mapping a key (what it should be in the
     * result) to a value (the name in the state).
     */
    const getParamsFromState = (to_obtain_params) => {
        if (to_obtain_params) {
            const state = getState();
            const params = {};
            for (const [target_field, state_field] of Object.entries(to_obtain_params)) {
                params[target_field] = getattrd(state, state_field);
            }
            return params;
        }
        return {};
    }

    /**
     * Go to the next workflow step.
     */
    const goToNextStep = () => {
        currentWorkflow.value.doNext();
        persistWorkflow();
    }

    /**
     * Go to the next workflow step.
     */
    const goToPreviousStep = () => {
        currentWorkflow.value.doPrevious();
        persistWorkflow();
    }

    /**
     * Go to given step.
     */
    const goToStep = (stepIdx) => {
        currentWorkflow.value.doNext(stepIdx);
        persistWorkflow();
    }

    /**
     * Unroll the previous steps to go to the first step.
     */
    const goToFirstStep = () => {
        while (currentWorkflow.value.hasPreviousStep()) {
            goToPreviousStep();
        }
    }

    const closeWorkflow = () => {
        currentWorkflow.value = null;
    }

    return {
        currentWorkflow,
        goToStep,
        goToFirstStep,
        goToNextStep,
        goToPreviousStep,
        getState,
        getFromState,
        getParamsFromState,
        startNewWorkflow,
        closeWorkflow,
        startOver,
        setWorkflowName,
        persistWorkflow,
        deletePersistedWorkflow,
        savedWorkflows,
        activatePersistedWorkflow,
    }
}

export class Workflow {
    constructor(service_index, service) {
        // The array index in the list sent from the server.
        this.uuid = uuidv4();
        this.service_index = service_index;
        this.service = service;
        this.workflowStep = service.workflow[0];
        this.prevWorkflowSteps = [];
        this.state = {};
        this.name = null;
        this.persisted = false;
        this.restartable = service.restartable || false;
        this.drive_paths = [];
    }

    setName(name) {
        this.name = name;
    }

    setPersistence(truefalse) {
        this.persisted = truefalse;
    }

    setDrivePaths(drive_paths) {
        this.drive_paths = drive_paths;
    }

    /**
     * Go to the next step.
     */
    doNext(targetStepIdx = null) {
        if (targetStepIdx === null || targetStepIdx === undefined) {
            targetStepIdx = this.workflowStep.next_step;
        }
        if (targetStepIdx >= 0) {
            this.prevWorkflowSteps.push(this.workflowStep);
            this.workflowStep = this.service.workflow[targetStepIdx];
        }
    }

    /**
     * Go to the previous step.
     */
    doPrevious() {
        this.workflowStep = this.prevWorkflowSteps.pop();
        // this.stepIdx = this.workflowStep.previous_step;
        // this.workflowStep = this.service.workflow[this.stepIdx];
    }

    hasPreviousStep() {
        return this.prevWorkflowSteps.length > 0;
    }
}
