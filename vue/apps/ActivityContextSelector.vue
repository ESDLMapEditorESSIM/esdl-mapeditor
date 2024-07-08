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
import {onMounted, ref, watch} from 'vue';
import {useActivityContext} from '@/composables/activityContext';

const {activeActivityContext, activateActivityContext, clearActivityContext, fetchActivityContexts} = useActivityContext();

const selected_context = ref("");
const activityContexts = ref([]);
const $ = window.$;

const initializeSelectmenu = () => {
  $("#activity_context").selectmenu({
    width: 350,
    change: function (event, ui) {
      handleChange({ target: { value: ui.item.value } });
    }
  });
};

const updateSelectmenuValue = async (value) => {
  $("#activity_context").val(value).selectmenu("refresh");
};

onMounted(async () => {
  activityContexts.value = await fetchActivityContexts();
  if (activityContexts.value.length > 0) {
    initializeSelectmenu();
  } else {
    $("#activity_context").hide();
  }
});

watch(() => activeActivityContext.value, (newValue) => {
  updateSelectmenuValue(newValue?.activity_id || "");
});

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
