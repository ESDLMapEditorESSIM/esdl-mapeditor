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
      @beforeCellFocus="beforeFocus"
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
  console.log(asset_list.value);
  // create list of unique asset types
  asset_types_list.value = [...new Set(asset_list.value.map(asset=>asset.type))];
}
get_asset_type_list();

const get_asset_data = async (asset_type) => {
  const response = await fetch("/table_editor/asset_data/" + asset_type);
  console.log(response);
  if (response.ok) {
    const table_editor_info = await response.json();
    console.log(table_editor_info);

    columns.value = table_editor_info['column_info']
    for (const col_info of columns.value) {
      if ('options' in col_info) {
        col_info['editor'] = "select_grid_ant";
        col_info['cellTemplate'] = VGridVueTemplate(SelectGridAntViewer);
      }
    }
    rows.value = table_editor_info['row_info']
  }
  console.log(columns.value);
}

function selected_asset_changed(asset_type) {
  console.log(asset_type);
  get_asset_data(asset_type);
}

const rowHeaders = ref({ size: 100 });
const gridEditors = ref({
  select_grid_ant: VGridVueEditor(SelectGridAnt),
  select_grid_plain: VGridVueEditor(SelectGridPlain),
});

const columns = ref([
        { name: "Name", prop: "name" },
        { name: "Details", prop: "details" },
        {
          name: "Button",
          prop: "button"
        },
        // { name: "Editor", prop: "editor", size: 200, editor: "myEditor" },
        {
          name: "Dropdown Ant",
          prop: "dropdown_ant",
          autosize: true,
          editor: "select_grid_ant",
          cellTemplate: VGridVueTemplate(SelectGridAntViewer),
          options: [
            {
              value: "jack",
              label: "Jack",
            },
            {
              value: "lucy",
              label: "Lucy",
            },
            {
              value: "disabled",
              label: "Disabled",
              disabled: true,
            },
            {
              value: "yiminghe",
              label: "Yiminghe",
            },
          ],
        },
        {
          name: "Dropdown Plain",
          prop: "dropdown_plain",
          autosize: true,
          editor: "select_grid_plain",
        },
]);

const rows = ref([
        {
          name: "Row 1a",
          details: "Item 1",
          button: 5,
          // editor: 2,
          dropdown_ant: "lucy",
          dropdown_plain: "lucy",
        },
        {
          name: "Row 2",
          details: "Item 2",
          button: 7,
          // editor: 3,
          dropdown_ant: "jack",
          dropdown_plain: "jack",
        },
        {
          name: "Row 3",
          details: "Item 3",
          button: 7,
          // editor: 3,
          dropdown_ant: "jack",
          dropdown_plain: "jack",
        },
        {
          name: "Row 4",
          details: "Item 4",
          button: 7,
          // editor: 3,
          dropdown_ant: "jack",
          dropdown_plain: "jack",
        },
        {
          name: "Row 5",
          details: "Item 5",
          button: 7,
          // editor: 3,
          dropdown_ant: "jack",
          dropdown_plain: "jack",
        },
        {
          name: "Row 6",
          details: "Item 6",
          button: 7,
          // editor: 3,
          dropdown_ant: "jack",
          dropdown_plain: "jack",
        },
]);

function beforeFocus(e) {
  e.preventDefault();
}

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
