<template>
  <p v-if="workflowStep.service.auto">
    The ESDL service will be called automatically. Please click next when the ESDL is visible on the map.
  </p>
  <div v-else>
    <p>
      Please select the "Run ESDL service" button below to run the ESDL service
      and load the results.
    </p>
    <a-button
      v-if="!workflowStep.service.auto"
      type="primary"
      @click="clearLayersAndLoadEsdl"
    >
      Run ESDL service
    </a-button>
  </div>
  <next-or-close :workflow-step="workflowStep" />
</template>

<script setup="props">
import { useWorkflow } from "../../composables/workflow.js";
import { useEsdlLayers } from "../../composables/esdlLayers.js";
import { defineProps } from 'vue'
// eslint-disable-next-line no-unused-vars
import { default as NextOrClose } from "./NextOrClose";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { getFromState, getParamsFromState, goToNextStep } = useWorkflow();
const { clearEsdlLayers } = useEsdlLayers()

const workflowStep = props.workflowStep;

const clearLayersAndLoadEsdl = () => {
  if (workflowStep.service.clearLayers) {
    clearEsdlLayers();
    setTimeout(loadEsdl, 1000);
  } else {
    loadEsdl();
  }
}

const loadEsdl = () => {
  let params = {};
  params["service_id"] = workflowStep.service.id;

  params["query_parameters"] = getParamsFromState(workflowStep["state_params"]);

  window.show_loader();
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
};

if (workflowStep.service.auto) {
  // Load the ESDL upon loading of this step.
  clearLayersAndLoadEsdl();
}
</script>
