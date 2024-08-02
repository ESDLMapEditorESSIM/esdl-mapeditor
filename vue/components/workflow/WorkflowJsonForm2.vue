<template>
  <p v-if="isLoading">Loading...</p>
  <div v-else-if="jsonFromDataReceived">
    <json-forms
      :data="formData"
      :schema="schema"
      :uischema="uischema"
      :renderers="renderers"
      @change="onChange"
      @error="console.log('ERROR')"
    />

    <a-button v-if="!autoNextStep" type="primary" @click="onSubmit">{{ buttonText }}</a-button>
  </div>
</template>

<script setup="props">
import {ref, watch} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {getJsonForm, postJsonForm} from "./utils/api";
import {JsonForms} from "@jsonforms/vue";
// eslint-disable-next-line no-unused-vars
import {defaultStyles, mergeStyles, vanillaRenderers,} from "@jsonforms/vue-vanilla";
import "@jsonforms/vue-vanilla/vanilla.css";

const renderers = Object.freeze([...vanillaRenderers]);

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

let workflowStep = props.workflowStep;
let workflowTrigger = props.workflowStep.workflowTrigger;

// eslint-disable-next-line no-unused-vars
watch(workflowTrigger, (currentValue, oldValue) => {
  init();
});

let buttonText = workflowStep.button || "Submit";

const schema = ref({});
// eslint-disable-next-line no-unused-vars
const formData = ref({});
const uischema = ref(null);

const dataToSubmit = {};
const isLoading = ref(true);
const jsonFromDataReceived = ref(false);

const autoNextStep = ref(false);

const {goToNextStep, getState, getFromState} = useWorkflow();

const updateData = (jsonFormData) => {
  const jsonFormDataConfig = workflowStep.data;

  if (jsonFormData && "schema" in jsonFormData || "schema" in jsonFormDataConfig) {
    jsonFromDataReceived.value = true;
  } else {
    jsonFromDataReceived.value = false;
    isLoading.value = false;
    return;
  }

  // Optionally override schema/uischema/formData received from url/state/socket by json config
  if ("schema" in jsonFormDataConfig) {
    schema.value = jsonFormDataConfig.schema;
  } else {
    schema.value = jsonFormData.schema;
  }
  if ("uischema" in jsonFormDataConfig) {
    uischema.value = jsonFormDataConfig.uischema;
  } else if (jsonFormData && "uischema" in jsonFormData) {
    uischema.value = jsonFormData.uischema;
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
  } else if ("from_socket_emit" in workflowStep.data) {
    const fromSocketEmit = workflowStep.data.from_socket_emit;
    let params = {};
    if ("params" in fromSocketEmit) {
      params = fromSocketEmit.params;
    }
    if ("state_params" in fromSocketEmit) {
      for (const [key, state_key] of Object.entries(fromSocketEmit.state_params)) {
        params[key] = getFromState(state_key);
      }
    }
    window.socket.emit(fromSocketEmit.event, params, (res) => {
      updateData(res);
    });
  } else {
    updateData(null);
  }
};

const onChange = (event) => {
  Object.assign(dataToSubmit, event.data);
  if (autoNextStep.value) {
    onSubmit();
  }
};

const updateState = () => {
  let dataSubmitFormatted = {};
  if ("target_variable" in workflowStep) {
    dataSubmitFormatted[workflowStep.target_variable] = jsonFromDataReceived.value ? dataToSubmit : {};
  } else {
    dataSubmitFormatted = jsonFromDataReceived.value ? dataToSubmit : {};
  }
  Object.assign(getState(), dataSubmitFormatted);
  return dataSubmitFormatted
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
init();

const onSubmit = async () => {
  const dataSubmitFormatted = updateState();

  if (workflowStep.url) {
    // POST data to remote URL.
    isLoading.value = true;
    try {
      const response = await postJsonForm(workflowStep.url, dataSubmitFormatted);
      console.log(response);
      if (response != null && response.ok && workflowStep.auto) {
        goToNextStep();
      }
    } finally {
      isLoading.value = false;
    }
  } else if ("to_socket_emit" in workflowStep.data) {
    window.socket.emit(workflowStep.data.to_socket_emit.event, dataSubmitFormatted, (res) => {
      goToNextStep();
    });
  } else {
    goToNextStep();
  }
};
</script>

<style scoped>
</style>