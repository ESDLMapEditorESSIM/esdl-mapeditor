<template>
  <div />
</template>

<script setup>
import { notification } from 'ant-design-vue';
import {onMounted} from "vue";

onMounted(() => {
  notification.open({
        message: 'Notification Title',
        description:
          'This is the content of the notification. This is the content of the notification. This is the content of the notification.',
        onClick: () => {
          console.log('Notification Clicked!');
        },
     });
});

</script>

<style>
.leaflet-result-visualizations-toolbar {
  padding: 5px;
  z-index: 2000;
  background: white;

  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  border-radius: 5px;
}

.leaflet-result-visualizations-toolbar p {
  margin-bottom: 0;
}

</style>
