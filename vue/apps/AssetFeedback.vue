<template>
  <h1>Asset feedback</h1>
  <template
    v-if="asset_feedback_list.length"
  >
    <a-card style="width: 100%">
      <p>
        The following feedback was given for the assets in the energy system. You can click on an item in the list
        to let the map zoom into the specific asset
      </p>
    </a-card>
    <a-input
      v-model:value="search_text"
      placeholder="Enter search term..."
    />
    <a-table
      :columns="columns"
      :data-source="filtered_asset_feedback_list"
      row-key="id"
      :custom-row="customRow"
      :pagination="{ pageSize: 50 }"
      :scroll="{ y: 'max-content' }"
    >
      <template #name="{ record }">
        <b>{{ record.name }}</b><br>
        <span
          v-for="item in record.messages"
          :key="item.key"
          style="font-size: x-small"
        >
          <span :style="severity_color_mapping[item.severity]">{{ item.severity }}:</span> {{ item.message }}<br>
        </span>
      </template>
    </a-table>
  </template>
  <template v-else>
    <a-card style="width: 100%">
      <p>
        The validation service could not detect any errors. Well done!
      </p>
    </a-card>
  </template>
  <a-space>
    <a-button type="primary" @click="close_window">Ok</a-button>
    <a-button
      v-if="asset_feedback_list.length"
      type="primary"
      @click="clear_asset_feedback_from_map"
    >
      Clear feedback from map
    </a-button>
  </a-space>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAssetFeedbackList } from '../composables/assetFeedback';
import { v4 as uuidv4 } from 'uuid';

const { currentAssetFeedbackList } = useAssetFeedbackList();

const columns = [
  {
    title: 'Asset with error(s)',
    dataIndex: 'name',
    width: 150,
    slots: { customRender: "name" },
  },
];

const asset_feedback_list = ref([]);
const search_text = ref("");

const severity_color_mapping =  {
  "INFO": "color:#00FF00",
  "WARNING": "color:#FFA500",
  "ERROR": "color:#FF0000",
}

const filtered_asset_feedback_list = computed(() => {
  return asset_feedback_list.value.filter((record) => {
    return record.name.includes(search_text.value); // || record.message.includes(search_text.value);
  });
})

function customRow(record) {
  return {
    onClick: () => {
      console.log(record);
      if (record.layer instanceof window.L.Marker) {
        window.map.setView(record.layer.getLatLng(), 20);
      } else {
        window.map.fitBounds(record.layer.getBounds());
      }
    },
  };
}

function clear_asset_feedback_from_map() {
  window.clear_layers(window.active_layer_id, 'sim_layer');
}

function close_window() {
  window.sidebar.hide();
}

function create_asset_feedback_list() {
  // Retrieve list of ESDL layers from the map, such that feedback can refer to this data
  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  console.log(currentAssetFeedbackList.value);
  let tmp_asset_feedback_list = [];

  for (let i=0; i<active_es_asset_layers.length; i++) {
    let asset = active_es_asset_layers[i];
    if (asset.id in currentAssetFeedbackList.value) {

      let messages = [];
      for (let j=0; j<currentAssetFeedbackList.value[asset.id].length; j++) {
        messages.push({
          key: uuidv4(),
          message: currentAssetFeedbackList.value[asset.id][j]['message'],
          severity: currentAssetFeedbackList.value[asset.id][j]['severity'],
        });
      }

      let feedback_item = {
        key: asset.id,
        name: asset.name,
        messages: messages,
        layer: asset,
      }
      tmp_asset_feedback_list.push(feedback_item);
    }
  }
  asset_feedback_list.value = tmp_asset_feedback_list;
}

create_asset_feedback_list();

</script>
