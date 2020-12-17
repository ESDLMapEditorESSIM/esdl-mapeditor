<template>
  <p v-if="isLoading">Loading...</p>
  <div v-else>
    <p v-if="message != ''">
      {{ message }}
    </p>
    <p v-else>Request complete.</p>
    <a-button type="primary" @click="goToNextStep"> Next </a-button>
  </div>
</template>


<script setup="props">
import { defineProps, ref } from "vue";
import { genericErrorHandler } from "../../utils/errors.js";
import { useWorkflow } from "../../composables/workflow.js";

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
const form = {};
form[workflowStep.target_variable] = "";

const { goToNextStep } = useWorkflow();
const { getFromState } = useWorkflow();

const message = ref("");

const doPost = async () => {
  // Build the target request parameters by getting the values from the state.
  const request_params = getFromState(workflowStep.target["request_params"]);
  const params = {
    remote_url: workflowStep.target.url,
    request_params: request_params,
  };

  window.show_loader();
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
        message.value = "Request complete."
      } else {
        message.value = "Error while performing request: " + response.statusText;
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
}

doPost();
</script>
