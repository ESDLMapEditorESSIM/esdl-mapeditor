<template>
  <div />
</template>

<script setup>
import {notification, Button} from 'ant-design-vue';
import {h} from 'vue';

import {onMounted} from "vue";

onMounted(() => {
  console.log("Registering socket io bindings for ToastNotifications");
  setTimeout(function () {
    window.socket.on('toast_notification', showNotification);
    // TODO send 'toast_notification_service_ready' to backend after which backed up messages can be received
  }, 2000);
});

const showNotification = (data) => {
  // TODO implement button with a way to link activate Vue workflow step? Or other view?
  // const key = `open${Date.now()}`;
  notification[data["type"]]({
    message: data["title"],
    description: data["description"],
    placement: data["placement"],
    duration: data["close_after_seconds"],
    // btn: () =>
    //     h(
    //         Button,
    //         {
    //           type: 'primary',
    //           size: 'small',
    //           onClick: () => notification.close(key),
    //         },
    //         {default: () => 'Confirm'},
    //     ),
    // key,
    onClick: () => {
      console.log('Notification Clicked!');
    },
  });
};

</script>

<style>
</style>
