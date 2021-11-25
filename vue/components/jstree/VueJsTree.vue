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
import {defineProps, onMounted} from "vue";

const props = defineProps({
  treeId: String,
  data: Object,
  // Mapping from type to context menu.
  contextmenusByType: Object,
  typeSettings: Object,
})

const $ = window.$;

const getTree = () => $('#' + props.treeId).jstree(true);

onMounted(() => {
  $('#' + props.treeId).jstree({
    core: {
      data: props.data,
      check_callback: true,
    },
    plugins: ["contextmenu", "types"],
    contextmenu: {
      items: (node) => {
        const contextmenusByType = props.contextmenusByType || {};
        const nodeContextMenu = contextmenusByType[node.type]
        if (nodeContextMenu) {
          return nodeContextMenu(node, getTree());
        }
        return {};
      },
      select_node: false,
    },
    types: props.typeSettings,
  });
});
</script>