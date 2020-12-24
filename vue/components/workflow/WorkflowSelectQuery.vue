<template>
  <p v-if="isLoading">
    Loading...
  </p>
  <a-form
    v-else
    :model="form"
    :label-col="{ span: 0 }"
  >
    <a-form-item :label="workflowStep.name">
      <a-select v-model:value="form[workflowStep.target_variable]">
        <a-select-option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </a-select-option>
      </a-select>
    </a-form-item>
    <a-button
      type="primary"
      @click="onSubmit"
    >
      Select
    </a-button>
  </a-form>
</template>

<script setup="props">
import { ref } from 'vue';
import { genericErrorHandler } from '../../utils/errors.js'
import { useWorkflow } from '../../composables/workflow.js';
import { defineProps } from 'vue'

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const isLoading = ref(true);
const options = ref([]);
const form = {}
form[workflowStep.target_variable] = '';

const { goToNextStep, getState } = useWorkflow();
const state = getState();

const onSubmit = () => {
  const value = form[workflowStep.target_variable];
  if (!value) {
    alert("Please select a valid option.");
    return;
  }
  state[workflowStep.target_variable] = value;
  goToNextStep();
}

const request_params = {};
request_params['url'] = workflowStep.source.url;
const queryString = new URLSearchParams(request_params).toString();
fetch(`workflow/get_data?${queryString}`)
  .then(response => response.json())
  .then(data => {
    const source = workflowStep.source;
    const entities = data[source.choices_attr];
    options.value = entities.map(entity => {
      const label_list = source.label_fields.map(label_field => entity[label_field]).filter(value => value);
      const label = label_list.join(' - ');
      return {
        'label': label,
        'value': entity[source.value_field]
      };
    });
  })
  .catch(genericErrorHandler)
  .finally(() => isLoading.value = false);

</script>
