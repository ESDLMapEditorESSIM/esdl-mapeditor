<template>
  <p v-html="text" />
  <a-button v-if="showButton" type="primary" @click="goToNextStep">{{ buttonText }}</a-button>
</template>

<script setup="props">
import {ref, watch} from "vue";
import {useWorkflow} from "@/composables/workflow";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

let workflowStep = props.workflowStep;
let workflowTrigger = props.workflowStep.workflowTrigger;
watch(workflowTrigger, (currentValue, oldValue) => {
  init();
});

const text = ref("");
let showButton = false;
let buttonText = "";

const {getFromState, goToNextStep} = useWorkflow();

const handleData = (data) => {
  text.value = data;
}

const doGetData = () => {
  if ("from_socket_emit" in workflowStep.data) {
    const fromSocketEmit = workflowStep.data.from_socket_emit;
    let params = fromSocketEmit.params;
    if ("state_params" in fromSocketEmit) {
      for (const [key, state_key] of Object.entries(fromSocketEmit.state_params)) {
        params[key] = getFromState(state_key);
      }
    }
    window.socket.emit(fromSocketEmit.event, fromSocketEmit.params, (res) => {
      handleData(res);
    });
  } else {
    handleData(workflowStep.text);
  }
};

const init = () => {
  workflowStep = props.workflowStep;
  workflowTrigger = props.workflowStep.workflowTrigger;
  buttonText = workflowStep.button || "Submit";
  showButton = !!("showButton" in workflowStep && workflowStep.showButton);
  doGetData();
};
init();
</script>
