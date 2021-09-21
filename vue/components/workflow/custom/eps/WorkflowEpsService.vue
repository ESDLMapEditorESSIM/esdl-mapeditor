<template>
  <p v-if="isLoading">Sending data...</p>
  <p v-else-if="message != ''">
    {{ message }}
    <next-or-close :workflow-step="workflowStep" />
  </p>
  <div v-else>
    <p>Please select the "Run ESDL service" button below to start the EPS.</p>

    <json-forms
      :data="formData"
      :schema="schema"
      :uischema="uischema"
      :renderers="renderers"
      @change="onChange"
    />

    <a-button type="primary" @click="doPost"> Run ESDL service </a-button>
  </div>
</template>

<script setup="props">
import { defineProps, ref } from "vue";
import { genericErrorHandler } from "../../../../utils/errors.js";
import { useWorkflow } from "../../../../composables/workflow.js";
// eslint-disable-next-line no-unused-vars
import { default as NextOrClose } from "../../NextOrClose";
import { workflowGetJsonForm } from "../../lib/api.js";
// eslint-disable-next-line no-unused-vars
import { JsonForms } from "@jsonforms/vue";
import {
  defaultStyles,
  mergeStyles,
  vanillaRenderers,
} from "@jsonforms/vue-vanilla";
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

const { getParamsFromState, goToNextStep } = useWorkflow();
const workflowStep = props.workflowStep;

let formData = { };

// eslint-disable-next-line no-unused-vars
const uischema = {
  type: "VerticalLayout",
  elements: [
    {
      type: "Control",
      scope: "#/properties/project_name",
      label: "Project",
    },
    {
      type: "Control",
      scope: "#/properties/file_name",
      label: "Project file"
    },
  ],
};

const isLoading = ref(true);
const schema = ref({});
const getJsonForm = async () => {
  const request_params = getParamsFromState(
    workflowStep.target["request_params"]
  );
  request_params["url"] = workflowStep.url;
  const queryString = new URLSearchParams(request_params).toString();

  try {
    schema.value = await workflowGetJsonForm(queryString, "RunEpsSchemaForProject");
  } finally {
    isLoading.value = false;
  }
}
getJsonForm();

// eslint-disable-next-line no-unused-vars
const onChange = (event) => {
  formData = event.data;
};

const message = ref("");

// eslint-disable-next-line no-unused-vars
const doPost = async () => {
  isLoading.value = true;
  window.show_loader();

  const params = {
    remote_url: workflowStep.url,
    request_params: formData,
  };

  try {
    // Perform the request to the mapeditor backend, who will forward it to the service.
    const response = await fetch("workflow/post_data", {
      method: "POST",
      body: JSON.stringify(params),
      headers: {
        "Content-Type": "application/json",
      },
    });
    // Give a user response if a spec is defined.
    const user_response_spec = workflowStep.target.user_response_spec;
    if (user_response_spec) {
      let user_response = user_response_spec[response.status.toString()];
      if (user_response) {
        message.value = user_response.message;
      } else if (response.ok) {
        message.value = "Request complete.";
      } else {
        message.value =
          "Error while performing request: " + response.statusText;
      }
    }

    if (response.ok && workflowStep.auto) {
      goToNextStep();
    }
  } catch (e) {
    genericErrorHandler(e);
  } finally {
    window.hide_loader();
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

.array-list-no-data {
  background-color: rgb(238, 238, 238) !important;
}
</style>
