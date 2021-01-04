<template>
  <a-button type="primary" @click="onSubmit"> Download </a-button>
</template>

<script setup="props">
import { download_binary_file_from_base64_str_with_type } from "../../utils/files.js";
import { genericErrorHandler } from "../../utils/errors.js";
import { useWorkflow } from "../../composables/workflow.js";
import { defineProps } from 'vue'

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const { getParamsFromState, goToNextStep } = useWorkflow();

const onSubmit = async () => {
  const requestParams = getParamsFromState(workflowStep.source.request_params);
  const params = {
    remote_url: workflowStep.source.url,
    request_params: requestParams,
  };
  window.show_loader();

  try {
    // Perform the request to the mapeditor backend, who will forward it to the service.
    const response = await fetch("workflow/download_file", {
      method: "POST",
      body: JSON.stringify(params),
      headers: {
        "Content-Type": "application/json",
      },
    });
    const data = await response.json()
    download_binary_file_from_base64_str_with_type(
      data["base64file"],
      data["filename"],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    );
    goToNextStep();
  } catch (e) {
    genericErrorHandler(e);
  } finally {
    window.hide_loader();
  }
};
</script>
