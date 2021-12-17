<template>
  <div>
    <h3 class="panel_title">
      {{ options.title }}
    </h3>
  </div>
  <div style="position: absolute; top: 3px; right: 20px;">
    <span class="settings" @click="showImageSettings"><i class="fa fa-edit" /></span>
  </div>
  <div class="panel_image_div">
    <img
      v-if="options.base64_image_data"
      :src="options.base64_image_data"
      class="panel_image"
    >
  </div>

  <a-modal v-model:visible="image_settings_visible" title="Edit image" width="750px" @ok="handleOk">
    <a-row>
      <a-col :span="4">
        <span>Title:</span>
      </a-col>
      <a-col :span="20">
        <a-input v-model:value="options.title" />
      </a-col>
    </a-row>
    <a-row>
      <a-card style="width: 100%">
        <h1>DropZone</h1>
        <DropZone @drop.prevent="drop" @change="selectedFile" />
        <span class="file-info">File: {{ dropzoneFile.name }}</span>
      </a-card>
    </a-row>
  </a-modal>
</template>

<script setup>
import { ref, defineProps, defineEmit } from 'vue'
import DropZone from './Dropzone.vue'

const image_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmit(['updateImageSettings']);

const showImageSettings = () => {
  image_settings_visible.value = true;
}

const fileToBase64String = (file) => {
  let reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = readerEvent => {
    props.options.base64_image_data = readerEvent.target.result;
  }
}

const handleOk = () => {
  image_settings_visible.value = false;
  emit('updateImageSettings', props.options);
}

const dropzoneFile = ref("");

const drop = (e) => {
  dropzoneFile.value = e.dataTransfer.files[0];
  fileToBase64String(dropzoneFile.value);
};

const selectedFile = () => {
  dropzoneFile.value = document.querySelector(".dropzoneFile").files[0];
  fileToBase64String(dropzoneFile.value);
};

</script>

<style>

.panel_title {
    font-weight: bold;
    color: darkblue;
}

.settings {
  cursor: default;
}
.settings i {
  color: lightgrey;
}

.panel_image_div {
  position: relative;
  height: 90%;
  width: 90%;
  margin: 4px;
  bottom: 4px;
  box-sizing: border-box;
}

.panel_image {
  border_radius: 8px;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  border: 0;
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  margin: auto;
  padding: 4px;
  box-sizing: border-box;
}

</style>