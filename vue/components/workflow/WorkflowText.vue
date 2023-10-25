<template>
  <p>
    {{ workflowStep.text }}
  </p>
</template>

<script setup="props">
import { defineProps } from 'vue'

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const workflowStep = props.workflowStep;
</script>
