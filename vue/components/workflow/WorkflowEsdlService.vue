<template>
  <p>Please select the "Load ESDL" button below to call the ESDL service.</p>
  <a-button type="primary" @click="loadEsdl">
    Load ESDL
  </a-button>
</template>

<script setup="props">
import { ref } from "vue";
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

export const esdlLoaded = ref(false);
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
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
  goToNextStep();
};

if (workflowStep.service.auto) {
  // Load the ESDL upon loading of this step.
  loadEsdl();
}
</script>
