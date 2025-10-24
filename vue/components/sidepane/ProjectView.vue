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
    v-model:selected-keys="selectedKeys"
    :show-icon="true"
    :tree-data="treeData"
    checkable
    :check-strictly="true"
    :checked-keys="checkedKeys"
    @check="onCheck"
    @select="onSelect"
    @right-click="onRightClick"
  >
    <template #icon="{ iconClass }">
      <span v-if="iconClass" :class="iconClass" />
    </template>
  </a-tree>

  <a-dropdown
    v-if="contextMenu.open"
    :open="true"
  >
    <span
      :style="{
        position: 'fixed',
        left: `${contextMenu.x}px`,
        top: `${contextMenu.y}px`,
        zindex: 2000,
      }"
    />
    <template #overlay>
      <a-menu
        :disabled="contextMenuItems.length === 0"
        @click="onContextMenuClick"
      >
        <template v-for="item in contextMenuItems" :key="item.key">
          <a-menu-item>
            <i :class="item.icon" style="margin-right: 6px" />
            {{ item.label }}
          </a-menu-item>
        </template>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue';
import { useESDLProjects } from '@/composables/esdlProjects';
import { useBaseLayers } from '@/composables/baseLayers';
import { useEsdlLayers } from '@/composables/esdlLayers';
import {useSocketIO} from "@/composables/socketio";

// Composables
const { esdlProject, getESDLProject, activeVariant, setActiveVariant } = useESDLProjects();
const { baseLayerDefinitions, showBaseLayer, hideBaseLayer, getBaseLayerByLabel } = useBaseLayers();
const { enableEsdl, disableEsdl, enabledEsdlIdList } = useEsdlLayers();
const { socket } = useSocketIO();

// State for Ant Tree
const selectedKeys = computed(() => activeVariant().id ? [activeVariant().id] : []);
const checkedBaseLayers = ref([baseLayerDefinitions[0].label]);
const expandedKeys = ref([]);

onMounted(() => {
  getESDLProject();
});

const contextMenu = ref({
  open: false,
  x: 0,
  y: 0,
  node: null,
});

const contextMenuItems = computed(() => {
  const dataType = contextMenu.value.node?.dataType;

  if (dataType === 'variant') {
    return [
      { key: 'create', icon: 'fas fa-plus', label: 'Create new variant' },
      { key: 'rename', icon: 'fas fa-edit', label: 'Rename variant' },
      { key: 'delete', icon: 'fas fa-trash', label: 'Remove variant' },
      { key: 'flatten', icon: 'fas fa-layer-group', label: 'Flatten variant' },
    ];
  } else if (dataType === 'project') {
    return [{ key: 'create', icon: 'fas fa-plus', label: 'Create new variant' }];
  }

  return []; // no options for other types
});

// Convert project data to Ant Tree format
const treeData = computed(() => {
  if (!esdlProject.value) return [];

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

  function variantNode(variant) {
    return {
      title: variant.name,
      key: variant.id,
      variant: variant,
      esId: variant.es_id,
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
      key: `change_${Math.random().toString(36).slice(2, 11)}`,
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
    dataType: 'project',
    checkable: false,
    selectable: false,
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
    console.log("select_node: set active variant", node);
    if (!data.variant.active) {
      setActiveVariant(data.variant.id);
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
            }
          }
          // If the currently active variant is not the one we just enabled, make it active.
          if (activeVariant().es_id !== data.esId) {
            setActiveVariant(data.variant.id);
          }
        }
      } else {
        // We have no way to just get the energy system without activating it right now. I don't think it's a problem.
        console.debug("check_node: set active variant");
        setActiveVariant(data.variant.id)
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
  if (info.node.dataType !== 'variant' && info.node.dataType !== 'project') {
    return;
  }
  console.debug("SIDE PANE: onRightClick", info);

  contextMenu.value = {
    open: true,
    x: info.event.clientX,
    y: info.event.clientY,
    node: info.node,
  };

  document.addEventListener('click', hidecontextMenuOnce);
}

function hidecontextMenuOnce() {
  contextMenu.value.open = false;
  document.removeEventListener('click', hidecontextMenuOnce);
}

function onContextMenuClick({ item, key, keyPath }) {
  // TODO: This is in progress.
  const node = contextMenu.value.node?.dataRef;
  console.debug('SIDE PANE: onContextMenuClick', item, key, keyPath, node);
  if (!node || (node.dataType !== 'variant' && node.dataType !== 'project')) {
    return;
  }

  if (key === 'create') {
    // TODO: Check if it is a project or a variant.
    createNewVariant(node.variant);
  } else if (key === 'rename') {
    renameVariant(node.variant);
  } else if (key === 'delete') {
    removeVariant(node.variant);
  } else if (key === 'flatten') {
    flattenVariant(node.variant);
  }

  contextMenu.value.open = false;
}

function createNewVariant(parentVariant) {
  console.debug(`Create new variant under ${parentVariant.id}`);
  // TODO
  // socket.value.emit("create_variant_collection");
  // const msg = {parent_variant_id: node.original.id};
  // socket.value.emit("create_child_variant", msg);
}

function renameVariant(variant) {
  const newName = window.prompt('New name:', variant.title);
  if (newName && newName !== variant.title) {
    // emit via socket, or call composable to update backend
    console.debug(`Rename variant ${variant.id} to ${newName}`);
    socket.value.emit("rename_variant", {id: variant.id, name: newName});
  }
}

function removeVariant(variant) {
  if (window.confirm(`Remove variant "${variant.title}"?`)) {
    console.debug(`Remove variant ${variant.variantId}`);
    const loaderScope = "delete_variant"
    window.show_loader(loaderScope)
    disableEsdl(variant.es_id);
    const msg = {id: variant.id};
    socket.value.emit.emit("delete_variant", msg, () => {
      window.hide_loader(loaderScope)
    })
  }
}

function flattenVariant(variant) {
  console.debug(`Flatten variant ${variant.id}`);
  // TODO
  const msg = {id: variant.id};
  socket.value.emit("flatten_variant", msg);
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
