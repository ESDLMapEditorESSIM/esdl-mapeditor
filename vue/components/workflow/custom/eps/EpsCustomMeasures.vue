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
  <p>Please configure custom energy saving measures to apply to the ESDL.</p>
  <hr>
  <p v-if="isLoading">Loading...</p>
  <div v-for="building in buildings" v-else :key="building.id" :data-esdl-id="building.id">
    <h4>{{ building.name }}</h4>
    <a-table :data-source="formState[building.id].table" :columns="columns" :pagination="false" />
    <a-form layout="vertical" :model="formState" :label-col="{ span: 0 }">
      <a-form-item label="Aardgasgebruik gebouw schalingsfactor" :min="0" :step="scalingFactorStepSize">
        <a-input-number v-model:value="formState[building.id].pand_energiegebruik_aardgas_gebouw_schalingsfactor" />
      </a-form-item>
      <a-form-item label="Aardgasgebruik proces schalingsfactor" :min="0" :step="scalingFactorStepSize">
        <a-input-number v-model:value="formState[building.id].pand_energiegebruik_aardgas_proces_schalingsfactor" />
      </a-form-item>
      <a-form-item label="Elektriciteitsgebruik gebouw schalingsfactor" :min="0" :step="scalingFactorStepSize">
        <a-input-number v-model:value="formState[building.id].pand_energiegebruik_elektriciteit_gebouw_schalingsfactor" />
      </a-form-item>
      <a-form-item label="Elektriciteitsgebruik proces schalingsfactor" :min="0" :step="scalingFactorStepSize">
        <a-input-number v-model:value="formState[building.id].pand_energiegebruik_elektriciteit_proces_schalingsfactor" />
      </a-form-item>
      <a-form-item label="Elektriciteit warmtepomp (kWh)" :min="0" :step="scalingFactorStepSize">
        <a-input-number v-model:value="formState[building.id].pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh" />
      </a-form-item>
      <a-form-item label="Elektriciteit proceselektrificatie warmte (kWh)" :min="0" :step="scalingFactorStepSize">
        <a-input-number
          v-model:value="formState[building.id].pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh"
        />
      </a-form-item>
    </a-form>
  </div>
  <a-button type="primary" @click="onSubmit"> Apply measures</a-button>
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

const scalingFactorStepSize = '0.001';

const formState = ref({});

const isLoading = ref(true);
const buildings = ref([]);

// const EpsKPIs = Object.freeze({
//   pand_energiegebruik_aardgas_gebouw_huidig_m3: "pand_energiegebruik_aardgas_gebouw_huidig_m3",
//   pand_energiegebruik_aardgas_proces_huidig_m3: "pand_energiegebruik_aardgas_proces_huidig_m3",
//   pand_energiegebruik_elektriciteit_gebouw_huidig_kWh: "pand_energiegebruik_elektriciteit_gebouw_huidig_kWh",
//   pand_energiegebruik_elektriciteit_proces_huidig_kWh: "pand_energiegebruik_elektriciteit_proces_huidig_kWh",
//   pand_energiegebruik_aardgas_gebouw_scenario_m3: "pand_energiegebruik_aardgas_gebouw_scenario_m3",
//   pand_energiegebruik_aardgas_proces_scenario_m3: "pand_energiegebruik_aardgas_proces_scenario_m3",
//   pand_energiegebruik_elektriciteit_gebouw_scenario_kWh: "pand_energiegebruik_elektriciteit_gebouw_scenario_kWh",
//   pand_energiegebruik_elektriciteit_proces_scenario_kWh: "pand_energiegebruik_elektriciteit_proces_scenario_kWh",
// });

const columns = [
  {
    title: "KPI",
    dataIndex: "name",
    key: "name"
  },
  {
    title: "Value",
    dataIndex: "value",
    key: "value"
  },
];

const doGetData = async () => {
  isLoading.value = true;
  try {
    const response = await doGet("measures/get_buildings");
    if (!response) {
      alert("No buildings received.");
      return
    }
    for (const building of response) {
      const kpis = building.kpis;
      const pand_energiegebruik_aardgas_gebouw_huidig_m3 = kpis.pand_energiegebruik_aardgas_gebouw_huidig_m3;
      const pand_energiegebruik_aardgas_proces_huidig_m3 = kpis.pand_energiegebruik_aardgas_proces_huidig_m3;
      const pand_energiegebruik_elektriciteit_gebouw_huidig_kWh = kpis.pand_energiegebruik_elektriciteit_gebouw_huidig_kWh;
      const pand_energiegebruik_elektriciteit_proces_huidig_kWh = kpis.pand_energiegebruik_elektriciteit_proces_huidig_kWh;

      const pand_energiegebruik_aardgas_gebouw_schalingsfactor = pand_energiegebruik_aardgas_gebouw_huidig_m3 > 0 ? kpis.pand_energiegebruik_aardgas_gebouw_scenario_m3 / pand_energiegebruik_aardgas_gebouw_huidig_m3 : 0;
      const pand_energiegebruik_aardgas_proces_schalingsfactor = pand_energiegebruik_aardgas_proces_huidig_m3 > 0 ? kpis.pand_energiegebruik_aardgas_proces_scenario_m3 / pand_energiegebruik_aardgas_proces_huidig_m3 : 0;
      const pand_energiegebruik_elektriciteit_gebouw_schalingsfactor = pand_energiegebruik_elektriciteit_gebouw_huidig_kWh > 0 ? kpis.pand_energiegebruik_elektriciteit_gebouw_scenario_kWh / pand_energiegebruik_elektriciteit_gebouw_huidig_kWh : 0;
      const pand_energiegebruik_elektriciteit_proces_schalingsfactor = pand_energiegebruik_elektriciteit_proces_huidig_kWh > 0 ? kpis.pand_energiegebruik_elektriciteit_proces_scenario_kWh / pand_energiegebruik_elektriciteit_proces_huidig_kWh : 0;
      formState.value[building.id] = {
        table: [
          {
            key: "pand_energiegebruik_aardgas_gebouw_huidig_m3",
            name: "Huidig aardgasgebruik gebouw",
            value: pand_energiegebruik_aardgas_gebouw_huidig_m3.toLocaleString(),
          },
          {
            key: "pand_energiegebruik_aardgas_proces_huidig_m3",
            name: "Huidig aardgasgebruik proces",
            value: pand_energiegebruik_aardgas_proces_huidig_m3.toLocaleString(),
          },
          {
            key: "pand_energiegebruik_aardgas_proces_scenario_m3",
            name: "Scenario aardgasgebruik proces",
            value: kpis.pand_energiegebruik_aardgas_proces_scenario_m3.toLocaleString(),
          },
          {
            key: "pand_energiegebruik_elektriciteit_gebouw_huidig_kWh",
            name: "Huidig elektriciteitsgebruik gebouw",
            value: pand_energiegebruik_elektriciteit_gebouw_huidig_kWh.toLocaleString(),
          },
          {
            key: "pand_energiegebruik_elektriciteit_proces_huidig_kWh",
            name: "Huidig elektriciteitsgebruik proces",
            value: pand_energiegebruik_elektriciteit_proces_huidig_kWh.toLocaleString(),
          },
        ],
        pand_energiegebruik_aardgas_gebouw_schalingsfactor: pand_energiegebruik_aardgas_gebouw_schalingsfactor,
        pand_energiegebruik_aardgas_proces_schalingsfactor: pand_energiegebruik_aardgas_proces_schalingsfactor,
        pand_energiegebruik_elektriciteit_gebouw_schalingsfactor: pand_energiegebruik_elektriciteit_gebouw_schalingsfactor,
        pand_energiegebruik_elektriciteit_proces_schalingsfactor: pand_energiegebruik_elektriciteit_proces_schalingsfactor,
        pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh: kpis.pand_energiegebruik_elektriciteit_gebouw_warmtepomp_scenario_kWh,
        pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh: 0,
      };
    }
    buildings.value = response;
  } finally {
    isLoading.value = false;
  }
}
doGetData();

const onSubmit = async () => {
  await doPost("measures/apply", formState.value);
  window.refresh_esdl();
  doGetData();
}
</script>

<style scoped>

</style>