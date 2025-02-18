<template>
  <div
    v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.LOADING_COMPLETE"
  >
    <p v-if="workflowStep.service.description">
      {{ workflowStep.service.description }}
    </p>
    <p v-else>
      The ESDL service will be called automatically. Please click the button below when the ESDL was loaded fully.
    </p>
    <div id="service_results_div" />
    <a-button v-if="stepParams.buttonText" type="primary" @click="goToPreviousStep()">
      {{ stepParams.buttonText }}
    </a-button>
    <a-button v-else type="primary" @click="esdlWasLoaded()"> ESDL was loaded</a-button>
  </div>
  <div v-else>
    <p v-if="workflowStep.service.description">
      {{ workflowStep.service.description }}
    </p>
    <p v-else-if="workflowStep.service.description!==''">
      Please select the "Run ESDL service" button below to run the ESDL service
      and load the results.
    </p>
    <a-button
      v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK"
      type="primary"
      :disabled="!isAllInputValid()"
      @click="clearLayersAndLoadEsdl"
    >
      <div v-if="stepParams.buttonText"> {{ stepParams.buttonText }}</div>
      <div v-else>
        Run ESDL service
      </div>
    </a-button>
    <div id="service_results_div" />
  </div>
</template>

<script setup="props">
import {setattrd} from "@/utils/utils";

import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";
import {useEsdlLayers} from "@/composables/esdlLayers";
import {onMounted, ref, watch} from "vue";

// eslint-disable-next-line no-unused-vars
const {
  getWorkflowStepParameters,
  getParamsFromState,
  goToPreviousStep,
  goToFirstStep,
  getState,
  goToStep,
  isAllInputValid
} = useWorkflow();
const state = getState();
const {clearEsdlLayers} = useEsdlLayers()

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const stepParams = ref({});

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const esdlWasLoaded = () => {
  if (stepParams.value.config.target_variable && stepParams.value.target_variable_value) {
    setattrd(state, stepParams.value.target_variable, stepParams.value.target_variable_value);
  }
  goToFirstStep();
};

const clearLayersAndLoadEsdl = () => {
  if (stepParams.value.service.clearLayers) {
    clearEsdlLayers();
    // Allow a second for the layers to be cleared.
    setTimeout(loadEsdl, 1000);
  } else {
    loadEsdl();
  }
};

const loadEsdl = () => {
  let params = {};
  params["service_config"] = stepParams.value.service;

  if (stepParams.value.config["state_params"]) {
    params["state_params"] = getParamsFromState(stepParams.value.config["state_params"]);
  } else {
    params["state_params"] = {};
  }
  if (stepParams.value.config["datetimes_convert_Z"]) {  // for i.e. essim
    for (const [key, value] of Object.entries(params["state_params"])) {
      if (!isNaN(new Date(value).getTime())) { // string is in datetime format
        params["state_params"][key] = value.replace(".000Z", "+0100");
      }
    }
  }

  window.show_loader();

  if (stepParams.value.workflowEngine) {
    params["type"] = "esdl_service";
    params["main_service_id"] = props.workflowStep.main_service_id;
    params["run_name_key"] = stepParams.value.workflowEngine.run_name;
    params["workflow_engine_next_step"] = stepParams.value.workflowEngine.workflow_engine_next_step;

    window.socket.emit("wfe_initialize_sequence", params, (sequenceId) => {
      // after workflow engine start, set id and go to next Vue step (table overview or monitor progress)
      Object.assign(getState(), {"wfeSequenceId": sequenceId});
      goToStep(stepParams.value.nextStep);
      window.hide_loader();
    });
  } else {
    window.socket.emit("command", {cmd: "query_esdl_service", params: params}, () => {
      goToStep(stepParams.value.nextStep);
    });
  }
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  stepParams.value.service = props.workflowStep.service;
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.LOADING_COMPLETE) {
    // Load the ESDL upon loading of this step.
    clearLayersAndLoadEsdl();
  }
};

</script>
