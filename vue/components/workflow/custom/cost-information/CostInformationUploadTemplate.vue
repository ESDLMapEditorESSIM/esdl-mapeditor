<template>
  <p>
    Upload cost information template for the selected ESDL layer. Please make sure to use a generated cost information template.
  </p>

  <p>
    NB. The cost information template is coupled to the ESDL layer it has been generated for in the previous step. It can therefore only be uploaded for this ESDL layer.
  </p>

  <a-form-item label="File to upload">
    <a-input id="upload-file" type="file"/>
  </a-form-item>
  <a-button type="primary" @click="uploadTemplate">Upload cost information</a-button>
</template>

<script setup="props">
import {doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
import {genericErrorHandler} from "../../../../utils/errors";

const {startLongProcess} = useLongProcessState();

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

const uploadTemplate = async () => {
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
      const response = await doPost("cost_information/template/upload", payload);
      const responseJson = await response.json()
      const process_id = responseJson.process_id;
      startLongProcess("Upload cost information", `/cost_information/template/upload/progress/${process_id}`, {}, "progress", "message", "failed", onComplete)
      alert("Started uploading cost information. When complete, the new ESDL will be loaded automatically.");
    } catch (e) {
      genericErrorHandler(e);
    }
  }
  file_reader.onload = upload_file
// Trigger the onload.
  file_reader.readAsDataURL(file_to_upload);
}

</script>

<style scoped></style>