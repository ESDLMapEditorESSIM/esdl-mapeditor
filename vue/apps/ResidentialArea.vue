<template>
  <a class="dropdown-item" href="#" @click="showWindowResidentialArea">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fas fa-home" aria-hidden="true" /></div>
    Residential Area
  </a>
  <a-modal v-model:open="open" title="Residential Area" width="1200px">
    <template #footer>
      <a-button key="ok" type="primary" @click="handleOk">
        Ok
      </a-button>
    </template>

    <a-space direction="vertical" style="width: 100%">
      <a-card v-if="primos_info">
        <h3>
          PRIMOS data for {{ primos_gm_naam }} ({{ primos_gm_code }})
        </h3>
        <a-table :columns="primos_info_columns" :data-source="primos_info" :pagination="false" size="small" style="width: 100%">
        </a-table>
      </a-card>

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
    </a-space>
  </a-modal>
</template>

<script setup>
import {ref} from "vue";
import {doGet, doPost} from "../utils/api";
// import {startDrawAggregatedBuilding} from "../utils/startDrawAsset";

const open = ref(false);
const building_list = ref([]);
const res_area_info = ref();
const primos_info = ref([]);
const primos_gm_naam = ref();
const primos_gm_code = ref();

const buildingListColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Number', dataIndex: 'num', key: 'num', slots: { customRender: 'enter_number_of_buildings' }},
];

const primos_info_columns = [
  { title: 'Period', dataIndex: 'label', key: 'label' },
  { title: 'Planned additions', dataIndex: 'additions'},
  { title: 'Planned removals', dataIndex: 'removals'},
  { title: 'Cumulative', dataIndex: 'cumulative'},
];

const handleOk = () => {
  createAggregatedBuilding();
  open.value = false;
}

const createAggregatedBuilding = () => {
  console.log("==========================================");
  console.log(res_area_info.value);
  if (res_area_info.value) {
    window.socket.emit(
      "residential_area_create",
      {
        "building_composition": building_list.value,
        "id": res_area_info.value.id,
        "lat": res_area_info.value.lat,
        "lon": res_area_info.value.lng
      },
      function() {
        res_area_info.value = null;
      }
    );
  } else {
    window.socket.emit(
      "residential_area_create", {
        "building_composition": building_list.value
      },
      function() {
        res_area_info.value = null;

        // The post call to the backend above put the right aggregatedbuilding in "memory"
        window.startDrawMarkerAsset("AggregatedBuilding");
      }
    );
  }
}

const showWindowResidentialArea = () => {
  open.value = true;
}
window.showWindowResidentialArea = showWindowResidentialArea;

const showWindowResidentialAreaForMunicipality = async (e, info) => {
  res_area_info.value = info;
  const response = await doPost("residential_area/get_primos", {"id": info.id});
  const responseJson = await response.json();

  if ("info" in responseJson) {
    primos_info.value = responseJson.info;
    primos_gm_naam.value = responseJson.gm_naam;
    primos_gm_code.value = responseJson.gm_code;
  }

  open.value = true
}
window.showWindowResidentialAreaForMunicipality = showWindowResidentialAreaForMunicipality;

const get_building_list = async () => {
  const response = await doGet("residential_area/get_building_list");
  building_list.value = response["building_list"];
}
get_building_list();



</script>