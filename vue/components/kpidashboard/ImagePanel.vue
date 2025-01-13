<template>
  <a-row style="justify-content: space-between;">
    <a-col :span="20">
      <a-typography-title :level="5" style="padding-left: 12px;">
        {{ options.title }}
      </a-typography-title>
    </a-col>
    <a-col>
      <a-button 
        type="text" 
        @click="showImageSettings"
      >
        <template #icon>
          <FormOutlined />
        </template>
      </a-button>
      <a-button 
        type="text" 
        @click="emit('onRemove')"
      >
        <template #icon>
          <CloseOutlined />
        </template>
      </a-button>
    </a-col>
  </a-row>
  <img
    v-if="options.base64_image_data"
    :src="options.base64_image_data"
    class="panel_image"
  >

  <a-modal v-model:open="image_settings_visible" title="Edit image" width="750px" @ok="handleOk">
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
import { ref } from 'vue';
import { CloseOutlined, FormOutlined } from "@ant-design/icons-vue";
import DropZone from './Dropzone.vue';


const image_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmits(['updateImageSettings', 'onRemove']);

// eslint-disable-next-line no-unused-vars
const showImageSettings = () => {
  image_settings_visible.value = true;
};

const fileToBase64String = (file) => {
  let reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = readerEvent => {
    props.options.base64_image_data = readerEvent.target.result;
  };
};

// eslint-disable-next-line no-unused-vars
const handleOk = () => {
  image_settings_visible.value = false;
  emit('updateImageSettings', props.options);
};

const dropzoneFile = ref("");

// eslint-disable-next-line no-unused-vars
const drop = (e) => {
  dropzoneFile.value = e.dataTransfer.files[0];
  if (dropzoneFile.value.size > 100000) {
    alert("Maximal image size is 100 kB. Please resize the image before uploading...");
  } else {
    fileToBase64String(dropzoneFile.value);
  }
};

// eslint-disable-next-line no-unused-vars
const selectedFile = () => {
  dropzoneFile.value = document.querySelector(".dropzoneFile").files[0];
  if (dropzoneFile.value.size > 100000) {
    alert("Maximal image size is 100 kB. Please resize the image before uploading...");
  } else {
    fileToBase64String(dropzoneFile.value);
  }
};

</script>

<style scoped>


.panel_image {
  border-radius: 8px;
  overflow: hidden;
  object-fit: contain;
}

</style>