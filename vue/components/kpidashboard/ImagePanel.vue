<template>
  <a-row style="justify-content: space-between;">
    <a-col :span="20">
      <a-typography-title :level="5" style="padding-left: 12px;">
        {{ panelTitle }}
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
    v-if="panelImg"
    :src="panelImg"
    class="panel_image"
  >

  <a-modal v-model:open="image_settings_visible" title="Edit image" width="750px" @ok="handleOk">
    <a-row>
      <a-col :span="4">
        <span>Title:</span>
      </a-col>
      <a-col :span="20">
        <a-input v-model:value="panelTitle" />
      </a-col>
    </a-row>
    <a-row>
      <a-card style="width: 100%">
        <h1>DropZone</h1>
        <DropZone
          @drop.prevent="drop"
          @change="selectedFile"
        />
        <span class="file-info">File: {{ dropzoneFile.name }}</span>
      </a-card>
    </a-row>
  </a-modal>
</template>

<script setup>
import { defineProps, ref } from 'vue';
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

const panelTitle = ref(props.options.title);
const panelImg = ref(props.options.base64_image_data);

const emit = defineEmits(['onEditSave', 'onRemove']);

const showImageSettings = () => {
  image_settings_visible.value = true;
};

const fileToBase64String = (file) => {
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = (readerEvent) => {
    panelImg.value = readerEvent.target.result;
  };
};

const handleOk = () => {
  image_settings_visible.value = false;
  emit('onEditSave', {
    title: panelTitle.value,
    base64_image_data: panelImg.value
  });
};

const dropzoneFile = ref("");

const drop = (e) => {
  dropzoneFile.value = e.dataTransfer.files[0];
  if (dropzoneFile.value.size > 100000) {
    alert("Maximal image size is 100 kB. Please resize the image before uploading...");
  } else {
    fileToBase64String(dropzoneFile.value);
  }
};

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