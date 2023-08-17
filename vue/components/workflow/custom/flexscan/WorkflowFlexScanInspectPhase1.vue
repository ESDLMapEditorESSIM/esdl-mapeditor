<template>
  <p>
    Here you can find an overview of the FlexScan phase 1 results.
  </p>
  <p>
    For now you can view the results in the FlexScan Dashoard.
    If you have not yet confirmed these results, you can change them there.
  </p>
  <a-button type="primary" :href="flexDashboardResultUrl" target="_blank" >Go to FlexScan F1 results dashboard</a-button>
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

const flexDashboardResultUrl = workflowStep.custom_data.flex_frontend_host + "/#/scans/" + getFromState("execution.id") + "/phase1";
</script>
