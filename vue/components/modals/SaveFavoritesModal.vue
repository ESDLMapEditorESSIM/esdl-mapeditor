<template>
  <a-modal
    v-model:open="isOpen"
    :title="title"
    ok-text="Save"
    :ok-button-props="{ disabled: !nameInput }"
    @ok="onOk"
    @cancel="onCancel"
  >
    <a-form layout="vertical">
      <a-form-item label="Name" required>
        <a-input
          v-model:value="nameInput"
          :placeholder="namePlaceholder"
        />
      </a-form-item>
      <a-form-item label="Group">
        <a-auto-complete
          v-model:value="groupInput"
          :options="groupOptions"
          placeholder="Select an existing group or type a new one"
          :filter-option="filterGroupOption"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "Save to favorites",
  },
  /**
   * List of already-used group names, used to populate the auto-complete options.
   * @type {string[]}
   */
  existingGroups: {
    type: Array,
    default: () => [],
  },
  namePlaceholder: {
    type: String,
    default: "Enter a name",
  },
});

const emit = defineEmits(["update:open", "save", "cancel"]);

const nameInput = ref("");
const groupInput = ref(undefined);

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit("update:open", val),
});

const groupOptions = computed(() =>
  props.existingGroups.map((g) => ({ value: g }))
);

const filterGroupOption = (inputValue, option) =>
  option.value.toLowerCase().includes(inputValue.toLowerCase());

// Reset inputs whenever the modal is opened.
watch(
  () => props.open,
  (opened) => {
    if (opened) {
      nameInput.value = "";
      groupInput.value = undefined;
    }
  }
);

const onOk = () => {
  if (!nameInput.value) return;
  emit("save", { name: nameInput.value, group: groupInput.value || undefined });
  isOpen.value = false;
};

const onCancel = () => {
  emit("cancel");
};
</script>
