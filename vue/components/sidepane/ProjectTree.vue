<!--
  - This work is based on original code developed and copyrighted by TNO 2020.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<!--
TODO:
- Remember expanded keys
-->

<template>
  <a-tree
    v-model:expanded-keys="expandedKeys"
    :selected-keys="selectedKeys"
    :show-icon="true"
    :show-line="true"
    :tree-data="treeData"
    checkable
    :check-strictly="true"
    :checked-keys="checkedKeys"
    @check="onCheck"
    @select="onSelect"
    @right-click="onRightClick"
  >
    <template #icon="{ iconClass }">
      <span v-if="iconClass" :class="iconClass" />
    </template>

    <template #switcherIcon="{ switcherCls }"><caret-down-filled :class="switcherCls" /></template>
    <template #title="{ title }">
      <a-dropdown :trigger="['contextmenu']">
        <span>{{ title }}</span>
        <template #overlay>
          <a-menu
            :disabled="contextMenuItems.length === 0"
            @click="onContextMenuClick"
          >
            <template v-for="item in contextMenuItems" :key="item.key">
              <a-menu-item class="menu-item-with-icon">
                <i :class="item.icon" />
                {{ item.label }}
              </a-menu-item>
            </template>
          </a-menu>
        </template>
      </a-dropdown>
    </template>
  </a-tree>
</template>

<script setup>
import {computed, onMounted, ref, watch} from 'vue';
import {CaretDownFilled} from '@ant-design/icons-vue';
import {useESDLProjects} from '@/composables/esdlProjects';
import {useEsdlLayers} from '@/composables/esdlLayers';
import {useLoader} from "@/composables/loader";
import {useSocketIO} from "@/composables/socketio";
import {theme} from 'ant-design-vue';

// Composables
const { esdlProject, getESDLProject, activeVariant, setActiveVariant, getAllVariants } = useESDLProjects();
const { enableEsdl, disableEsdl, enabledEsdlIdList } = useEsdlLayers();
const { startLoader, stopLoader } = useLoader();
const { socket } = useSocketIO();
const {token} = theme.useToken();

// State for Ant Tree
const selectedKeys = computed(() => activeVariant() ? [activeVariant().id] : []);
const expandedKeys = ref([]);

onMounted(() => {
  getESDLProject();
});

const contextMenu = ref({
  open: false,
  x: 0,
  y: 0,
  node: null,
});

const contextMenuItems = computed(() => {
  const dataType = contextMenu.value.node?.dataType;

  if (dataType === 'variant') {
    return [
      { key: 'create', icon: 'fas fa-plus', label: 'Create new variant' },
      { key: 'rename', icon: 'fas fa-edit', label: 'Rename variant' },
      { key: 'delete', icon: 'fas fa-trash', label: 'Remove variant' },
      { key: 'flatten', icon: 'fas fa-layer-group', label: 'Flatten variant' },
      { key: 'refresh', icon: 'fas fa-sync', label: 'Refresh variant' },
    ];
  } else if (dataType === 'project') {
    return [
      { key: 'create', icon: 'fas fa-plus', label: 'Create new base variant' },
      { key: 'rename', icon: 'fas fa-edit', label: 'Rename project' },
    ];
  }

  return []; // no options for other types
});

// Convert project data to Ant Tree format
const treeData = computed(() => {
  if (!esdlProject.value) return [];

  function variantNode(variant) {
    return {
      title: variant.name,
      key: variant.id,
      variant: variant,
      esId: variant.es_id,
      children: [
        ...variant.children.map(variantNode),
        ...variant.changes.map(changeNode)
      ],
      iconClass: 'fas fa-bezier-curve',
      checkable: true,
      selectable: true,
      showIcon: true,
      class: variant.active ? 'is-active' : '',
      dataType: 'variant',
    };
  }

  function changeNode(change) {
    let text = change.type;
    if (change.feature) {
      text += ` on ${change.feature}`;
    }
    if (change.object_value_type) {
      text += `: ${change.object_value_type}`;
    }
    let icon;
    if (change.type === 'HighLevelChange') {
      icon = 'far fa-object-group';
    } else if (change.type === 'Add') {
      icon = 'fas fa-plus';
    } else if (change.type === 'Set') {
      icon = 'fas fa-arrow-right';
    }

    return {
      title: text,
      key: `change_${Math.random().toString(36).slice(2, 11)}`,
      icon,
      isLeaf: !change.changes,
      selectable: false,
      checkable: false,
      children: change.changes ? change.changes.map(changeNode) : []
    };
  }

  const projectNode = {
    title: esdlProject.value.name,
    key: esdlProject.value.id,
    children: esdlProject.value.variants.map(variantNode),
    project: esdlProject,
    iconClass: 'fas fa-project-diagram',
    dataType: 'project',
    checkable: false,
    selectable: false,
  };

  return [
    projectNode,
  ];
});

let expandedInitialized = false;
watch(treeData, (newData) => {
  // Expand the top-level nodes (Base layers + Project) after data initialization.
  if (!expandedInitialized && newData.length) {
    expandedKeys.value = newData.map((node) => node.key);
    expandedInitialized = true;
  }
}, { immediate: true });

const checkedKeys = computed(() => {
  const allVariants = getAllVariants();
  const enabledVariantIds = [];
  for (const variant of allVariants) {
    if (enabledEsdlIdList.value.includes(variant.es_id)) {
      enabledVariantIds.push(variant.id);
    }
  }
  return enabledVariantIds;
});

// Handlers
function onSelect(selected, info) {
  const node = info.node;
  const data = node.dataRef;
  console.debug('PROJECT TREE: onSelect', selected, info);
  if (info.nativeEvent.button === 2) {
    // Right-click, do not change selection
    return;
  }
  if (data.dataType === 'variant') {
    console.debug("select_node: set active variant", node);
    if (!data.variant.active) {
      setActiveVariant(data.variant.id);
      for (const enabledEsdlId of enabledEsdlIdList.value) {
        if (enabledEsdlId !== data.esId) {
          disableEsdl(enabledEsdlId);
        }
      }
      enableEsdl(data.esId)
    }
  }
}

async function onCheck(_, info) {
  const node = info.node;
  const isChecked = info.checked;
  // Data is the reference to the original data object that we create.
  const data = node.dataRef;
  const ctrlPressed = info.nativeEvent?.ctrlKey;
  console.debug('PROJECT TREE: onCheck', isChecked, info);
  if (data.dataType === 'variant') {
    if (isChecked) {
      if (data.esId in window.esdl_list) {
        enableEsdl(data.esId);
        // if (!ctrlPressed) {
          // If the currently active variant is not the one we just enabled, make it active.
          if (activeVariant().es_id !== data.esId) {
            setActiveVariant(data.variant.id);
          }
        // }
      } else {
        // We have no way to just get the energy system without activating it right now. I don't think it's a problem.
        console.debug("check_node: set active variant");
        setActiveVariant(data.variant.id)
      }
      if (!ctrlPressed) {
        // Disable other variants.
        for (const enabledEsdlId of enabledEsdlIdList.value) {
          if (enabledEsdlId !== data.esId) {
            disableEsdl(enabledEsdlId);
          }
        }
      }
    } else {
      disableEsdl(data.esId);
    }
  }
}

function onRightClick(info) {
  info.event.preventDefault();
  if (info.node.dataType !== 'variant' && info.node.dataType !== 'project') {
    return;
  }
  console.debug("PROJECT TREE: onRightClick", info);

  contextMenu.value = {
    open: true,
    x: info.event.clientX,
    y: info.event.clientY,
    node: info.node,
  };

  document.addEventListener('click', hideContextMenuOnce);
}

function hideContextMenuOnce() {
  contextMenu.value.open = false;
  document.removeEventListener('click', hideContextMenuOnce);
}

function onContextMenuClick({ key }) {
  const node = contextMenu.value.node?.dataRef;
  console.debug('PROJECT TREE: onContextMenuClick', key, node);
  if (!node || (node.dataType !== 'variant' && node.dataType !== 'project')) {
    return;
  }

  if (key === 'create') {
    createNewVariant(node);
  } else if (key === 'rename') {
    if (node.dataType === 'project') {
      renameProject(node.project);
    } else {
      renameVariant(node.variant);
    }
  } else if (key === 'delete') {
    removeVariant(node.variant);
  } else if (key === 'flatten') {
    flattenVariant(node.variant);
  } else if (key === 'refresh') {
    refreshVariant(node.variant);
  }

  contextMenu.value.open = false;
}

function createNewVariant(node) {
  const parentVariant = node.dataType === 'project' ? null : node.variant;
  console.debug("Create new variant. Parent:", parentVariant);
  if (parentVariant) {
    const msg = {parent_variant_id: parentVariant.id};
    socket.value.emit("create_child_variant", msg);
  } else {
    socket.value.emit("create_variant_collection");
  }
}

function renameProject(project) {
  const newName = window.prompt('New project name:', project.name);
  if (newName && newName !== project.name) {
    // emit via socket, or call composable to update backend
    console.debug(`Rename project ${project.id} to ${newName}`);
    socket.value.emit("rename_project", {id: project.id, name: newName}, () => {
      project.name = newName;
    });
  }
}

function renameVariant(variant) {
  const newName = window.prompt('New variant name:', variant.name);
  if (newName && newName !== variant.name) {
    // emit via socket, or call composable to update backend
    console.debug(`Rename variant ${variant.id} to ${newName}`);
    socket.value.emit("rename_variant", {id: variant.id, name: newName}, () => {
      variant.name = newName;
    });
  }
}

function removeVariant(variant) {
  if (window.confirm(`Remove variant "${variant.name}"?`)) {
    console.debug(`Remove variant ${variant.id}`);
    const loaderId = startLoader();
    disableEsdl(variant.es_id);
    const msg = {id: variant.id};
    socket.value.emit("delete_variant", msg, () => {
      stopLoader(loaderId);
    })
  }
}

function flattenVariant(variant) {
  console.debug(`Flatten variant ${variant.id}`);
  // TODO
  const msg = {id: variant.id};
  socket.value.emit("flatten_variant", msg);
}

function refreshVariant(variant) {
  console.debug(`Refresh variant ${variant.id}`);
  // TODO
  const msg = {id: variant.id};
  socket.value.emit("refresh_variant", msg);
}
</script>

<style scoped lang="scss">
.is-active {
  font-weight: bold;
  background-color: v-bind('token.controlItemBgActive');
}

.menu-item-with-icon i {
  width: 18px;
}

</style>
