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
  <div id="visible_layers_view" style="padding-left: 8px;">
    <a-row>
      <h4>Visible layers</h4>
    </a-row>
    <a-row v-if="treeData.length > 0">
      <a-col :span="24">
        <vue-js-tree
          :tree-id="treeId" :plugins="['contextmenu', 'types', 'dnd']"
          :data="treeData" :events="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
          :check-call-back="checkCallBack"
        />
      </a-col>
      <a-col>
        <LayerOpacityPopover 
          :layer-id="selectedLayerId" 
          @close-popover="closeLayerOpacityPopover"
        />
      </a-col>
    </a-row>
    <a-row v-else>
      <p class="text-only">No map layers loaded.</p>
    </a-row>
  </div>
</template>

<script setup>
import {computed, ref} from 'vue';
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import LayerOpacityPopover from "../components/popover/LayerOpacityPopover.vue";
import {useSocketIO} from "@/composables/socketio";
import {useVisibleLayers} from "@/composables/visibleLayers";

// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const {getVisibleLayerList, updateDisplayOrderVisibleLayers, hideVisibleLayer, hideAllVisibleLayers} = useVisibleLayers();

// eslint-disable-next-line no-unused-vars
const treeId = "visible_layer_tree";

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  if (getVisibleLayerList()) {
    let visibleLayersJsreeData = [];
    for (const visibleLayer of getVisibleLayerList()) {
      visibleLayersJsreeData.push({
        id: visibleLayer.id,
        text: visibleLayer.description,
        type: "visible_layer",
      });
    }
    return visibleLayersJsreeData;
  } else {
    return null;
  }
});

// Reference to the targeted layer when adjusting the layer opacity.
const selectedLayerId = ref("");

/**
 * Open the LayerOpacityPopover component by setting the selectedLayerId value.
 * 
 * @param {object} node jsTree node
 */
const openLayerOpacityPopover = (node) => {
  selectedLayerId.value = node.id;
};

/**
 * Close the LayerOpacityPopover component by resetting selectedLayerId to an empty string.
 */
const closeLayerOpacityPopover = () => {
  selectedLayerId.value = "";
};

class MovableLayerTreeSpec {
  constructor() {
    this.type = "visible_layer";
    this.icon = "fas fa-grip-lines";
    this.max_depth = 0;
  }

  contextMenus(node, tree) {
    return {
      'adjust_opacity': {
        'label': 'Adjust layer opacity',
        'icon': 'fa fa-sliders',
        'action': function () {
          openLayerOpacityPopover(node);
        }
      },
      'hide_layer': {
        'label': 'Hide layer',
        'icon': 'fas fa-minus',
        'action': function () {
          hideVisibleLayer(node.id);
        }
      },
      'hide_all_layers': {
        'label': 'Hide all layers',
        'icon': 'fas fa-minus-square',
        'action': function () {
          hideAllVisibleLayers();
        }
      }
    };
  }
}

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new MovableLayerTreeSpec()];

// eslint-disable-next-line no-unused-vars
const eventHandlersByName = {
  'move_node.jstree': function (e, data) {
    updateDisplayOrderVisibleLayers(data.node.id, data.node.position);
  },
  'hover_node.jstree': function (e, data, treeElement) {
    treeElement.attr("title", data.node.text);
  },
}

// eslint-disable-next-line no-unused-vars
const checkCallBack = (operation, node, node_parent, node_position, more) => {
  if (operation === 'move_node') {
    if (node.type !== 'visible_layer') {
      return false;
    }
  } else if (operation === 'copy_node') {
    return false;
  }
  return true;
};

</script>

<style lang="scss">
#visible_layers_view {
  .text-only {
    padding-left: 8px;
  }

}

.bold {
  font-weight: bold;
}
</style>