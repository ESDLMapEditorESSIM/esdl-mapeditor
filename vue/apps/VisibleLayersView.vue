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
  <a-card id="visible_layers_view">
    <h3>Visible WMS layers</h3>
    <vue-js-tree v-if="treeData.length > 0" :tree-id="treeId" :plugins="['contextmenu', 'types', 'dnd']"
                 :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
                 :check-call-back="checkCallBack"
    />
    <div v-else>
      <p class="text-only">No map layers loaded.</p>
    </div>
  </a-card>
</template>

<script setup>
import {computed} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useSocketIO} from "../composables/socketio";
import {useVisibleLayers} from "../composables/visibleLayers"

// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const {getVisibleLayerList, updateDisplayOrderVisibleLayers} = useVisibleLayers();

// eslint-disable-next-line no-unused-vars
const treeId = "visible_layer_tree"

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

class MovableLayerTreeSpec {
  constructor() {
    this.type = "visible_layer";
    this.icon = "fas fa-grip-lines";
    this.max_depth = 0;
  }
}

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new MovableLayerTreeSpec()];

// TODO: Move into tree specs
// eslint-disable-next-line no-unused-vars
const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'move_node.jstree',
  handler: function (e, data) {
    updateDisplayOrderVisibleLayers(data.node.id, data.node.position);
  }
}, {
  eventName: 'hover_node.jstree',
  handler: function (e, data, treeElement) {
    console.log('hover')
    treeElement.attr("title", data.node.text);
  },
}];

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