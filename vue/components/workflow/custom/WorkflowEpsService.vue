<template>
  <p v-if="isLoading">Sending data...</p>
  <p v-else-if="message != ''">
    {{ message }}
    <next-or-close :workflow-step="workflowStep" />
  </p>
  <div v-else>
    <p>Please select the "Run ESDL service" button below to start the EPS.</p>

    <a-form :model="form" :label-col="{ span: 0 }">
      <a-form-item label="Aggregate buildings">
        <a-switch @change="setAggregateBuildings">
          <template #checkedChildren><check-outlined /></template>
          <template #unCheckedChildren><close-outlined /></template>
        </a-switch>
      </a-form-item>
      <a-form-item label="Number of scenarios to generate">
        <a-input-number :min="1" :max="5" @change="setNrOfScenarios" />
      </a-form-item>
    </a-form>
    <a-button type="primary" @click="doPost"> Run ESDL service </a-button>
  </div>
</template>

<script setup="props">
import { CheckOutlined, CloseOutlined } from "@ant-design/icons-vue";
import { defineProps, ref } from "vue";
import { genericErrorHandler } from "../../../utils/errors.js";
import { useWorkflow } from "../../../composables/workflow.js";
// eslint-disable-next-line no-unused-vars
import { default as NextOrClose } from "../NextOrClose";

// eslint-disable-next-line no-unused-vars
const components = {
  CheckOutlined,
  CloseOutlined,
};

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const isLoading = ref(false);
const form = { nr_of_scenarios: 1, aggregate_buildings: false };

// These 2 set functions should not be necessary, according to the docs. We should be
// able to use v-model:value and things would work. Unfortunately it doesn't though,
// but this works.
// eslint-disable-next-line no-unused-vars
const setAggregateBuildings = (checked) => {
  form.aggregate_buildings = checked;
};

// eslint-disable-next-line no-unused-vars
const setNrOfScenarios = (value) => {
  form.nr_of_scenarios = value;
};

const { getParamsFromState, goToNextStep } = useWorkflow();

const message = ref("");

// eslint-disable-next-line no-unused-vars
const doPost = async () => {
  isLoading.value = true;
  window.show_loader();

  // Build the target request parameters by getting the values from the state and the form.
  const request_params = getParamsFromState(
    workflowStep.target["request_params"]
  );
  request_params["nr_of_scenarios"] = form.nr_of_scenarios;
  request_params["aggregate_buildings"] = form.aggregate_buildings;
  const params = {
    remote_url: workflowStep.target.url,
    request_params: request_params,
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
.ant-form-item {
  margin-bottom: 0;
}
</style>
