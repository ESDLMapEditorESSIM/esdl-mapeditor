<template>
  <a-button
    v-if="workflowStep.next_step != null &&
      stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
    type="primary"
    @click="() => goToStep(stepParams.nextStep)"
  >
    {{ stepParams.buttonText }}
  </a-button>
  <div v-else>
    <a-button @click="startOver">Back to beginning</a-button>
  </div>
</template>

<script setup="props">
import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";
import {onMounted, ref} from "vue";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const {getWorkflowStepParameters, goToStep, startOver} = useWorkflow();
/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});

onMounted(() => {
  init();
});

const init = () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
}
</script>
