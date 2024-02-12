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
    <option value="" selected>I want to...</option>
    <option
      v-for="activityContext in activityContexts" :key="activityContext.activity_id"
      :value="activityContext.activity_id"
    >
      {{ activityContext.name }}
    </option>
  </select>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {useActivityContext} from '@/composables/activityContext';

const {activateActivityContext, clearActivityContext} = useActivityContext();

const selected_context = ref("");
const activityContexts = ref([]);

const get_activity_contexts = async () => {
  const response = await fetch('/context/activities')
  const data = await response.json()
  activityContexts.value = data
}
get_activity_contexts();

onMounted(async () => {
  const $ = window.$;
  $("#activity_context").selectmenu({width: 350}).on('selectmenuchange', function() {
    handleChange({target: {value: $(this).val()}});
  })
})

const handleChange = (e) => {
  // Find the selected activity context.
  const selectedActivityContext = activityContexts.value.find(context => context.activity_id === e.target.value);
  if (selectedActivityContext) {
    activateActivityContext(selectedActivityContext);
  } else {
    clearActivityContext();
  }
}
</script>
