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
  
<!-- 
  
This template uses a few tricks to use one .vue file for 2 menu items: 

In index.js add the following

mountEl = document.querySelector("#vue_redo_menu");
createApp(UndoRedoMenu, {...mountEl.dataset}).mount('#vue_redo_menu');

And in the HTML add the following:
<li id="vue_undo_menu" data-type="undo"/>

The data-type attribute translates to the 'type'-prop of this vue component.
The mountEl.dataset is a list of all data- prefixed attributes on the element.

-->
<template>
  <a v-if="type === 'undo'" class="dropdown-item" href="#" @click="undo" :class="{ 'disabled': !canUndo }">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fa fa-undo fa-smaller" aria-hidden="true" /></div>
    Undo
  </a>
  <a v-if="type === 'redo'" class="dropdown-item" href="#" @click="redo" :class="{ 'disabled': !canRedo }">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fa fa-redo fa-smaller" aria-hidden="true" /></div>
    Redo
  </a>
</template>

<script setup>

import {defineProps } from "vue";
import { useUndoRedo } from "../../composables/undoRedo.js";
const { stack, stack_index, canUndo, canRedo, undo, redo } = useUndoRedo();
const props = defineProps({
  type: String  // String to define if we show undo or redo menu
})

</script>
<style scoped>
.disabled {
  color: lightgray;
}
</style>