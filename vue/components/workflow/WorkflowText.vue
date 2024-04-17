<template>
  <p>
    {{ workflowStep.text }}
  </p>
</template>

<script setup="props">

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;
</script>
