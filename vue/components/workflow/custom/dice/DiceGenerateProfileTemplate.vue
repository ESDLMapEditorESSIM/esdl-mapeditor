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
  <p>Download a profiles template for the selected Energy System.</p>

  <a-button type="primary" @click="generateTemplate">Generate profiles template</a-button>
</template>

<script setup="props">
import {defineProps} from "vue";
import {doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
import {download_binary_file_from_base64_str_with_type} from "../../../../utils/files";
import {genericErrorHandler} from "../../../../utils/errors";
// import {download_binary_file_from_base64_str_with_type} from "../../../../utils/files";
const { startLongProcess } = useLongProcessState();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const onComplete = (data) => {
  download_binary_file_from_base64_str_with_type(
      data["base64file"],
      data["filename"],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  );
}

const generateTemplate = async () => {
  try {
    const response = await doPost("dice_workflow/profiles/template");
    const responseJson = await response.json()
    const process_id = responseJson.process_id;
    startLongProcess("Profile template", `/dice_workflow/profiles/template/check/${process_id}`, {}, "progress", "message", "failed", onComplete)
    alert("Started generating profile template. When it is complete it will be downloaded automatically.");
  } catch (e) {
    genericErrorHandler(e);
  }
}

</script>

<style scoped>

</style>