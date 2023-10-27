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
  <div id="layers_view">
    <div v-if="treeData != null">
      <vue-js-tree tree-id="layer_tree" :plugins="['contextmenu', 'types', 'checkbox']"
                   :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
      />
      <VisibleView />
    </div>
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
// eslint-disable-next-line no-unused-vars
import VisibleView from "./VisibleLayersView.vue";
import {useWmsLayers} from "../composables/wmsLayers";

const {showBaseLayer, baseLayerDefinitions, getBaseLayerByLabel, hideBaseLayer} = useBaseLayers();
const {getWmsLayerList, showWmsLayer, hideWmsLayer, removeWmsLayer} = useWmsLayers();

// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();


// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  if (getWmsLayerList()) {
    let wmsGroupsJstreeData = [];
    for (const wmsGroup of getWmsLayerList().groups) {
      const children = getGroupLayers(wmsGroup.setting_type);
      wmsGroupsJstreeData.push({
        id: wmsGroup.setting_type,
        text: wmsGroup.name,
        type: 'wms_layer_folder',
        state: {opened: true},
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

// eslint-disable-next-line no-unused-vars
function showAddLayerDialog(objectId) {
  window.add_edit_wms_layer(objectId);
}

function getGroupLayers(setting_type) {
  const layers = [];
  for (const [key, layer] of Object.entries(getWmsLayerList().layers)) {
    if (layer.setting_type === setting_type) {
      layers.push({
        id: key,
        text: layer.description,
        setting_type: setting_type,
        type: "wms_layer",
        a_attr: {
          "class": layer.active ? "bold" : "",
        },
        state: {"checked": layer.visible, opened: true},
      })
    }
  }
  return layers;
}

class LayerFolderTreeSpec {
  constructor() {
    this.type = "wms_layer_folder";
    this.icon = 'fas fa-layer-group';
  }

  contextMenus() {
    return {
      'add_layer': {
        'label': 'Add WMS layer',
        'icon': 'fas fa-plus',
        'action': function () {
          showAddLayerDialog(null);
        }
      },
      'add_folder': {
        'label': 'Add folder',
        'icon': 'fas fa-plus',
        'action': function () {
          window.socket.emit('add_wms_layer_group', {
            'id': 'groupID',
            'name': 'groupName',
            'setting_type': 'user',
            'parent_group_id': 'user',
          })
        }
      },
    }
  }
}

class LayerTreeSpec {
  constructor() {
    this.type = "wms_layer";
    this.icon = 'fas fa-map';
    this.max_depth = 0;
  }

  contextMenus(node) {
    return {
      'edit': {
        'label': 'Edit WMS layer',
        'icon': 'far fa-edit',
        'action': function () {
          showAddLayerDialog(node.id);
        },
        '_disabled': node.original.setting_type === 'system',
      },
      'delete': {
        'label': 'Remove WMS layer',
        'icon': 'fa fa-trash-o',
        'action': function () {
          removeWmsLayer(node.id);
        },
        '_disabled': node.original.setting_type === 'system',
      },
    };
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

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new LayerFolderTreeSpec(), new BaseLayerTreeSpec(), new BaseLayerFolderTreeSpec(), new LayerTreeSpec];

// TODO: Move into tree specs
// eslint-disable-next-line no-unused-vars
const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'create_node.jstree',
  handler: function () {
  }
}, {
  eventName: 'select_node.jstree',
  handler: function () {
  }
}, {
  eventName: 'check_node.jstree',
  handler: function (e, data, treeElement) {
    const type = data.node.type;
    const id = data.node.id;
    if (type === 'base_layer') {
      // Single base layer selection
      for (const checkedNode of treeElement.get_checked_descendants(data.node.parent)) {
        if (checkedNode !== id) {
          treeElement.uncheck_node(checkedNode)
        }
      }
      for (const baseLayer of baseLayerDefinitions) {
        hideBaseLayer(baseLayer);
      }

      const baseLayer = getBaseLayerByLabel(id);
      showBaseLayer(baseLayer);
    } else if (type === 'wms_layer') {
      showWmsLayer(id);
    }
  }
}, {
  eventName: 'uncheck_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const id = data.node.id;
    if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(id);
      hideBaseLayer(baseLayer);
    } else if (type === 'wms_layer') {
      hideWmsLayer(id);
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

  return {
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
  };
}

</script>

<style lang="scss">
#layers_view {
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