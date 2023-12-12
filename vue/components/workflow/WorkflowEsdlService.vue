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
    <a-button v-else type="primary" @click="esdlWasLoaded()"> ESDL was loaded </a-button>
  </div>
  <div v-else>
    <p v-if="workflowStep.service.description">
      {{ workflowStep.service.description }}
    </p>
    <p v-else>
      Please select the "Run ESDL service" button below to run the ESDL service
      and load the results.
    </p>
    <a-button v-if="!workflowStep.service.auto" type="primary" @click="clearLayersAndLoadEsdl">
      <div v-if="workflowStep.service.button_label"> {{ workflowStep.service.button_label }} </div>
      <div v-else>
        Run ESDL service
      </div>
    </a-button>
    <div id="service_results_div" />
  </div>
</template>

<script setup="props">
 // more info on service_results_div @see esdl_services.js

import { useWorkflow } from "../../composables/workflow.js";
import { useEsdlLayers } from "../../composables/esdlLayers.js";
import { defineProps } from 'vue'
// eslint-disable-next-line no-unused-vars

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { getParamsFromState, goToPreviousStep, goToFirstStep } = useWorkflow();
const { clearEsdlLayers } = useEsdlLayers()

const workflowStep = props.workflowStep;

const esdlWasLoaded = () => {
  goToFirstStep();
}

const clearLayersAndLoadEsdl = () => {
  if (workflowStep.service.clearLayers) {
    clearEsdlLayers();
    // Allow a second for the layers to be cleared.
    setTimeout(loadEsdl, 1000);
  } else {
    loadEsdl();
  }
}

const loadEsdl = () => {
  let params = {};
  params["service_id"] = workflowStep.service.id;

  if (workflowStep["state_params"]) {
    params["query_parameters"] = getParamsFromState(workflowStep["state_params"]);
  } else {
    params["query_parameters"] = {};
  }

  window.show_loader();
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
};

if (workflowStep.service.auto) {
  // Load the ESDL upon loading of this step.
  clearLayersAndLoadEsdl();
}

</script>
