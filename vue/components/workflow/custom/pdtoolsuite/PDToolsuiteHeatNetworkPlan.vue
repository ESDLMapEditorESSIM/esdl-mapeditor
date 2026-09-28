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
  <p v-else-if="loadError">{{ loadError }}</p>
  <p v-else-if="buildings.length === 0">No buildings found in the active ESDL.</p>
  <div v-else @mouseover.stop @focusin.stop>
    <p>
      Select the type of heat network and the buildings to include in the plan.
    </p>

    <a-form-item label="Type warmtenet" required>
      <a-select
        v-model:value="selectedHeatNetworkType"
        allow-clear
        placeholder="Select type of heat network"
        style="width: 300px"
        :options="HEAT_NETWORK_TYPE_OPTIONS"
      />
    </a-form-item>
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
        :disabled="!selectedHeatNetworkType"
      />
      <a-button type="default" :disabled="buildingDropdownOptions.length === 0" @click="selectAll"> Select all</a-button>
    </a-form-item>

    <a-form-item>
      <a-checkbox v-model:checked="autoRoute">Route along roads</a-checkbox>
      <p v-if="autoRoute">Road routing requires at least two buildings.</p>
    </a-form-item>

    <a-form-item>
      <a-button type="primary" :disabled="!canSubmit" @click="onSubmit"> Create heat network plan</a-button>
    </a-form-item>
  </div>
</template>

<script setup="props">
import {computed, onUnmounted, ref} from "vue";
import {doGet} from "@/utils/api";
import {MessageNames, PubSubManager} from "@/bridge";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const selectedBuildingIds = ref([]);
const selectedHeatNetworkType = ref();
const autoRoute = ref(true);

const isLoading = ref(true);
const loadError = ref("");
const buildings = ref([]);

const HEAT_NETWORK_TYPE_OPTIONS = [
  {value: "ht", label: "Hogetemperatuur warmtenet"},
  {value: "mt", label: "Middentemperatuur warmtenet"},
  {value: "lt", label: "Lagetemperatuur warmtenet"},
];

const buildingDropdownOptions = computed(() => {
  return buildings.value.map((building) => {
    let label = building.name;
    if ((building.residual_heat_sources || []).length > 0) {
      label += " (supplier)";
    }

    return {
      label,
      value: building.id,
      title: "",
    };
  });
});

const canSubmit = computed(() => {
  const buildingIds = new Set(buildingDropdownOptions.value.map((option) => option.value));
  return !isLoading.value && Boolean(selectedHeatNetworkType.value) && selectedBuildingIds.value.length > 0
    && selectedBuildingIds.value.every((id) => buildingIds.has(id))
    && (!autoRoute.value || selectedBuildingIds.value.length >= 2);
});

const doGetData = async () => {
  selectedBuildingIds.value = [];
  selectedHeatNetworkType.value = undefined;
  isLoading.value = true;
  buildings.value = [];
  loadError.value = "";
  try {
    const response = await doGet("pdtoolsuite_workflow/get_buildings");
    if (!Array.isArray(response)) {
      loadError.value = "Could not load buildings from the active ESDL. Check the request error and reopen this workflow to retry.";
      return;
    }
    buildings.value = response;

  } finally {
    isLoading.value = false;
  }
}
doGetData();

const workflowStep = props.workflowStep;

const onSubmit = async () => {
  if (!canSubmit.value) {
    return;
  }
  const params = {};
  params["service_id"] = workflowStep.service.id;
  params["state_params"] = {};
  params["state_params"]['building_ids'] = selectedBuildingIds.value;
  params["state_params"]['heat_network_type'] = selectedHeatNetworkType.value;
  params["state_params"]['auto_route'] = autoRoute.value;

  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
  window.show_loader();
}

/**
 * Select all buildings, or unselect if all are already selected..
 */
const selectAll = () => {
  if (buildingDropdownOptions.value.length === selectedBuildingIds.value.length) {
    selectedBuildingIds.value = [];
  } else {
    selectedBuildingIds.value = buildingDropdownOptions.value.map((option) => option.value);
  }
}

const subscriptionId = PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
  doGetData();
});
onUnmounted(() => PubSubManager.unsubscribe(subscriptionId));
</script>

<style scoped>

</style>
