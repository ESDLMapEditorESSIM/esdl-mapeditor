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
  <p>
    In this step, custom energy saving and electrification measures can be applied for building-related and industrial process energy use, through modifying a number of parameters.
  </p>
  <p>
    <strong class="text-warning">Note:</strong> Please make sure to select the ESDL on which to apply these measures. Apply custom measures only on ESDLs loaded from the EPS.
  </p>
  <p>
    The values for custom measures applied are stored for this ESDL, for later adjustments.
  </p>
  <p v-if="isLoading">Loading...</p>
  <p v-else-if="buildings.length === 0">No buildings found in ESDL. Please load a valid EPS ESDL and try again.</p>
  <div v-else>
    <a-select
      v-model:value="selectedBuildingIds"
      mode="multiple"
      allow-clear
      show-search
      :filter-option="(inputValue, option) => option.label.toLowerCase().includes(inputValue.toLowerCase())"
      placeholder="Select a building"
      style="width: 300px"
      :options="buildingDropdownOptions"
      @change="onSelectBuilding"
    />
    <a-button type="default" @click="selectAll"> Select all</a-button>
    <hr>

    <div v-if="firstSelectedBuilding">
      <a-form layout="vertical" :model="formState" :label-col="{ span: 0 }">
        <h4>Huidige inzet gasgebruik proces</h4>

        <a-form-item label="Percentage gasgebruik proces voor warmte">
          <a-input-number
            v-model:value="formState.percentage_proces_gas_warmte"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(percentage_proces_gas_warmte, value)"
          />
        </a-form-item>
        <a-form-item label="Huidige efficiëntie warmte-installatie proces gas">
          <a-input-number
            v-model:value="formState.efficientie_proces_gas_warmte"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_proces_gas_warmte, value)"
          />
        </a-form-item>
        
        <!-- Warmtevraag gebouw -->
        <h4>Maatregelen warmtevraag gebouw</h4>
        <p v-if="heatpumpApplied" style="color: var(--gray)">
          <small>A heat pump was applied in this ESDL. Therefore, heat demand has been assigned to electricity and heat demand cannot be assigned to gas.</small>
        </p>
        <p v-if="heatpumpConflict" style="color: var(--gray)">
          <strong>Warning</strong>: The selected buildings contain conflicting energy measures. If you proceed, you could overwrite previously applied measures.
        </p>

        <a-form-item label="Schalingsfactor warmtevraag gebouw">
          <a-input-number
            v-model:value="formState.schalingsfactor_warmtevraag_gebouw"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(schalingsfactor_warmtevraag_gebouw, value)"
          />
        </a-form-item>

        <a-form-item label="Warmte installatie">
          <a-radio-group v-model:value="heatingType">
            <a-radio-button value="HEATPUMP">Warmtepomp</a-radio-button>
            <a-radio-button value="GAS" :disabled="heatpumpApplied">Gas</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <!--        <a-form-item label="Percentage warmtevraag gebouw door gas">-->
        <!--          <a-input-number-->
        <!--            v-model:value="formState.percentage_warmtevraag_gebouw_gas"-->
        <!--            :disabled="heatpumpApplied"-->
        <!--            :step="scalingFactorStepSize"-->
        <!--            style="width: 300px;"-->
        <!--            @change="(value) => updateValue(percentage_warmtevraag_gebouw_gas, value)"-->
        <!--          />-->
        <!--        </a-form-item>-->
        <a-form-item label="Efficiëntie warmte-installatie gebouw gas">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_gebouw_gas"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_gebouw_gas, value)"
          />
        </a-form-item>
        <!--        <a-form-item label="Percentage warmtevraag gebouw door elektriciteit">-->
        <!--          <a-input-number-->
        <!--            v-model:value="formState.percentage_warmtevraag_gebouw_elektriciteit"-->
        <!--            :step="scalingFactorStepSize"-->
        <!--            style="width: 300px;"-->
        <!--            @change="(value) => updateValue(percentage_warmtevraag_gebouw_elektriciteit, value)"-->
        <!--          />-->
        <!--        </a-form-item>-->
        <a-form-item label="COP warmtepomp gebouw elektriciteit">
          <a-input-number
            v-model:value="formState.efficientie_warmteinstallatie_gebouw_elektriciteit"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(efficientie_warmteinstallatie_gebouw_elektriciteit, value)"
          />
        </a-form-item>

        <!-- Warmtevraag proces -->
        <h4>Maatregelen warmtevraag proces</h4>
        <a-form-item label="Schalingsfactor warmtevraag proces">
          <a-input-number
            v-model:value="formState.schalingsfactor_warmtevraag_proces"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(schalingsfactor_warmtevraag_proces, value)"
          />
        </a-form-item>
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
        <h4>Maatregelen gasgebruik proces (niet voor warmte)</h4>
        <a-form-item label="Schalingsfactor gasgebruik proces (niet voor warmte)">
          <a-input-number
            v-model:value="formState.schalingsfactor_gasgebruik_proces_excl_warmte"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(schalingsfactor_gasgebruik_proces_excl_warmte, value)"
          />
        </a-form-item>

        <h4>Maatregelen elektriciteitsgebruik gebouw</h4>
        <a-form-item label="Schalingsfactor elektriciteitsgebruik gebouw">
          <a-input-number
            v-model:value="formState.schalingsfactor_elektriciteitsgebruik_gebouw"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(schalingsfactor_elektriciteitsgebruik_gebouw, value)"
          />
        </a-form-item>

        <h4>Maatregelen elektriciteitsgebruik proces</h4>
        <a-form-item label="Schalingsfactor elektriciteitsgebruik proces">
          <a-input-number
            v-model:value="formState.schalingsfactor_elektriciteitsgebruik_proces"
            :step="scalingFactorStepSize"
            style="width: 300px;"
            @change="(value) => updateValue(schalingsfactor_elektriciteitsgebruik_proces, value)"
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
import {useEsdlLayers} from "../../../../composables/esdlLayers.js";
import {MessageNames, PubSubManager} from "../../../../bridge";

const { getActiveEsdlLayerId } = useEsdlLayers();
const { getState, goToPreviousStep } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const scalingFactorStepSize = 0.01;

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
const heatingType = ref(null);
const heatpumpApplied = ref(false);
const heatpumpConflict = ref(false);

const HeatingType = Object.freeze({
  GAS: 'GAS',
  HEATPUMP: 'HEATPUMP',
});

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
  for (const selectedBuildingId of selectedBuildingIds.value) {
    formState.value[field_name] = value;
  }
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
  selectedBuildingIds.value = [];
  isLoading.value = true;
  try {
    const response = await doGet("dice_workflow/get_buildings");
    if (!response) {
      alert("No buildings received.");
      return
    }
    buildings.value = response;

  } finally {
    isLoading.value = false;
  }
}
doGetData();

const workflowStep = props.workflowStep;

const onSubmit = async () => {
  if (formState.value.percentage_warmtevraag_proces_gas + formState.value.percentage_warmtevraag_proces_elektriciteit !== 100) {
    alert("Please make sure the sum of the heat demand percentages of gas and electricity is 100.")
    return false;
  }
  const params = {};
  params["service_id"] = workflowStep.service.id;
  params["query_parameters"] = {};

  params["query_parameters"]['building_ids'] = selectedBuildingIds.value;

  // Selection of heating type currently happens with a radio button. In the future we could support partials.
  if (heatingType.value === HeatingType.HEATPUMP) {
    formState.value.percentage_warmtevraag_gebouw_gas = 0;
    formState.value.percentage_warmtevraag_gebouw_elektriciteit = 100;
  } else {
    formState.value.percentage_warmtevraag_gebouw_gas = 100;
    formState.value.percentage_warmtevraag_gebouw_elektriciteit = 0;
  }
  params["query_parameters"]['measures_to_apply'] = formState.value;

  // Store the form entry values.
  // The structure:
  // state.custom_measures: {
  //   esdl_id: {
  //     building_id1: {<formState>},
  //     building_id2: {<formState>},
  //   }
  // }
  const state = getState();
  if (!state.customMeasures) {
    state.customMeasures = {};
  }
  state.customMeasures[getActiveEsdlLayerId().value] = {};
  for (const selectedBuildingId of selectedBuildingIds.value) {
    state.customMeasures[getActiveEsdlLayerId().value][selectedBuildingId] = formState.value;
  }

  window.socket.emit("command", { cmd: "query_esdl_service", params: params });

  window.show_loader();
}

/**
 * Select all buildings, or unselect if all are already selected..
 */
const selectAll = () => {
  if (buildings.value.length === selectedBuildingIds.value.length) {
    // Everything is already selected. Unselect everything.
    selectedBuildingIds.value = [];
  } else {
    // Keep a list so we can trigger a one-by-one addition in the onSelectBuilding.
    const innerSelectedBuildingIds = [];
    for (const building of buildings.value) {
      innerSelectedBuildingIds.push(building.id);
      onSelectBuilding(innerSelectedBuildingIds);
      selectedBuildingIds.value = innerSelectedBuildingIds;
    }
  }
}

const onSelectBuilding = async (newSelectedBuildingIds) => {
  const newlySelectedBuildingId = newSelectedBuildingIds.filter(x => !selectedBuildings.value.includes(x))[0];
  const newlySelectedBuilding = buildings.value.find(building => building.id === newlySelectedBuildingId);
  if (newlySelectedBuilding) {
    if (newSelectedBuildingIds.length === 1) {
      formState.value = {
        efficientie_warmteinstallatie_gebouw_gas: 1,
        percentage_warmtevraag_gebouw_gas: 100,
        efficientie_warmteinstallatie_gebouw_elektriciteit: newlySelectedBuilding.heatpump_efficiency || 1,
        percentage_warmtevraag_gebouw_elektriciteit: 0,
        percentage_warmtevraag_proces_gas: 100,
        efficientie_warmteinstallatie_proces_gas: 1,
        percentage_warmtevraag_proces_elektriciteit: 0,
        efficientie_warmteinstallatie_proces_elektriciteit: 1,

        percentage_proces_gas_warmte: 100,
        efficientie_proces_gas_warmte: 1,

        schalingsfactor_warmtevraag_gebouw: 1,
        schalingsfactor_elektriciteitsgebruik_gebouw: 1,
        schalingsfactor_gasgebruik_proces_excl_warmte: 1,
        schalingsfactor_elektriciteitsgebruik_proces: 1,
        schalingsfactor_warmtevraag_proces: 1,
      };

      // The heat pump is applied if we don't have any aardgas usage.
      heatpumpApplied.value = newlySelectedBuilding.heatpump_efficiency != null;

      // Load the form entry values.
      const state = getState();
      if (state.customMeasures && state.customMeasures[getActiveEsdlLayerId().value] && state.customMeasures[getActiveEsdlLayerId().value][newlySelectedBuildingId]) {
        formState.value = state.customMeasures[getActiveEsdlLayerId().value][newlySelectedBuildingId];
        if (formState.value.percentage_warmtevraag_gebouw_gas < 100) {
          heatpumpApplied.value = true;
          newlySelectedBuilding.heatpump_efficiency = 1;
        }
      }

      heatingType.value = heatpumpApplied.value ? HeatingType.HEATPUMP : HeatingType.GAS;
      if (heatpumpApplied.value) {
        formState.value.percentage_warmtevraag_gebouw_gas = 0;
        formState.value.percentage_warmtevraag_gebouw_elektriciteit = 100;
      }
    }
  }

  // If a building is selected that conflicts in terms of heatpump, show a warning.
  heatpumpConflict.value = false;
  for (const selectedBuilding of selectedBuildings.value) {
    const buildingHeatpumpApplied = newlySelectedBuilding.heatpump_efficiency != null;
    if (buildingHeatpumpApplied !== heatpumpApplied.value) {
      heatpumpConflict.value = true;
    }
  }
}

PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
  doGetData();
});
</script>

<style scoped>

</style>