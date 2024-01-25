<template>
  <p>
    In the FlexSCan, the capacities of current and future flex assets on the business park can be estimated.
  </p>
  <p>
    Click the button below to navigate to the FlexScan dashboard. In this dashboard, you can import the EPS data, run the FlexScan phase 1, and edit/correct its results if more information is available.
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