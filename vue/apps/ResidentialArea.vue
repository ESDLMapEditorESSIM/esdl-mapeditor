<template>
  <a class="dropdown-item" href="#" @click="showWindowResidentialArea">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fas fa-home" aria-hidden="true" /></div>
    Residential Area
  </a>
  <a-modal v-model:visible="visible" title="Residential Area" width="1200px">
    <template #footer>
      <a-button key="ok" type="primary" @click="handleOk">
        Ok
      </a-button>
    </template>

    <a-table :columns="buildingListColumns" :data-source="building_list" size="middle" style="width: 100%">
      <template #enter_number_of_buildings="{ record }">
        <a-input
          v-model:value="record.num"
          class="fe_box"
          size="small"
          type="text"
        />
      </template>
    </a-table>
  </a-modal>
</template>

<script setup>
import {ref} from "vue";
import {doGet, doPost} from "../utils/api";
// import {startDrawAggregatedBuilding} from "../utils/startDrawAsset";

const visible = ref(false);
const building_list = ref([]);

const buildingListColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Number', dataIndex: 'num', key: 'num', slots: { customRender: 'enter_number_of_buildings' }},
];

const handleOk = () => {
  createAggregatedBuilding();
  visible.value = false;
}

const createAggregatedBuilding = async () => {
  const response = await doPost("residential_area/create", {"building_composition": building_list.value});

  // The post call to the backend above put the right aggregatedbuilding in "memory"
  window.startDrawMarkerAsset("AggregatedBuilding");
}

const showWindowResidentialArea = () => {
  visible.value = true;
}

const get_building_list = async () => {
  const response = await doGet("residential_area/get_building_list");
  building_list.value = response["building_list"];
}
get_building_list();



</script>