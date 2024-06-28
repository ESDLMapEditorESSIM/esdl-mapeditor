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
      v-for="applicationContext in applicationContexts" :key="applicationContext.application_id"
      :value="applicationContext.application_id"
    >
      {{ applicationContext.name }}
    </option>
  </select>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {useApplicationContext} from '../../composables/applicationContext';

const {activateApplicationContext, activeApplicationContext, clearApplicationContext, fetchApplicationContexts} = useApplicationContext();

const selected_context = ref(activeApplicationContext.value.application_id);
const applicationContexts = ref([]);

onMounted(async () => {
  applicationContexts.value = await fetchApplicationContexts()
  // TODO: Figure out how to maintain the selection.
  // const $ = window.$;
  // if (applicationContexts.value.length > 0) {
  //   $("#application_context").selectmenu({width: 150}).on('selectmenuchange', function() {
  //     handleChange({target: {value: $(this).val()}})
  //   })
  // } else {
  //   // We cannot easily do this in vue, because the above .selectmenu also hides the select. So that conflicts.
  //   $("#application_context").hide()
  // }
})

const handleChange = (e) => {
  // Find the selected application context.
  const selectedApplicationContext = applicationContexts.value.find(context => context.application_id === e.target.value);
  if (selectedApplicationContext) {
    activateApplicationContext(selectedApplicationContext);
  } else {
    clearApplicationContext();
  }
}
</script>
