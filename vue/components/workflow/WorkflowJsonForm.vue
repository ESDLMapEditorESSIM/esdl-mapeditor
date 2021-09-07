<template>
  <p v-if="isLoading">
    Loading...
    <spinner />
  </p>

  <div v-else>
    <json-forms
      :data="formData"
      :schema="schema"
      :renderers="renderers"
      @change="onChange"
    />

    <a-button type="primary" @click="onSubmit">{{ buttonText }}</a-button>
  </div>
</template>

<script setup="props">
import { ref } from "vue";
import { genericErrorHandler } from "../../utils/errors.js";
import { useWorkflow } from "../../composables/workflow.js";
import { defineProps } from "vue";
import { workflowPostData } from "./lib/api.js";
import { JsonForms } from "@jsonforms/vue";
import {
  defaultStyles,
  mergeStyles,
  vanillaRenderers,
} from "@jsonforms/vue-vanilla";
// eslint-disable-next-line no-unused-vars
import spinner from "../Spinner.vue";
import "@jsonforms/vue-vanilla/vanilla.css";

// eslint-disable-next-line no-unused-vars
const myStyles = mergeStyles(defaultStyles, { control: { label: "mylabel" } });

// eslint-disable-next-line no-unused-vars
const renderers = Object.freeze([...vanillaRenderers]);

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;
// eslint-disable-next-line no-unused-vars
const buttonText = workflowStep.button || "Submit";

const isLoading = ref(true);
const schema = ref({});
const formData = {};
const dataToSubmit = {};

const { goToNextStep } = useWorkflow();

const request_params = {};
request_params["url"] = workflowStep.url;
const queryString = new URLSearchParams(request_params).toString();

fetch(`workflow/get_options?${queryString}`)
  .then((response) => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error("No data received - status " + response.status);
    }
  })
  .then((data) => {
    if (data == null || data == undefined) {
      alert("No data received.");
      return;
    }
    schema.value = data.definitions[workflowStep.schema_name];
  })
  .catch(genericErrorHandler)
  .finally(() => (isLoading.value = false));


// eslint-disable-next-line no-unused-vars
const onChange = (event) => {
  Object.assign(dataToSubmit, event.data)
};


// eslint-disable-next-line no-unused-vars
const onSubmit = async () => {
  console.log("submit");
  console.log(dataToSubmit);
  isLoading.value = true;

  try {
    const response = workflowPostData(workflowStep.url, dataToSubmit);
    if (response != null && response.ok && workflowStep.auto) {
      goToNextStep();
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.vertical-layout-item {
  padding-bottom: 5px;
}
.array-list-label {
  font-size: 1rem;
}
</style>