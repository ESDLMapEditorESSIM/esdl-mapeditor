<template>
  <h1>Search for assets</h1>
  <a-card style="width: 100%">
    <p>
      You can search for assets based on the type, name and id. Just start typing in the search box
      and the list of assets is filtered automatically. Click on an asset in the list to let the map
      zoom to this asset.
    </p>
  </a-card>
  <a-input
    v-model:value="search_text"
    placeholder="Enter search term..."
  />
  <a-table
    :columns="columns"
    :data-source="filtered_asset_list"
    row-key="id"
    :custom-row="customRow"
    :pagination="{ pageSize: 50 }"
    :scroll="{ y: 'max-content' }"
  >
    <template #name="{ record }">
      <b>{{ record.type }}:</b> {{ record.name }}<br>
      <span style="font-size: x-small">(id: {{ record.id }})</span>
    </template>
  </a-table>
</template>

<script setup>
import { ref, computed } from 'vue'

const columns = [
  {
    title: 'Asset',
    dataIndex: 'name',
    width: 150,
    slots: { customRender: "name" },
  },
];

const asset_list = ref([]);
const search_text = ref("");

const filtered_asset_list = computed(() => {
  return asset_list.value.filter((asset) => {
    return asset.name.includes(search_text.value) || asset.id.includes(search_text.value) ||
      asset.type.includes(search_text.value);
  });
})

function customRow(record) {
  return {
    onClick: () => {
      console.log(record);
      if (record instanceof window.L.Marker) {
        window.map.setView(record.getLatLng(), 20);
      } else {
        window.map.fitBounds(record.getBounds());
      }
    },
  };
}

function get_asset_list() {
  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  asset_list.value = active_es_asset_layers;
  console.log(asset_list.value);
}

get_asset_list();

</script>
