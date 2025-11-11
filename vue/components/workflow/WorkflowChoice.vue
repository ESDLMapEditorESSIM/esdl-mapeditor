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
      <div
        v-else-if="option.type === 'subheader'"
        class="choice-subheader"
      >
        {{ option.name }}
      </div>
      <a-button
        v-else
        :type="option.type || 'primary'"
        block
        ghost
        :disabled="isOptionDisabled(option)"
        class="choice-button"
        @click="optionClick(option)"
      >
        {{ option.name }}
      </a-button>
      <p v-if="option.description">{{ option.description }}</p>
    </div>
  </div>
</template>

<script setup="props">
import {setattrd} from "../../utils/utils.js";
import {useWorkflow} from '../../composables/workflow';

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

// eslint-disable-next-line no-unused-vars
const { getFromState, goToStep, getState } = useWorkflow();
const state = getState();
// eslint-disable-next-line no-unused-vars
const options = props.workflowStep.options;

const everyCondition = (conditions) => {
  return conditions.every((condition) => Boolean(getFromState(condition)));
}

const someCondition = (conditions) => {
  return conditions.some((condition) => Boolean(getFromState(condition)));
}

// eslint-disable-next-line no-unused-vars
const isOptionDisabled = (option) => {
  if (option.disabled) {
    return true;
  }

  const ifStateConditionsMet = (if_state) => {
    if (typeof if_state === "object") {
      if (!if_state.type || !if_state.conditions) {
        throw new Error("Incorrect if_state structure");
      }

      if (if_state.type === "every") {
        return everyCondition(if_state.conditions);
      } else if (if_state.type === "some") {
        return someCondition(if_state.conditions);
      } else {
        throw new Error("Invalid if_state type:", if_state);
      }
    }

    return Boolean(getFromState(if_state));
  }

  const shouldBeDisabled = option.disable_if_state ? ifStateConditionsMet(option.disable_if_state) : false;
  const shouldBeEnabled = option.enable_if_state ? ifStateConditionsMet(option.enable_if_state) : true;

  return shouldBeDisabled || !shouldBeEnabled;
}

// eslint-disable-next-line no-unused-vars
const optionClick = (option) => {
  if (props.workflowStep.target_variable && option.target_variable_value){
    setattrd(state, props.workflowStep.target_variable, option.target_variable_value);
  }

  goToStep(option.next_step);
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
  font-size: 1.5em;
}
.choice-list .choice-entry .choice-subheader {
  text-align: center;
  font-size: 1.2em;
  color: #333;
}
</style>
