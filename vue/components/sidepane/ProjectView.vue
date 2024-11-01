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
    <vue-js-tree
      v-if="treeData != null" :tree-id="treeId" :plugins="['contextmenu', 'types', 'checkbox']"
      :data="treeData" :events="eventHandlersByName" :tree-type-specs="treeTypeSpecs" 
      :checkbox="{'three_state': false, 'whole_node': false, 'tie_selection': false}"
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
import VueJsTree from "../jstree/VueJsTree.vue";
import {useESDLProjects} from "../../composables/esdlProjects";
import {useSocketIO} from "../../composables/socketio";
import {useMultiEsdl} from "../../composables/multiEsdl";
import {useBaseLayers,} from "../../composables/baseLayers";

const {
  showBaseLayer,
  baseLayerDefinitions,
  getBaseLayerByLabel,
  hideBaseLayer
} = useBaseLayers();
// eslint-disable-next-line no-unused-vars
const {esdlProject, getESDLProject} = useESDLProjects();
const {socket} = useSocketIO();
const {isEsdlShownOnMap, showEsdlLayerOnMap, hideEsdlLayerFromMap, esdlList} = useMultiEsdl();

const treeId = "project_tree"
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  console.log("Compute tree data")
  if (esdlProject.value) {
    const variants = esdlProject.value.variants;
    const variantJstreeDatas = [];
    for (const variant of variants) {
      const variantJstreeData = variantToJstreeData(variant);
      variantJstreeDatas.push(variantJstreeData)
    }

    const projectData = {
      text: esdlProject.value.name, type: 'project', state: {opened: true},
      children: [...variantJstreeDatas],
      a_attr: {
        "class": "no_checkbox"
      }
    };
    return [
      get_base_layers_control_tree_data(),
      projectData,
    ];
  } else {
    console.log("No data...");
    return null;
  }
});

// function baseVariantToJstreeData(baseVariant) {
//   const variantsData = [];
//   for (const variant of baseVariant.variants) {
//     const variantTreeData = variantToJstreeData(variant);
//     variantsData.push(variantTreeData);
//   }
//   return {
//     baseVariantId: baseVariant.id,
//     text: baseVariant.name,
//     children: variantsData,
//     type: "base_variant",
//     state: {
//       opened: true
//     },
//     a_attr: {
//       "class": "no_checkbox"
//     },
//   }
// }

function variantToJstreeData(variant) {
  const children = [];
  for (const child of variant.children) {
    const variantTreeData = variantToJstreeData(child);
    children.push(variantTreeData);
  }
  for (const change of variant.changes) {
    const changeTreeData = changeToJstreeData(change);
    children.push(changeTreeData);
  }
  return {
    id: variant.id,
    esId: variant.es_id,
    text: variant.name,
    children: children,
    type: "variant",
    a_attr: {
      "class": variant.active ? "bold" : "",
    },
    state: {"checked": variant.active || isEsdlShownOnMap(variant.es_id), opened: children.length > 0},
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
  if (change.feature) {
    text += " on " + change.feature
  }
  if (change.object_value_type) {
     text += ": " + change.object_value_type;
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
    icon: icon,
    a_attr: {
      "class": "no_checkbox"
    }
  }
}

class ProjectTreeSpec {
  constructor() {
    this.type = "project";
    this.icon = 'fas fa-project-diagram';
  }

  contextMenus(node, tree) {
    return {
      'create': {
        'label': 'Create new Energy System',
        'icon': 'fas fa-plus',
        'action': function () {
          socket.value.emit("create_variant_collection");
        }
      },
      'rename': {
        'label': 'Rename ESDL Project',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node, undefined, (node, isSuccessful, isCancelled) => {
            if (isSuccessful && !isCancelled) {
              socket.value.emit("rename_project", {name: node.text});
            }
          });
        }
      },
      'refresh': {
        'label': 'Refresh Project',
        'icon': 'fa fa-refresh',
        'action': function () {
            getESDLProject();
        } 
      },
    }
  }
}

class VariantTreeSpec {
  constructor() {
    this.type = "variant";
    this.icon = 'fas fa-bezier-curve';
  }

  contextMenus(node, tree) {
    return {
      'create': {
        'label': 'Create new Variant',
        'icon': 'fas fa-plus',
        'action': function () {
          const msg = {parent_variant_id: node.original.id};
          socket.value.emit("create_child_variant", msg);
        }
      },
      'rename': {
        'label': 'Rename Variant',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node, undefined, (node, isSuccessful, isCancelled) => {
            if (isSuccessful && !isCancelled) {
              socket.value.emit("rename_variant", {id: node.original.id, name: node.text});
            }
          });
        }
      },
      'delete': {
        'label': 'Remove Variant',
        'icon': 'fa fa-trash-o',
        'action': function () {
          const msg = {id: node.original.id};
          socket.value.emit("delete_variant", msg);
        }
      },
    }
  }

  // eventHandlers() {
  //   return {
  //     'select_node.jstree': (e, data, treeElement) => {
  //       const original = data.node.original;
  //       socket.value.emit("set_active_variant", {id: original.id});
  //     }
  //   }
  // }
}

class BaseLayerTreeSpec {
  constructor() {
    this.type = "base_layer";
    this.icon = 'fas fa-layer-group layer-node';
  }
}

const treeTypeSpecs = [new ProjectTreeSpec(), new VariantTreeSpec(), new BaseLayerTreeSpec()];

// TODO: Move into tree specs
const eventHandlersByName = {
  'ready.jstree': function () {
  },
  'select_node.jstree': function (e, data, treeElement) {
    const type = data.node.type;
    const original = data.node.original;
    if (data.event.button == 2) {
      // on right click do not switch to other variant, but only show context menu
      return;
    }
    if (type === 'variant') {
      const tree = treeElement.jstree(true);
      tree.check_node(data.node);
      hideOtherVariantsInTree(data.node);
      if (!original.active) {
        window.show_loader();
        socket.value.emit("set_active_variant", {id: original.id});
      }
    }
  },
  'check_node.jstree': function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      if (original.esId in esdlList.value) {
        showEsdlLayerOnMap(original.esId); 
        if (data.event) {
          if (!data.event.ctrlKey) {
            // if event and ctrlKey + click do not hide other variants
            hideOtherVariantsInTree(data.node);
          }
        } else {
          hideOtherVariantsInTree(data.node);
        }
      } else {
        // TODO: Just get the energy system from this variant, it should not be necessary to also activate it.
        socket.value.emit("set_active_variant", {id: original.id});
      }
    } else if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      showBaseLayer(baseLayer);     
      selectOnlyOneBaseLayer(data.node);
    }
  },
  'uncheck_node.jstree': function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      hideEsdlLayerFromMap(original.esId);
    } else if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      hideBaseLayer(baseLayer);
    }
  }
};

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
  }

  const group = {
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

function hideOtherVariantsInTree(node) {
  let checked_nodes = getTree().get_checked(true);
  for(const checked_node of checked_nodes) {
    if (checked_node.type === 'variant' && checked_node.id !== node.id) {
      getTree().uncheck_node(checked_node.id);
      hideEsdlLayerFromMap(checked_node.id);  
    }
  }
}

function selectOnlyOneBaseLayer(node) {
  // show only one base layer at the time, deselect others
  const selected = node.id;
  const parent = node.parent;
  const children = getTree().get_node(parent).children;
  for (const child of children) {
    if (child != selected) {
      getTree().uncheck_node(child);      
    }
  }
}

</script>

<style lang="scss">
#project_view {
  padding: 8px 5px 8px 2px;
  overflow-x: hidden;
  overflow-y: auto;
  resize: horizontal;
  height: 100%;
  min-width: 200px;

  .text-only {
    padding-left: 8px;
  }
}

.bold {
  font-weight: bold;
  background-color: #beebff //#92a800; // esdl green
}
</style>