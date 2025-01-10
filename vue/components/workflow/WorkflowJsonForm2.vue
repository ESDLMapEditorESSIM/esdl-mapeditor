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
    <a-button v-if="!autoNextStep" type="primary" @click="onSubmit">{{ buttonText }}</a-button>
  </div>
</template>

<script setup="props">
import {onMounted, ref, watch} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {getJsonForm, postJsonForm} from "./utils/api";
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

let workflowStep = props.workflowStep;
let workflowTrigger = props.workflowStep.workflowTrigger;
let buttonText = workflowStep.button || "Submit";

const formData = ref({});
let schema = {};
let uischema = {};

const dataToSubmit = {};
const isLoading = ref(true);
const jsonFormDataReceived = ref(false);

const autoNextStep = ref(false);

const {goToNextStep, getState, getFromState, setWorkflowStepInputValid} = useWorkflow();

onMounted(() => {
  init();
});

watch(workflowTrigger, () => {
  init();
});

const updateData = (jsonFormData) => {
  const jsonFormDataConfig = workflowStep.data;

  jsonFormDataReceived.value = true;
  if ("schema" in jsonFormDataConfig) {
    schema = jsonFormDataConfig.schema;
  } else if (jsonFormData && "schema" in jsonFormData) {
    schema = jsonFormData.schema;
  } else {
    schema = {};
    jsonFormDataReceived.value = false;
    setWorkflowStepInputValid(workflowStep.reference, true);
    isLoading.value = false;
    return;
  }

  // Ensure that 'end_time' is larger than 'start_time'.
  // TODO for omotes: to come via omotes-rest when sdk and protocol updated.
  // TODO for essim: to come via service json config, issue: mongodb does not allow keys starting with '$'.
  if ("end_time" in schema["properties"] && "start_time" in schema["properties"]) {
    schema["properties"]["end_time"]["formatExclusiveMinimum"] = {$data: "1/start_time"};
  }

  if ("uischema" in jsonFormDataConfig) {
    uischema = jsonFormDataConfig.uischema;
  } else if (jsonFormData && "uischema" in jsonFormData) {
    uischema = jsonFormData.uischema;
  } else {
    uischema = null;
  }

  if ("formData" in jsonFormDataConfig) {
    formData.value = jsonFormDataConfig.formData;
  } else if (jsonFormData && "formData" in jsonFormData) {
    formData.value = jsonFormData.formData;
  }
  isLoading.value = false;
};

const doGetData = async () => {
  if (workflowStep.url) {
    updateData(await getJsonForm(workflowStep.url));
  } else if ("from_state_variable" in workflowStep.data) {
    updateData(getState()[workflowStep.data.from_state_variable]);
  } else if ("from_socket" in workflowStep.data) {
    const fromSocket = workflowStep.data.from_socket;

    let params = "params" in fromSocket ? fromSocket.params : {};
    if ("state_params" in fromSocket) {
      for (const [key, state_key] of Object.entries(fromSocket.state_params)) {
        params[key] = getFromState(state_key);
      }
    }
    window.socket.emit(fromSocket.event, params, (res) => {
      updateData(res);
    });
  } else {
    updateData(null);
  }
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
  if (autoNextStep.value) {
    goToNextStep();
  }
};

const onChange = (event) => {
  Object.assign(dataToSubmit, event.data);
  validateJsonForm(event.data);
  if (autoNextStep.value) {
    onSubmit();
  }
};

const updateState = () => {
  let dataSubmitFormatted = {};
  if ("target_variable" in workflowStep) {
    dataSubmitFormatted[workflowStep.target_variable] = jsonFormDataReceived.value ? dataToSubmit : {};
  } else {
    dataSubmitFormatted = jsonFormDataReceived.value ? dataToSubmit : {};
  }
  Object.assign(getState(), dataSubmitFormatted);
  return dataSubmitFormatted;
};

const init = () => {
  workflowStep = props.workflowStep;
  workflowTrigger = props.workflowStep.workflowTrigger;
  if ("auto_next_step" in workflowStep) {
    autoNextStep.value = workflowStep.auto_next_step;
  } else {
    autoNextStep.value = false;
  }
  buttonText = workflowStep.button || "Submit";
  doGetData();
  updateState();
};

const onSubmit = async () => {
  const dataSubmitFormatted = updateState();

  if (workflowStep.url) {
    // POST data to remote URL.
    isLoading.value = true;
    try {
      const response = await postJsonForm(workflowStep.url, dataSubmitFormatted);
      console.log(response);
      if (response != null && response.ok) {
        goToNextStep();
      }
    } finally {
      isLoading.value = false;
    }
  } else if ("to_socket" in workflowStep.data) {
    window.socket.emit(workflowStep.data.to_socket.event, dataSubmitFormatted, () => {
      goToNextStep();
    });
  } else {
    goToNextStep();
  }
};

const validateJsonForm = (data) => {
  const validate = ajv.compile(schema);
  const isValid = validate(data) || schema === {};
  setWorkflowStepInputValid(workflowStep.reference, isValid);
  return {isValid, errors: validate.errors};
};
</script>

<style scoped>
</style>