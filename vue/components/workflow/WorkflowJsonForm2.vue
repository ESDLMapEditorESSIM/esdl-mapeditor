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
      @focusout="validateEvent"
    />
    <a-button
      v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK"
      type="primary"
      :disabled="!isAllInputValid()"
      @click="onSubmit"
    >
      {{ stepParams.buttonText || 'Submit' }}
    </a-button>
  </div>
</template>

<script setup="props">
import {onMounted, onUnmounted, ref, watch} from "vue";
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
/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});

const formData = ref({});
let schema = {};
let uischema = {};

const dataToSubmit = {};
const isLoading = ref(true);
const jsonFormDataReceived = ref(false);

let subscriptionId = null;

const {
  getWorkflowStepParameters,
  goToStep,
  setWorkflowStepInputValid,
  getInputData,
  sendOutputData,
  isAllInputValid,
  getState,
} = useWorkflow();

const insertedPreviousValues = ref(false);

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
  if (stepParams.value.reloadOnEsdlActivation) {
    subscriptionId = PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
      init();
    });
  }
});

onUnmounted(() => {
  if (subscriptionId !== null) {
    PubSubManager.unsubscribe(subscriptionId);
  }
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

  if (!insertedPreviousValues.value) {
    // overwrite default values with last submitted values if present in state
    const state = getState();
    for (const propName of Object.keys(schema["properties"])) {
      if (propName in state) {
        formData.value[propName] = state[propName];
      }
    }
    insertedPreviousValues.value = true;
  }

  isLoading.value = false;
};

const validateEvent = (event) => {
  const varName = event.target.id.replace("#/properties/", "").replace("-input", "");

  // skip if varName not in schema or date-time object
  if (!(varName in schema["properties"]) || schema["properties"][varName]["type"] === "string"
      && schema["properties"][varName]["format"] === "date-time") {
    return;
  }

  const propertyType = schema["properties"][varName]["type"];
  let varValue = propertyType === "boolean" ? event.target.checked : event.target.value;
  if (["number", "integer"].includes(propertyType) && varValue !== "") {
    varValue = Number(varValue);
  }

  if (dataToSubmit[varName] === varValue) {
    return;
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
  const isValid = validate(data) || Object.keys(schema).length === 0;
  setWorkflowStepInputValid(stepParams.value.id, isValid);
  console.log("jsonforms Validation result:", {isValid, errors: validate.errors});
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
