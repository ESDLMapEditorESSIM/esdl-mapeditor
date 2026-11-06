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
  <div class="base-layers">
    <a-tree
      v-model:expanded-keys="expandedKeys"
      :virtual="false"
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
  </div>
</template>

<script setup>
import {ref, computed} from 'vue';
import { useBaseLayers } from '@/composables/baseLayers';
import {theme} from 'ant-design-vue';

// Composables
const { baseLayerDefinitions, showBaseLayer, hideBaseLayer, getBaseLayerByLabel } = useBaseLayers();
const {token} = theme.useToken();

// State for Ant Tree
const checkedBaseLayers = ref([baseLayerDefinitions[0].label]);
const expandedKeys = ref(['group_base_layers']);

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
    if (checkedBaseLayers.value.length === 0) {
      const defaultLayer = baseLayerDefinitions[0];
      showBaseLayer(defaultLayer);
      checkedBaseLayers.value = [defaultLayer.label];
    }
  }
}
</script>

<style scoped lang="scss">
.base-layers {
  :deep(.ant-tree-list-holder) {
    max-height: min(160px, 20vh);
    overflow-y: auto;
  }

  :deep(.ant-tree-list-holder-inner > .ant-tree-treenode:first-child) {
    position: sticky;
    top: 0;
    z-index: 1;
    align-self: stretch;
    background-color: v-bind('token.colorBgContainer');
  }
}
</style>
