<template>
  <h2>Run name: {{ runName }}</h2>
  <div v-for="(stepProgress, key) in stepsProgress" :key="key">
    <hr>
    <h3>{{ stepProgress["name"] }}</h3>
    <a-progress
      v-if="stepProgress['progress_fraction'] !== null"
      :percent="getProgressPercent(stepProgress)"
      :status="getProgressStatus(stepProgress)"
    />
    <p v-if="stepProgress['status'] !== null">Status: {{ stepProgress["status"] }}</p>
    <!-- eslint-disable vue/no-v-html (sanitized with DOMPurify) -->
    <p v-if="stepProgress['message'] !== null" v-html="DOMPurify.sanitize(stepProgress['message'], {ADD_ATTR: ['target', 'rel']})" />
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
import DOMPurify from "dompurify";

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
