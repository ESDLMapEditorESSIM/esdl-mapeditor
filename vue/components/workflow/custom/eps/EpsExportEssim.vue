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
        {{ simulation.simulation_descr || "No description" }} - {{ simulation.simulation_es_name }}`
      </a-select-option>
    </a-select>
  </div>
  <div v-if="selected_simulation" style="margin-top: 10px;">
    Description: {{ selected_simulation.simulation_descr }}<br>
    Energy system name: {{ selected_simulation.simulation_es_name }}<br>
    <span v-if="selected_simulation.es_id">Energy system ID: {{ selected_simulation.es_id }}<br></span>
    Simulation ID: {{ selected_simulation.simulation_id }}
    <p>Please make sure the above energy system is loaded in the mapeditor before generating the ESSIM export.</p>
  </div>
  <a-button type="primary" @click="onSubmit">Generate ESSIM export</a-button>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {doGet, doPost} from "../../../../utils/api";

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
  const response = await doPost("dice_workflow/export_essim", {
    simulation_id: selected_simulation.simulation_id,
    es_id: selected_simulation.es_id,
  });
  console.log(response);
}

const loadSimulations = async () => {
  const simulations_list = await doGet("simulations_list");
  console.log(simulations_list);
  simulations.value = simulations_list;
}
loadSimulations();
</script>

<style scoped>

</style>