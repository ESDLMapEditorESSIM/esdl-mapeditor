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
import {nextTick, onMounted, ref, watch} from 'vue';
import {useActivityContext} from '@/composables/activityContext';
import {useApplicationContext} from '@/composables/applicationContext';
import {MessageNames, PubSubManager} from "@/bridge";

const {activeActivityContext, activateActivityContext, clearActivityContext, fetchActivityContexts} = useActivityContext();
const {activeApplicationContext} = useApplicationContext();

const selected_context = ref("");
const activityContexts = ref([]);
const $ = window.$;
const isInitialized = ref(false);

const initializeSelectmenu = () => {
  $("#activity_context").selectmenu({
    width: 350,
    change: function (event, ui) {
      handleChange({ target: { value: ui.item.value } });
    }
  });
  isInitialized.value = true;
};

const updateSelectmenuValue = (value) => {
  $("#activity_context").val(value).selectmenu("refresh");
};

const refreshSelectmenu = async () => {
  await nextTick();
  const selectMenu = $("#activity_context");
  if (!isInitialized.value) {
    if (activityContexts.value.length > 0) {
      selectMenu.show();
      initializeSelectmenu();
    } else {
      selectMenu.hide();
    }
    return;
  }

  selectMenu.selectmenu("refresh");
  if (activityContexts.value.length > 0) {
    selectMenu.selectmenu("widget").show();
    updateSelectmenuValue(activeActivityContext.value?.activity_id || "");
  } else {
    selectMenu.selectmenu("widget").hide();
  }
};

const loadActivityContexts = async () => {
  const applicationId = activeApplicationContext.value.application_id;
  const contexts = await fetchActivityContexts(applicationId);
  if (activeApplicationContext.value.application_id !== applicationId) {
    return;
  }

  activityContexts.value = contexts;
  const activeActivityId = activeActivityContext.value?.activity_id;
  if (activeActivityId && !contexts.some(context => context.activity_id === activeActivityId)) {
    clearActivityContext();
  }
  await refreshSelectmenu();
};

onMounted(loadActivityContexts);

watch(() => activeApplicationContext.value.application_id, loadActivityContexts);

watch(() => activeActivityContext.value, (newValue) => {
  if (isInitialized.value) {
    updateSelectmenuValue(newValue?.activity_id || "");
  }
});

function handleChange(e) {
    // Find the selected activity context.
    const selectedActivityContext = activityContexts.value.find(context => context.activity_id === e.target.value);
    if (selectedActivityContext) {
        activateActivityContext(selectedActivityContext);
    } else {
        clearActivityContext();
    }
}

PubSubManager.subscribe(MessageNames.KEY_ESCAPE, () => {
  clearActivityContext();
});

</script>
