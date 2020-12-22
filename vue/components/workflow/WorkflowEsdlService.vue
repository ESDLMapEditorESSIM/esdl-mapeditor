<template>
  <p v-if="workflowStep.service.auto">
    The ESDL service will be called automatically. Please click next when all data is loaded.
  </p>
  <div v-else>
    <p>
      Please select the "Run ESDL service" button below to run the ESDL service
      and load the results.
    </p>
    <a-button
      v-if="!workflowStep.service.auto"
      type="primary"
      @click="loadEsdl"
    >
      Run ESDL service
    </a-button>
  </div>
  <next-or-close workflow-step="workflowStep" />
</template>

<script setup="props">
import { useWorkflow } from "../../composables/workflow.js";
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
const { getFromState, goToNextStep } = useWorkflow();

const workflowStep = props.workflowStep;

const loadEsdl = () => {
  let params = {};
  params["service_id"] = workflowStep.service.id;

  params["query_parameters"] = {};
  let q_params = workflowStep.service["query_parameters"];
  for (let i = 0; i < q_params.length; i++) {
    let parameter_name = q_params[i]["parameter_name"];
    let parameter_value = getFromState(parameter_name);
    params["query_parameters"][parameter_name] = parameter_value;
  }

  window.hide_loader();
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
};

if (workflowStep.service.auto) {
  // Load the ESDL upon loading of this step.
  loadEsdl();
}
</script>
