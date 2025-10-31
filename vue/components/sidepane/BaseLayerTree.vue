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
  <a-tree
    v-model:expanded-keys="expandedKeys"
    :show-icon="true"
    :tree-data="treeData"
    checkable
    :check-strictly="true"
    :checked-keys="checkedBaseLayers"
    @check="onCheck"
  >
    <template #icon="{ iconClass }">
      <span v-if="iconClass" :class="iconClass" />
    </template>
  </a-tree>
</template>

<script setup>
import {ref, computed, watch} from 'vue';
import { useBaseLayers } from '@/composables/baseLayers';

// Composables
const { baseLayerDefinitions, showBaseLayer, hideBaseLayer, getBaseLayerByLabel } = useBaseLayers();

// State for Ant Tree
const checkedBaseLayers = ref([baseLayerDefinitions[0].label]);
const expandedKeys = ref([]);

// Convert project data to Ant Tree format
const treeData = computed(() => {
  const baseLayersNode = {
    title: 'Base layers',
    key: 'group_base_layers',
    selectable: false,
    iconClass: 'fas fa-object-group',
    checkable: false,
    children: baseLayerDefinitions.map(bl => ({
      title: bl.label,
      key: bl.label,
      isLeaf: true,
      iconClass: 'fas fa-layer-group',
      selectable: false,
      dataType: 'base_layer',
      children: []
    })),
  };

  return [
    baseLayersNode,
  ];
});

let expandedInitialized = false;
watch(treeData, (newData) => {
  // Expand the top-level node (Base layers) after data initialization.
  if (!expandedInitialized && newData.length) {
    expandedKeys.value = newData.map((node) => node.key);
    expandedInitialized = true;
  }
}, { immediate: true });


async function onCheck(_, info) {
  const node = info.node;
  const isChecked = info.checked;
  const ctrlPressed = info.nativeEvent?.ctrlKey;
  console.debug('BASE LAYER TREE: onCheck', isChecked, info);
  const layer = getBaseLayerByLabel(node.key);
  if (isChecked) {
    // Disable other base layers if ctrl is not pressed
    if (!ctrlPressed) {
      for (const blKey of checkedBaseLayers.value) {
        const blLayer = getBaseLayerByLabel(blKey);
        hideBaseLayer(blLayer);
      }
      checkedBaseLayers.value = [];
    }
    checkedBaseLayers.value.push(node.key);
    showBaseLayer(layer);
  } else {
    hideBaseLayer(layer);
    checkedBaseLayers.value = checkedBaseLayers.value.filter(key => key !== node.key);
  }
}
</script>
