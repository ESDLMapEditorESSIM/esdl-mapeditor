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

    <a-row v-if="layerGroups.length > 0">
      <a-col :span="24">
        <draggable v-model="layerGroups" group="groups" @end="onEndDrag">
          <transition-group name="layer">
            <!-- Group Item -->
            <div v-for="group in layerGroups" :key="group.id" class="layer-group-item">
              <!-- Group Header with Collapse Toggle, Visibility, and Hamburger Menu -->
              <div class="group-header">
                <div class="group-info">
                  <i class="fas" :class="group.collapsed ? 'fa-chevron-right' : 'fa-chevron-down'" @click="toggleCollapse(group)" />
                  <div class="group-visibility-toggle" @click="toggleGroupVisibility(group.id)">
                    <i :class="group.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
                  </div>
                  <span>{{ group.description }}</span>
                </div>
                <!-- Group Hamburger Menu -->
                <div class="group-actions">
                  <i class="fas fa-bars" @click="toggleActionMenu(group.id)" />
                  <div v-if="activeMenu === group.id" class="action-menu">
                    <ul>
                      <li @click="hideAllLayersInGroup(group.id)">Hide All Layers</li>
                      <li @click="removeGroup(group.id)">Remove Group</li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- Individual Layers in Group -->
              <draggable v-if="!group.collapsed" v-model="group.layers" group="layers" @end="onEndDragLayer(group.id)">
                <div v-for="layer in group.layers" :key="layer.id" class="layer-item">
                  <div class="layer-info">
                    <div class="visibility-toggle" @click="toggleLayerVisibility(layer)">
                      <i :class="layer.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
                    </div>
                    <span class="layer-text">{{ getLayerDescription(layer) }}</span>
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
              </draggable>
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
  getVisibleLayerGroups,
  toggleGroupVisibility,
  hideVisibleLayer,
  showVisibleLayer,
  hideAllVisibleLayers,
  getLayerType,
} = useVisibleLayers();


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

const selectedLayerId = ref('');
const activeMenu = ref('');

const layerGroups = computed(() => {
  return getVisibleLayerGroups();
});

// Toggle visibility of an individual layer
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

// Handle drag and drop for groups
const onEndDrag = (evt) => {
  const movedGroup = layerGroups.value[evt.newIndex];
  // Logic to handle drag-and-drop reordering for groups
};

// Handle drag and drop for layers within a group
const onEndDragLayer = (groupId) => (evt) => {
  const movedLayer = layerGroups.value.find((group) => group.id === groupId).layers[evt.newIndex];
  // Logic to handle drag-and-drop reordering for layers within a group
};

// Close opacity popover
const closeLayerOpacityPopover = () => {
  selectedLayerId.value = '';
};

// Hide all visible layers
const hideAllLayers = () => {
  hideAllVisibleLayers();
};

// Hide all layers in a specific group
const hideAllLayersInGroup = (groupId) => {
  const group = layerGroups.value.find((g) => g.id === groupId);
  if (group) {
    group.layers.forEach((layer) => hideVisibleLayer(layer.id));
  }
};

// Remove a group
const removeGroup = (groupId) => {
  const group = layerGroups.value.find((g) => g.id === groupId);
  if (group) {
    group.layers.forEach((layer) => hideVisibleLayer(layer.id));
  }
};

// Toggle the action menu (hamburger menu)
const toggleActionMenu = (id) => {
  activeMenu.value = activeMenu.value === id ? '' : id;
};

// Toggle the collapse state of a group
const toggleCollapse = (group) => {
  group.collapsed = !group.collapsed;
};

const getLayerDescription = (visibleLayer) => {
  if (getLayerType(visibleLayer) === VisibleLayerType.WMS) {
    return visibleLayer.description;
  } else if (getLayerType(visibleLayer) === VisibleLayerType.ESDL) {
    const esdlLayerName = esdlLayerNameMap[visibleLayer.layer_type] || 'Unknown Layer';
    return visibleLayer.es.title + ' - ' + esdlLayerName;
  } else {
    console.error("Unknown layer type", visibleLayer);
    return "Unknown Layer";
  }
};
</script>

<style scoped>
.layer-group-item {
  margin-bottom: 15px;
  border: 1px solid #ddd;
  padding: 10px;
  background-color: #f4f4f4;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #e8e8e8;
  padding: 8px;
  border-bottom: 1px solid #ddd;
  font-weight: bold;
}

.layer-item {
  padding-left: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  border-bottom: 1px solid #ddd;
  background-color: #fff;
}

.visibility-toggle, .group-visibility-toggle {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.group-info {
  display: flex;
  align-items: center;
}

.group-actions, .layer-actions {
  position: relative;
  margin-left: auto;
}

.group-actions i, .layer-actions i {
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
