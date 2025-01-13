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
        @click="showTextSettings"
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
  <a-row class="text-panel-text">
    {{ options.text }}
  </a-row>

  <a-modal v-model:open="text_settings_visible" title="Edit text" width="750px" @ok="handleOk">
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
import { ref } from 'vue';
import { CloseOutlined, FormOutlined } from "@ant-design/icons-vue";

const text_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmits(['updateTextSettings', 'onRemove']);

// eslint-disable-next-line no-unused-vars
const showTextSettings = () => {
  text_settings_visible.value = true;
};

// eslint-disable-next-line no-unused-vars
const handleOk = () => {
  text_settings_visible.value = false;
  emit('updateTextSettings', props.options);
};

</script>

<style scoped>
.text-panel-text {
  padding-left: 12px;
  overflow: auto
}
</style>