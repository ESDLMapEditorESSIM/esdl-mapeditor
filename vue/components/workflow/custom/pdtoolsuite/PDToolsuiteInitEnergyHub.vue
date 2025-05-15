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
  <p v-if="isLoading">Loading...</p>
  <p v-else-if="buildings.length === 0">No buildings found in ESDL. Please load a valid EPS ESDL and try again.</p>
  <div v-else>
    <p>
      Select which buildings will be part of the energy hub.
    </p>
    <p>
      For these buildings, an energy hub will be configured in the ESDL layer, represented by 2 GenericConversion assets, 2 ElectricityCable assets and 1 ElectricityNetwork asset. The capacity constraints for the energy hub can be added to the ElectricityCable assets. Collective assets (in front of the meter) can be manually connected to the ElectricityNetwork asset via the Map Editor functionalities.
    </p>
    <p>
      See the user manual for more information on configuring an energy hub in an ESDL layer.
    </p>

    <a-form-item>
      <a-select
        v-model:value="selectedBuildingIds"
        mode="multiple"
        allow-clear
        show-search
        :filter-option="(inputValue, option) => option.label.toLowerCase().includes(inputValue.toLowerCase())"
        placeholder="Select a building"
        style="width: 300px"
        :options="buildingDropdownOptions"
        @popup-scroll="hide_jquery_ui_popup()"
      />
      <a-button type="default" @click="selectAll"> Select all</a-button>
    </a-form-item>

    <a-form-item>
      <a-button type="primary" @click="onSubmit"> Create ESDL with Energy Hub</a-button>
    </a-form-item>
  </div>
</template>

<script setup="props">
import {computed, onUnmounted, ref} from "vue";
import {doGet, doPost} from "@/utils/api";
import {useWorkflow} from "@/composables/workflow";
import {MessageNames, PubSubManager} from "@/bridge";

const { getState } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const selectedBuildingIds = ref([]);
const formState = ref({});

const isLoading = ref(true);
const buildings = ref([]);

const selectedBuildings = computed(() => {
  const selectedBuildings = []
  for (const building of buildings.value) {
    if (selectedBuildingIds.value.includes(building.id)) {
      selectedBuildings.push(building)
    }
  }
  return selectedBuildings;
})

const buildingDropdownOptions = computed(() => {
  return buildings.value.map((building) => {
    return {
      label: building.name,
      value: building.id,
    };
  })
});

const doGetData = async () => {
  selectedBuildingIds.value = [];
  isLoading.value = true;
  try {
    const response = await doGet("pdtoolsuite_workflow/get_buildings");
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
  const params = {};
  params["service_id"] = workflowStep.service.id;
  params["state_params"] = {};
  params["state_params"]['building_ids'] = selectedBuildingIds.value;

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
    const innerSelectedBuildingIds = [];
    for (const building of buildings.value) {
      innerSelectedBuildingIds.push(building.id);
      selectedBuildingIds.value = innerSelectedBuildingIds;
    }
  }
}

const subscriptionId = PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
  doGetData();
});
onUnmounted(() => PubSubManager.unsubscribe(subscriptionId));

function hide_jquery_ui_popup() {
  window.jquery(".ui-tooltip-content").parents('div').remove();
}
</script>

<style scoped>

</style>