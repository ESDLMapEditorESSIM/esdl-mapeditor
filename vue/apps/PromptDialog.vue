<template>
  <a-modal
      :open="isOpen"
      :title="activePrompt?.title"
      :closable="false"
      :maskClosable="false"
      :footer="null"
      :z-index="100002"
      width="520px"
  >
    <div class="prompt-message">
      {{ activePrompt?.message }}
    </div>
    <div v-if="activePrompt?.details" class="prompt-details">
      <a-button type="link" size="small" class="details-toggle" @click="detailsOpen = !detailsOpen">
        {{ detailsOpen ? '▾ Hide details' : '▸ Show details' }}
      </a-button>
      <pre v-if="detailsOpen">{{ activePrompt.details }}</pre>
    </div>
    <div class="prompt-actions">
      <a-button
          v-for="choice in sortedChoices"
          :key="choice.key"
          :type="choice.style === 'primary' ? 'primary' : 'default'"
          :danger="choice.style === 'danger'"
          @click="respond(choice.key)"
      >
        {{ choice.label }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup>
import {computed, onMounted, ref, watch} from "vue";
import {usePrompts} from "@/composables/prompts";

const {promptQueue, enqueue, shift} = usePrompts();

const detailsOpen = ref(false);
const activePrompt = computed(() => promptQueue.value.length > 0 ? promptQueue.value[0] : null);
watch(activePrompt, () => { detailsOpen.value = false; });
const isOpen = computed(() => activePrompt.value !== null);

const STYLE_ORDER = {'default': 0, 'danger': 1, 'primary': 2};
const sortedChoices = computed(() => {
  const choices = activePrompt.value?.choices || [];
  return [...choices].sort((a, b) => (STYLE_ORDER[a.style] ?? 0) - (STYLE_ORDER[b.style] ?? 0));
});

function respond(choiceKey) {
  if (!activePrompt.value) {
    return;
  }
  if (window.socket) {
    window.socket.emit('prompt_response', {
      prompt_id: activePrompt.value.id,
      choice_key: choiceKey,
    });
  }
  shift();
}

onMounted(() => {
  window.addEventListener('load', () => {
    if (window.socket) {
      window.socket.on('prompt', (data) => {
        enqueue(data);
      });
    }
  });
});
</script>

<style scoped>
.prompt-message {
  margin-bottom: 12px;
  white-space: pre-wrap;
}

.prompt-details {
  margin-bottom: 16px;
}

.details-toggle {
  padding: 0;
  font-size: 12px;
  color: #888;
}

.prompt-details pre {
  margin: 4px 0 0;
  max-height: 200px;
  overflow-y: auto;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 8px 12px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
}

.prompt-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.prompt-actions :deep(.ant-btn) {
  min-width: 120px;
}
</style>
