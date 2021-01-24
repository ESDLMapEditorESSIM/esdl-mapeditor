<template>
  <div>
    <input
      v-for="el in hidden_elements"
      :id="el.id"
      :key="el.id"
      type="hidden"
      :value="el.state_param_nam"
    >
    <a-button-group>
      <a-button type="primary" @click="callFunction()">
        {{ button_name }}
      </a-button>
    </a-button-group>
  </div>
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

const dom_elements = workflowStep["dom_elements"];
const hidden_elements = [];
for (const [id, state_param_name] of Object.entries(dom_elements)) {
  const param = this.state[state_param_name];
  hidden_elements.append({ id: id, value: param });
}

const callFunction = () => {
  const js_function_name = workflowStep["js_function"];
  window[js_function_name](...workflowStep.parameters);
};
</script>
