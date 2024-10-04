<template>
  <p>Run name: {{ runName }}</p>
  <div v-for="(stepProgress, key) in stepsProgress" :key="key">
    <hr>
    <p>{{ stepProgress["name"] }}</p>
    <a-progress :percent="getProgressPercent(stepProgress)" :status="getProgressStatus(stepProgress)" />
    <p>Status: {{ stepProgress["status"] }}</p>
  </div>
  <a-button v-if="showButton" type="primary" @click="goToNextStep">{{ buttonText }}</a-button>
</template>

<script setup="props">
import {onMounted, ref, watch} from "vue";
import {useWorkflow} from "@/composables/workflow";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const {goToNextStep, getState} = useWorkflow();
let workflowStep = props.workflowStep;
let wfeSequenceId = null;
const runName = ref(null);
const stepsProgress = ref();

let workflowTrigger = props.workflowStep.workflowTrigger;
// eslint-disable-next-line no-unused-vars
watch(workflowTrigger, (currentValue, oldValue) => {
  init();
});

onMounted(() => {
  init();
});

let showButton = false;
let buttonText = "";

const doGetData = () => {
  wfeSequenceId = getState().wfeSequenceId;
};

const getProgressStatus = (stepProgress) =>{
  if (["SUBMITTED", "RUNNING"].includes(stepProgress["status"])) {
    return "normal";
  } else if (["SUCCEEDED", "INPUT_NEEDED"].includes(stepProgress["status"])) {
    return "success";
  } else if (["CANCELLED", "ERROR"].includes(stepProgress["status"])) {
    return "exception";
  }
};

const getProgressPercent = (stepProgress) =>{
  if (stepProgress["status"]=== "SUCCEEDED") {
    return 100;
  }
  const progress_fraction = stepProgress["progress_fraction"];
  if (!isNaN(progress_fraction)) {
    return 100 * progress_fraction;
  }
};

const updateValues = (data) =>{
  if (wfeSequenceId === data["wfe_sequence_id"]) {
      runName.value = data["run_name"];
      stepsProgress.value = data["steps_progress"];
    }
}

const init = () => {
  workflowStep = props.workflowStep;
  workflowTrigger = props.workflowStep.workflowTrigger;
  buttonText = workflowStep.button || "Submit";
  showButton = !!("showButton" in workflowStep && workflowStep.showButton);
  doGetData();

  console.log("Registering socket io bindings for WorkflowEngineMonitor");
  window.socket.off('wfe_sequence_progress');
  window.socket.on('wfe_sequence_progress', updateValues);
};
init();
</script>
