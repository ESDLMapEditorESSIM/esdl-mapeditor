<template>
  <p>
    Please refer to the active process view in the bottom left for the current status.
  </p>
</template>

<script setup="props">
import { useWorkflow } from '../../composables/workflow';
import { useLongProcessState } from '../../composables/longProcess';

export const { activeLongProcess, showActiveLongProcess, startLongProcess } = useLongProcessState();
const { getFromState } = useWorkflow();

export default {
  inheritAttrs: false,
  props: {
    workflowStep: {
      type: Object,
      default: null,
      required: true,
    },
  },
}

const workflowStep = props.workflowStep;

const requestParams = getFromState(workflowStep.source.request_params);
requestParams['url'] = workflowStep.source.url;
const queryString = new URLSearchParams(requestParams).toString();
const progressUrl = `workflow/get_data?${queryString}`;
startLongProcess(workflowStep.name, progressUrl, workflowStep.source.progress_field, workflowStep.source.message_field)

showActiveLongProcess.value = true;

</script>
