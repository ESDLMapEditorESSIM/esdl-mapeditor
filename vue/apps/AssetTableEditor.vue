<template>
  <a-select
    v-model:value="selected_asset_type"
    style="width: 100%"
    @change="selected_asset_changed"
  >
    <a-select-option
      v-for="type in asset_types_list"
      :key="type"
      :value="type"
    >
      {{ type }}
    </a-select-option>
  </a-select>

  <div id="grid_div">
    <v-grid
      theme="compact"
      :source="rows"
      :columns="columns"
      :editors="gridEditors"
      :rowHeaders="rowHeaders"
      :autoSizeColumn="{
        mode: 'autoSizeOnTextOverlap',
      }"
      resize="true"
      range="true"
      @afteredit="process_changes"
      @beforecellfocus="before_cell_focus"
    />
  </div>
</template>

<script setup>

import { ref, computed } from 'vue'
import VGrid, {
  VGridVueEditor,
  VGridVueTemplate,
} from "@revolist/vue3-datagrid";
import SelectGridAnt from "../components/revogrid/SelectGridAnt.vue";
import SelectGridAntViewer from "../components/revogrid/SelectGridAntViewer.vue";
import SelectGridPlain from "../components/revogrid/SelectGridPlain.vue";

const asset_list = ref([]);
const asset_types_list = ref([]);
const selected_asset_type = ref();

function get_asset_type_list() {
  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  asset_list.value = active_es_asset_layers;
  // create list of unique asset types
  asset_types_list.value = [...new Set(asset_list.value.map(asset=>asset.type))];
}
get_asset_type_list();

const get_asset_data = async (asset_type) => {
  const response = await fetch("/table_editor/asset_data/" + asset_type);
  if (response.ok) {
    const table_editor_info = await response.json();
    // console.log(table_editor_info);

    columns.value = table_editor_info['column_info']
    for (const col_info of columns.value) {
      if ('options' in col_info) {
        col_info['editor'] = "select_grid_ant";
        col_info['cellTemplate'] = VGridVueTemplate(SelectGridAntViewer);
      }
    }
    rows.value = table_editor_info['row_info']
    window.hide_loader();
  } else {
    window.hide_loader();
    console.log('Error getting asset data');
  }
}

function selected_asset_changed(asset_type) {
  window.show_loader();
  get_asset_data(asset_type);
}

const rowHeaders = ref({ size: 100 });
const gridEditors = ref({
  select_grid_ant: VGridVueEditor(SelectGridAnt),
  select_grid_plain: VGridVueEditor(SelectGridPlain),
});

function process_changes(e) {
  /*
    e.detail.xxx, where xxx is:
    - in case of multiple changes:
      - models: dict with rowIndex as key
        {1: Proxy {id:..., name:..., power:..., prodType:..., state:...}}
      - data: dict with rowIndex as key
        {1: {power: 200000, state: ENABLED}, 2: {power: 200000, state: ENABLED}}

    - in case of a single change:
      - model ({id:..., name:..., power:..., prodType:..., state:...})
      - rowIndex
      - prop ('power')
      - value ('3000')
  */

  let changes = e.detail;

  if ('model' in changes) {
    /* Single change */
    if ('id' in changes.model) {
      window.socket.emit("command", {
        cmd: "set_asset_param",
        id: changes.model['id'],
        param_name: changes['prop'],
        param_value: changes['val'],
      });
      window.PubSubManager.broadcast('ASSET_PROPERTIES', {
        id: changes.model['id'],
        name: changes['prop'],
        value: changes['val'],
      });
    } else {
      console.log("Can't find object ID in row data of revolist datagrid");
    }
  } else if ('models' in changes) {
    /* Multiple changes */
    for (const [rowIndex, row] of Object.entries(changes['models'])) {
      if ('id' in row) {
        let id = row['id'];
        let data = changes['data'][rowIndex];
        for (const [attr, value] of Object.entries(data)) {
          window.socket.emit("command", {
            cmd: "set_asset_param",
            id: id,
            param_name: attr,
            param_value: value,
          });
          window.PubSubManager.broadcast('ASSET_PROPERTIES', {
            id: id,
            name: attr,
            value: value,
          });
        }
      } else {
        console.log("Can't find object ID in row data of revolist datagrid");
      }
    }
  } else {
    console.log("Don't understand format of change handler in revolist datagrid");
  }
}

function before_cell_focus(e) {
  console.log(e);
  let asset_id = e.detail.model.id;

  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  for (let i=0; i<active_es_asset_layers.length; i++) {
    if (active_es_asset_layers[i].id == asset_id) {
      // window.map.setView(active_es_asset_layers[i].getLatLng(), 20);
      window.select_assets.deselect_all_assets();
      window.select_assets.toggle_selected(active_es_asset_layers[i]);
    }
  }
}

const columns = ref([
        { name: "Please select an asset type from the select menu above", prop: "action", size: 500 },
]);

const rows = ref([]);

</script>

<style>
#grid_div {
  height: 100%;
  width: 100%;
}
revo-grid {
  height: 100%;
}
</style>
