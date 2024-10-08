import {ref} from "vue";
import {getattrd} from "@/utils/utils";
import {v4 as uuidv4} from 'uuid';
import {nextStepsSchemaValidator} from "@/utils/workflowSchemas";


export const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    SELECT_QUERY: 'select-query',
    TABLE_QUERY: 'table-query',
    MULTI_SELECT_QUERY: 'multi-select-query',
    // TODO: Rename?
    ESDL_SERVICE: 'service',
    JSON_FORM: 'json-form',
    JSON_FORM2: 'json-form2',
    DOWNLOAD_FILE: 'download_file',
    UPLOAD_FILE: 'upload_file',
    GET_DATA: 'get_data',
    HTTP_POST: 'http_post',
    // Call a global JS function.
    CALL_JS_FUNCTION: 'call_js_function',
    PROGRESS: 'progress',
    TEXT: 'text',
    ENGINE_MONITOR: 'workflow-engine-monitor',
    // Custom component.
    CUSTOM: 'custom',
});

// TODO: Move to different file
function evaluateRule(rule, data) {
    const {field, operator, value} = rule;
    switch (operator) {
        case 'eq':
            return data[field] === value;
        case 'neq':
            return data[field] !== value;
        case 'gt':
            return data[field] > value;
        case 'lt':
            return data[field] < value;
        case 'gte':
            return data[field] >= value;
        case 'lte':
            return data[field] <= value;
        default:
            return false;
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

export const RESET_WORKFLOW = "reset_workflow";

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
        window.socket.emit('/workflow/load', {workflow_id: uuid}, function (response) {
            if (response.message) {
                window.hide_loader();
                alert(response.message);
                return;
            }
            if (response.uuid) {
                // A workflow was returned. Load the workflow.
                const parsedWorkflow = response;
                const workflowObj = new Workflow(currentWorkflow.value.service_index, currentWorkflow.value.service);
                workflowObj.uuid = parsedWorkflow.uuid;
                workflowObj.activeWorkflowSteps = parsedWorkflow.workflowStep;
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
                window.socket.emit('/workflow/persist', {
                    workflow_id: currentWorkflow.value.uuid,
                    workflow_json: jsonWorkflow
                }, function (msg) {
                    window.hide_loader();
                    currentWorkflow.value.setDrivePaths(msg.drive_paths);
                    loadSavedWorkflows();
                });
            }
        }
    }

    const deletePersistedWorkflow = (uuid) => {
        window.show_loader();
        window.socket.emit('/workflow/delete', {workflow_id: uuid}, function (msg) {
            window.hide_loader();
            loadSavedWorkflows();
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
        RESET_WORKFLOW,
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

        this.workflowTrigger = {"index": 0};  // for component watcher
        this.setActiveWorkflowSteps(0);

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
            const nextStepData = this.activeWorkflowSteps[0].next_step;
            if (nextStepData === undefined) {
                // No next step. Go to the beginning.
                while (this.hasPreviousStep()) {
                    this.doPrevious();
                }
                return;
            } else if (typeof nextStepData === 'object') {
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

        if (typeof targetStepIdx === "string") {
            targetStepIdx = this.getStepIdxFromReference(targetStepIdx);
        }
        if (targetStepIdx >= 0) {
            if (targetStepIdx !== this.activeWorkflowIndex) {
                this.prevWorkflowSteps.push(this.activeWorkflowSteps);
            }
            this.setActiveWorkflowSteps(targetStepIdx);
        }
    }

    getStepIdxFromReference(stepReference) {
        for (const [index, step] of this.service.workflow.entries()) {
            if ("reference" in step && step.reference === stepReference) {
                return index;
            }
        }
    }

    /**
     * Go to the previous step.
     */
    doPrevious() {
        this.activeWorkflowSteps = this.prevWorkflowSteps.pop();
        this.workflowTrigger["index"] += 1;
        // to avoid infinite loop with auto_next_step
        this.workflowTrigger[RESET_WORKFLOW] = true;
        // to update values in other 'co view steps' via 'watch'
        for (const step of this.activeWorkflowSteps) {
            step.workflowTrigger = this.workflowTrigger;
        }
    }

    hasPreviousStep() {
        return this.prevWorkflowSteps && this.prevWorkflowSteps.length > 0;
    }

    setActiveWorkflowSteps(targetStepIdx) {
        this.workflowTrigger["index"] += 1;
        // to avoid infinite loop with auto_next_step: don't reset when staying on the same steps
        this.workflowTrigger[RESET_WORKFLOW] = this.activeWorkflowIndex !== targetStepIdx;
        this.activeWorkflowIndex = targetStepIdx;
        const currentSteps = [this.add_main_service_id(this.service.workflow[targetStepIdx])];
        if ("co_view_steps" in currentSteps[0]) {
            for (let stepIndex of currentSteps[0].co_view_steps) {
                if (typeof stepIndex === "string") {
                    stepIndex = this.getStepIdxFromReference(stepIndex);
                }
                if (stepIndex < targetStepIdx) {
                    currentSteps.unshift(this.add_main_service_id(this.service.workflow[stepIndex]));
                } else {
                    currentSteps.push(this.add_main_service_id(this.service.workflow[stepIndex]));
                }
            }
        }
        // to update values in other 'co view steps' via 'watch'
        for (const step of currentSteps) {
            step.workflowTrigger = this.workflowTrigger;
        }
        this.activeWorkflowSteps = currentSteps;
    }

    add_main_service_id(step) {
        step["main_service_id"] = this.service.id;
        return step;
    }
}
