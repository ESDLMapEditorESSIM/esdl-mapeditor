<template>
  <div v-if="workflowStep.service.auto">
    <p>
      The ESDL service will be called automatically. Please click the button below when the ESDL was loaded fully.
    </p>
    <a-button type="primary" @click="esdlWasLoaded()"> ESDL was loaded </a-button>
  </div>
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
</template>

<script setup="props">
import {useWorkflow} from "../../composables/workflow.js";
import {useEsdlLayers} from "../../composables/esdlLayers.js";
import {defineProps} from 'vue'
// eslint-disable-next-line no-unused-vars

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { getParamsFromState, setWorkflowName, goToFirstStep, getState } = useWorkflow();
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
  window.socket.on('esdl_service_result', function(results) {
    setWorkflowName(results.es_name)
  });
};

if (workflowStep.service.auto) {
  // Load the ESDL upon loading of this step.
  clearLayersAndLoadEsdl();
}

</script>
