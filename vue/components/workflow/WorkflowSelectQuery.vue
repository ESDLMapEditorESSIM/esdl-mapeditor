<template>
  <p v-if="isLoading">Loading...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
      <a-select v-model:value="form[workflowStep.target_variable]" :options="options" />
    </a-form-item>
    <a-form-item>
      <a-button type="primary" @click="onSubmit"> Select </a-button>
    </a-form-item>
  </a-form>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {useWorkflow} from "../../composables/workflow.js";
import {workflowGetData} from "./utils/api.js";

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
const form = {};
form[workflowStep.target_variable] = "";

const { getParamsFromState, goToNextStep, getState } = useWorkflow();
const state = getState();

// Variable for indexing all choices by the value (which is rendered in HTML).
let choicesByValue;

// eslint-disable-next-line no-unused-vars
const onSubmit = () => {
  const value = form[workflowStep.target_variable];
  if (!value) {
    alert("Please select a valid option.");
    return;
  }
  state[workflowStep.target_variable] = choicesByValue.get(value);
  goToNextStep();
};

const doGetData = async () => {
  const request_params = getParamsFromState(workflowStep.source.request_params);
  const data = await workflowGetData(workflowStep.source.url, request_params)
  // if (data == null) {
  //   alert("No data received.");
  //   return;
  // }
  if (data != null) {
    const source = workflowStep.source;
    let choices = [];
    // Choices data can be found as an attribute in a dict or is directly returned as a list
    if ("choices_attr" in source) {
      choices = data[source.choices_attr];
    } else {
      choices = data;
    }

    // Convert the choices to a list of options.
    options.value = choices.map((choice) => {
      const label_list = source.label_fields
          .map((label_field) => choice[label_field])
          .filter((value) => value);
      const label = label_list.join(" - ");
      return {
        label: label,
        value: choice[source.value_field],
      };
    });
    // Index all choices by value, so we can store them in the state entirely.
    choicesByValue = new Map(
        choices.map((choice) => [choice[source.value_field], choice])
    );
  }
  isLoading.value = false;
}
doGetData();
</script>
