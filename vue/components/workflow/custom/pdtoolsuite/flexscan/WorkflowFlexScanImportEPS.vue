<template>
  <p>
    In the Flex Scan, the capacities of current and future flex assets on the business park can be estimated.
  </p>
  <p>
    Click the button below to navigate to the Flex Scan dashboard. In this dashboard, you can import the EPS data, run the Flex Scan phase 1, and edit/correct its results if more information is available.
  </p>
  <p>
    After a successful Flex Scan phase 1 run in the Flex Scan dashboard, the results can be added to the baseline energy system ESDL in the next step: Load FS phase 1 results.
  </p>
  <a-button type="primary" :href="flexDashboardImportEPSUrl" style="color: #fff" target="_blank">Go to Flex Scan dashboard</a-button>
</template>

<script setup="props">
import {defineProps} from "vue";
import {useWorkflow} from "../../../../../composables/workflow.js";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});
const workflowStep = props.workflowStep;
const { getFromState } = useWorkflow();

// eslint-disable-next-line no-unused-vars
const flexDashboardImportEPSUrl = workflowStep.custom_data.flex_frontend_host + "/#/eps/" + getFromState("execution.id");
</script>