<template>
  <a-select
    v-model:value="selected_asset_type"
    style="width: 100%"
    :options="asset_types_list"
    @change="selected_asset_changed"
  />
  <div v-if="selected_asset_type && !isLoading"
      id="grid_div"
  >
    <v-grid  v-if="selected_asset_type && !isLoading"
      
      theme="compact"
      :source="rows"
      :columns="columns"
      :editors="gridEditors"
      :auto-size-column="{
        mode: 'autoSizeOnTextOverlap',
      }"
      resize="true"
      range="true"
      @afteredit="process_changes"
      @beforecellfocus="before_cell_focus"
    />
  </div>
  <h3 v-else-if="isLoading">Loading...</h3>
  <h3 v-else>Please select an asset type from the select menu above.</h3>
</template>

<script setup>

import { ref } from 'vue'
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
const isLoading = ref(false);

function get_asset_type_list() {
  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  asset_list.value = active_es_asset_layers;
  // create list of unique asset types
  const unique_asset_types = [...new Set(asset_list.value.map(asset=>asset.type))];
  asset_types_list.value = unique_asset_types.map((asset_type) => {
    return {
      label: asset_type,
      value: asset_type,
    };
  });
}
get_asset_type_list();

const get_asset_data = async (asset_type) => {
  const response = await fetch("/table_editor/asset_data/" + asset_type);

  if (response.ok) {
    const table_editor_info = await response.json();
    // console.log(table_editor_info);
    columns.value = table_editor_info['column_info'];

    for (const col_info of columns.value) {
      if ('options' in col_info) {
        col_info['editor'] = "select_grid_ant";
        col_info['cellTemplate'] = VGridVueTemplate(SelectGridAntViewer);
      }
    }
    rows.value = table_editor_info['row_info']
  } else {
    console.error('Error getting asset data', response);
  }
  isLoading.value = false;
  window.hide_loader();
}

function selected_asset_changed(asset_type) {
  window.show_loader();
  // Use this to unrender the previous vgrid, so that it doesn't conflict with the new data.
  isLoading.value = true;
  get_asset_data(asset_type);
}

// const rowHeaders = ref({ size: 100 });
const gridEditors = ref({
  select_grid_ant: VGridVueEditor(SelectGridAnt),
  select_grid_plain: VGridVueEditor(SelectGridPlain),
});

function change_basic_attribute(id, attr, value) {
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

function check_cost_info(attr) {
  for (const col_info of columns.value) {
    if (col_info['prop'] == attr) {
      if ('ref' in col_info) {
        if (col_info['ref'].startsWith('costInformation')) {
          return true;
        }
      }
    }
  }
  return false;
}

function change_cost_attribute(id, attr, value) {
  // console.log("change_cost_attr", attr, value);
  window.socket.emit("change_cost_attr", {
    id: id,
    attr: attr,
    value: value,
  });
}

function change_multiple_attributes(changed_attr_list) {
  window.socket.emit("change_multiple_attributes", {
    changed_attr_list: changed_attr_list
  });
  // also update gui for multiple attributes
  for (let i in changed_attr_list) {
    window.PubSubManager.broadcast('ASSET_PROPERTIES', {
      id: changed_attr_list[i].id,
      name: changed_attr_list[i].attr,
      value: changed_attr_list[i].value,
    });
  }  
}

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
  // console.log(changes);

  if ('model' in changes) {
    /* Single change */
    if ('id' in changes.model) {
      if (check_cost_info(changes['prop'])) {
        change_cost_attribute(changes.model['id'], changes['prop'], changes['val']);
      } else {
        change_basic_attribute(changes.model['id'], changes['prop'], changes['val']);
      }
    } else {
      console.log("Can't find object ID in row data of revolist datagrid");
    }
  } else if ('models' in changes) {
    /* Multiple changes */
    let changed_attr_list = [];
    for (const [rowIndex, row] of Object.entries(changes['models'])) {
      if ('id' in row) {
        let id = row['id'];
        let data = changes['data'][rowIndex];
        for (const [attr, value] of Object.entries(data)) {
          changed_attr_list.push({id: id, attr: attr, value: value});
        }
      } else {
        console.log("Can't find object ID in row data of revolist datagrid");
      }
    }
    change_multiple_attributes(changed_attr_list);
  } else {
    console.log("Don't understand format of change handler in revolist datagrid");
  }
}

function before_cell_focus(e) {
  // console.log(e);
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

const columns = ref([]);
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
