<template>
  <div id="project_view">
    <div id="project_tree" />
    <vue-js-tree v-if="treeData != null" :tree-id="treeId"
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
import {computed, watchEffect} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useESDLProjects} from "../composables/esdlProjects";
import {useSocketIO} from "../composables/socketio";

const {esdlProject, getESDLProject, showProjectView} = useESDLProjects();
const {socket} = useSocketIO();

const treeId = window.uuidv4();
const baseTree = window.baseTree;
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
    console.log("Ready!");
  }
}, {
  eventName: 'select_node.jstree',
  handler: function (e, data) {
    console.log("Select node");
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      socket.value.emit("set_active_variant", {base_variant_id: original.baseVariantId, name: original.text});
    } else if (type === 'base_layer') {
      const map = window.map;
      const treeElement = $("#" + treeId.value);
      const baseLayerGroup = treeElement.jstree("get_node", 'group_es_layers');
      console.log(baseLayerGroup);
      if (baseLayerGroup)
        for (let bl = 0; bl < baseLayerGroup.children.length; bl++) {
          const base_layer = baseLayerGroup.children[bl];
          const bl_node = treeElement.jstree("get_node", base_layer);
          if (treeElement.jstree(true).is_selected(bl_node)) {
            if (!map.hasLayer(baseTree.children[bl_node.data.baseTreeIndex].layer)) {
              map.addLayer(baseTree.children[bl_node.data.baseTreeIndex].layer);
            }
          } else {
            if (map.hasLayer(baseTree.children[bl_node.data.baseTreeIndex].layer)) {
              map.removeLayer(baseTree.children[bl_node.data.baseTreeIndex].layer);
            }
          }
        }
    }
  }
}, {
  eventName: 'check_node.jstree',
  handler: function (e, data) {
    let node = data.node;
    if (node.type === 'variant') {
      window.show_esdl_layer_on_map(node.original.esId);
    }
  }
}, {
  eventName: 'uncheck_node.jstree',
  handler: function (e, data) {
    let node = data.node;
    if (node.type === 'variant') {
      window.hide_esdl_layer_from_map(node.original.esId);
    }
  }
}];

function get_base_layers_control_tree_data() {
  let children = [];

  for (let i = 0; i < baseTree['children'].length; i++) {
    let state = {};
    if (i === 0) {
      state = {"checked": true};
    }

    let child = {
      id: baseTree['children'][i].label,
      text: baseTree['children'][i].label,
      type: "base_layer",
      data: {
        baseTreeIndex: i
      },
      state: state,
    }
    children.push(child);
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