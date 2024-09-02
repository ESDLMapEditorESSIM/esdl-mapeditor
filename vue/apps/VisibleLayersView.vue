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
      <h4>Visible WMS layers</h4>
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
import {useVisibleLayers, VisibleLayerType} from "@/composables/visibleLayers";

// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const {
  getVisibleLayerList,
  updateDisplayOrderVisibleLayers,
  getLayerType,
  hideVisibleLayer,
  hideAllVisibleLayers,
  hideRelatedVisibleLayers,
  showVisibleLayer
} = useVisibleLayers(window.map, socket);

// eslint-disable-next-line no-unused-vars
const treeId = "visible_layer_tree";

const esdlLayerNameMap = {
    "esdl_layer": "Assets",
    "area_layer": "Area",
    "bld_layer": "Buildings",
    "connection_layer": "Connections",
    "kpi_layer": "KPIs",
    "notes_layer": "Notes",
    "pot_layer": "Potentials",
    "sim_layer": "Simulation results",
};

// Function to convert input to desired string
const getEsdlLayerName = (input) => {
    return esdlLayerNameMap[input] || 'Unknown Layer';
}

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  if (getVisibleLayerList()) {
    let visibleLayersJstreeData = [];
    for (const visibleLayer of getVisibleLayerList()) {
      if (getLayerType(visibleLayer) === VisibleLayerType.WMS) {
        // WMS Layer.
        visibleLayersJstreeData.push({
          id: visibleLayer.id,
          text: visibleLayer.description,
          type: "visible_layer",
        });
      } else if (getLayerType(visibleLayer) === VisibleLayerType.ESDL) {
        // ESDL Layer.
        const esdlLayerName = getEsdlLayerName(visibleLayer.layer_type);
        visibleLayersJstreeData.push({
          id: visibleLayer.id,
          text: visibleLayer.es.title + " - " + esdlLayerName,
          type: "visible_esdl_layer",
          es_id: visibleLayer.es.id,
        });
      } else {
        console.error("Unknown layer type", visibleLayer);
      }
    }
    return visibleLayersJstreeData;
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

class MovableWmsLayerTreeSpec {
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
      'hide_all_wms_layers': {
        'label': 'Hide all WMS layers',
        'icon': 'fas fa-minus-square',
        'action': function () {
          hideRelatedVisibleLayers();
        }
      },
      // TODO: This should be a separate button in the UI, plus a show all.
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

class MovableEsdlLayerTreeSpec {
  constructor() {
    this.type = "visible_esdl_layer";
    this.icon = "fas fa-grip-lines";
    this.max_depth = 0;
  }

  contextMenus(node, tree) {
    return {
      'hide_layer': {
        'label': 'Hide layer',
        'icon': 'fas fa-eye-slash',
        'action': function () {
          hideVisibleLayer(node.id);
        }
      },
      'show_layer': {
        'label': 'Show layer',
        'icon': 'fas fa-eye',
        'action': function () {
          showVisibleLayer(node.id);
        }
      },
      'hide_all_layers_of_esdl': {
        'label': 'Hide all layers of this ESDL',
        'icon': 'fas fa-minus-square',
        'action': function () {
          hideRelatedVisibleLayers(node.id);
        }
      }
    };
  }
}

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new MovableEsdlLayerTreeSpec(), new MovableWmsLayerTreeSpec()];

// eslint-disable-next-line no-unused-vars
const eventHandlersByName = {
  'move_node.jstree': function (e, data) {
    updateDisplayOrderVisibleLayers(data.node.id, data.position);
  },
  'hover_node.jstree': function (e, data, treeElement) {
    treeElement.attr("title", data.node.text);
  },
}

// eslint-disable-next-line no-unused-vars
const checkCallBack = (operation, node, node_parent, node_position, more) => {
  if (operation === 'move_node') {
    if (node.type !== 'visible_layer' && node.type !== 'visible_esdl_layer') {
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