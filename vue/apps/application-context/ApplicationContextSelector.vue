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
    id="application_context"
    v-model="selected_context"
    @change="handleChange"
  >
    <option
      v-for="applicationContext in applicationContexts"
      :key="applicationContext.application_id"
      :value="applicationContext.application_id"
    >
      {{ applicationContext.name }}
    </option>
  </select>
</template>

<script setup>
import {nextTick, onMounted, ref, watch} from 'vue';
import { useApplicationContext } from '../../composables/applicationContext';

const { activateApplicationContext, activeApplicationContext, clearApplicationContext, fetchApplicationContexts } = useApplicationContext();

const $ = window.$;
const selected_context = ref(activeApplicationContext.value.application_id);
const applicationContexts = ref([]);

onMounted(async () => {
  applicationContexts.value = await fetchApplicationContexts();
  selected_context.value = activeApplicationContext.value.application_id;

  if (applicationContexts.value.length > 0) {
    // Initialize the selectmenu
    $("#application_context").selectmenu({
      width: 150,
      change: function (event, ui) {
        handleChange({ target: { value: ui.item.value } });
      }
    });
  } else {
    // Hide the select menu if no application contexts are available
    $("#application_context").hide();
  }
});

// Watch for changes in `selected_context` and update the selectmenu value accordingly
watch(selected_context, async (newValue) => {
  if (newValue) {
    await nextTick();
    $("#application_context").val(newValue).selectmenu("refresh");
  }
});

const handleChange = (e) => {
  // Find the selected application context.
  const selectedApplicationContext = applicationContexts.value.find(context => context.application_id === e.target.value);
  if (selectedApplicationContext) {
    activateApplicationContext(selectedApplicationContext);
  } else {
    clearApplicationContext();
  }
};
</script>
