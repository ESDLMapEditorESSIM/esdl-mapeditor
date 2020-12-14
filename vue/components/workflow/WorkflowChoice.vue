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

export const { goToStep } = useWorkflow();

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

export const options = props.workflowStep.options;
</script>
