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
  <div id="live_model_interfaces">
    <div v-if="liveModelInterfaces.length">
      <a-card v-for="liveModelInterface in liveModelInterfaces" :key="liveModelInterface.lmi_id" :title="liveModelInterface.name" hoverable="true">
        <template #extra>
          <input v-model="liveModelInterface.enabled" :checked="liveModelInterface.enabled" type="checkbox" :disabled="!liveModelInterface.can_be_disabled" @change="updateLiveModelInterface(liveModelInterface.lmi_id, liveModelInterface.enabled)">
        </template>
        <p>{{ liveModelInterface.description }}</p>
      </a-card>
    </div>
    <p v-else>No live model interfaces available in this application context.</p>
  </div>
</template>

<script setup>
import {computed} from 'vue'

import {useApplicationContext} from '../../composables/applicationContext';
const {activeApplicationContext} = useApplicationContext();

const liveModelInterfaces = computed(() => activeApplicationContext.value.live_model_interfaces || []);

function updateLiveModelInterface(lmi_id, enabled) {
  fetch(`/context/applications/${activeApplicationContext.value.application_id}/lmis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({enabled: enabled, lmi_id: lmi_id})
  }).catch(error => console.error('Error:', error));
}
</script>