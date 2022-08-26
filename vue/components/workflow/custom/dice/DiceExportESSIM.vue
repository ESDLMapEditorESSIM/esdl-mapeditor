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
  <div>
    <label>Choose ESSIM simulation to export.</label>
    <a-select
      v-model:value="simulation_id"
      style="width: 100%; margin-bottom: 10px;"
      :options="simulations_options"
      @change="onChange"
    />
    <label>Export type: </label>
    <a-radio-group v-model:value="export_type">
      <a-radio-button value="BUSINESS_CASE">Business case</a-radio-button>
      <a-radio-button value="ICE">DICE Dashboard (MapGear)</a-radio-button>
    </a-radio-group>
  </div>
  <div v-if="selected_simulation" style="margin-top: 10px;">
    <strong>ESSIM description</strong>: {{ selected_simulation.simulation_descr }}<br>
    <strong>Energy system name</strong>: {{ selected_simulation.simulation_es_name }}<br>
    <strong>Energy system ID</strong>:
    <span v-if="selected_simulation.es_id">{{ selected_simulation.es_id }}</span>
    <span v-else>Unknown</span>
    <br>
    <strong>ESSIM simulation ID</strong>: {{ selected_simulation.simulation_id }}
  </div>
  <a-button type="primary" style="margin-top: 10px" @click="onSubmit">Generate ESSIM export</a-button>
  <div style="margin-top: 20px;">
    <h4>Previous ESSIM exports</h4>
    <a-table :columns="essim_export_columns" :data-source="essim_exports">
      <template #action="{ record }">
        <span>
          <a-button type="link" @click="downloadEssimExport(record.key)">Download</a-button>
        </span>
      </template>
      <template #date="{ record }">
        {{ record.date.substring(0, 10) }}
      </template>
    </a-table>
  </div>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {doGet, doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
import {download_binary_file_from_base64_str_with_type} from "../../../../utils/files";
const { startLongProcess } = useLongProcessState();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const ExportType = Object.freeze({
  ICE: 'ICE',
  BUSINESS_CASE: 'BUSINESS_CASE',
});

const simulation_id = ref("");
const simulations = ref([]);
const export_type = ref(ExportType.BUSINESS_CASE);
const simulations_options = ref([]);
const selected_simulation = ref(null);
const essim_exports = ref([])
const essim_export_columns = [
  {
    title: 'Date',
    dataIndex: 'date',
    key: 'date',
    slots: { customRender: 'date' },
  },
  {
    title: 'Type',
    dataIndex: 'export_type',
    key: 'export_type',
  },
  {
    title: 'Description',
    dataIndex: 'description',
    key: 'description',
  },
  {
    title: 'Action',
    key: 'action',
    slots: { customRender: 'action' },
  },
];

const onChange = async () => {
  for (const simulation of simulations.value) {
    if (simulation.simulation_id === simulation_id.value) {
      selected_simulation.value = simulation;
      break
    }
  }
}

const onSubmit = async () => {
  if (!selected_simulation.value) {
    alert("No simulation selected");
    return
  }
  const simulation_id = selected_simulation.value.simulation_id;
  await doPost("dice_workflow/export_essim", {
    simulation_id: simulation_id,
    export_type: export_type.value,
  });
  startLongProcess("ESSIM export", `/dice_workflow/export_essim/${simulation_id}`, {}, "progress", "message", "failed")
  alert("Download process started.");
}

const downloadEssimExport = async (simulation_id) => {
  console.log("Downloading essim export.")
  const response = await doPost(`/dice_workflow/export_essim/${simulation_id}/download`);
  const body = await response.json();
  download_binary_file_from_base64_str_with_type(
      body.base64_file,
      body.filename,
      'application/x-zip',
  );
}

const loadSimulations = async () => {
  const simulations_list = await doGet("simulations_list");
  simulations.value = simulations_list;

  simulations_options.value = simulations_list.filter((simulation) => simulation.dashboard_url).map((simulation) => {
    const description = simulation.simulation_descr || "No description"
    return {
      label: description + " - " + simulation.simulation_es_name,
      value: simulation.simulation_id,
    };
  });
}
loadSimulations();

const loadReadyExports = async () => {
  const essim_exports_response = await doGet("dice_workflow/export_essim");
  essim_exports.value = essim_exports_response;
}
loadReadyExports();
</script>

<style scoped>

</style>