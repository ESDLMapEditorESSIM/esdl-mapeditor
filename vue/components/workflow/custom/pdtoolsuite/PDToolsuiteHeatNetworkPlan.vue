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
  <p v-else-if="buildings.length === 0">No buildings found. Load an EPS ESDL with industrial heating mode enabled to create a heat network plan.</p>
  <p v-else-if="carriers.length === 0">No carriers found in this ESDL.</p>
  <div v-else>
    <p>
      Select buildings and the carrier for this heat network plan.
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
      <a-select
        v-model:value="selectedCarrierId"
        allow-clear
        show-search
        :filter-option="(inputValue, option) => option.label.toLowerCase().includes(inputValue.toLowerCase())"
        placeholder="Select a carrier"
        style="width: 300px"
        :options="carrierDropdownOptions"
        @popup-scroll="hide_jquery_ui_popup()"
      />
    </a-form-item>

    <a-form-item>
      <a-checkbox v-model:checked="autoRoute">Route along roads</a-checkbox>
      <p v-if="autoRoute">Road routing requires at least two buildings.</p>
    </a-form-item>

    <a-form-item>
      <a-button type="primary" @click="onSubmit"> Create heat network plan</a-button>
    </a-form-item>
  </div>
</template>

<script setup="props">
import {computed, onUnmounted, ref} from "vue";
import {doGet, fetchData} from "@/utils/api";
import {MessageNames, PubSubManager} from "@/bridge";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const selectedBuildingIds = ref([]);
const selectedCarrierId = ref();
const autoRoute = ref(true);

const isLoading = ref(true);
const buildings = ref([]);
const carriers = ref([]);

const buildingDropdownOptions = computed(() => {
  return buildings.value.map((building) => {
    return {
      label: building.name,
      value: building.id,
    };
  })
});

const carrierDropdownOptions = computed(() => {
  return carriers.value.map((carrier) => {
    return {
      label: carrier.name,
      value: carrier.id,
    };
  })
});

const doGetData = async () => {
  selectedBuildingIds.value = [];
  selectedCarrierId.value = undefined;
  isLoading.value = true;
  try {
    const response = await doGet("pdtoolsuite_workflow/get_buildings");
    if (!response) {
      alert("No buildings received.");
      return
    }
    buildings.value = response;
    carriers.value = await fetchData("DLA_get_carrier_list", {});

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
  params["state_params"]['carrier_id'] = selectedCarrierId.value;
  params["state_params"]['auto_route'] = autoRoute.value;

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
