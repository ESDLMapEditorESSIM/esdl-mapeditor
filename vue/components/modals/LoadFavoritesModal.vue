<template>
  <a-modal
    v-model:open="isOpen"
    :title="title"
    :ok-text="okText"
    :ok-button-props="{ disabled: !isItemSelected }"
    @ok="onOk"
    @cancel="onCancel"
  >
    <a-empty v-if="items.length === 0" :description="emptyText" />
    <template v-else>
      <a-tree-select
        v-model:value="selectedKey"
        :tree-data="treeData"
        tree-default-expand-all
        :dropdown-match-select-width="false"
        style="width: 100%"
        :placeholder="placeholder"
      >
        <template #title="nodeData">
          <span
            style="
              display: flex;
              align-items: center;
              justify-content: space-between;
              width: 100%;
            "
          >
            <span>{{ nodeData.title }}</span>
            <a-button
              type="text"
              size="small"
              danger
              @click.stop="onDeleteNode(nodeData)"
            >
              <component
                :is="DeleteOutlined"
                style="vertical-align: 0.1rem"
              />
            </a-button>
          </span>
        </template>
      </a-tree-select>
      <a-typography-text
        v-if="hint && isItemSelected"
        type="secondary"
        style="font-size: small; margin-top: 8px; display: block"
      >
        {{ hint }}
      </a-typography-text>
    </template>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { Modal } from "ant-design-vue";
import { DeleteOutlined } from "@ant-design/icons-vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "Load from favorites",
  },
  okText: {
    type: String,
    default: "Load",
  },
  /**
   * Flat list of saved items. Each item must have { id: string, name: string }.
   * An optional `group` string is used to organise items into tree folders.
   * Any extra fields are passed through to `labelFormatter`.
   * @type {Array<{ id: string, name: string, group?: string }>}
   */
  items: {
    type: Array,
    default: () => [],
  },
  /**
   * Optional function to customise the display label of a leaf node.
   * Receives the raw item object and should return a string.
   * Defaults to `(item) => item.name`.
   * @type {(item: object) => string}
   */
  labelFormatter: {
    type: Function,
    default: (item) => item.name,
  },
  /**
   * Optional hint text shown below the tree-select when an item is selected.
   */
  hint: {
    type: String,
    default: "",
  },
  placeholder: {
    type: String,
    default: "Select a saved item",
  },
  emptyText: {
    type: String,
    default: "No saved items yet.",
  },
});

const emit = defineEmits([
  "update:open",
  "load",
  /** Emitted after the user confirms deletion of a single item. Payload: item id (string). */
  "delete-item",
  /** Emitted after the user confirms deletion of a group. Payload: group name (string). */
  "delete-group",
  "cancel",
]);

const selectedKey = ref(undefined);

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit("update:open", val),
});

const isItemSelected = computed(
  () => !!selectedKey.value && selectedKey.value.startsWith("item:")
);

// Build a grouped tree structure from the flat items list.
const treeData = computed(() => {
  const groups = {};
  props.items.forEach((item) => {
    const groupName = item.group || "Ungrouped";
    if (!groups[groupName]) {
      groups[groupName] = [];
    }
    groups[groupName].push(item);
  });

  return Object.entries(groups).map(([groupName, groupItems]) => ({
    key: `group:${groupName}`,
    value: `group:${groupName}`,
    title: groupName,
    selectable: false,
    children: groupItems.map((item) => ({
      key: `item:${item.id}`,
      value: `item:${item.id}`,
      title: props.labelFormatter(item),
      isLeaf: true,
    })),
  }));
});

// Clear the selection if the currently selected item is removed from the items list.
watch(
  () => props.items,
  (newItems) => {
    if (selectedKey.value?.startsWith("item:")) {
      const id = selectedKey.value.slice("item:".length);
      if (!newItems.some((item) => item.id === id)) {
        selectedKey.value = undefined;
      }
    }
  }
);

// Reset selection whenever the modal is opened.
watch(
  () => props.open,
  (opened) => {
    if (opened) {
      selectedKey.value = undefined;
    }
  }
);

const onOk = () => {
  if (!isItemSelected.value) return;
  const id = selectedKey.value.slice("item:".length);
  emit("load", id);
  isOpen.value = false;
};

const onCancel = () => {
  emit("cancel");
};

const onDeleteNode = (nodeData) => {
  const key = nodeData.key ?? nodeData.value;
  if (typeof key !== "string") return;

  if (key.startsWith("group:")) {
    const groupName = key.slice("group:".length);
    Modal.confirm({
      title: `Delete group '${groupName}'?`,
      content: "This will delete all saved items within this group.",
      okText: "Delete",
      okType: "danger",
      onOk: () => {
        emit("delete-group", groupName);
      },
    });
  } else if (key.startsWith("item:")) {
    const id = key.slice("item:".length);
    const target = props.items.find((item) => item.id === id);
    Modal.confirm({
      title: `Delete '${target?.name ?? "this item"}'?`,
      okText: "Delete",
      okType: "danger",
      onOk: () => {
        emit("delete-item", id);
      },
    });
  }
};
</script>
