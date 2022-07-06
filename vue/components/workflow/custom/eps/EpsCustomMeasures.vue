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
      v-model:value="selectedBuildingIds"
      mode="multiple"
      show-search
      placeholder="Select a building"
      style="width: 300px"
      :options="buildingDropdownOptions"
    />
    <hr>
    <div v-if="firstSelectedBuilding">
      <a-table v-if="firstSelectedBuilding" :data-source="formState[firstSelectedBuilding.id].table" :columns="columns" :pagination="false" />
      <br>
      <a-form layout="vertical" :model="formState" :label-col="{ span: 0 }">
        <!-- Warmtevraag gebouw -->
        <a-form-item label="Percentage warmtevraag gebouw door gas">
          <a-input-number
            v-model:value="formState.percentage_warmtevraag_gebouw_gas"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_warmtevraag_gebouw_gas, value)"
          />
        </a-form-item>
        <a-form-item label="Efficiëntie warmte-installatie gebouw gas">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_gebouw_gas"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_gebouw_gas, value)"
          />
        </a-form-item>
        <a-form-item label="Percentage warmtevraag gebouw door elektriciteit">
          <a-input-number
            v-model:value="formState.percentage_warmtevraag_gebouw_elektriciteit"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_warmtevraag_gebouw_elektriciteit, value)"
          />
        </a-form-item>
        <a-form-item label="Efficiëntie warmte-installatie gebouw elektriciteit">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_gebouw_elektriciteit"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_gebouw_elektriciteit, value)"
          />
        </a-form-item>
        <!-- Warmtevraag proces -->
        <a-form-item label="Percentage warmtevraag proces door gas">
          <a-input-number
            v-model:value="formState.percentage_warmtevraag_proces_gas"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_warmtevraag_proces_gas, value)"
          />
        </a-form-item>
        <a-form-item label="Efficiëntie warmte-installatie proces gas">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_proces_gas"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_proces_gas, value)"
          />
        </a-form-item>
        <a-form-item label="Percentage warmtevraag proces door elektriciteit">
          <a-input-number
            v-model:value="formState.percentage_warmtevraag_proces_elektriciteit"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_warmtevraag_proces_elektriciteit, value)"
          />
        </a-form-item>
        <a-form-item label="Efficiëntie warmte-installatie proces elektriciteit">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_proces_elektriciteit"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_proces_elektriciteit, value)"
          />
        </a-form-item>
        <!-- Procesgas -->
        <a-form-item label="Percentage gasgebruik proces voor warmte">
          <a-input-number
            v-model:value="formState.percentage_proces_gas_warmte"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_proces_gas_warmte, value)"
          />
        </a-form-item>
        <a-form-item label="Efficiëntie warmte-installatie proces gas">
          <a-input-number
            v-model:value="formState.efficientie_proces_gas_warmte"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_proces_gas_warmte, value)"
          />
        </a-form-item>
      </a-form>
    </div>
    <a-button type="primary" @click="onSubmit"> Apply measures</a-button>
  </div>
</template>

<script setup="props">
import {computed, defineProps, ref} from "vue";
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

const selectedBuildingIds = ref([]);

const firstSelectedBuilding = computed(() => {
  return selectedBuildings.value ? selectedBuildings.value[0] : null;
})

const selectedBuildings = computed(() => {
  const selectedBuildings = []
  for (const building of buildings.value) {
    if (selectedBuildingIds.value.includes(building.id)) {
      selectedBuildings.push(building)
    }
  }
  return selectedBuildings;
})

const formState = ref({});

const isLoading = ref(true);
const buildings = ref([]);

const buildingDropdownOptions = computed(() => {
  return buildings.value.map((building) => {
    return {
      label: building.name,
      value: building.id,
    };
  })
});

/**
 * Update the value for all selected buildings.
 *
 * TODO: This does not yet work!
 * @param field_name
 * @param value
 */
function updateValue(field_name, value) {
  console.log(field_name)
  console.log(value)
  for (const selectedBuildingId of selectedBuildingIds.value) {
    console.log(selectedBuildingId);
    formState.value[field_name] = value;
  }
  console.log(formState.value);
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
    const response = await doGet("dice_workflow/get_buildings");
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