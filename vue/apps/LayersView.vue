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
  <div id="layers_view">
    <div v-if="treeData != null">
      <vue-js-tree :tree-id="treeId" :plugins="['contextmenu', 'types', 'checkbox', 'dnd']"
                   :data="treeData" :event-handlers-by-name="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
                   :check-call-back="checkCallBack" :dnd-is-draggable="dnbIsDraggable"
      />
      <VisibleView />
    </div>
    <div v-else>
      <p class="text-only">No map layers loaded.</p>
    </div>
  </div>
</template>

<script setup>
import {computed} from 'vue'
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useSocketIO} from "../composables/socketio";
import {useBaseLayers,} from "../composables/baseLayers";
// eslint-disable-next-line no-unused-vars
import VisibleView from "./VisibleLayersView.vue";
import {useWmsLayers} from "../composables/wmsLayers";

const {showBaseLayer, baseLayerDefinitions, getBaseLayerByLabel, hideBaseLayer} = useBaseLayers();
const {
  getWmsLayerList,
  showWmsLayer,
  hideWmsLayer,
  removeWmsLayer,
  addWmsLayerGroup,
  renameWmsLayerGroup,
  removeWmsLayerGroup,
  moveWmsItem
} = useWmsLayers();


// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const treeId = "layer_tree";
const $ = window.$;

const getTree = () => $('#' + treeId).jstree(true);
// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
  console.log(getWmsLayerList())
  if (getWmsLayerList()) {
    let wmsGroupsJstreeData = [];
    for (const [key, rootGroup] of Object.entries(getRootGroupsWithChildren())) {
      addTreeItem(wmsGroupsJstreeData, rootGroup, key, "wms_layer_folder", rootGroup.children);
    }

    return [
      getBaseLayersControlTreeData(),
      ...wmsGroupsJstreeData,
    ];
  } else {
    return null;
  }
});

const showAddLayerDialog = (objectId) => {
  window.add_edit_wms_layer(objectId);
}

const getRootGroupsWithChildren = () => {
  const rootGroups = [];
  const foundChildIds = []
  for (const [key, layerGroup] of Object.entries(getWmsLayerList().layer_groups)) {
    if (layerGroup.parent_group_id === 'root') {
      rootGroups[key] = {...layerGroup};
      rootGroups[key]['children'] = getChildrenOfGroup(layerGroup, foundChildIds);
    }
  }

  // add 'non-root' groups that are not found in any 'child_ids' list (legacy) to the 'Personal Layers' folder
  for (const [key, layerGroup] of Object.entries(getWmsLayerList().layer_groups)) {
    if (layerGroup.parent_group_id !== 'root' && !foundChildIds.includes(key)) {
      addTreeItem(rootGroups['personal_layers'].children, layerGroup, key, "wms_layer_folder", getChildrenOfGroup(layerGroup, foundChildIds));
    }
  }
  // add layers that are not found in any 'child_ids' list (legacy) to the 'Personal Layers' folder
  for (const [key, layer] of Object.entries(getWmsLayerList().layers)) {
    if (!foundChildIds.includes(key)) {
      addTreeItem(rootGroups['personal_layers'].children, layer, key, "wms_layer", []);
    }
  }

  return rootGroups;
}

const getChildrenOfGroup = (layerGroup, foundChildIds) => {
  const layers = [];
  if (typeof layerGroup.child_ids !== 'undefined' && layerGroup.child_ids.length > 0) {
    for (const childId of layerGroup.child_ids) {
      // check if child is a group
      let child = getWmsLayerList().layer_groups[childId];
      let type = "wms_layer";
      let children = [];
      if (child !== undefined && child !== null) {  // if a group, find children
        type = "wms_layer_folder";
        children = getChildrenOfGroup(child, foundChildIds);
      } else { // get layer
        child = getWmsLayerList().layers[childId];
      }

      if (child !== undefined && child !== null) {
        addTreeItem(layers, child, childId, type, children);
        foundChildIds.push(childId);
      }
    }
  }
  return layers;
}

const addTreeItem = (items, item, itemId, type, children) => {
  let a_attr = {"class": "no_checkbox"};
  if (type === "wms_layer") {
    a_attr = {"class": item.active ? "bold" : ""};
  }
  items.push({
    id: itemId,
    text: item.description,
    setting_type: item.setting_type,
    project_name: item.project_name,
    readonly: item.readonly,
    type: type,
    a_attr: a_attr,
    state: {"checked": item.visible, opened: true},
    children: children,
  });
}

class LayerFolderTreeSpec {
  constructor() {
    this.type = "wms_layer_folder";
    this.icon = 'fas fa-layer-group';
  }

  contextMenus(node, tree) {
    return {
      'add_layer': {
        'label': 'Add WMS layer',
        'icon': 'fas fa-plus',
        'action': function () {
          showAddLayerDialog("__" + node.id); // add '__' to give parent folder id
        },
        '_disabled': node.original.readonly
      },
      'add_folder': {
        'label': 'Add folder',
        'icon': 'fas fa-plus',
        'action': function () {
          console.log(node)
          let project_name;
          if (Object.hasOwn(node.original, 'project_name')) {
            project_name = node.original.project_name;
          } else {
            project_name = node.original.setting_type;
          }
          console.log(project_name)
          addWmsLayerGroup(node.id, node.original.setting_type, project_name);
        },
        '_disabled': node.original.readonly
      },
      'rename_folder': {
        'label': 'Rename folder',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node, undefined, (node, isSuccessful, isCancelled) => {
            if (isSuccessful && !isCancelled) {
              renameWmsLayerGroup(node.id, node.text);
            }
          });
        },
        '_disabled': node.original.readonly || node.parents.length < 2, // do not rename root folders
      },
      'delete': {
        'label': 'Delete folder',
        'icon': 'fa fa-trash-o',
        'action': function () {
          removeWmsLayerGroup(node.id, node.parents[0]);
        },
        '_disabled': node.original.readonly || node.parents.length < 2, // do not delete root folders
      },
    }
  }
}

class LayerTreeSpec {
  constructor() {
    this.type = "wms_layer";
    this.icon = 'fas fa-map';
    this.max_depth = 0;
  }

  contextMenus(node) {
    return {
      'edit': {
        'label': 'Edit WMS layer',
        'icon': 'far fa-edit',
        'action': function () {
          showAddLayerDialog(node.id);
        },
        '_disabled': node.original.readonly,
      },
      'delete': {
        'label': 'Delete WMS layer',
        'icon': 'fa fa-trash-o',
        'action': function () {
          removeWmsLayer(node.id, node.parents[0]);
        },
        '_disabled': node.original.readonly,
      },
    };
  }
}

class BaseLayerFolderTreeSpec {
  constructor() {
    this.type = "root_layer_folder";
    this.icon = "fas fa-layer-group";
  }
}

class BaseLayerTreeSpec {
  constructor() {
    this.type = "base_layer";
    this.icon = 'far fa-map';
    this.max_depth = 0;
  }
}

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new LayerFolderTreeSpec(), new BaseLayerTreeSpec(), new BaseLayerFolderTreeSpec(), new LayerTreeSpec];

// TODO: Move into tree specs
// eslint-disable-next-line no-unused-vars
const eventHandlersByName = [{
  eventName: 'ready.jstree',
  handler: function () {
  }
}, {
  eventName: 'create_node.jstree',
  handler: function () {
  }
}, {
  eventName: 'select_node.jstree',
  handler: function () {
  }
}, {
  eventName: 'check_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const id = data.node.id;
    if (type === 'base_layer') {
      // Single base layer selection
      for (const checkedNode of getTree().get_checked_descendants(data.node.parent)) {
        if (checkedNode !== id) {
          getTree().uncheck_node(checkedNode)
        }
      }
      for (const baseLayer of baseLayerDefinitions) {
        hideBaseLayer(baseLayer);
      }

      const baseLayer = getBaseLayerByLabel(id);
      showBaseLayer(baseLayer);
    } else if (type === 'wms_layer') {
      showWmsLayer(id);
    }
  }
}, {
  eventName: 'uncheck_node.jstree',
  handler: function (e, data) {
    const type = data.node.type;
    const id = data.node.id;
    if (type === 'base_layer') {
      const baseLayer = getBaseLayerByLabel(id);
      hideBaseLayer(baseLayer);
    } else if (type === 'wms_layer') {
      hideWmsLayer(id);
    }
  }
}, {
  eventName: 'move_node.jstree',
  handler: function (e, data) {
    moveWmsItem(data.node.id, data.old_parent, data.node.parents[0]);
  },
}, {
  eventName: 'create_node.jstree',
  handler: function (e, data) {
    getTree().edit(data.node, undefined, (node, isSuccessful, isCancelled) => {
      if (isSuccessful && !isCancelled) {
        renameWmsLayerGroup(node.id, node.text);
      }
    });
  },
}];

// $(document).on('dnd_start.vakata', function (e, data, tree, dd) {
//   data.event.originalEvent.preventDefault();
// });

// eslint-disable-next-line no-unused-vars
const checkCallBack = (operation, node, node_parent, node_position, more) => {
  if (operation === 'move_node') {
    const old_root_folder_id = node.parents[node.parents.length - 2];
    let new_root_folder_id;
    if (node_parent.parents.length > 1) {
      new_root_folder_id = node_parent.parents[node_parent.parents.length - 2];
    } else {
      new_root_folder_id = node_parent.id;
    }
    if (old_root_folder_id === new_root_folder_id) { // always allow within root folder
      return true;
    } else if (new_root_folder_id === '#' || new_root_folder_id === 'group_base_layers'
        || new_root_folder_id === 'standard_layers') { // don't move into 'root'', 'Base layers' and 'Standard layers'
      return false;
    }
  }
  return true;
};

// eslint-disable-next-line no-unused-vars
const dnbIsDraggable = (node) => {
  return !node[0].original.readonly && node[0].type !== "visible_layer" &&
      node[0].type !== "base_layer";
};

function getBaseLayersControlTreeData() {
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

  return {
    id: "group_base_layers",
    text: "Base layers",
    type: "wms_layer_folder",
    readonly: true,
    state: {
      opened: true
    },
    children: children,
    a_attr: {
      "class": "no_checkbox"
    }
  };
}

</script>

<style lang="scss">
#layers_view {
  padding: 8px 5px 8px 2px;
  overflow: scroll;
  //resize: horizontal;
  width: 100%;

  .text-only {
    padding-left: 8px;
  }

}

.bold {
  font-weight: bold;
}
</style>