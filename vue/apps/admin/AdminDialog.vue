<template>
  <h1>Admin</h1>

  <vue-js-tree
    :tree-id="treeId"
    :data="treeData" :events="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
  />
  <ActivityContextsAdmin v-if="selectedMenu==='activity_context'" />
</template>

<script setup>
import { ref } from 'vue';
import VueJsTree from "@/components/jstree/VueJsTree.vue";
import ActivityContextsAdmin from "@/apps/admin/ActivityContextsAdmin.vue";

const treeId = "layer_tree";
// const $ = window.$;
// const getTree = () => $('#' + treeId).jstree(true);

const selectedMenu = ref(null);

const treeData = [
  {
    id: 'activity_context',
    text: 'Activity Contexts',
  },
];

const eventHandlersByName = {
  'select_node.jstree': function (event, data) {
    selectedMenu.value = data.node.id
  }
}

const treeTypeSpecs = [];

</script>

<style>
</style>
