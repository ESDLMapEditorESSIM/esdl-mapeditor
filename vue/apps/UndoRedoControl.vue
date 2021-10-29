<template>
  <div v-show="showUndoRedoControl" class="my-control leaflet-undo-redo">
    <h1>
      UndoRedo
      <a-button type="dashed" shape="circle" size="small" @click="toggleShowUndoRedoControl">
        <template #icon><i class="fas fa-times" /></template>
      </a-button>
      <a-button type="default" shape="circle" size="small" @click="loadUndoRedo">
        <template #icon><i class="fas fa-sync-alt" /></template>
      </a-button>
      <a-button type="primary" shape="circle" size="small" @click="redo">
        <template #icon><i class="fas fa-redo" /></template>
      </a-button>
      <a-button type="primary" shape="circle" size="small" @click="undo">
        <template #icon><i class="fas fa-undo" /></template>
      </a-button>
    </h1>
    <div id="undo-redo-content">
      <spinner v-if="isLoading" />
      <a-timeline v-else>
        <a-timeline-item v-for="(entry, idx) in stack" :key="entry.label" :color="labelToColor(entry.label)" :class="{active: isActiveIndex(idx), undone: isUndone(idx)}">
          <strong>{{ entry.label }}</strong>
          <a-button v-show="!isActiveIndex(idx)" type="link" shape="circle" size="small">
            <template #icon><i class="fas fa-arrow-left" /></template>
          </a-button>
          <a-button v-show="canHighlight(entry)" type="link" shape="circle" size="small" @click="highlight(entry)">
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

// eslint-disable-next-line no-unused-vars
const { showUndoRedoControl, toggleShowUndoRedoControl, undo, redo } = useUndoRedo();

const stack = ref([]);
const stack_index = ref(null);
const isLoading = ref(false);

function loadUndoRedo() {
  isLoading.value = true;
  window.socket.emit('undoredo_stack', {}, (res) => {
    console.log("Received undo/redo stack")
    console.log(res);
    stack.value = res.stack;
    stack_index.value = res.stack_index;
    isLoading.value = false;
  });
}
function subscribeUndoRedo() {
  window.socket.on('undoredo_update', function (res) {
    console.log("Undo/redo update")
    console.log(res)
    stack.value = res
  });
}
setTimeout(loadUndoRedo, 2000);
setTimeout(subscribeUndoRedo, 2000);

// eslint-disable-next-line no-unused-vars
function labelToColor(label) {
  if (label.toLowerCase().startsWith('create')) {
    return 'green';
  }
  if (label.toLowerCase().startsWith('remove')) {
    return 'red';
  }
  return 'blue';
}

// eslint-disable-next-line no-unused-vars
function canHighlight(entry) {
  return !entry.label.toLowerCase().startsWith("remove");
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
  alert("Not found");
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
  console.log("Here");
  const contentDiv = document.getElementById("undo-redo-content");
  console.log(contentDiv);
  contentDiv.scrollTop = contentDiv.scrollHeight;
})

</script>

<style lang="scss">
.leaflet-undo-redo {
  z-index: 2000;
  width: 300px;
  height: 400px;
  background: white;
  overflow: hidden;

  h1 {
    padding: 8px;
  }

  #undo-redo-content {
    height: 90%;
    overflow: scroll;
    padding: 0 8px 8px 8px;
  }

  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  border-radius: 5px;

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
