<template>
  <p v-if="isLoading">Loading data...</p>
  <div v-else>
    <p v-if="errorMessage !== ''">
      {{ errorMessage }}
    </p>
    <a-button
      v-else-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
      type="primary"
      @click="onSubmit"
    >
      {{ stepParams.buttonText }}
    </a-button>
    <p v-if="errorMessage !== ''">
      {{ errorMessage }}
    </p>
    <div v-if="textBelowButton !== ''">
      <a-divider />
      <!-- eslint-disable vue/no-v-html -->
      <p v-html="textBelowButton" />
    </div>
  </div>
</template>

<script setup="props">
import {onMounted, ref, watch} from "vue";
import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";

const {getWorkflowStepParameters, goToStep, getInputData, sendOutputData} = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});
const isLoading = ref(true);
const errorMessage = ref("");
const textBelowButton = ref("");
const ioData = ref(null);

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  await getInputData(stepParams.value.data, onDataRetrieved);
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.LOADING_COMPLETE) {
    goToStep(stepParams.value.nextStep);
  } else {
    isLoading.value = false;
  }
};

const onDataRetrieved = async (data) => {
  if (stepParams.value.config && stepParams.value.config.text_below_button_variable) {
    textBelowButton.value = data[stepParams.value.config.text_below_button_variable];
  }
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.LOADING_COMPLETE) {
    await sendOutputData(stepParams.value.data, data, onDataSent);
  } else {
    ioData.value = data;
    isLoading.value = false;
  }
};
const onSubmit = async () => {
  await sendOutputData(stepParams.value.data, ioData.value, onDataSent);
};

const onDataSent = (responseOk) => {
  if (responseOk) {
    goToStep(stepParams.value.nextStep);
  } else {
    errorMessage.value = "Error submitting data.";
  }
  isLoading.value = false;
};
</script>

<style scoped>
</style>