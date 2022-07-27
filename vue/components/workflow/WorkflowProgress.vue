<template>
  <p>
    Please refer to the active process view in the bottom left for the current status.
  </p>
  <next-or-close :workflow-step="workflowStep" />
</template>

<script setup="props">
import { useWorkflow } from '../../composables/workflow';
import { useLongProcessState } from '../../composables/longProcess';
import { defineProps } from 'vue'
// eslint-disable-next-line no-unused-vars
import { default as NextOrClose } from "./NextOrClose";

const { showActiveLongProcess, startLongProcess } = useLongProcessState();
const { getParamsFromState } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const requestParams = getParamsFromState(workflowStep.source.request_params);
requestParams['url'] = workflowStep.source.url;
const queryString = new URLSearchParams(requestParams).toString();
const progressUrl = `workflow/get_data?${queryString}`;
startLongProcess(workflowStep.name, progressUrl, workflowStep.source.progress_field, workflowStep.source.message_field, workflowStep.source.failed_field)

showActiveLongProcess.value = true;

</script>
