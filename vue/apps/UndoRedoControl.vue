<template>
  <div v-show="showUndoRedoControl" class="my-control leaflet-undo-redo">
    <h1>
      UndoRedo
      <a-button type="primary" shape="circle" size="small" @click="loadTrackerstack">
        <template #icon><i class="fas fa-sync-alt" /></template>
      </a-button>
    </h1>
    <spinner v-if="isLoading" />
    <a-timeline v-else>
      <a-timeline-item v-for="entry in stack" :key="entry.label" :color="labelToColor(entry.label)">
        <strong>{{ entry.label }}</strong>
        <p v-for="command in entry.data" :key="command.name">
          {{ command.type }}
          <a-button type="link" shape="circle" size="small" @click="highlight(command)">
            <template #icon><i class="fas fa-search" /></template>
          </a-button>
          <!--          <button @click="highlight(command)">{{ command.name }}</button>-->
        </p>
      </a-timeline-item>
    </a-timeline>
  </div>
</template>

<script setup>
import {ref} from 'vue';
// eslint-disable-next-line no-unused-vars
import Spinner from "../components/Spinner";
import { useUndoRedo } from "../composables/undoRedo.js";

const { showUndoRedoControl } = useUndoRedo();

const stack = ref([]);
const isLoading = ref(false);

function loadTrackerstack() {
  isLoading.value = true;
  window.socket.emit('trackerstack', {}, (res) => {
    console.log("Have trackerstack")
    console.log(res);
    stack.value = res
    isLoading.value = false;
  });
}
function subscribeTrackerstack() {
  window.socket.on('trackerstack_update', function (res) {
    console.log("trackerstack update")
    console.log(res)
    stack.value = res
  });
}
setTimeout(loadTrackerstack, 2000);
setTimeout(subscribeTrackerstack, 2000);

function labelToColor(label) {
  // TODO: Labels as enums
  if (label === 'add_object') {
    return 'green';
  }
  return 'blue';
}

// eslint-disable-next-line no-unused-vars
function highlight(entry) {
  console.log(entry);
  const layer = window.get_layers(window.active_layer_id, 'esdl_layer');
  console.log(layer);
  const esdl_objects = layer.getLayers();
  console.log(esdl_objects);
  let found;
  for (const esdl_object of esdl_objects) {
    if (esdl_object.id === entry.id) {
      console.log("FOUND!")
      found = esdl_object;
      break;
    }
  }
  if (found === undefined) {
    alert("Not found");
    return;
  }
  console.log(found);
  window.select_assets.deselect_all_assets();
  window.select_assets.toggle_selected(found);
  console.log("Done highlighting");
}

</script>

<style lang="scss">
.leaflet-undo-redo {
  padding: 8px;
  z-index: 2000;
  width: 300px;
  height: 400px;
  background: white;
  overflow: auto;

  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  border-radius: 5px;

  .ant-timeline-item {
    padding: 0;
    .ant-timeline-item-content p {
      margin-bottom: 0;
    }
  }
}
</style>
