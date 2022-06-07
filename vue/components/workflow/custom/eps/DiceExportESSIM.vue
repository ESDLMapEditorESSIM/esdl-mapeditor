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
    <label>Choose ESSIM simulation to export</label>
    <a-select
      v-model:value="simulation_id"
      style="width: 100%"
      @change="onChange"
    >
      <a-select-option
        v-for="simulation in simulations"
        :key="simulation.simulation_id"
        :value="simulation.simulation_id"
      >
        {{ simulation.simulation_descr || "No description" }} - {{ simulation.simulation_es_name }}
      </a-select-option>
    </a-select>
  </div>
  <div v-if="selected_simulation" style="margin-top: 10px;">
    <strong>Description</strong>: {{ selected_simulation.simulation_descr }}<br>
    <strong>Energy system name</strong>: {{ selected_simulation.simulation_es_name }}<br>
    <strong>Energy system ID</strong>:
    <span v-if="selected_simulation.es_id">{{ selected_simulation.es_id }}</span>
    <span v-else>Unknown</span>
    <br>
    <strong>Simulation ID</strong>: {{ selected_simulation.simulation_id }}
    <br>
    <p>Please make sure the above energy system is loaded in the mapeditor before generating the ESSIM export.</p>
  </div>
  <a-button type="primary" style="margin-top: 10px" @click="onSubmit">Generate ESSIM export</a-button>
  <div style="margin-top: 20px;">
    <h4>Previous ESSIM exports</h4>
    <a-table :columns="essim_export_columns" :data-source="essim_exports">
      <template v-if="column.key === 'action'">
        test
        <span>
          <a-button type="link" @click="downloadEssimExport">Download</a-button>
        </span>
      </template>
    </a-table>
  </div>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {doGet, doPost} from "../../../../utils/api";
import {useLongProcessState} from "../../../../composables/longProcess";
const { startLongProcess } = useLongProcessState();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const simulation_id = ref("");
const simulations = ref([]);
const selected_simulation = ref(null);
const essim_exports = ref([])
const essim_export_columns = [
  {
    title: 'ID',
    dataIndex: 'simulation_id',
    key: 'id',
  },
  {
    title: 'Action',
    key: 'action',
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
  });
  startLongProcess("ESSIM export", `/dice_workflow/export_essim/${simulation_id}`, {}, "progress", "message")
  alert("Download process started.");
}

const downloadEssimExport = async () => {
  console.log("Downloading essim export.")
  const response = await doPost(`/dice_workflow/export_essim/${simulation_id}/download`);
  console.log(response)
}

const loadSimulations = async () => {
  const simulations_list = await doGet("simulations_list");
  simulations.value = simulations_list;
}
loadSimulations();

const loadReadyExports = async () => {
  const essim_exports_response = await doGet("dice_workflow/export_essim");
  console.log(essim_exports_response)
  essim_exports.value = essim_exports_response;
}
loadReadyExports();
</script>

<style scoped>

</style>