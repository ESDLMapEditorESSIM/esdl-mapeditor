<template>
  <p v-if="isLoading">Confirming Phase 1 results...</p>
  <p v-else-if="message != ''">
    {{ message }}
    <next-or-close :workflow-step="workflowStep" />
  </p>
  <div v-else>
    <p>
      You are about to confirm the FlexScan phase 1, this means you won't be able to change it in the future.
    </p>
    <a-button type="primary" @click="confirmPhase1()">Confirm</a-button>
  </div>
</template>

<script setup="props">
import { defineProps, ref } from "vue";
import { useWorkflow } from "../../../../composables/workflow.js";
import { default as NextOrClose } from "../../NextOrClose";
import { workflowPostData } from "../../utils/api.js";
import { genericErrorHandler } from "../../../../utils/errors";

const workflowStep = props.workflowStep;
const { getFromState, getState, goToNextStep } = useWorkflow();
const state = getState()

const confirmFlexScanPhase1ResultsUrl = workflowStep.custom_data.flex_backend_host + "/executions/" + getFromState("execution.id") + "/phase1/confirm";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const isLoading = ref(false);
const message = ref("");

const confirmPhase1 = async () => {
  isLoading.value = true;
  try {
    const response = await workflowPostData(confirmFlexScanPhase1ResultsUrl, {});
    if (response != null) {
      if (response.ok) {
        message.value = "Phase 1 results confirmed.";
        state[workflowStep.target_variable].confirmed = true;
      }
      if (response.ok && workflowStep.auto) {
        goToNextStep();
      }
    }
  } catch (e) {
    genericErrorHandler(e);
  } finally {
    isLoading.value = false;
  }
}
</script>
