<!--
  - This work is based on original code developed and copyrighted by TNO 2020.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <p>Upload profiles template for the selected Energy System. Please make sure to use a generated profile template.</p>

  <a-form-item label="File to upload">
    <a-input id="upload-file" type="file" />
  </a-form-item>
  <a-button type="primary" @click="uploadProfiles">Upload profiles</a-button>
</template>

<script setup="props">
import {defineProps} from "vue";
import {doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
import {genericErrorHandler} from "../../../../utils/errors";
const { startLongProcess } = useLongProcessState();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});


const onComplete = () => {
  window.socket.emit('command', {cmd: 'refresh_esdl', es_id: window.active_layer_id});
}

const uploadProfiles = async () => {
  const file_input = document.getElementById("upload-file");
  const file_reader = new FileReader();
  const file_to_upload = file_input.files[0];
  const file_name = file_to_upload.name;

  // This function will do the actual uploading. It is triggered when
  // calling readAsDataURL on the file_reader.
  const upload_file = async () => {
    const payload = {
      'base64_file': file_reader.result,
      'file_name': file_name,
    };

    try {
      const response = await doPost("dice_workflow/profiles/upload", payload);
      const responseJson = await response.json()
      const process_id = responseJson.process_id;
      startLongProcess("Upload profiles", `/dice_workflow/profiles/upload/progress/${process_id}`, {}, "progress", "message", "failed", onComplete)
      alert("Started uploading profiles. When complete, the new ESDL will be loaded automatically.");
    } catch (e) {
      genericErrorHandler(e);
    }
  }
  file_reader.onload = upload_file
  // Trigger the onload.
  file_reader.readAsDataURL(file_to_upload);
}

</script>

<style scoped>

</style>