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

<template>
  <div id="project_view">
    <vue-js-tree v-if="treeData != null" :tree-id="treeId" :plugins="['contextmenu', 'types', 'checkbox']"
                 :data="treeData" :contextmenus-by-type="contextmenusByType"
                 :type-settings="treeTypeSettings" :event-handlers-by-name="eventHandlersByName"
    />
    <div v-else>
      <p class="text-only">No project loaded.</p>
      <div style="margin-top: 15px">
        <button @click="getESDLProject">Refresh project</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useESDLProjects} from "../composables/esdlProjects";
import {useSocketIO} from "../composables/socketio";
import {
  addBaseLayerToMap, baseLayerDefinitions,
  getBaseLayerByLabel,
  removeBaseLayerFromMap
} from "../components/projects/baseLayers";

const {esdlProject, getESDLProject, showProjectView} = useESDLProjects();
const {socket} = useSocketIO();

const treeId = "project_tree"
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);

const treeData = computed(() => {
  if (esdlProject.value) {
    const baseVariants = esdlProject.value.base_variants;
    // const variants = baseVariant.children;
    const baseVariantJstreeDatas = [];
    for (const baseVariant of baseVariants) {
      const baseVariantJstreeData = baseVariantToJstreeData(baseVariant);
      baseVariantJstreeDatas.push(baseVariantJstreeData)
    }

    const projectData = {
      text: esdlProject.value.name, type: 'project', state: {opened: true},
      children: [...baseVariantJstreeDatas],
      a_attr: {
        "class": "no_checkbox"
      }
    };
    return [
      get_base_layers_control_tree_data(),
      projectData,
    ];
  } else {
    return null;
  }
});

function baseVariantToJstreeData(baseVariant) {
  const variantsData = [];
  for (const variant of baseVariant.variants) {
    const variantTreeData = variantToJstreeData(variant);
    variantsData.push(variantTreeData);
  }
  return {
    baseVariantId: baseVariant.id,
    text: baseVariant.name,
    children: variantsData,
    type: "base_variant",
    a_attr: {
      "class": "no_checkbox"
    },
  }
}

function variantToJstreeData(variant) {
  const children = [];
  for (const child of variant.children) {
    const variantTreeData = baseVariantToJstreeData(child);
    children.push(variantTreeData);
  }
  for (const change of variant.changes) {
    const changeTreeData = changeToJstreeData(change);
    children.push(changeTreeData);
  }
  return {
    baseVariantId: variant['base_variant_id'],
    esId: variant.es_id,
    text: variant.name,
    children: children,
    type: "variant",
    state: {"checked": variant.active},
  }
}

function changeToJstreeData(change) {
  const children = [];
  if (change.changes) {
    for (const childChange of change.changes) {
      const childChangeTreeData = changeToJstreeData(childChange);
      children.push(childChangeTreeData);
    }
  }
  let text = change.type;
  if (change.label) {
    text = change.label;
  }
  let icon = null
  if (change.type === "HighLevelChange") {
    icon = "far fa-object-group"
  } else if (change.type === "Add") {
    icon = "fas fa-plus"
  } else if (change.type === "Set") {
    icon = "fas fa-arrow-right"
  }
  return {
    text: text,
    children: children,
    type: "change",
    icon: icon
  }
}

const treeTypeSettings = {
  project: {
    icon: 'fas fa-project-diagram',
  },
  base_variant: {
    icon: 'fas fa-bezier-curve'
  },
  variant: {
    icon: 'fas fa-bezier-curve'
  },
  base_layer: {
    icon: "fas fa-layer-group layer-node"
  },
}

const contextmenusByType = {
  "project": (node, tree) => {
    return {
      'rename': {
        'label': 'Rename ESDL Project',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node);
        }
      },
    };
  },
  "variant": (node, tree) => {
    return {
      'load': {
        'label': 'Add as ESDL layer',
        'icon': 'fas fa-plus',
        'action': function () {
          // TODO: Make work
          window.socket.emit('activate_project_variant', {id: node.original.text}, () => {
            window.socket.emit('process_loaded_energysystems');
          });
        }
      },
      'rename': {
        'label': 'Rename Variant',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node);
        }
      },
      'delete': {
        'label': 'Remove Variant',
        'icon': 'fa fa-trash-o',
        'action': function () {
          const msg = {name: node.original.text, base_variant_id: node.original.baseVariantId};
          socket.value.emit("delete_variant", msg);
        }
      },
    }
  },
  "base_variant": (node, tree) => {
    return {
      'create': {
        'label': 'Create new Variant',
        'icon': 'fas fa-plus',
        'action': function () {
          const msg = {base_variant_id: node.original.baseVariantId};
          socket.value.emit("create_variant", msg);
        }
      },
      'rename': {
        'label': 'Rename Base Variant',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node);
        }
      },
      'delete': {
        'label': 'Remove Base Variant',
        'icon': 'fa fa-trash-o',
        'action': function () {
          socket.value.emit("delete_base_variant", {id: node.original.baseVariantId});
        }
      },
    }
  },
}

const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'select_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      socket.value.emit("set_active_variant", {base_variant_id: original.baseVariantId, name: original.text});
    }
  }
}, {
  eventName: 'check_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      window.show_esdl_layer_on_map(original.esId);
    } else if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      addBaseLayerToMap(baseLayer);
    }
  }
}, {
  eventName: 'uncheck_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      window.hide_esdl_layer_from_map(original.esId);
    } else if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      removeBaseLayerFromMap(baseLayer);
    }
  }
}];

function get_base_layers_control_tree_data() {
  let children = [];

  for (const baseLayer of baseLayerDefinitions) {
    let state = {};
    if (baseLayer.enabled) {
      state.checked = true;
    }

    const child = {
      id: baseLayer.label,
      text: baseLayer.label,
      type: "base_layer",
      state: state,
    }
    children.push(child);
    console.log(child);
  }

  let group = {
    id: "group_base_layers",
    text: "Base layers",
    type: "group",
    state: {
      opened: true
    },
    children: children,
    a_attr: {
      "class": "no_checkbox"
    }
  }

  return group;
}

</script>

<style scoped lang="scss">
#project_view {
  padding: 8px 5px 8px 2px;
  overflow: scroll;
  //resize: horizontal;
  width: 100%;

  .text-only {
    padding-left: 8px;
  }
}

</style>