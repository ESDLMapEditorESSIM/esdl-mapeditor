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
import {ref} from "vue";
import {getattrd} from "@/utils/utils";
import {v4 as uuidv4} from 'uuid';
import {nextStepsSchemaValidator} from "@/utils/workflowSchemas";
import {workflowGetData, workflowPostData} from "@/components/workflow/utils/api";
import {useOngoingBackendProcesses} from "@/composables/ongoingBackendProcesses";

const {getStartingBackendProcessId} = useOngoingBackendProcesses();

export const WorkflowStepTypes = Object.freeze({
    CHOICE: 'choice',
    SELECT: 'select',
    TABLE: 'table',
    TABLE_EXTERNAL_MODEL: 'table-external-model',
    ESDL_SERVICE: 'esdl-service',
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
    GET_SEND_DATA: 'get-send-data',
    COMPOSITE: 'composite',
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
    };

    const loadSavedWorkflows = () => {
        window.socket.emit('/workflow/list', function (workflow_list) {
            savedWorkflows.value = workflow_list.map((workflow) => {
                return {uuid: workflow.uuid, name: workflow.name};
            });
        });
    };

    /**
     * Start over the current workflow.
     *
     */
    const startOver = () => {
        currentWorkflow.value = new Workflow(currentWorkflow.value.service_index, currentWorkflow.value.service);
        return currentWorkflow;
    };

    /**
     * Get the current workflow state.
     */
    const getState = () => {
        return currentWorkflow.value.state;
    };

    /**
     * Get value from the state.
     *
     * @param {*} to_obtain_field The name of the field in the state to get.
     */
    const getFromState = (to_obtain_field) => {
        const state = getState();
        return getattrd(state, to_obtain_field);
    };

    /**
     * Set name of the workflow. Used to retrieve it later.
     * @param name
     */
    const setWorkflowName = (name) => {
        currentWorkflow.value.setName(name);
    };

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
                workflowObj.workflowStep = parsedWorkflow.step;
                workflowObj.prevWorkflowSteps = parsedWorkflow.prevWorkflowSteps;
                workflowObj.state = parsedWorkflow.state;
                workflowObj.name = parsedWorkflow.name;
                workflowObj.persisted = parsedWorkflow.persisted;
                workflowObj.drive_paths = parsedWorkflow.drive_paths;
                workflowObj.resumable = parsedWorkflow.resumable;
                currentWorkflow.value = workflowObj;
            }
        });
    };

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
    };

    const deletePersistedWorkflow = (uuid) => {
        window.show_loader();
        window.socket.emit('/workflow/delete', {workflow_id: uuid}, function () {
            window.hide_loader();
            loadSavedWorkflows();
        });
    };

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
    };

    /**
     * Go to the next workflow step.
     */
    const goToPreviousStep = () => {
        currentWorkflow.value.doPrevious();
        persistWorkflow();
    };

    /**
     * Get workflow step, used by the composite workflow component
     */
    const getWorkflowStep = (stepIndexOrReference) => {
        return currentWorkflow.value.getWorkflowStep(stepIndexOrReference);
    };

    /**
     * Go to given step.
     *
     * @param stepIdOrObject Step id (string) or object with rules/conditions
     */
    const goToStep = (stepIdOrObject) => {
        currentWorkflow.value.doNext(stepIdOrObject);
        persistWorkflow();
    };

    /**
     * Unroll the previous steps to go to the first step.
     */
    const goToFirstStep = () => {
        while (currentWorkflow.value.hasPreviousStep()) {
            goToPreviousStep();
        }
    };

    const closeWorkflow = () => {
        currentWorkflow.value = null;
    };

    const setWorkflowStepInputValid = (workflowStepId, valid) => {
        currentWorkflow.value.inputValidDict[workflowStepId] = valid;
    };

    const isAllInputValid = () => {
        if (Object.keys(currentWorkflow.value.inputValidDict).length === 0) {
            return true;
        } else {
            return Object.values(currentWorkflow.value.inputValidDict).every(value => value === true);
        }
    };

    /**
     * Get the workflow step input.
     *
     * @param {*} dataConfig the data config from the json service configuration for the workflow step
     * @param {*} afterDataRetrievedFunction optional function that will be called after getting the data
     */
    const getInputData = async (dataConfig, afterDataRetrievedFunction = () => {}) => {
        if (dataConfig === null || dataConfig === undefined) {
            throw new Error("No data config found for workflow step");
        }

        let data = {};

        if ("from_config" in dataConfig) {
            data = {...data, ...dataConfig.from_config};
        }

        if ("from_url" in dataConfig) {
            const urlConfig = dataConfig.from_url;
            const url = urlConfig.url;
            const method = urlConfig.method || 'GET';
            const headers = urlConfig.headers || {};

            if (method.toLowerCase() !== 'post' && method.toLowerCase() !== 'get') {
                throw new Error(`Unsupported HTTP method: ${method}`);
            }

            let request_params = {};
            if ("request_params" in urlConfig) {
                urlConfig.request_params.forEach(function (param) {
                    if ("value" in param) {
                        request_params[param.name] = param.value;
                    } else if ("parameter_name" in param) {
                        request_params[param.name] = getFromState(param.parameter_name);
                    } else {
                        console.error("request parameter found in service config without 'value' or 'parameter_name'");
                    }
                });
            }

            try {
                let response;
                if (method.toLowerCase() === 'POST') {
                    const body = urlConfig.body || request_params;
                    response = await workflowPostData(url, body, headers);
                } else {
                    response = await workflowGetData(url, request_params, headers);
                }

                if ("wrapper_variable" in urlConfig) {
                    data[urlConfig.wrapper_variable] = response;
                } else {
                    data = {...data, ...response};
                }
            } catch (error) {
                console.error(`Error in HTTP ${method} request:`, error);
            }
        }

        if ("from_state" in dataConfig) {
            for (const [key, value] of Object.entries(dataConfig.from_state)) {
                data[key] = getFromState(value);
            }
        }

        if ("from_socket" in dataConfig) {
            // In case of socket, we work with a callback.
            const fromSocket = dataConfig.from_socket;

            let params = "params" in fromSocket ? fromSocket.params : {};
            if ("state_params" in fromSocket) {
                for (const [key, state_key] of Object.entries(fromSocket.state_params)) {
                    params[key] = getFromState(state_key);
                }
            }
            window.socket.emit(fromSocket.event, params, (response) => {
                if ("wrapper_variable" in fromSocket) {
                    data[fromSocket.wrapper_variable] = response;
                } else {
                    data = {...data, ...response};
                }
                afterDataRetrievedFunction(data);
            });
        } else {
            // This should only be done if there is no from_socket handler, as that one has to wait for the callback.
            if (Object.keys(data).length === 0) {
                data = null;
            }
            afterDataRetrievedFunction(data);
        }

    };

    /**
     * Send the workflow step output.
     *
     * @param {*} dataConfig the data config from the json service configuration for the workflow step
     * @param {*} output output data that will be sent
     * @param {*} afterDataSentFunction function that will be called after the data has been sent
     */
    const sendOutputData = async (dataConfig, output, afterDataSentFunction = () => {
    }) => {
        if (getStartingBackendProcessId() !== null) {
            output["backend_process_id"] = getStartingBackendProcessId();
        }
        let formattedOutput;
        if (dataConfig.output_wrapper_variable) {
            formattedOutput = {}
            formattedOutput[dataConfig.output_wrapper_variable] = output;
        } else {
            formattedOutput = output;
        }
        let responseOk = true;
        if ("to_url" in dataConfig) {
            try {
                const response = await workflowPostData(dataConfig.to_url.url, formattedOutput);
                responseOk = response.ok;
            } catch {
                console.error("Problem sending POST:", dataConfig.to_url, formattedOutput);
                responseOk = false;
            }
        }
        if ("to_state" in dataConfig) {
            Object.assign(getState(), {...getState(), ...formattedOutput});
        }
        if ("to_socket" in dataConfig) {
            window.socket.emit(dataConfig.to_socket.event, formattedOutput, () => {
                afterDataSentFunction(responseOk);
            });
        } else {
            afterDataSentFunction(responseOk);
        }
    };

    const getWorkflowStepParameters = (stepConfig) => {
        if (!stepConfig.id) {
            console.error("Workflow step without id found:", stepConfig.name);
        }
        let nextStepTrigger = null;
        if (stepConfig.next_step_trigger) {
            if (Object.values(WorkflowNextStepTriggerOptions).includes(stepConfig.next_step_trigger)) {
                nextStepTrigger = stepConfig.next_step_trigger;
            } else {
                console.error("Workflow next step trigger option not found:", stepConfig.next_step_trigger);
            }
        } else {
            nextStepTrigger = WorkflowNextStepTriggerOptions.BUTTON_CLICK;  // default
        }
        return new StepParameters(
            stepConfig.id,
            stepConfig.config || null,
            stepConfig.data || null,
            stepConfig.button_text,
            stepConfig.workflow_engine || null,
            stepConfig.next_step,
            nextStepTrigger,
        );
    };

    return {
        currentWorkflow,
        goToStep,
        goToFirstStep,
        goToPreviousStep,
        getWorkflowStep,
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
        setWorkflowStepInputValid,
        isAllInputValid,
        getWorkflowStepParameters,
        getInputData,
        sendOutputData
    };
}

export const WorkflowNextStepTriggerOptions = Object.freeze({
    LOADING_COMPLETE: "loading_complete",
    INPUT_CHANGE: "input_change",
    BUTTON_CLICK: "button_click",
});

/**
 * @typedef {Object} StepConfig
 * @property {Object|null} [state_params] - Mapping of parameters in state
 * @property {boolean} [datetimes_convert_Z] - Whether to convert datetime formats
 * @property {string|null} [button_text]
 * @property {Object|null} workflow_engine
 * @property {string|null} next_step
 * @property {string} next_step_trigger
 */

/**
 * @typedef {Object} StepParameters
 * @property {string} id - Step identifier
 * @property {StepConfig|null} config - Configuration options
 * @property {Object|null} data - Data for the step
 * @property {string|null} [buttonText] - Optional button text
 * @property {Object|null} workflowEngine - Workflow engine configuration
 * @property {string|null} nextStep - Next step identifier
 * @property {string} nextStepTrigger - Trigger type for next step
 * @property {Object|null} [service] - Service configuration
 */

export class StepParameters {
    constructor(id, config, data, buttonText, workflowEngine, nextStep, nextStepTrigger) {
        this.id = id;
        this.config = config;
        this.data = data;
        this.buttonText = buttonText;
        this.workflowEngine = workflowEngine;
        this.nextStep = nextStep;
        this.nextStepTrigger = nextStepTrigger;
        this.service = null;
    }
}

export class Workflow {
    constructor(service_index, service, initialState) {
        // The array index in the list sent from the server.
        this.uuid = uuidv4();
        this.service_index = service_index;
        this.service = service;

        this.workflowTrigger = {"index": 0};  // for component watcher
        this.workflowStep = this.getWorkflowStep(this.service.workflow[0].id);

        this.prevWorkflowSteps = [];
        if (!initialState) {
            initialState = {};
        }
        this.state = initialState;
        this.name = null;
        this.persisted = false;
        this.resumable = service.resumable || false;
        this.drive_paths = [];
        this.inputValidDict = {};
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
     *
     * @param nextStepIdOrObject Step id (string) or object with rules/conditions
     */
    doNext(nextStepIdOrObject) {
        let targetStepId = null;
        if (nextStepIdOrObject === null || nextStepIdOrObject === undefined) {
            // No next step. Go to the beginning.
            while (this.hasPreviousStep()) {
                this.doPrevious();
            }
            return;
        } else if (typeof nextStepIdOrObject === 'object') {
            // Step with multiple next steps.
            const ifRules = nextStepIdOrObject.if;
            for (const ifRule of ifRules) {
                const isValid = nextStepsSchemaValidator(ifRule);
                if (!isValid) {
                    console.error("Invalid next steps schema", ifRule);
                    continue;
                }
                const isConditionMet = evaluateConditions(ifRule, this.state);
                if (isConditionMet) {
                    targetStepId = ifRule.then;
                    break;
                }
            }
            if (targetStepId === null && nextStepIdOrObject.else !== undefined) {
                // No if rule matches. Trigger the else if it's there.
                targetStepId = nextStepIdOrObject.else.then;
            }
        } else {
            // Step with a single next step.
            targetStepId = nextStepIdOrObject;
        }

        const nextStep = this.getWorkflowStep(targetStepId);

        // Don't add to previous steps if staying on the same step which happens with the 'composite' step
        if (nextStep !== null && nextStep !== this.workflowStep) {
            this.prevWorkflowSteps.push(this.workflowStep);
            this.inputValidDict = {};
            this.workflowStep = nextStep;
        }
    }

    addStep(step) {
        // Don't add to previous steps if staying on the same step which happens with the 'composite' step
        if (step !== null && step !== this.workflowStep) {
            this.prevWorkflowSteps.push(this.workflowStep);
            this.workflowTrigger["index"] += 1;
            step.workflowTrigger = this.workflowTrigger;
            step["main_service_id"] = this.service.id;
            this.inputValidDict = {};
            this.workflowStep = step;
        }
    }

    getStepIndexFromId(stepId) {
        for (const [index, step] of this.service.workflow.entries()) {
            if ("id" in step && step.id === stepId) {
                return index;
            }
        }
        return null;
    }

    /**
     * Go to the previous step.
     */
    doPrevious() {
        this.workflowStep = this.prevWorkflowSteps.pop();
        this.workflowTrigger["index"] += 1;
    }

    hasPreviousStep() {
        return this.prevWorkflowSteps && this.prevWorkflowSteps.length > 0;
    }

    getWorkflowStep(stepId) {
        let stepIndex = this.getStepIndexFromId(stepId);
        if (stepIndex === null) {
            console.error("Workflow step id could not be found: ", stepId);
            return null;
        }
        const wfStep = this.service.workflow[stepIndex];

        this.workflowTrigger["index"] += 1;
        wfStep.workflowTrigger = this.workflowTrigger;
        wfStep["main_service_id"] = this.service.id;
        return wfStep;
    }
}
