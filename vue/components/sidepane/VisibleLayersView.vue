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
  <div id="visible_layers_view">
    <BaseLayerTree class="base-layer-tree" />
    <hr>
    <a-row justify="space-between" align="middle">
      <h4>Visible layers</h4>
      <button class="hide-all-btn" @click="toggleAllLayers">
        <i :class="allLayersHidden ? 'fas fa-eye-slash' : 'fas fa-eye'" />
        &nbsp;
        {{ allLayersHidden ? 'Show All' : 'Hide All' }}
      </button>
    </a-row>

    <a-row v-if="layerGroups.length > 0">
      <a-col :span="24" class="layer-groups">
        <draggable v-model="layerGroups" group="groups" @end="onEndDrag">
          <transition-group name="layer">
            <!-- Group Item -->
            <div v-for="group in layerGroups" :key="group.id">
              <div :class="['group-header', { 'active-group': isActiveGroup(group), 'variant-group': getGroupVariant(group) }]" @click="clickGroup(group)">
                <div class="layer-info">
                  <a-button
                    v-if="getGroupVariant(group)"
                    class="group-name"
                    type="text"
                    :aria-pressed="isActiveGroup(group)"
                    :aria-expanded="isGroupExpanded(group.id)"
                    @click.stop="clickGroup(group)"
                  >
                    {{ group.description }}
                  </a-button>
                  <span v-else>{{ group.description }}</span>
                  <div class="layer-info-right">
                    <div class="group-visibility-toggle" @click.stop="toggleGroupVisibility(group.id)">
                      <i :class="group.visible ? 'fas fa-eye' : 'fas fa-eye-slash'" />
                    </div>
                    <a-button
                      class="group-expansion-toggle"
                      size="small"
                      type="text"
                      :aria-label="'Expand or collapse ' + group.description"
                      :aria-expanded="isGroupExpanded(group.id)"
                      @click.stop="toggleExpanded(group)"
                    >
                      <i class="fas" :class="isGroupExpanded(group.id) ? 'fa-chevron-down' : 'fa-chevron-right'" />
                    </a-button>
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
    <LayerStyleEditor />
  </div>
</template>

<script setup>
import {ref, watch} from 'vue';
import { VueDraggableNext as draggable } from 'vue-draggable-next';
import { useVisibleLayers, VisibleLayerType } from '@/composables/visibleLayers';
const {esdlProject, getAllVariants, setActiveVariant} = useESDLProjects();
import LayerStyleEditor from "@/apps/LayerStyleEditor.vue";
import LayerOpacityPopover from "@/components/popover/LayerOpacityPopover.vue";
import {useESDLProjects} from "@/composables/esdlProjects";
import BaseLayerTree from "@/components/sidepane/BaseLayerTree.vue";
import {theme} from 'ant-design-vue';

const {token} = theme.useToken();

const {
  getVisibleLayerGroups,
  toggleGroupVisibility,
  hideVisibleLayer,
  showVisibleLayer,
  hideAllVisibleLayers,
  showAllVisibleLayers,
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
  "plan_layer": "Plans",
  "pot_layer": "Potentials",
  "sim_layer": "Simulation results",
};

const selectedLayerId = ref('');
const layerGroups = ref([]);
const allLayersHidden = ref(false);

watch(() => getVisibleLayerGroups(), (newGroups) => {
  layerGroups.value = [...newGroups];
}, { immediate: true, deep: true });

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
 */
const onEndDrag = () => {
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
 * Toggles the visibility of all layers.
 */
const toggleAllLayers = () => {
  if (allLayersHidden.value) {
    showAllVisibleLayers();
  } else {
    hideAllVisibleLayers();
  }
  allLayersHidden.value = !allLayersHidden.value;
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
  return group.id === esdlProject.value?.active_es_id;
};

const getGroupVariant = (group) => {
  return getAllVariants().find(variant => variant.es_id === group.id);
};

/**
 * Activates the variant, or toggles its layer group if already active.
 */
const clickGroup = (group) => {
  const variant = getGroupVariant(group);
  if (variant && !isActiveGroup(group)) {
    setActiveVariant(variant.id);
    return;
  }
  toggleExpanded(group);
};
</script>

<style scoped lang="scss">
.base-layer-tree {
  :deep(.ant-tree-treenode) {
    padding-bottom: 0;
  }
  :deep(.ant-tree-switcher) {
    line-height: inherit;

    .ant-tree-switcher-line-icon {
      display: none;
    }
  }
  :deep(.ant-tree-checkbox) {
    align-self: flex-start;
    margin-inline-end: auto;
  }
}

.layer-groups {
  margin-top: 10px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: v-bind('token.colorFillTertiary');
  padding: 8px;
  border-bottom: 1px solid v-bind('token.colorBorderSecondary');
  font-weight: bold;
  cursor: move;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: v-bind('token.colorFillSecondary');
  }
}

.active-group {
  background-color: v-bind('token.controlItemBgActive');

  &:hover {
    background-color: v-bind('token.controlItemBgActive');
  }
}

.variant-group {
  cursor: pointer;
}

.group-name {
  flex: 1;
  height: auto;
  padding: 0;
  color: inherit;
  font-weight: inherit;
  text-align: left;
  white-space: normal;

  &:not(:disabled):hover, &:not(:disabled):active {
    color: inherit;
    background: none;
  }
}

.group-expansion-toggle {
  width: 20px;
  height: 20px;
  padding: 0;
  color: inherit;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 5px 5px 20px;
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

.hide-all-btn {
  background-color: #f4f4f4;
  border: 1px solid #ccc;
  cursor: pointer;
  padding: 5px 10px;
  display: flex;
  align-items: center;
  margin-left: 10px;

  &:hover {
    background-color: #ddd;
  }
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 5px 5px 10px;
  border-bottom: 1px solid #ddd;
  background-color: #fff;
  cursor: move;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #f4f4f4;
  }
}
</style>
