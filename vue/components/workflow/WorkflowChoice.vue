<template>
  <div>
    <a-button-group>
      <a-button
        v-for="option in options"
        :key="option.name"
        type="primary"
        :disabled="option.disabled"
        @click="goToStep(option.next_step)"
      >
        {{ option.name }}
      </a-button>
    </a-button-group>
  </div>
</template>

<script setup="props">
import { useWorkflow } from '../../composables/workflow';
import { defineProps } from 'vue'

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const { goToStep } = useWorkflow();
const options = props.workflowStep.options;
</script>
