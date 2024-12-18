<template>
  <p>
    Download a template for filling in the cost information per asset for the selected ESDL layer.
  </p>
  <p>
    This cost information is needed for running the Energy Hub Configurator in the next step, but only for the assets that are part of the energy hub.
  </p>

  <a-button type="primary" @click="generateTemplate">Generate cost information template</a-button>
</template>

<script setup="props">
import {doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
import {download_binary_file_from_base64_str_with_type} from "../../../../utils/files";
import {genericErrorHandler} from "../../../../utils/errors";

const {startLongProcess} = useLongProcessState();

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
    const response = await doPost("cost_information/template");
    const responseJson = await response.json()
    const process_id = responseJson.process_id;
    startLongProcess("Cost information template", `/cost_information/template/progress/${process_id}`, {}, "progress", "message", "failed", onComplete)
    alert("Started generating cost information template. When it is complete it will be downloaded automatically.");
  } catch (e) {
    genericErrorHandler(e);
  }
}

</script>

<style scoped></style>