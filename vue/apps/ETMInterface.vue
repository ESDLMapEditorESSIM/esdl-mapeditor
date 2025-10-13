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
  <h1>
    ETM Interface
  </h1>
  <a-space
    v-if="!isLoading"
    id="etm_interface"
    direction="vertical"
    style="width: 100%"
  >
    <a-card style="width: 100%">
      <p>
        The ETM interface allows you to load specific ETM scenarios as an ESDL into the MapEditor
      </p>
    </a-card>

    <a-collapse v-model:activeKey="activePanel">
      <a-collapse-panel key="ETM_scenarios" header="ETM scenarios" >
        <a-space
          direction="vertical"
        >
          <label>Select a predefined ETM scenario: </label>
          <a-select
            v-model:value="selected_scenario_id"
            style="width: 300px;"
          >
            <a-select-option
              v-for="scenario in scenario_list"
              :key="scenario.scenario_id"
            >
              {{ scenario.name }}
            </a-select-option>
          </a-select>

          <label>Use ETM data for: </label>
          <a-radio-group v-model:value="year_source" name="year_source">
            <a-radio value="present_year">Present year</a-radio>
            <a-radio value="future_year">Future year</a-radio>
          </a-radio-group>

        </a-space>
      </a-collapse-panel>
      <a-collapse-panel key="manual" header="Manual scenario ID" collapsible="disabled">
        <p>Not implemented yet</p>
      </a-collapse-panel>
    </a-collapse>

    <a-space>
      <a-button
        type="primary"
        @click="select"
      >
        Select
      </a-button>
      <a-button
        type="primary"
        @click="cancel"
      >
        Cancel
      </a-button>
    </a-space>
  </a-space>
  <spinner v-else />
</template>

<script setup>
import {ref} from 'vue';
import axios from 'axios'
import spinner from "@/components/Spinner.vue";

const isLoading = ref(true);
const activePanel = ref(['ETM_scenarios'])
const scenario_list = ref([]);
const selected_scenario_id = ref();
const year_source = ref("future_year");

function get_ETM_scenarios()  {
  const path = '/etm_interface/etm_scenarios';
  axios.get(path)
    .then((res) => {
      scenario_list.value = res['data'];
      if (scenario_list.value.length > 0) {
        selected_scenario_id.value = scenario_list.value[0].scenario_id;
      }
      isLoading.value = false;
    })
    .catch((error) => {
      // eslint-disable-next-line
      console.error(error);
    });
}
get_ETM_scenarios();

function select() {
  window.socket.emit('etm_select_scenario', {scenario_id: selected_scenario_id.value, year_source: year_source.value});
  window.show_loader();
  window.sidebar.hide();
}

function cancel() {
  window.sidebar.hide();
}

</script>
