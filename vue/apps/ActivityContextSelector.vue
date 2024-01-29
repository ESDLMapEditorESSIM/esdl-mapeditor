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
  <select
    id="activity_context"
    v-model="selected_context"
    @change="handleChange"
  >
    <option value="" disabled selected>I want to...</option>
    <option v-for="(context, id) in ActivityContexts" :key="id" :value="id">{{ context.name }}</option>
    <div v-for="(context, id) in ActivityContexts" :key="id">
      {{ id }} - {{ context }}
    </div>
  </select>
</template>

<script setup>
import { ref } from 'vue';
import { ActivityContexts } from '../composables/activityContext.js';
import { useWmsLayers } from '../composables/wmsLayers.js';

const { clearWmsLayers, showWmsLayer } = useWmsLayers();

const selected_context = ref("");

// onMounted( async () => {
//   const $ = window.$;
//   $("#activity_context").selectmenu({ width:350 });
// })

const handleChange = (e) => {
  clearWmsLayers()
  for (const layer of ActivityContexts[selected_context.value].wms_layers) {
    showWmsLayer(layer)
  }
}
</script>
