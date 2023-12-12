import {ref} from "vue";
import {getattrd} from "../utils/utils";
import {v4 as uuidv4} from 'uuid';
import {nextStepsSchemaValidator} from "../utils/workflowSchemas";
import workflow from "../apps/Workflow.vue";

export const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    SELECT_QUERY: 'select-query',
    TABLE_QUERY: 'table-query',
    MULTI_SELECT_QUERY: 'multi-select-query',
    // TODO: Rename?
    ESDL_SERVICE: 'service',
    JSON_FORM: 'json-form',
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

// TODO: Move to different file
function evaluateRule(rule, data) {
    const { field, operator, value } = rule;
    switch (operator) {
        case 'eq': return data[field] === value;
        case 'neq': return data[field] !== value;
        case 'gt': return data[field] > value;
        case 'lt': return data[field] < value;
        case 'gte': return data[field] >= value;
        case 'lte': return data[field] <= value;
        default: return false;
    }
}

// TODO: Move to different file
// Recursive function to evaluate conditions with AND/OR logic
function evaluateConditions(conditions, data) {
    if (conditions.condition === 'AND') {
        return conditions.rules.every(rule =>
            rule.condition ? evaluateConditions(rule, data) : evaluateRule(rule, data)
        );
    } else if (conditions.condition === 'OR') {
        return conditions.rules.some(rule =>
            rule.condition ? evaluateConditions(rule, data) : evaluateRule(rule, data)
        );
    }
    return false;
}

// The currently active workflow.
export const currentWorkflow = ref(null);
// Saved workflows that the user can load.
export const savedWorkflows = ref([]);

export function useWorkflow() {
    /**
     * Start a brand new workflow.
     *
     * @param {*} service_index
     * @param {*} service
     */
    const startNewWorkflow = (service_index, service, state) => {
        currentWorkflow.value = new Workflow(service_index, service, state);
        return currentWorkflow;
    }

    const loadSavedWorkflows = () => {
        window.socket.emit('/workflow/list', function (workflow_list) {
            savedWorkflows.value = workflow_list.map((workflow) => {
                return {uuid: workflow.uuid, name: workflow.name};
            });
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
        window.show_loader();
        window.socket.emit('/workflow/load', {workflow_id: uuid}, function (parsedWorkflow) {
            console.log(parsedWorkflow);
            if (parsedWorkflow) {
                const workflowObj = new Workflow(currentWorkflow.value.service_index, currentWorkflow.value.service);
                workflowObj.uuid = parsedWorkflow.uuid;
                workflowObj.workflowStep = parsedWorkflow.workflowStep;
                workflowObj.prevWorkflowSteps = parsedWorkflow.prevWorkflowSteps;
                workflowObj.state = parsedWorkflow.state;
                workflowObj.name = parsedWorkflow.name;
                workflowObj.persisted = parsedWorkflow.persisted;
                workflowObj.drive_paths = parsedWorkflow.drive_paths;
                workflowObj.resumable = parsedWorkflow.resumable;
                currentWorkflow.value = workflowObj;
            }
        });
    }

    const persistWorkflow = (uploadEsdls) => {
        if (currentWorkflow.value.persisted) {
            const key = `wf.${currentWorkflow.value.uuid}`;
            const jsonWorkflow = JSON.stringify(currentWorkflow.value);
            localStorage.setItem(key, jsonWorkflow);
            if (uploadEsdls) {
                window.show_loader();
                window.socket.emit('/workflow/persist', {workflow_id: currentWorkflow.value.uuid, workflow_json: jsonWorkflow}, function (msg) {
                    window.hide_loader();
                    currentWorkflow.value.setDrivePaths(msg.drive_paths);
                });
            }
        }
    }

    const deletePersistedWorkflow = (uuid) => {
        window.show_loader();
        window.socket.emit('/workflow/delete', {workflow_id: currentWorkflow.value.uuid}, function(msg) {
            window.hide_loader();
            currentWorkflow.value.setDrivePaths([]);
        });
    }

    /**
     * Get values from the state, as a parameter mapping.
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
        loadSavedWorkflows,
        activatePersistedWorkflow,
    }
}

export class Workflow {
    constructor(service_index, service, initialState) {
        // The array index in the list sent from the server.
        this.uuid = uuidv4();
        this.service_index = service_index;
        this.service = service;
        this.workflowStep = service.workflow[0];
        this.prevWorkflowSteps = [];
        if (!initialState) {
            initialState = {};
        }
        this.state = initialState;
        this.name = null;
        this.persisted = false;
        this.resumable = service.resumable || false;
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
            const nextStepData = this.workflowStep.next_step;
            if (typeof nextStepData === 'object') {
                // Step with multiple next steps.
                const ifRules = nextStepData.if;
                for (const ifRule of ifRules) {
                    const isValid = nextStepsSchemaValidator(ifRule);
                    if (!isValid) {
                        console.error("Invalid next steps schema", ifRule);
                        continue
                    }
                    const isConditionMet = evaluateConditions(ifRule, this.state);
                    if (isConditionMet) {
                        targetStepIdx = ifRule.then;
                        break
                    }
                }
                if (targetStepIdx === null && nextStepData.else !== undefined) {
                    // No if rule matches. Trigger the else if it's there.
                    targetStepIdx = nextStepData.else.then;
                }
            } else {
                // Step with a single next step.
                targetStepIdx = nextStepData;
            }
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
        return this.prevWorkflowSteps && this.prevWorkflowSteps.length > 0;
    }
}
