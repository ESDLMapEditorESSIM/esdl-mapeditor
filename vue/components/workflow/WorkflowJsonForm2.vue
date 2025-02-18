<template>
  <p v-if="isLoading">Loading...</p>
  <div v-else-if="jsonFormDataReceived">
    <json-forms
      :data="formData"
      :schema="schema"
      :uischema="uischema"
      :renderers="renderers"
      :ajv="ajv"
      @change="onChange"
      @input="validateEvent"
      @keyup="validateEvent"
    />
    <a-button
      v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
      type="primary"
      :disabled="!isAllInputValid()"
      @click="onSubmit"
    >
      {{ stepParams.buttonText }}
    </a-button>
  </div>
</template>

<script setup="props">
import {onMounted, ref, watch} from "vue";
import {useWorkflow, WorkflowNextStepTriggerOptions} from "@/composables/workflow";
import {JsonForms} from "@jsonforms/vue";
import Ajv from "ajv";
import addFormats from "ajv-formats";

import {vanillaRenderers,} from "@jsonforms/vue-vanilla";
import "@jsonforms/vue-vanilla/vanilla.css";

const renderers = Object.freeze([...vanillaRenderers]);

const ajv = new Ajv({allErrors: true, useDefaults: true, $data: true});
addFormats(ajv);

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const stepParams = ref({});

const formData = ref({});
let schema = {};
let uischema = {};

const dataToSubmit = {};
const isLoading = ref(true);
const jsonFormDataReceived = ref(false);

const {
  getWorkflowStepParameters,
  goToStep,
  setWorkflowStepInputValid,
  getInputData,
  sendOutputData,
  isAllInputValid
} = useWorkflow();

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const updateData = (jsonFormData) => {
  jsonFormDataReceived.value = true;
  if (stepParams.value.config && stepParams.value.config.data_from_variable) {
    jsonFormData = jsonFormData[stepParams.value.config.data_from_variable];
  }
  if (jsonFormData && "schema" in jsonFormData) {
    schema = jsonFormData.schema;
  } else {
    schema = {};
    jsonFormDataReceived.value = false;
    setWorkflowStepInputValid(stepParams.value.id, true);
    isLoading.value = false;
    return;
  }

  // Ensure that 'end_time' is larger than 'start_time'.
  // TODO for omotes: to come via omotes-rest when sdk and protocol updated.
  // TODO for essim: to come via service json config, issue: mongodb does not allow keys starting with '$'.
  if ("end_time" in schema["properties"] && "start_time" in schema["properties"]) {
    schema["properties"]["end_time"]["formatExclusiveMinimum"] = {$data: "1/start_time"};
  }

  uischema = jsonFormData && "uischema" in jsonFormData ? jsonFormData.uischema : null;
  formData.value = jsonFormData && "formData" in jsonFormData ? jsonFormData.formData : formData.value;

  isLoading.value = false;
};

const validateEvent = (event) => {
  const varName = event.target.id.replace("#/properties/", "").replace("-input", "");

  // skip if varName not in schema or date-time object
  if (!(varName in schema["properties"]) || schema["properties"][varName]["type"] === "string"
      && schema["properties"][varName]["format"] === "date-time") {
    return;
  }

  let varValue = event.target.value;
  if (schema["properties"][varName]["type"] === "number" && varValue !== "") {
    varValue = Number(varValue);
  }

  dataToSubmit[varName] = varValue;
  validateJsonForm(dataToSubmit);
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
    goToStep(stepParams.value.nextStep); // make sure components in the same composite step are refreshed
  }
};

const onChange = (event) => {
  Object.assign(dataToSubmit, event.data);
  validateJsonForm(event.data);
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
    onSubmit();
  }
};

const validateJsonForm = (data) => {
  const validate = ajv.compile(schema);
  const isValid = validate(data) || schema === {};
  setWorkflowStepInputValid(stepParams.value.id, isValid);
  return {isValid, errors: validate.errors};
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  await getInputData(stepParams.value.data, updateData);
};

const onSubmit = async () => {
  isLoading.value = true;
  await sendOutputData(stepParams.value.data, dataToSubmit, afterSendOutput);
  isLoading.value = false;
};

const afterSendOutput = () => {
  isLoading.value = false;
  goToStep(stepParams.value.nextStep);
};

</script>

<style scoped>
</style>