<template>
  <div />
</template>

<script setup>
import {onMounted, h} from "vue";
import {notification, Button} from 'ant-design-vue';
import {download_binary_file_from_base64_str_with_type} from "@/utils/files";
import {FileDownload} from "@/composables/toastNotifications";

onMounted(() => {
  console.log("Registering socket io bindings for ToastNotifications");
  window.addEventListener('load', () => {
    // run after everything is in-place
    window.socket.on('toast_notification', showNotificationFromBackend);
  });
});

const showNotificationFromBackend = (data) => {
  const title = data["title"];
  const description = data["description"];
  const type = data["type"];
  const placement = data["placement"];
  const closeAfterSeconds = data["closeAfterSeconds"];
  let fileDownload = null;
  if (data.file_download) {
    fileDownload = new FileDownload(
        data.file_download.file_name, data.file_download.content_b64string, data.file_download.file_type
    );
  }
  showNotification(title, description, type, placement, closeAfterSeconds, fileDownload);
};

const showNotification = (title, description, type, placement, closeAfterSeconds, fileDownload) => {
  // TODO implement button with a way to link to other view?
  // const key = `open${Date.now()}`;
  if (fileDownload !== null) {
    download_binary_file_from_base64_str_with_type(
        fileDownload.contentB64string,
        fileDownload.fileName,
        fileDownload.fileType
    );
  }
  notification[type]({
    message: title,
    description: description,
    placement: placement,
    duration: closeAfterSeconds,
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
defineExpose({showNotification});
</script>

<style scoped>
</style>
