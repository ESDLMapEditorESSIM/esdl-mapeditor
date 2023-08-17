<template>
  <div class="choice-list">
    <div
      v-for="option in options"
      :key="option.name"
      class="choice-entry"
    >
      <div
        v-if="option.type === 'header'"
        class="choice-header"
      >
        {{ option.name }}
      </div>
      <a-button
        v-else
        :type="option.type || 'primary'"
        block
        :disabled="isOptionDisabled(option)"
        @click="goToStep(option.next_step)"
        class="choice-button"
      >
        {{ option.name }}
      </a-button>
      <p v-if="option.description">{{ option.description }}</p>
    </div>
  </div>
</template>

<script setup="props">
import {useWorkflow} from '../../composables/workflow';
import {defineProps} from 'vue'

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { getFromState, goToStep } = useWorkflow();
// eslint-disable-next-line no-unused-vars
const options = props.workflowStep.options;

// eslint-disable-next-line no-unused-vars
const isOptionDisabled = (option) => {
  if (option.disabled) {
    return true;
  }
  if (option.disable_if_state && option.enable_if_state){
    const disableStateField = getFromState(option.disable_if_state)
    const enableStateField = getFromState(option.enable_if_state)
    return Boolean(disableStateField) || !enableStateField; 
  }
  if (option.disable_if_state) {
    const stateField = getFromState(option.disable_if_state);
    return Boolean(stateField);
  }
  if (option.enable_if_state) {
    const stateField = getFromState(option.enable_if_state);
    return !stateField;
  }
  return false;
}

</script>

<style scoped>
.choice-list .choice-entry {
  margin-bottom: 10px;
}
.choice-list .choice-entry .choice-button {
  border-radius: 16px;
}
.choice-list .choice-entry p {
  margin-bottom: 0;
  color: #777;
}
.choice-list .choice-entry .choice-header {
  text-align: center;
  font-weight: bolder;
}
</style>
