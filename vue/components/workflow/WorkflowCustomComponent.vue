<template>
  <div>
    <component
      :is="current"
      :workflow-step="workflowStep"
    />
  </div>
</template>

<script setup="props">
import { default as WorkflowEpsInspectResult } from './custom/WorkflowEpsInspectResult';
import { defineProps } from 'vue'

const components = {
  "eps-inspect-result": WorkflowEpsInspectResult,
};
const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;
// The current custom component.
// eslint-disable-next-line no-unused-vars
const current = components[workflowStep.component];

</script>
