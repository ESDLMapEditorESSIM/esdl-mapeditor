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
      <h4>Visible layers</h4>
      <button class="hide-all-btn" @click="hideAllLayers">
        <i class="fas fa-eye-slash" /> Hide All
      </button>
    </a-row>

    <a-row v-if="layerGroups.length > 0">
      <a-col :span="24" class="layer-groups">
        <draggable v-model="layerGroups" group="groups" @end="onEndDrag">
          <transition-group name="layer">
            <!-- Group Item -->
            <div v-for="group in layerGroups" :key="group.id">
              <!-- Group Header with Collapse Toggle, Visibility, and Hamburger Menu -->
              <div :class="['group-header', { 'active-group': isActiveGroup(group) }]" @click="toggleExpanded(group)">
                <div class="layer-info">
                  <span>{{ group.description }}</span>
                  <div class="layer-info-right">
                    <div class="group-visibility-toggle" @click.stop="toggleGroupVisibility(group.id)">
                      <i :class="group.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
                    </div>
                    <i class="fas" :class="isGroupExpanded(group.id) ? 'fa-chevron-down' : 'fa-chevron-right'" />
                  </div>
                </div>
              </div>

              <!-- Individual Layers in Group -->
              <draggable v-if="isGroupExpanded(group.id)" v-model="group.layers" group="layers" @end="onEndDragLayer(group.id)">
                <div v-for="layer in group.layers" :key="layer.id" class="layer-item">
                  <div class="layer-info">
                    <span class="layer-text">{{ getLayerDescription(layer) }}</span>
                    <div class="layer-info-right">
                      <div class="visibility-toggle" @click.stop="toggleLayerVisibility(layer)">
                        <i :class="layer.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
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
import {ref, watch} from 'vue';
import { VueDraggableNext as draggable } from 'vue-draggable-next';
import { useVisibleLayers, VisibleLayerType } from '@/composables/visibleLayers';
const {esdlProject} = useESDLProjects();
import LayerOpacityPopover from "@/components/popover/LayerOpacityPopover.vue";
import {useESDLProjects} from "@/composables/esdlProjects";

const {
  getVisibleLayerGroups,
  toggleGroupVisibility,
  hideVisibleLayer,
  showVisibleLayer,
  hideAllVisibleLayers,
  getLayerType,
  updateGroupOrder,
  updateDisplayOrderVisibleLayers,
} = useVisibleLayers();

const expandedGroups = ref([]);

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

const layerGroups = ref([]);

watch(getVisibleLayerGroups(), (newGroups) => {
  console.log("Updating layer groups", newGroups);
  layerGroups.value = [...newGroups];
}, { immediate: true });

/**
 * Toggles the visibility of an individual layer.
 * @param {Object} layer - The layer object to toggle visibility.
 */
const toggleLayerVisibility = (layer) => {
  if (layer.visible) {
    hideVisibleLayer(layer.id);
  } else {
    showVisibleLayer(layer.id);
  }
};

/**
 * Handles drag-and-drop reordering for groups.
 * @param {Object} evt - The event object from the drag-and-drop action.
 */
const onEndDrag = (evt) => {
  const newOrder = layerGroups.value.map(group => group.id);
  updateGroupOrder(newOrder);
};

const onEndDragLayer = (groupId) => {
  const group = layerGroups.value.find(group => group.id === groupId);
  const newOrder = group.layers.map(layer => layer.id);
  updateDisplayOrderVisibleLayers(groupId, newOrder);
};

/**
 * Closes the layer opacity popover.
 */
const closeLayerOpacityPopover = () => {
  selectedLayerId.value = '';
};

/**
 * Hides all visible layers.
 */
const hideAllLayers = () => {
  hideAllVisibleLayers();
};

/**
 * Toggles the visibility of the action menu (hamburger menu).
 * @param {string} id - The ID of the layer for which the action menu is toggled.
 */
const toggleActionMenu = (id) => {
  activeMenu.value = activeMenu.value === id ? '' : id;
};

/**
 * Toggles the expanded state of a group.
 * @param {Object} group - The group object to toggle expansion.
 */
const toggleExpanded = (group) => {
  expandedGroups.value = expandedGroups.value.includes(group.id)
      ? expandedGroups.value.filter((id) => id !== group.id)
      : [...expandedGroups.value, group.id];
};

/**
 * Checks if a group is expanded.
 * @param {string} groupId - The ID of the group to check.
 * @returns {boolean} True if the group is expanded, false otherwise.
 */
const isGroupExpanded = (groupId) => {
  return expandedGroups.value.includes(groupId);
};

/**
 * Returns a description for the given visible layer based on its type.
 * @param {VisibleLayer} visibleLayer - The layer object.
 * @returns {string} The description of the layer.
 */
const getLayerDescription = (visibleLayer) => {
  if (getLayerType(visibleLayer) === VisibleLayerType.WMS) {
    return visibleLayer.description;
  } else if (getLayerType(visibleLayer) === VisibleLayerType.ESDL) {
    const esdlLayerName = esdlLayerNameMap[visibleLayer.description] || visibleLayer.description
    return esdlLayerName;
  } else {
    console.error("Unknown layer type", visibleLayer);
    return "Unknown Layer";
  }
};

/**
 * Checks if the group's ID matches the active ESDL project ID.
 * @param {VisibleLayerGroup} group - The group to check.
 * @returns {boolean} True if the group's ID matches the active ESDL project ID, false otherwise.
 */
const isActiveGroup = (group) => {
  return group.id === esdlProject.value.active_es_id;
};
</script>

<style scoped>
.layer-groups {
  margin-top: 10px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #e8e8e8;
  padding: 8px;
  border-bottom: 1px solid #ddd;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.group-header:hover {
  background-color: #d8d8d8;
}

.active-group {
  background-color: lightblue;
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

.layer-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.layer-info-right {
  display: flex;
  align-items: center;
  margin-left: auto;
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
  margin-left: 10px;
}

.hide-all-btn:hover {
  background-color: #ddd;
}
</style>
