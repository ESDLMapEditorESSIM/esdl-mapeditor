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
import {defineProps, ref} from "vue";
import {useWorkflow} from "../../composables/workflow.js";
import {workflowGetData, workflowPostData} from "./utils/api.js";
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

const { goToNextStep } = useWorkflow();

const doGetData = async () => {
  const data = await workflowGetData(workflowStep.url, {})
        // if (data == null || data == undefined) {
        //   alert("No data received.");
        //   return;
        // }
  schema.value = data.definitions[workflowStep.schema_name];
  isLoading.value = false;
}
doGetData();

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