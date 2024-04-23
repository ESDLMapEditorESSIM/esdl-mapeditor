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
  <div v-show="showUndoRedoControl" class="leaflet-undo-redo">
    <h1>
      Action history
      <a-button type="default" shape="circle" title="Refresh" size="small" @click="loadUndoRedoStack">
        <template #icon><i class="fas fa-sync-alt" /></template>
      </a-button>
      <a-button type="primary" shape="circle" title="Redo" size="small" @click="redo">
        <template #icon><i class="fas fa-redo" /></template>
      </a-button>
      <a-button type="primary" shape="circle" title="Undo" size="small" @click="undo">
        <template #icon><i class="fas fa-undo" /></template>
      </a-button>
    </h1>
    <div id="undo-redo-content">
      <spinner v-if="isLoading" />
      <a-timeline v-else>
        <a-timeline-item v-for="(entry, idx) in stack" :key="entry.label" :color="typeToColor(entry.type)" :class="{active: isActiveIndex(idx), undone: isUndone(idx)}">
          <strong>{{ entry.label }}</strong>
          <a-button v-show="!isActiveIndex(idx)" type="link" shape="circle" title="Undo/Redo to this point" size="small" @click="undoRedoUntil(idx)">
            <template #icon><i class="fas fa-arrow-left" /></template>
          </a-button>
          <a-button v-show="!isUndone(idx) && canHighlight(entry)" type="link" shape="circle" title="Highlight asset" size="small" @click="highlight(entry)">
            <template #icon><i class="fas fa-search" /></template>
          </a-button>
        </a-timeline-item>
      </a-timeline>
    </div>
  </div>
</template>

<script setup>
import {ref, onUpdated} from 'vue';
// eslint-disable-next-line no-unused-vars
import Spinner from "../components/Spinner";
import { useUndoRedo } from "../composables/undoRedo.js";
import {MessageNames, PubSubManager} from "../bridge";

// eslint-disable-next-line no-unused-vars
const { stack, stack_index, showUndoRedoControl, undo, redo, undoRedoUntil } = useUndoRedo();

//const stack = ref([]);
//const stack_index = ref(null);
const isLoading = ref(false);

/**
 * Loads the undo redo stack and subscribes to any updates.
 */
function loadUndoRedoStack() {
  if (!window.socket) {
    setTimeout(loadUndoRedoStack, 2000);
    return
  }
  isLoading.value = true;
  window.socket.emit('get_undo_redo_stack', {}, (res) => {
    console.log(res);
    stack.value = res.stack;
    stack_index.value = res.stack_index;
    isLoading.value = false;
    console.log('undo', stack, stack_index)
  });
}

function subscribeUndoRedoStack() {
  if (!window.socket) {
    setTimeout(subscribeUndoRedoStack, 2000);
    return
  }
  window.socket.on('update_undo_redo_stack', function (res) {
    stack.value = res.stack;
    stack_index.value = res.stack_index;
    scrollDown();
  });
}

// Load stack and subscribe.
loadUndoRedoStack();
subscribeUndoRedoStack();

PubSubManager.subscribe(MessageNames.NEW_ESDL, (name, message) => {
  loadUndoRedoStack();
})

// eslint-disable-next-line no-unused-vars
function typeToColor(type) {
  if (type.toLowerCase() === 'add') {
    return 'green';
  }
  if (type.toLowerCase() === 'remove') {
    return 'red';
  }
  return 'blue';
}

// eslint-disable-next-line no-unused-vars
function canHighlight(entry) {
  return entry.type.toLowerCase() !== 'remove';
}

// eslint-disable-next-line no-unused-vars
function highlight(entry) {
  const layer = window.get_layers(window.active_layer_id, 'esdl_layer');
  const esdl_objects = layer.getLayers();
  for (const command of entry.commands) {
    for (const esdl_object of esdl_objects) {
      if (esdl_object.id === command.id) {
        window.select_assets.deselect_all_assets();
        window.select_assets.toggle_selected(esdl_object);
        return;
      }
    }
  }
  alert("The selected asset could not be found in this ESDL.");
}

/**
 * Return whether or not the entry with the given index in the stack is active (matches the stack index).
 * @param idx
 */
// eslint-disable-next-line no-unused-vars
function isActiveIndex(idx) {
  return idx === stack_index.value;
  // return stack.value.length - 1 - idx === stack_index.value;
}

/**
 * Return whether or not the entry with the given index in the stack has been undone.
 * @param idx
 */
// eslint-disable-next-line no-unused-vars
function isUndone(idx) {
  return idx > stack_index.value;
}

onUpdated(() => {
  scrollDown();
})

function scrollDown() {
  const contentDiv = document.getElementById("undo-redo-content");
  contentDiv.scrollTop = contentDiv.scrollHeight;
}
</script>

<style lang="scss">
.leaflet-undo-redo {
  background: white;
  overflow: hidden;

  h1 {
    padding: 8px;
  }

  #undo-redo-content {
    height: 90%;
    overflow: scroll;
    padding: 5px 8px 8px 8px;
  }

  h1 button {
    float: right;
    margin-right: 5px;
  }

  .ant-timeline-item {
    padding-bottom: 0;
    .ant-timeline-item-content {
      padding-left: 5px;
      padding-bottom: 5px;
      p {
        margin-bottom: 0;
      }
    }
    &.active {
      .ant-timeline-item-content {
        background-color: #c0d0e5;
      }
    }
    &.undone {
      .ant-timeline-item-content {
        color: #aaa;
      }
    }
  }
}
</style>
