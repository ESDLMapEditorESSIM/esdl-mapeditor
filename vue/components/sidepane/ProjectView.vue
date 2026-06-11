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
  <div id="project-view">
    <BaseLayerTree />
    <hr>
    <ProjectTree />
  </div>
</template>

<script setup>
import BaseLayerTree from "@/components/sidepane/BaseLayerTree.vue";
import ProjectTree from "@/components/sidepane/ProjectTree.vue";
</script>


<style lang="scss">

#project-view  {
  .ant-tree-treenode {
    padding-bottom: 0;
  }
  .ant-tree-switcher {
    line-height: inherit;

    .ant-tree-switcher-line-icon {
      display: none;
    }
  }
  .ant-tree-checkbox {
    align-self: flex-start;
    margin-inline-end: auto;
  }
}


</style>
