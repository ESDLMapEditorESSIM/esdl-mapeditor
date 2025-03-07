<template>
  <a-row style="justify-content: space-between;">
    <a-col :span="20">
      <a-typography-title :level="3" style="padding-left: 12px;">
        {{ options.title }}
      </a-typography-title>
    </a-col>
    <a-col>
      <a-button 
        type="text" 
        @click="showTitleSettings"
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

  <a-modal v-model:open="title_settings_visible" title="Edit title" width="750px" @ok="handleOk">
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
import { ref } from 'vue';
import { CloseOutlined, FormOutlined } from "@ant-design/icons-vue";

const title_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const emit = defineEmits(['updateTitleSettings', 'onRemove']);

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

<style scoped>

</style>