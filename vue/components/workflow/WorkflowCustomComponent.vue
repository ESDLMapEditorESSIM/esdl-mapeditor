<template>
  <div>
    <component
      :is="current"
      :workflow-step="workflowStep"
    />
    <a-button
      type="primary"
      @click="goToNextStep"
    >
      Next
    </a-button>
  </div>
</template>

<script setup="props">
import { useWorkflow } from '../../composables/workflow';
import { default as WorkflowEpsInspectResult } from './custom/WorkflowEpsInspectResult';

export default {
  components: {
    "eps-inspect-result": WorkflowEpsInspectResult,
  },
  inheritAttrs: false,
  props: {
    workflowStep: {
      type: Object,
      default: null,
      required: true,
    },
  },
}

export const { goToNextStep } = useWorkflow();
export const workflowStep = props.workflowStep;
// The current custom component (key in components map above).
export const current =  workflowStep.component;

</script>
