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
    :tree-data="treeData"
    checkable
    :check-strictly="true"
    :selected-keys="selectedKey"
    :checked-keys="checkedKeys"
    :expanded-keys="expandedKeys"
    @check="onCheck"
    @select="onSelect"
    @expanded-change="onExpand"
    @right-click="onRightClick"
  >
    <template #icon="{ record }">
      <span :class="record.icon" />
    </template>
  </a-tree>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue';
import { useESDLProjects } from '@/composables/esdlProjects';
import { useSocketIO } from '@/composables/socketio';
import { useBaseLayers } from '@/composables/baseLayers';
import { useEsdlLayers } from '@/composables/esdlLayers';

// Composables
const { esdlProject, getESDLProject, setActiveVariant } = useESDLProjects();
const { baseLayerDefinitions, showBaseLayer, hideBaseLayer, getBaseLayerByLabel } = useBaseLayers();
const { enableEsdl, disableEsdl, enabledEsdlIdList, hideEsdlLayerFromMap } = useEsdlLayers();

// State for Ant Tree
const selectedKey = ref(null);
const checkedKeys = ref([]);
const expandedKeys = ref([]);

onMounted(() => {
  getESDLProject();
});

// Convert project data to Ant Tree format
const treeData = computed(() => {
  if (!esdlProject.value) return [];

  const baseLayersNode = {
    title: 'Base layers',
    key: 'group_base_layers',
    selectable: false,
    children: baseLayerDefinitions.map(bl => ({
      title: bl.label,
      key: bl.label,
      isLeaf: true,
      icon: ['fas', 'fa-layer-group'],
      checkable: true,
      disableCheckbox: false,
      selectable: false,
      children: []
    })),
    icon: ['fas', 'fa-layer-group'],
    expanded: true,
  };

  function variantNode(variant) {
    return {
      title: variant.name,
      key: variant.id,
      variant: variant,
      children: [
        ...variant.children.map(variantNode),
        ...variant.changes.map(changeNode)
      ],
      icon: ['fas', 'bezier-curve'],
      checkable: true,
      selectable: true,
      showIcon: true,
      class: variant.active ? 'is-active' : '',
      dataType: 'variant',
      esId: variant.es_id
    };
  }

  function changeNode(change) {
    let text = change.type;
    if (change.feature) {
      text += ` on ${change.feature}`;
    }
    if (change.object_value_type) {
      text += `: ${change.object_value_type}`;
    }
    let icon;
    if (change.type === 'HighLevelChange') {
      icon = ['far', 'object-group'];
    } else if (change.type === 'Add') {
      icon = ['fas', 'fa-plus'];
    } else if (change.type === 'Set') {
      icon = ['fas', 'fa-arrow-right'];
    }

    return {
      title: text,
      key: `change_${Math.random().toString(36).substr(2, 9)}`,
      icon,
      isLeaf: !change.changes,
      selectable: false,
      checkable: false,
      children: change.changes ? change.changes.map(changeNode) : []
    };
  }

  return [
    baseLayersNode,
    {
      title: esdlProject.value.name,
      key: esdlProject.value.id,
      children: esdlProject.value.variants.map(variantNode),
      icon: ['fas', 'project-diagram'],
      selectable: false
    }
  ];
});

// Initialize checked and expanded keys when data updates
watch(treeData, (newData) => {
  // expand root nodes
  expandedKeys.value = newData.map(node => node.key);
  // check enabled ESDL variants
  checkedKeys.value = newData
      .flatMap(node => node.children || [])
      .filter(n => n.dataType === 'variant' && enabledEsdlIdList.value.includes(n.esId))
      .map(n => n.key);
}, { immediate: true });

watch(enabledEsdlIdList, (newData) => {
  checkedKeys.value = treeData.value;
      // .flatMap(node => node.children || [])
      // .filter(n => n.dataType === 'variant' && newData.includes(n.esId))
      // .map(n => n.key);
});

// Handlers
function onSelect(selected, info) {
  const node = info.node;
  const data = node.dataRef;
  console.debug('SIDE PANE: onSelect', selected, info);
  if (info.nativeEvent.button === 2) {
    // Right-click, do not change selection
    return;
  }
  if (data.dataType === 'variant') {
    selectedKey.value = node.key;
    if (!node.active) {
      checkedKeys.value = [node.key];
      setActiveVariant(node.key, data.esId);
    }
  }
}

function onCheck(checked, info) {
  const node = info.node;
  const data = node.dataRef;
  console.debug('SIDE PANE: onCheck', checked, info);
  if (data.dataType === 'variant') {
    if (checked) {
      enableEsdl(data.esId);
    } else {
      disableEsdl(data.esId);
    }
    checkedKeys.value = checked ? [node.key] : [];
  } else if (data.dataType === 'base_layer') {
    const layer = getBaseLayerByLabel(node.key);
    if (checked) {
      showBaseLayer(layer);
    } else {
      hideBaseLayer(layer);
    }
    checkedKeys.value = checked ? [node.key] : [];
  }
}

function onExpand(keys) {
  expandedKeys.value = keys;
}

function onRightClick(info) {
  info.event.preventDefault();
  const node = info.node;
  const data = node.dataRef;
  console.log('Right click on:', data);
  // Build your <a-dropdown> menu here, dispatching socket.emit actions
  // e.g. if data.dataType === 'variant', menu items for create, rename, delete, flatten
}
</script>

<style scoped lang="scss">
.is-active {
  font-weight: bold;
  background-color: #beebff;
}
#project_view {
  padding: 8px 5px;
  overflow: auto;
  height: 100%;
}
</style>
