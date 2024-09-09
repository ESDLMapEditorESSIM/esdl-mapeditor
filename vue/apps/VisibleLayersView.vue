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
    <a-row justify="space-between" align="middle">
      <h4>Visible WMS layers</h4>
      <button class="hide-all-btn" @click="hideAllLayers">
        <i class="fas fa-eye-slash" /> Hide All
      </button>
    </a-row>
    <a-row v-if="treeData.length > 0">
      <a-col :span="24">
        <draggable v-model="treeData" @end="onEndDrag">
          <transition-group name="layer">
            <div v-for="layer in treeData" :key="layer.id" class="layer-item">
              <div class="layer-info">
                <!-- Toggle visibility with an eye icon -->
                <div class="visibility-toggle" @click="toggleLayerVisibility(layer)">
                  <i :class="layer.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
                </div>
                <span class="layer-text">{{ getLayerDescription(layer) }}</span>
                <!-- Hamburger menu for actions -->
                <div class="layer-actions">
                  <i class="fas fa-bars" @click="toggleActionMenu(layer.id)" />
                  <div v-if="activeMenu === layer.id" class="action-menu">
                    <ul>
                      <li @click="removeLayer(layer.id)">Remove Layer</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </transition-group>
        </draggable>
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
import { computed, ref } from 'vue';
import { VueDraggableNext as draggable } from 'vue-draggable-next';
import LayerOpacityPopover from '../components/popover/LayerOpacityPopover.vue';
import { useVisibleLayers, VisibleLayerType } from '@/composables/visibleLayers';

const {
  getVisibleLayerList,
  updateDisplayOrderVisibleLayers,
  hideVisibleLayer,
  showVisibleLayer,
  hideAllVisibleLayers,
  getLayerType,
} = useVisibleLayers();

const treeData = computed(() => {
  return getVisibleLayerList();
});

const selectedLayerId = ref('');
const activeMenu = ref('');

// Toggle visibility of a layer
const toggleLayerVisibility = (layer) => {
  if (layer.visible) {
    hideVisibleLayer(layer.id);
  } else {
    showVisibleLayer(layer.id);
  }
};

// Remove a layer
const removeLayer = (id) => {
  hideVisibleLayer(id);
};

// Handle drag and drop
const onEndDrag = (evt) => {
  const movedLayer = treeData.value[evt.newIndex];
  updateDisplayOrderVisibleLayers(movedLayer.id, evt.newIndex);
};

// Close opacity popover
const closeLayerOpacityPopover = () => {
  selectedLayerId.value = '';
};

// Hide all visible layers
const hideAllLayers = () => {
  hideAllVisibleLayers();
};

// Toggle the action menu (hamburger menu)
const toggleActionMenu = (id) => {
  activeMenu.value = activeMenu.value === id ? '' : id;
};

const getLayerDescription = (layer) => {
  if (getLayerType(layer) === VisibleLayerType.WMS) {
    return layer.description;
  } else if (getLayerType(layer) === VisibleLayerType.ESDL) {
    return `${layer.es.title} - ${getEsdlLayerName(layer.layer_type)}`;
  } else {
    return "Unknown Layer";
  }
};

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

const getEsdlLayerName = (input) => {
  return esdlLayerNameMap[input] || 'Unknown Layer';
};
</script>

<style scoped>
.layer-view {
  width: 300px;
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #f4f4f4;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  background-color: #fff;
  margin-bottom: 5px;
  border: 1px solid #ccc;
  position: relative;
}

.layer-info {
  display: flex;
  align-items: center;
  flex-grow: 1;
}

.layer-text {
  flex-grow: 1;
  margin-left: 10px;
}

.visibility-toggle {
  width: 20px;
  height: 20px;
  cursor: pointer;
  margin-right: 10px;
}

.layer-actions {
  position: relative;
}

.layer-actions i {
  margin-left: auto;
  cursor: pointer;
}

.action-menu {
  position: absolute;
  right: 0;
  top: 25px;
  background-color: white;
  border: 1px solid #ccc;
  z-index: 10;
}

.action-menu ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.action-menu li {
  padding: 5px;
  cursor: pointer;
}

.hide-all-btn {
  background-color: #f4f4f4;
  border: 1px solid #ccc;
  cursor: pointer;
  padding: 5px 10px;
  display: flex;
  align-items: center;
}

.hide-all-btn:hover {
  background-color: #ddd;
}
</style>
