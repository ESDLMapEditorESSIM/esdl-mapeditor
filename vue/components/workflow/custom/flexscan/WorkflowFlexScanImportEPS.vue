<template>
  <p>
    Click the button below to navigate to the FlexScan dashboard where you can import the EPS data.
  </p>
  <p>
    Here, you can also edit the calculated FlexScan phase 1 results and accept them when they are correct.
  </p>
  <a-button type="primary" :href="flexDashboardImportEPSUrl" target="_blank">Go to FlexScan dashboard</a-button>
</template>

<script setup="props">
import {defineProps} from "vue";
import {useWorkflow} from "../../../../composables/workflow.js";

const workflowStep = props.workflowStep;
const { getFromState } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const flexDashboardImportEPSUrl = workflowStep.custom_data.flex_frontend_host + "/#/eps/" + getFromState("execution.id");
</script>