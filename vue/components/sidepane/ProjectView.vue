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
    :selected-keys="[selectedKey]"
    :checked-keys="checkedKeys"
    @check="onCheck"
    @select="onSelect"
    @right-click="onRightClick"
  >
    <template #icon="{ iconClass }">
      <span v-if="iconClass" :class="iconClass" />
    </template>
  </a-tree>
</template>

<script setup>
import {ref, computed, onMounted, watch, nextTick} from 'vue';
import { useESDLProjects } from '@/composables/esdlProjects';
import { useSocketIO } from '@/composables/socketio';
import { useBaseLayers } from '@/composables/baseLayers';
import { useEsdlLayers } from '@/composables/esdlLayers';

// Composables
const { esdlProject, getESDLProject, activeVariant, setActiveVariant } = useESDLProjects();
const { baseLayerDefinitions, showBaseLayer, hideBaseLayer, getBaseLayerByLabel } = useBaseLayers();
const { enableEsdl, disableEsdl, enabledEsdlIdList } = useEsdlLayers();

// State for Ant Tree
const selectedKey = ref(null);
const checkedBaseLayers = ref([baseLayerDefinitions[0].label]);
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
      iconClass: 'fas fa-layer-group',
      checkable: true,
      disableCheckbox: false,
      selectable: false,
      dataType: 'base_layer',
      children: []
    })),
    iconClass: 'fas fa-layer-group',
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
      iconClass: 'fas fa-bezier-curve',
      checkable: true,
      selectable: true,
      showIcon: true,
      class: variant.active ? 'is-active' : '',
      dataType: 'variant',
      variantId: variant.id,
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
      icon = 'far fa-object-group';
    } else if (change.type === 'Add') {
      icon = 'fas fa-plus';
    } else if (change.type === 'Set') {
      icon = 'fas fa-arrow-right';
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

  const projectNode = {
    title: esdlProject.value.name,
    key: esdlProject.value.id,
    children: esdlProject.value.variants.map(variantNode),
    iconClass: 'fas fa-project-diagram',
    selectable: false
  };

  return [
    baseLayersNode,
    projectNode,
  ];
});

let expandedInitialized = false;
watch(treeData, (newData) => {
  // Expand the top-level nodes (Base layers + Project) after data initialization.
  if (!expandedInitialized && newData.length) {
    expandedKeys.value = newData.map((node) => node.key);
    expandedInitialized = true;
  }
}, { immediate: true });

const checkedKeys = computed(() => {
  const variantKeys = treeData.value
    .flatMap(node => node.children || [])
    .filter(v => v.dataType === 'variant' && enabledEsdlIdList.value.includes(v.esId))
    .map(v => v.key);

  return [...variantKeys, ...checkedBaseLayers.value];
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
      setActiveVariant(node.key, data.esId);
      for (const enabledEsdlId of enabledEsdlIdList.value) {
        if (enabledEsdlId !== data.esId) {
          disableEsdl(enabledEsdlId);
        }
      }
      enableEsdl(data.esId)
    }
  }
}

async function onCheck(_, info) {
  const node = info.node;
  const isChecked = info.checked;
  // Data is the reference to the original data object that we create.
  const data = node.dataRef;
  const ctrlPressed = info.nativeEvent?.ctrlKey;
  console.debug('SIDE PANE: onCheck', isChecked, info);
  if (data.dataType === 'variant') {
    if (isChecked) {
      if (data.esId in window.esdl_list) {
        enableEsdl(data.esId);
        if (!ctrlPressed) {
          // Disable other variants.
          for (const enabledEsdlId of enabledEsdlIdList.value) {
            if (enabledEsdlId !== data.esId) {
              disableEsdl(enabledEsdlId);
              // TODO: This doesn't work, esId does not exist here.
              if (activeVariant.value.esId === enabledEsdlId) {
                console.debug("check_node: set active variant", data);
                setActiveVariant(data.variantId, data.esId);
              }
            }
          }
        }
      } else {
        // We have no way to just get the energy system without activating it right now. I don't think it's a problem.
        console.debug("check_node: set active variant");
        setActiveVariant(data.variantId, data.esId)
      }
    } else {
      disableEsdl(data.esId);
    }
  } else if (data.dataType === 'base_layer') {
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
