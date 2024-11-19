<template>
  <p v-if="isLoading">Loading...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
      <a-select
        v-model:value="form[workflowStep.target_variable]" :options="options" @change="selectValue"
        @popup-scroll="hide_jquery_ui_popup()"
      />
    </a-form-item>
    <a-form-item>
      <a-button type="primary" @click="onSubmit"> Select </a-button>
    </a-form-item>
  </a-form>
</template>

<script setup="props">
import {ref} from "vue";
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
const form = ref({});
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

const selectValue = (value) => {
  form[workflowStep.target_variable] = value;
}

const doGetData = async () => {
  const request_params = getParamsFromState(workflowStep.source.request_params);
  const data = await workflowGetData(workflowStep.source.url, request_params)

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
      const label_list = [];
      for (const label_field of source.label_fields) {
        // Check if label is string. If so, use it directly.
        if (typeof label_field === "string") {
          label_list.push(choice[label_field]);
        } else {
          const label = label_field.label;
          const default_value = label_field.default;
          const value = choice[label];
          const value_map = label_field.map;
          if (value_map && value in value_map) {
            label_list.push(value_map[value]);
          } else if (default_value) {
            label_list.push(default_value);
          } else {
            label_list.push(value);
          }
        }
      }
      const label = label_list.filter((value) => value).join(" - ");
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

function hide_jquery_ui_popup() {
  window.jquery(".ui-tooltip-content").parents('div').remove();
}
</script>
