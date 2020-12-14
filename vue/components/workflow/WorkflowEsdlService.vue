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
  <a-button type="primary" @click="goToNextStep"> Next </a-button>
</template>

<script setup="props">
import { useWorkflow } from "../../composables/workflow.js";

export default {
  inheritAttrs: false,
  props: {
    workflowStep: {
      type: Object,
      default: null,
      required: true,
    },
  },
};

export const { goToNextStep } = useWorkflow();
const { getState } = useWorkflow();
const state = getState();

export const workflowStep = props.workflowStep;

export const loadEsdl = () => {
  let params = {};
  params["service_id"] = workflowStep.service.id;

  params["query_parameters"] = {};
  let q_params = workflowStep.service["query_parameters"];
  for (let i = 0; i < q_params.length; i++) {
    let parameter_name = q_params[i]["parameter_name"];
    let parameter_value = state[parameter_name];
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
