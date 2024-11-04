<template>
  <div v-if="workflowStep.service.auto">
    <p v-if="workflowStep.service.description">
      {{ workflowStep.service.description }}
    </p>
    <p v-else>
      The ESDL service will be called automatically. Please click the button below when the ESDL was loaded fully.
    </p>
    <div id="service_results_div" />
    <a-button v-if="workflowStep.service.button_label" type="primary" @click="goToPreviousStep()">
      {{ workflowStep.service.button_label }}
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
    <a-button v-if="!workflowStep.service.auto" type="primary" :disabled="buttonDisabled" @click="clearLayersAndLoadEsdl">
      <div v-if="workflowStep.service.button_label"> {{ workflowStep.service.button_label }}</div>
      <div v-else>
        Run ESDL service
      </div>
    </a-button>
    <div id="service_results_div" />
  </div>
</template>

<script setup="props">
import {setattrd} from "@/utils/utils";

import {RESET_WORKFLOW, useWorkflow} from "@/composables/workflow";
import {useEsdlLayers} from "@/composables/esdlLayers";
import {onMounted, ref, watch} from "vue";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const {getParamsFromState, goToPreviousStep, goToFirstStep, getState, goToStep, isAllInputValid} = useWorkflow();
const state = getState();
const {clearEsdlLayers} = useEsdlLayers()

const workflowStep = props.workflowStep;
let workflowTrigger = props.workflowStep.workflowTrigger;
const buttonDisabled = ref(false);

onMounted(() => {
  init(true);
});

watch(workflowTrigger, (currentValue) => {
  init(currentValue[RESET_WORKFLOW]);
});

const esdlWasLoaded = () => {
  if (workflowStep.target_variable && workflowStep.target_variable_value) {
    setattrd(state, workflowStep.target_variable, workflowStep.target_variable_value);
  }
  goToFirstStep();
};

const clearLayersAndLoadEsdl = () => {
  if (workflowStep.service.clearLayers) {
    clearEsdlLayers();
    // Allow a second for the layers to be cleared.
    setTimeout(loadEsdl, 1000);
  } else {
    loadEsdl();
  }
};

const loadEsdl = () => {
  let params = {};
  params["service_id"] = workflowStep.service.id;

  if (workflowStep["state_params"]) {
    params["state_params"] = getParamsFromState(workflowStep["state_params"]);
  } else {
    params["state_params"] = {};
  }

  window.show_loader();

  if (workflowStep["workflow_engine_trigger"]) {
    params["type"] = "esdl_service"
    params["main_service_id"] = workflowStep.main_service_id;

    params["run_name_key"] = workflowStep.workflow_engine_run_name;
    params["workflow_engine_next_step"] = workflowStep.workflow_engine_next_step;

    window.socket.emit("wfe_initialize_sequence", params, (sequenceId) => {
      Object.assign(getState(), {"wfeSequenceId": sequenceId});

      goToStep(workflowStep["next_step"]);
      window.hide_loader();
    });
  } else {
    window.socket.emit("command", {cmd: "query_esdl_service", params: params}, () => {
      goToStep(workflowStep["next_step"]);
    });
  }
};

const init = (reset) => {
  if (reset && workflowStep.service.auto) {
    // Load the ESDL upon loading of this step.
    clearLayersAndLoadEsdl();
  }
  buttonDisabled.value = !isAllInputValid();
};

</script>
