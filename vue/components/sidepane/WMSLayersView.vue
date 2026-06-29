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
  <div id="wms_layers_view">
    <a-tree
      v-if="treeData != null"
      v-model:expanded-keys="expandedKeys"
      :show-icon="true"
      :show-line="true"
      :tree-data="treeData"
      checkable
      :check-strictly="true"
      :checked-keys="checkedKeys"
      @check="onCheck"
      @expand="onExpand"
      @right-click="onRightClick"
    >
      <template #icon="{ iconClass }">
        <span v-if="iconClass" :class="iconClass" />
      </template>

      <template #switcherIcon="{ switcherCls }"><caret-down-filled :class="switcherCls" /></template>
      <template #title="{ title }">
        <a-dropdown :trigger="['contextmenu']" overlay-class-name="wms-layer-context-menu">
          <span>{{ title }}</span>
          <template #overlay>
            <a-menu
              :disabled="contextMenuItems.length === 0"
              @click="onContextMenuClick"
            >
              <template v-for="item in contextMenuItems" :key="item.key">
                <a-menu-item class="menu-item-with-icon" :disabled="item.disabled">
                  <i :class="item.icon" />
                  {{ item.label }}
                </a-menu-item>
              </template>
            </a-menu>
          </template>
        </a-dropdown>
      </template>
    </a-tree>
    <div v-else>
      <p class="text-only">No WMS layers visible.</p>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, watch} from 'vue';
import {CaretDownFilled} from '@ant-design/icons-vue';
import {useWmsLayers, showLayer, hideLayer} from "@/composables/wmsLayers";
import {useVisibleLayers} from "@/composables/visibleLayers";
import {notification} from 'ant-design-vue';
import {useSocketIO} from "@/composables/socketio";

const {socket} = useSocketIO();
const {layerExists} = useVisibleLayers(window.map, socket);
const {
  getWmsLayerList,
  removeWmsLayer,
  addWmsLayerGroup,
  renameWmsLayerGroup,
  removeWmsLayerGroup,
  setWmsLayerGroupOpened,
  setVisibilityWmsLayerGroup,
} = useWmsLayers();

const expandedKeys = ref([]);
const contextMenu = ref({node: null});

const MaxLayerOpenCount = 10;

const treeData = computed(() => {
  if (getWmsLayerList()) {
    let wmsGroupsTreeData = [];
    for (const [key, rootGroup] of Object.entries(getRootGroupsWithChildren())) {
      addTreeItem(wmsGroupsTreeData, rootGroup, key, "wms_layer_folder", rootGroup.children, null);
    }

    return wmsGroupsTreeData.length ? wmsGroupsTreeData : null;
  } else {
    return null;
  }
});

const checkedKeys = computed(() => {
  const checked = [];

  const layerList = getWmsLayerList();
  if (!layerList) {
    return checked;
  }

  for (const layerId of Object.keys(layerList.layers)) {
    if (layerExists(layerId)) {
      checked.push(layerId);
    }
  }

  for (const groupId of Object.keys(layerList.layer_groups)) {
    const layerIds = getLayerIdsForGroup(groupId);
    if (layerIds.length && layerIds.every((layerId) => layerExists(layerId))) {
      checked.push(groupId);
    }
  }

  return checked;
});

watch(treeData, (newData) => {
  if (newData && !expandedKeys.value.length) {
    expandedKeys.value = getInitiallyExpandedKeys(newData);
  }
}, {immediate: true});

const contextMenuItems = computed(() => {
  const node = contextMenu.value.node?.dataRef;
  if (!node) {
    return [];
  }

  if (node.dataType === 'wms_layer_folder') {
    const readonly = node.readonly;
    const isRoot = node.isRoot;
    return [
      {key: 'add_layer', icon: 'fas fa-plus', label: 'Add WMS/WFS layer', disabled: readonly},
      {key: 'add_folder', icon: 'fas fa-plus', label: 'Add folder', disabled: readonly},
      {key: 'rename_folder', icon: 'far fa-edit', label: 'Rename folder', disabled: readonly || isRoot},
      {key: 'delete_folder', icon: 'fa fa-trash-o', label: 'Delete folder', disabled: readonly || isRoot},
    ];
  } else if (node.dataType === 'service_layer_tree') {
    return [
      {key: 'edit_layer', icon: 'far fa-edit', label: 'Edit layer', disabled: node.readonly},
      {key: 'delete_layer', icon: 'fa fa-trash-o', label: 'Delete layer', disabled: node.readonly},
    ];
  }

  return [];
});

function showAddLayerDialog(objectId) {
  window.add_edit_web_service_layer(objectId);
}

function getRootGroupsWithChildren() {
  const rootGroups = [];
  for (const [key, layerGroup] of Object.entries(getWmsLayerList().layer_groups)) {
    if (layerGroup.is_root) {
      rootGroups[key] = {...layerGroup};
      rootGroups[key]['children'] = getChildrenOfGroup(layerGroup, key);
    }
  }
  return rootGroups;
}

function getChildrenOfGroup(layerGroup, parentGroupId) {
  const layers = [];
  if (typeof layerGroup.child_ids !== 'undefined' && layerGroup.child_ids.length > 0) {
    for (const childId of layerGroup.child_ids) {
      let child = getWmsLayerList().layer_groups[childId];
      let type = "service_layer_tree";
      let children = [];
      if (child !== undefined && child !== null) {
        type = "wms_layer_folder";
        children = getChildrenOfGroup(child, childId);
      } else {
        child = getWmsLayerList().layers[childId];
      }

      if (child !== undefined && child !== null) {
        addTreeItem(layers, child, childId, type, children, parentGroupId);
      }
    }
  }
  return layers;
}

function addTreeItem(items, item, itemId, type, children, parentId) {
  items.push({
    title: item.description,
    key: itemId,
    setting_type: item.setting_type,
    project_name: item.project_name,
    parentId: parentId,
    readonly: item.readonly,
    dataType: type,
    iconClass: type === "service_layer_tree" ? 'fas fa-map' : 'fas fa-layer-group',
    checkable: true,
    selectable: false,
    isRoot: item.is_root,
    opened: item.opened,
    class: item.active ? 'bold' : '',
    children: children,
  });
}

function getInitiallyExpandedKeys(nodes) {
  const keys = [];
  for (const node of nodes) {
    if (node.isRoot || node.opened) {
      keys.push(node.key);
    }
    if (node.children?.length) {
      for (const childKey of getInitiallyExpandedKeys(node.children)) {
        keys.push(childKey);
      }
    }
  }
  return keys;
}

function onRightClick(info) {
  info.event.preventDefault();
  if (!['wms_layer_folder', 'service_layer_tree'].includes(info.node.dataType)) {
    return;
  }
  contextMenu.value = {node: info.node};
}

function onContextMenuClick({key}) {
  const node = contextMenu.value.node?.dataRef;
  if (!node) {
    return;
  }

  if (key === 'add_layer') {
    showAddLayerDialog("__" + node.key);
  } else if (key === 'add_folder') {
    addFolder(node);
  } else if (key === 'rename_folder') {
    renameFolder(node);
  } else if (key === 'delete_folder') {
    removeWmsLayerGroup(node.key, node.parentId);
  } else if (key === 'edit_layer') {
    showAddLayerDialog(node.key);
  } else if (key === 'delete_layer') {
    removeWmsLayer(node.key, node.parentId);
  }

  contextMenu.value = {node: null};
}

function addFolder(node) {
  let projectName;
  if (Object.hasOwn(node, 'project_name')) {
    projectName = node.project_name;
  } else {
    projectName = node.setting_type;
  }
  addWmsLayerGroup(node.key, node.setting_type, projectName);
}

function renameFolder(node) {
  const newName = window.prompt('New folder name:', node.title);
  if (newName && newName !== node.title) {
    renameWmsLayerGroup(node.key, newName);
  }
}

function onExpand(keys, info) {
  expandedKeys.value = keys;
  const node = info.node.dataRef;
  if (node.dataType === 'wms_layer_folder') {
    setWmsLayerGroupOpened(node.key, info.expanded);
  }
}

function onCheck(_, info) {
  const node = info.node.dataRef;
  const isChecked = info.checked;

  if (node.dataType === 'service_layer_tree') {
    if (isChecked) {
      showLayer(node.key);
    } else {
      hideLayer(node.key);
    }
  } else if (node.dataType === 'wms_layer_folder') {
    setGroupVisibility(node.key, isChecked);
  }
}

function setGroupVisibility(groupId, isChecked) {
  const layerIds = getLayerIdsForGroup(groupId);
  if (!isChecked) {
    setVisibilityWmsLayerGroup(groupId, false);
    return;
  }

  const visibleLayerIds = layerIds.filter((layerId) => layerExists(layerId));
  if (visibleLayerIds.length) {
    return;
  }

  if (layerIds.length <= MaxLayerOpenCount) {
    setVisibilityWmsLayerGroup(groupId, true);
  } else {
    showWarningMsg(layerIds.length, MaxLayerOpenCount);
  }
}

function getLayerIdsForGroup(groupId) {
  const layerList = getWmsLayerList();
  const layerIds = [];

  if (!layerList || !(groupId in layerList.layer_groups)) {
    return layerIds;
  }

  collectLayerIds(groupId, layerIds);
  return layerIds;
}

function collectLayerIds(itemId, layerIds) {
  const layerList = getWmsLayerList();
  if (itemId in layerList.layers) {
    layerIds.push(itemId);
  } else if (itemId in layerList.layer_groups) {
    for (const childId of layerList.layer_groups[itemId].child_ids) {
      collectLayerIds(childId, layerIds);
    }
  }
}

function showWarningMsg(hiddenLayerCount, maxLayerOpenCount) {
  notification['warning']({
    message: 'Warning',
    description: `You are trying to open ${hiddenLayerCount} map layers. Opening more than ${maxLayerOpenCount} layers at once is not allowed, `
      + "please open layers individually.",
    placement: 'bottomLeft',
  });
}
</script>

<style scoped lang="scss">
#wms_layers_view {
  overflow-y: auto;

  .text-only {
    padding-left: 8px;
  }

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

  :deep(.bold) {
    font-weight: bold;
  }
}

:global(.wms-layer-context-menu .menu-item-with-icon i) {
  width: 18px;
}
</style>
