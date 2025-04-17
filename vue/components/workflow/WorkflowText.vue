<template>
  <p v-if="isLoading">Loading...</p>
  <div v-else>
    <!-- eslint-disable vue/no-v-html -->
    <p v-html="text" />
    <a-button
      v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
      type="primary"
      @click="() => goToStep(stepParams.nextStep)"
    >
      {{ stepParams.buttonText }}
    </a-button>
  </div>
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

/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const text = ref("");
const isLoading = ref(true);

const {getWorkflowStepParameters, getInputData, goToStep} = useWorkflow();

const updateData = (data) => {
  if (typeof data !== "string") {
    data = Object.values(data).join("");
  }
  text.value = data;
  isLoading.value = false;
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  try {
    await getInputData(stepParams.value.data, updateData);
  } catch (error) {
    console.error("Error fetching input data:", error);
    updateData("Error fetching input data.");
  }
};
</script>
