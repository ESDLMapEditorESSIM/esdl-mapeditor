<template>
  <div>
    <h3 class="panel_title">
      {{ options.title }}
    </h3>
    <span class="settings" @click="showTextSettings"><i class="fas fa-edit" /></span>
  </div>
  <div class="text-panel-text">
    {{ options.text }}
  </div>

  <a-modal v-model:visible="text_settings_visible" title="Edit text" width="750px" @ok="handleOk">
    <a-row>
      <a-col :span="4">
        <span>Title:</span>
      </a-col>
      <a-col :span="20">
        <a-input v-model:value="options.title" />
      </a-col>
    </a-row>
    <a-row>
      <a-col :span="4">
        <span>Text:</span>
      </a-col>
      <a-col :span="20">
        <a-textarea v-model:value="options.text" :rows="6" />
      </a-col>
    </a-row>
  </a-modal>
</template>

<script setup>
import { ref, defineProps, defineEmit } from 'vue'

const text_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmit(['updateTextSettings']);

// eslint-disable-next-line no-unused-vars
const showTextSettings = () => {
  text_settings_visible.value = true;
}

// eslint-disable-next-line no-unused-vars
const handleOk = () => {
  text_settings_visible.value = false;
  emit('updateTextSettings', props.options);
}

</script>

<style>

.panel_title {
    font-weight: bold;
    color: darkblue;
}

.settings {
  cursor: default;
  position: absolute;
  top: 3px;
  right: 20px;
}

.settings i {
  color: lightgrey;
}

.text-panel-text {
  overflow: auto
}

</style>