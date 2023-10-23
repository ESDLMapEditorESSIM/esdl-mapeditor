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
  <div id="maps_view">
    <div>
      <button style="float:right" @click="showAddLayerDialog">Add WMS layer</button>
      <br>
    </div>
    <vue-js-tree v-if="treeData != null" :tree-id="treeId" :plugins="['contextmenu', 'types', 'checkbox']"
                 :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
    />
    <div v-else>
      <p class="text-only">No map layers loaded.</p>
    </div>
  </div>
</template>

<script setup>
import {computed} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useSocketIO} from "../composables/socketio";
import {useBaseLayers,} from "../composables/baseLayers";
import {useVisibleLayerList} from "../composables/useVisibleLayerList"


const {addToVisibleItemList, removeFromVisibleItemList} = useVisibleLayerList();

const {
  addBaseLayerToMap,
  baseLayerDefinitions,
  getBaseLayerByLabel,
  removeBaseLayerFromMap
} = useBaseLayers();
// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();

const treeId = "maps_tree"
const $ = window.$;
const wmsLayerList = window.wms_layer_list;

const getTree = () => $('#' + treeId).jstree(true);

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  if (wmsLayerList) {
    let wmsGroupsJstreeData = [];
    for (const wmsGroup of wmsLayerList.groups) {
      const children = getGroupLayers(wmsGroup.setting_type);
      wmsGroupsJstreeData.push({
        text: wmsGroup.name, type: 'wms_layer_folder', state: {opened: true},
        children: children,
        a_attr: {
          "class": "no_checkbox"
        }
      })
    }

    return [
      get_base_layers_control_tree_data(),
      ...wmsGroupsJstreeData,
    ];
  } else {
    return null;
  }
});

function showAddLayerDialog() {
  let sidebar_ctr = window.sidebar.getContainer();
  sidebar_ctr.innerHTML = '<h1>Add WMS layer</h1>';
  sidebar_ctr.innerHTML = sidebar_ctr.innerHTML + window.create_add_layer_div();
  window.sidebar.show();
}

function getGroupLayers(setting_type) {
  const layers = [];
  for (const [key, layer] of Object.entries(wmsLayerList.layers)) {
    if (layer.setting_type === setting_type) {
      layers.push({
        text: layer.description,
        type: "wms_layer",
        a_attr: {
          "class": layer.active ? "bold" : "",
        },
        state: {"checked": layer.active, opened: true},
      })
    }
  }
  return layers;
}

function show_wms_layer(id) {
  wmsLayerList['layers'][id].layer_ref.addTo(window.map);
  wmsLayerList['layers'][id].layer_ref.bringToFront();
  wmsLayerList['layers'][id].visible = true;
  if (wmsLayerList['layers'][id].legend_url !== "") {
    window.show_wms_legend(wmsLayerList['layers'][id].legend_url);
  }
}

function hide_wms_layer(id) {
  window.map.removeLayer(wmsLayerList['layers'][id].layer_ref);
  wmsLayerList['layers'][id].visible = false;
  if (wmsLayerList['layers'][id].legend_url !== "") {
    window.remove_wms_legend();
  }
}

class LayerFolderTreeSpec {
  constructor() {
    this.type = "wms_layer_folder";
    this.icon = 'fas fa-layer-group';
  }
}

class LayerTreeSpec {
  constructor() {
    this.type = "wms_layer";
    this.icon = 'fas fa-map';
    this.max_depth = 0;
  }
}

class BaseLayerFolderTreeSpec {
  constructor() {
    this.type = "base_layer_folder";
    this.icon = "fas fa-layer-group";
  }
}

class BaseLayerTreeSpec {
  constructor() {
    this.type = "base_layer";
    this.icon = 'far fa-map';
    this.max_depth = 0;
  }
}

const treeTypeSpecs = [new LayerFolderTreeSpec(), new BaseLayerTreeSpec(), new BaseLayerFolderTreeSpec(), new LayerTreeSpec];

// TODO: Move into tree specs
const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'select_node.jstree',
  handler: function (e, data, treeElement) {
    const type = data.node.type;
    const original = data.node.original;
  }
}, {
  eventName: 'check_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'base_layer') {
      // Single base layer selection
      for (const checkedNode of getTree().get_checked_descendants(data.node.parent)) {
        if (checkedNode !== data.node.id) {
          getTree().uncheck_node(checkedNode)
        }
      }
      for (const baseLayer of baseLayerDefinitions) {
        removeBaseLayerFromMap(baseLayer);
      }

      const baseLayer = getBaseLayerByLabel(original.text);
      addBaseLayerToMap(baseLayer);
    } else if (type === 'wms_layer') {
      show_wms_layer(original.text);
      addToVisibleItemList(data.node, 0);
    }
  }
}, {
  eventName: 'uncheck_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      removeBaseLayerFromMap(baseLayer);
    } else if (type === 'wms_layer') {
      hide_wms_layer(original.text);
      removeFromVisibleItemList(data.node);
    }
  }
}];

function get_base_layers_control_tree_data() {
  let children = [];

  for (const baseLayer of baseLayerDefinitions) {
    let state = {};
    if (baseLayer.enabled) {
      state.checked = true;
    }

    const child = {
      id: baseLayer.label,
      text: baseLayer.label,
      type: "base_layer",
      state: state,
    }
    children.push(child);
  }

  const group = {
    id: "group_base_layers",
    text: "Base layers",
    type: "base_layer_folder",
    state: {
      opened: true
    },
    children: children,
    a_attr: {
      "class": "no_checkbox"
    }
  }

  return group;
}

</script>

<style lang="scss">
#maps_view {
  padding: 8px 5px 8px 2px;
  overflow: scroll;
  //resize: horizontal;
  width: 100%;

  .text-only {
    padding-left: 8px;
  }

}

.bold {
  font-weight: bold;
}
</style>