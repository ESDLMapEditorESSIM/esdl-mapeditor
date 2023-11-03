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
  <div :id="props.treeId" />
</template>

<script setup="props">
import {defineProps, onMounted, watchEffect} from "vue";

const props = defineProps({
  treeId: String,
  data: Object,
  plugins: Array,
  treeTypeSpecs: Array,
  eventHandlersByName: Object,
  checkCallBack: {
    type: Function,
    required: false,
    default: () => true,
  },
  dndIsDraggable: {
    type: Function,
    required: false,
    default: () => true,
  },
});

const $ = window.$;

const getTreeElement = () => $('#' + props.treeId);
const getTree = () => getTreeElement().jstree(true);

const types = {};
const contextMenusByType = {};

for (const treeTypeSpec of props.treeTypeSpecs) {
  types[treeTypeSpec.type] = {
    icon: treeTypeSpec.icon,
    max_depth: treeTypeSpec.max_depth,
  }

  if (treeTypeSpec.contextMenus) {
    contextMenusByType[treeTypeSpec.type] = treeTypeSpec.contextMenus;
  }
}

onMounted(() => {
  const treeElement = getTreeElement();
  for (const eventHandlerByName of props.eventHandlersByName) {
    const eventName = eventHandlerByName.eventName;
    const handler = eventHandlerByName.handler;
    // Add tree element as extra parameter.
    treeElement.on(eventName, (e, data) => handler(e, data, getTreeElement()));
  }
  treeElement.jstree({
    core: {
      data: props.data,
      check_callback: (operation, node, node_parent, node_position, more) =>
          props.checkCallBack(operation, node, node_parent, node_position, more),
      animation: 200,
      multiple: false
    },
    plugins: props.plugins,
    checkbox: {
      "three_state": false,
      "whole_node": false,
      // uncouple selecting and checking
      "tie_selection": false
    },
    contextmenu: {
      items: (node) => {
        const nodeContextMenu = contextMenusByType[node.type];
        if (nodeContextMenu) {
          return nodeContextMenu(node, getTree());
        }
        return {};
      },
      select_node: false,
    },
    dnd: {
      inside_pos: "first",
      is_draggable: (node) => props.dndIsDraggable(node),
    },
    types: types,
  });
});

watchEffect(() => {
  // Refresh tree with new data.
  if (props.data && getTree() && getTree().refresh) {
    getTree().settings.core.data = props.data;
    getTree().refresh(false, true);
  }
});

</script>

<style>
.no_checkbox > i.jstree-checkbox {
  display: none;
}
</style>