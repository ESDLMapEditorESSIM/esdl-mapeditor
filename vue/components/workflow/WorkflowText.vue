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

const workflowStep = props.workflowStep;
</script>
