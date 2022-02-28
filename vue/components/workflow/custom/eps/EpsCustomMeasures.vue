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
  <p v-if="isLoading">Loading...</p>
  <p v-else-if="buildings.length === 0">No buildings found in ESDL. Please load a valid EPS ESDL and try again.</p>
  <div v-else>
    <a-select
      v-model:value="selectedBuildingId"
      show-search
      placeholder="Select a building"
      style="width: 300px"
      @change="selectBuilding"
    >
      <a-select-option
        v-for="building in buildings"
        :key="building.id"
      >
        {{ building.name }}
      </a-select-option>
    </a-select>
    <hr>
    <div v-if="selectedBuilding">
      <h4>{{ selectedBuilding.name }}</h4>
      <a-table :data-source="formState[selectedBuilding.id].table" :columns="columns" :pagination="false" />
      <br>
      <a-form layout="vertical" :model="formState" :label-col="{ span: 0 }">
        <a-form-item label="Aardgasgebruik gebouw schalingsfactor">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_aardgas_gebouw_schalingsfactor"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
        <a-form-item label="Aardgasgebruik proces schalingsfactor">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_aardgas_proces_schalingsfactor"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
        <a-form-item label="Elektriciteitsgebruik gebouw schalingsfactor">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_elektriciteit_gebouw_schalingsfactor"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
        <a-form-item label="Elektriciteitsgebruik proces schalingsfactor">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_elektriciteit_proces_schalingsfactor"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
        <a-form-item label="Elektriciteit warmtepomp (kWh)">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
        <a-form-item label="Elektriciteit proceselektrificatie warmte (kWh)">
          <a-input-number
            v-model:value="formState[selectedBuilding.id].pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh"
            :step="scalingFactorStepSize" style="width: 300px;"
          />
        </a-form-item>
      </a-form>
    </div>
    <a-button type="primary" @click="onSubmit"> Apply measures</a-button>
  </div>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {doGet} from "../../../../utils/api";
import {useWorkflow} from "../../../../composables/workflow";

const { goToPreviousStep } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const scalingFactorStepSize = 0.0001;

const selectedBuildingId = ref(null);
const selectedBuilding = ref(null);

const formState = ref({});

const isLoading = ref(true);
const buildings = ref([]);


function selectBuilding() {
  for (const building of buildings.value) {
    if (building.id === selectedBuildingId.value) {
      selectedBuilding.value = building;
      return;
    }
  }
  selectedBuilding.value = null;
}

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

function roundFactor(value) {
  return Math.round(value / scalingFactorStepSize) * scalingFactorStepSize;
}

const doGetData = async () => {
  isLoading.value = true;
  try {
    const response = await doGet("eps_workflow/get_buildings");
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

      const pand_energiegebruik_aardgas_gebouw_schalingsfactor = roundFactor(pand_energiegebruik_aardgas_gebouw_huidig_m3 > 0 ? kpis.pand_energiegebruik_aardgas_gebouw_scenario_m3 / pand_energiegebruik_aardgas_gebouw_huidig_m3 : 0);
      const pand_energiegebruik_aardgas_proces_schalingsfactor = roundFactor(pand_energiegebruik_aardgas_proces_huidig_m3 > 0 ? kpis.pand_energiegebruik_aardgas_proces_scenario_m3 / pand_energiegebruik_aardgas_proces_huidig_m3 : 0);
      const pand_energiegebruik_elektriciteit_gebouw_schalingsfactor = roundFactor(pand_energiegebruik_elektriciteit_gebouw_huidig_kWh > 0 ? kpis.pand_energiegebruik_elektriciteit_gebouw_scenario_kWh / pand_energiegebruik_elektriciteit_gebouw_huidig_kWh : 0);
      const pand_energiegebruik_elektriciteit_proces_schalingsfactor = roundFactor(pand_energiegebruik_elektriciteit_proces_huidig_kWh > 0 ? kpis.pand_energiegebruik_elektriciteit_proces_scenario_kWh / pand_energiegebruik_elektriciteit_proces_huidig_kWh : 0);
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
        pand_energiegebruik_elektriciteit_gebouw_warmtepomp_kWh: roundFactor(kpis.pand_energiegebruik_elektriciteit_gebouw_warmtepomp_scenario_kWh),
        pand_energiegebruik_elektriciteit_proces_elektrificatie_warmte_kWh: 0,
      };
    }
    buildings.value = response;
  } finally {
    isLoading.value = false;
  }
}
doGetData();

const workflowStep = props.workflowStep;

const onSubmit = async () => {

  const params = {};
  params["service_id"] = workflowStep.service.id;
  params["query_parameters"] = {};

  params["query_parameters"]['measures_to_apply'] = formState.value;

  window.socket.emit("command", { cmd: "query_esdl_service", params: params });

  goToPreviousStep();
}
</script>

<style scoped>

</style>