<template>
  <p>Run name: {{ runName }}</p>
  <div v-for="(stepProgress, key) in stepsProgress" :key="key">
    <hr>
    <p>{{ stepProgress["name"] }}</p>
    <a-progress :percent="getProgressPercent(stepProgress)" :status="getProgressStatus(stepProgress)" />
    <p>Status: {{ stepProgress["status"] }}</p>
  </div>
  <a-button
    v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
    type="primary"
    @click="() => goToStep(stepParams.nextStep)"
  >
    {{ stepParams.buttonText }}
  </a-button>
</template>

<script setup="props">
import {onMounted, ref, watch} from "vue";
import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const {getWorkflowStepParameters, goToStep, getState} = useWorkflow();
/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});
let wfeSequenceId = null;
const runName = ref(null);
const stepsProgress = ref();

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const getProgressStatus = (stepProgress) => {
  if (["SUBMITTED", "RUNNING"].includes(stepProgress["status"])) {
    return "normal";
  } else if (["SUCCEEDED", "NEED_INPUT"].includes(stepProgress["status"])) {
    return "success";
  } else if (["CANCELLED", "ERROR"].includes(stepProgress["status"])) {
    return "exception";
  }
};

const getProgressPercent = (stepProgress) => {
  if (stepProgress["status"] === "SUCCEEDED") {
    return 100;
  }
  const progress_fraction = stepProgress["progress_fraction"];
  if (!isNaN(progress_fraction)) {
    return Math.round(100 * progress_fraction);
  }
};

const init = () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  wfeSequenceId = getState().wfeSequenceId;

  // console.log("Registering socket io bindings for WorkflowEngineMonitor");
  window.socket.off('wfe_sequence_progress');
  window.socket.on('wfe_sequence_progress', (data) => {
    if (wfeSequenceId === data["wfe_sequence_id"]) {
      runName.value = data["run_name"];
      stepsProgress.value = data["steps_progress"];
    }
  });
};
</script>
