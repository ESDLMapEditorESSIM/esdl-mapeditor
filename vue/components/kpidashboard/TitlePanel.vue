<template>
  <span class="title">
    {{ options.title }}
  </span>
  <span class="settings" @click="showTitleSettings"><i class="fas fa-edit" /></span>

  <a-modal v-model:visible="title_settings_visible" title="Edit title" width="750px" @ok="handleOk">
    <a-row>
      <a-col :span="4">
        <span>Title:</span>
      </a-col>
      <a-col :span="20">
        <a-input v-model:value="options.title" />
      </a-col>
    </a-row>
  </a-modal>
</template>

<script setup>
import { ref, defineProps, defineEmit } from 'vue'

const title_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmit(['updateTitleSettings']);

// eslint-disable-next-line no-unused-vars
const showTitleSettings = () => {
  title_settings_visible.value = true;
}

// eslint-disable-next-line no-unused-vars
const handleOk = () => {
  title_settings_visible.value = false;
  emit('updateTitleSettings', props.options);
}

</script>

<style>

.settings {
  cursor: default;
  position: absolute;
  top: 3px;
  right: 20px;
}

.settings i {
  color: lightgrey;
}

.title {
  display: flex;
  justify-content: center;
  font-size: 40px;
  font-weight: bold;
  overflow: hidden;
  object-fit: contain;
}

</style>