<template>
  <div class="title">
    <span>
      {{ options.title }}
    </span>
  </div>
  <div style="position: absolute; top: 3px; right: 20px;">
    <span class="settings" @click="showTitleSettings"><i class="fas fa-edit" /></span>
  </div>

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

const showTitleSettings = () => {
  title_settings_visible.value = true;
}

const handleOk = () => {
  title_settings_visible.value = false;
  emit('updateTitleSettings', props.options);
}

</script>

<style>

.settings {
  cursor: default;
}
.settings i {
  color: lightgrey;
}

.title {
  display: flex;
  justify-content: center;
  position: relative;
}

.title span {
  font-size: 40px;
  font-weight: bold;
}

</style>