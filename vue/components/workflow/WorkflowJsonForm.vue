<template>
  <p v-if="isLoading">Loading...</p>

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
import {defineProps, ref} from "vue";
import {useWorkflow} from "../../composables/workflow.js";
import {workflowGetJsonForm, workflowPostData} from "./utils/api.js";
import { JsonForms } from "@jsonforms/vue";
// eslint-disable-next-line no-unused-vars
import {defaultStyles, mergeStyles, vanillaRenderers,} from "@jsonforms/vue-vanilla";
// eslint-disable-next-line no-unused-vars
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

const schema = ref({});
// eslint-disable-next-line no-unused-vars
const formData = {};
const dataToSubmit = {};
const isLoading = ref(true);

const { goToNextStep, getState } = useWorkflow();

const doGetData = async () => {
   schema.value = await workflowGetJsonForm(workflowStep.url, workflowStep.data.schema_name)
  isLoading.value = false;
}
if (workflowStep.url) {
  // Retrieve schema remotely.
  doGetData();
} else {
  // Retrieve schema from workflowStep.
  schema.value = workflowStep.data.schema;
  isLoading.value = false;
}

// eslint-disable-next-line no-unused-vars
const onChange = (event) => {
  Object.assign(dataToSubmit, event.data)
};


// eslint-disable-next-line no-unused-vars
const onSubmit = async () => {
  // Add data to state.
  const state = getState();
  Object.assign(state, dataToSubmit);
  if (workflowStep.url) {
    // POST data to remote URL.
    isLoading.value = true;

    try {
      const response = await workflowPostData(workflowStep.url, dataToSubmit);
      if (response != null && response.ok && workflowStep.auto) {
        goToNextStep();
      }
    } finally {
      isLoading.value = false;
    }
  } else {
    goToNextStep();
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