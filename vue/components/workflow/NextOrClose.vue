<template>
  <a-button v-if="workflowStep.next_step != null" type="primary" @click="goToNextStep"> Next </a-button>
  <div v-else>
    <a-button @click="startOver"> Back to beginning </a-button>
  </div>
</template>

<script setup="props">
import { defineProps } from "vue";
import { useWorkflow } from "../../composables/workflow.js";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { goToNextStep, startOver } = useWorkflow();
// eslint-disable-next-line no-unused-vars
const workflowStep = props.workflowStep;

</script>
