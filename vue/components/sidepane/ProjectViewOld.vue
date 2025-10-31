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
import {computed, onMounted} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../jstree/VueJsTree.vue";
import {useESDLProjects} from "@/composables/esdlProjects";
import {useSocketIO} from "@/composables/socketio";
import {useBaseLayers,} from "@/composables/baseLayers";
import {useEsdlLayers} from "@/composables/esdlLayers";

const {
  showBaseLayer,
  baseLayerDefinitions,
  getBaseLayerByLabel,
  hideBaseLayer
} = useBaseLayers();
// eslint-disable-next-line no-unused-vars
const {esdlProject, getESDLProject, setActiveVariant} = useESDLProjects();
const {socket} = useSocketIO();
const {disableEsdl, enableEsdl, enabledEsdlIdList, hideEsdlLayerFromMap} = useEsdlLayers();

const treeId = "project_tree"
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);

onMounted(() => {
  // When the component is mounted, get the ESDL project to make sure we show the most up to date info.
  console.debug("Mounted ProjectView")
  getESDLProject()
});

// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  console.debug("Compute tree data")
  if (esdlProject.value) {
    const variants = esdlProject.value.variants;
    const variantJstreeDatas = [];
    for (const variant of variants) {
      const variantJstreeData = variantToJstreeData(variant);
      variantJstreeDatas.push(variantJstreeData)
    }

    const projectData = {
      text: esdlProject.value.name, id: esdlProject.value.id, type: 'project', state: {opened: true},
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
      "class": variant.active ? "is-active" : "",
    },
    // TODO: The persisting of checked does not work when creating a child variant of a selected variant.
    state: {"checked": enabledEsdlIdList.value.includes(variant.es_id), opened: children.length > 0},
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
              window.add_layer_control(); // hard update the old layer control
            }
          });
        }
      },
      'delete': {
        'label': 'Remove Variant',
        'icon': 'fa fa-trash-o',
        'action': function () {
// the jstree component gets fck'd up when updating the data directly
// in the vue component, while this code is still running.
// get_selection() and get_checked() return the wrong data.
// also select_node and check_node do not work as expected.
// This whole component should be refactored imho.
          const msg = {id: node.original.id};
          const loaderScope = "delete_variant"
          window.show_loader(loaderScope)
          disableEsdl(node.original.esId);
          let checked_nodes = get_checked_nodes();
          checked_nodes = checked_nodes.filter(n => n.id !== node.id);
          socket.value.emit("delete_variant", msg, () => {
            window.hide_loader(loaderScope)

            if (checked_nodes.length === 0) {
              console.log(enabledEsdlIdList.value)
              if (enabledEsdlIdList.value[0]) {
                console.log("Select first enabledESDL", enabledEsdlIdList.value[0]);
                getTree().check_node(enabledEsdlIdList.value[0]);
              } else if (node.parent != null && node.parent !== "#" && !node.parent.startsWith("main_project")) {
                console.log("Select parent node", node.parent);
                getTree().check_node(node.parent);
              }
            }
          })
          // TODO: remove this when new layer control is ready
          window.remove_esdl_layer_from_ui(node.original.id);  // remove from old layer control layer and esdl_list
          //window.add_layer_control(); // hard update the old layer control
        }
      },
      'flatten': {
        'label': 'Flatten Variant',
        'icon': 'fa fa-layer-group',
        'action': function () {
          const msg = {id: node.original.id};
          socket.value.emit("flatten_variant", msg);
        }
      },
    }
  }

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
    if (data.event.button === 2) {
      // on right click do not switch to other variant, but only show context menu
      return;
    }
    if (type === 'variant') {
      const tree = treeElement.jstree(true);
      // The below also triggers the check_node handler, which handles visibility.
      console.log("Select node", data.node);
      tree.check_node(data.node.id);
      if (!original.active) {
        console.log("select_node: set active variant");
        setActiveVariant(original.id, original.esId);
        // window.add_layer_control(); // hard update the old layer control
      }
    }
  },
  'check_node.jstree': function (e, data) {
    const type = data.node.type;
    const original = data.node.original;
    if (type === 'variant') {
      if (original.esId in window.esdl_list) {
        console.log("check_node: enableESDL:", data);
        enableEsdl(original.esId);
        // When holding ctrl key, do not hide other variants.
      } else {
        // We have no way to just get the energy system without activating it right now. I don't think it's a problem.
        console.log("check_node: set active variant");
        setActiveVariant(original.id, original.esId)
      }
      if (!data.event || !data.event.ctrlKey) {
        // if event and ctrlKey + click do not hide other variants
        uncheckOtherVariantsInTree(data.node);
        // If any of the others were active, make this one active as it would be the only one left checked.
        // if (!original.active) {
        //   console.log("check_node: set active variant no data.event", data, e);
        //   setActiveVariant(original.id, original.esId);
        // }
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
      console.log("uncheck_node: disableESDL", data);
      disableEsdl(original.esId);
    } else if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(original.text);
      hideBaseLayer(baseLayer);
    }
  }
};

/**
 * Get the actual checked nodes, getTree().get_checked() returns bogus data in 3.2.1 and 3.3.17
 * @returns {[]} array of checked node ids
 */
function get_checked_nodes() {
  let checked_nodes = Object.values( getTree()._model.data )
      .filter(n => (n.type ==='variant' && n.state.checked === true));
  console.log("get_checked_nodes", checked_nodes);
  return checked_nodes;
}

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

function uncheckOtherVariantsInTree(node) {
  //let checked_nodes = get_checked_nodes();
  let nodes = getTree()._model.data;
  for(const key in nodes) {
    if (nodes[key].type === 'variant' && nodes[key].id !== node.id && nodes[key].state.checked === true) {
      console.log("uncheckOtherVariantsInTree: uncheck node", nodes[key].id);
      getTree().uncheck_node(key);
      hideEsdlLayerFromMap(key);
    }
  }
}

function selectOnlyOneBaseLayer(node) {
  // show only one base layer at the time, deselect others
  const selected = node.id;
  const parent = node.parent;
  const children = getTree().get_node(parent).children;
  for (const child of children) {
    if (child !== selected) {
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

.is-active {
  font-weight: bold;
  background-color: #beebff //#92a800; // esdl green
}
</style>