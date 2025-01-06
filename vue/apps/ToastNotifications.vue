<template>
  <div />
</template>

<script setup>
import {notification, Button} from 'ant-design-vue';
import {download_binary_file_from_base64_str_with_type} from "@/utils/files";

import {h} from 'vue';

import {onMounted} from "vue";

onMounted(() => {
  console.log("Registering socket io bindings for ToastNotifications");

  window.addEventListener('load', () => {
    // run after everything is in-place
    window.socket.on('toast_notification', showNotification);
    // TODO send 'toast_notification_service_ready' to backend after which backed up messages can be received
  });
});

const showNotification = (data) => {
  // TODO implement button with a way to link activate Vue workflow step? Or other view?
  // const key = `open${Date.now()}`;
  if ("file_download" in data && data["file_download"] !== null) {
    download_binary_file_from_base64_str_with_type(
        data.file_download.content_b64string,
        data.file_download.file_name,
        data.file_download.file_type
    );
  }
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
