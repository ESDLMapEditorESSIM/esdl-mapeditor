<template>
  <a-form-item label="File to upload">
    <a-input :id="inputId" type="file" />
  </a-form-item>

  <a-button type="primary" @click="onSubmit">Upload</a-button>
</template>

<script setup="props">
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

const inputId = 'workflow_file_upload';

const workflowStep = props.workflowStep;

const { getParamsFromState, getState, goToNextStep } = useWorkflow();
const state = getState();

// eslint-disable-next-line no-unused-vars
const onSubmit = async () => {
  const file_input = document.getElementById(inputId);
  const file_reader = new FileReader();
  const file_to_upload = file_input.files[0];
  const file_name = file_to_upload.name;

  // This function will do the actual uploading. It is triggered when
  // calling readAsDataURL on the file_reader.
  const upload_file = async () => {
    // Build the target request parameters by getting the values from the state.
    const request_params = getParamsFromState(workflowStep.target['request_params']);
    // Add file upload specific fields.
    request_params['base64_file'] = file_reader.result;
    request_params['file_name'] = file_name;
    const params = {
        'remote_url': workflowStep.target.url,
        'request_params': request_params,
    }
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
      if (response.ok) {
        alert('Upload successful!');
        const response_params = workflowStep.target.response_params;
        if (response_params) {
          const response_json = await response.json();
          for (const [response_field, target_field] of Object.entries(response_params)) {
            state[target_field] = response_json[response_field];
          }

        } 
        goToNextStep();
      } else {
        alert('Error while uploading file: ' + response.statusText)
      }
    } catch (e) {
      genericErrorHandler(e);
    } finally {
      window.hide_loader();
    }
  }

  file_reader.onload = upload_file
  // Trigger the onload.
  file_reader.readAsDataURL(file_to_upload);
}
</script>
