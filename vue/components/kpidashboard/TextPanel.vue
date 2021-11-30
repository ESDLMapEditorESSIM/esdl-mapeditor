<template>
  <h3>
    {{ options.title }}
  </h3>
  <div style="position: absolute; top: 3px; right: 20px;">
    <span class="settings" @click="showTextSettings"><i class="fas fa-edit" /></span>
  </div>
  <div style="position: relative; height: 90%; width: 90%;">
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

const showTextSettings = () => {
  text_settings_visible.value = true;
}

const handleOk = () => {
  text_settings_visible.value = false;
  emit('updateTextSettings', props.options);
}

</script>

<style>

.settings {
  cursor: default;
}
.settings i {
  color: lightgrey;
}

</style>