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
    <h3>Visible layers</h3>
    <vue-js-tree v-if="treeData != null" :tree-id="treeId" :plugins="['contextmenu', 'types', 'dnd']"
                 :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
    />
    <div v-else>
      <p class="text-only">No map layers loaded.</p>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, defineProps} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useSocketIO} from "../composables/socketio";
import {useVisibleLayers} from "../composables/visibleLayers"

// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const {getVisibleLayerList, updateDisplayOrderVisibleLayers} = useVisibleLayers();

const treeId = "visible_layer_tree"
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  if (getVisibleLayerList()) {
    let visibleLayersJsreeData = [];
    for (const visibleLayer of getVisibleLayerList()) {
      visibleLayersJsreeData.push({
        id : visibleLayer.id,
        text: visibleLayer.description,
        type: "movable_layer",
      });
    }
    return visibleLayersJsreeData;
  } else {
    return null;
  }
});

class MovableLayerTreeSpec {
  constructor() {
    this.type = "movable_layer";
    this.icon = "fas fa-grip-lines";
    this.max_depth = 0;
  }
}

const treeTypeSpecs = [new MovableLayerTreeSpec()];

// TODO: Move into tree specs
const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'move_node.jstree',
  handler: function (e, data, treeElement) {
    updateDisplayOrderVisibleLayers(data.node.id, data.node.position);
  }
}];

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