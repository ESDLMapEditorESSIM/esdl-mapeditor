<template>
  <h1>Admin</h1>

  <vue-js-tree
    :tree-id="treeId"
    :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
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
  {
    id: 'other',
    text: 'Other',
  },
];

const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'select_node.jstree',
  handler: function (event, data) {
    console.log("Selected!")
    console.log(event)
    console.log(data)
    selectedMenu.value = data.node.id
  }
}];

const treeTypeSpecs = [];

</script>

<style>
</style>
