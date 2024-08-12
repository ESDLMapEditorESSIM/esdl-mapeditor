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
  <div id="wms_layers_view">
    <a-space
      v-if="treeData != null"
      direction="vertical"
      style="width: 95%;"
    >
      <vue-js-tree
        :tree-id="treeId" :plugins="['contextmenu', 'types', 'checkbox', 'dnd']"
        :data="treeData" :events="eventHandlersByName" :tree-type-specs="treeTypeSpecs"
        :check-call-back="checkCallBack" :dnd-is-draggable="dnbIsDraggable"
      />
      <a-divider style="margin: 8px;" />
      <VisibleLayersView />
    </a-space>
    <div v-else>
      <p class="text-only">No WMS layers visible.</p>
    </div>
  </div>
</template>

<script setup>
import {computed} from 'vue';
// eslint-disable-next-line no-unused-vars
import VueJsTree from "../components/jstree/VueJsTree";
import {useSocketIO} from "@/composables/socketio";
import {useBaseLayers,} from "@/composables/baseLayers";
// eslint-disable-next-line no-unused-vars
import VisibleLayersView from "./VisibleLayersView.vue";
import {useWmsLayers} from "@/composables/wmsLayers";
import {useVisibleLayers} from "@/composables/visibleLayers";
import { notification } from 'ant-design-vue';

const {showBaseLayer, baseLayerDefinitions, getBaseLayerByLabel, hideBaseLayer} = useBaseLayers();
const {layerIsVisible} = useVisibleLayers();
const {
  getWmsLayerList,
  showWmsLayer,
  hideWmsLayer,
  removeWmsLayer,
  addWmsLayerGroup,
  renameWmsLayerGroup,
  removeWmsLayerGroup,
  setWmsLayerGroupOpened,
  getDescendantLayerNodeIds,
  setVisibilityWmsLayerGroup,
  moveWmsItem,
  copyWmsItem
} = useWmsLayers();


// eslint-disable-next-line no-unused-vars
const {socket} = useSocketIO();
const treeId = "layer_tree";
const $ = window.$;
const openedFolders = [];

// Maximum layer count to be opened by the user at once
const MaxLayerOpenCount = 10;

const getTree = () => $('#' + treeId).jstree(true);
// eslint-disable-next-line no-unused-vars
const treeData = computed(() => {
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
  // const foundChildIds = [];
  for (const [key, layerGroup] of Object.entries(getWmsLayerList().layer_groups)) {
    if (layerGroup.is_root) {
      rootGroups[key] = {...layerGroup};
      rootGroups[key]['children'] = getChildrenOfGroup(layerGroup);
    }
  }
  return rootGroups;
}

const getChildrenOfGroup = (layerGroup) => {
  const layers = [];
  if (typeof layerGroup.child_ids !== 'undefined' && layerGroup.child_ids.length > 0) {
    for (const childId of layerGroup.child_ids) {
      // check if child is a group
      let child = getWmsLayerList().layer_groups[childId];
      let type = "wms_layer";
      let children = [];
      if (child !== undefined && child !== null) {  // if a group, find children
        type = "wms_layer_folder";
        children = getChildrenOfGroup(child);
      } else { // get layer
        child = getWmsLayerList().layers[childId];
      }

      if (child !== undefined && child !== null) {
        addTreeItem(layers, child, childId, type, children);
      }
    }
  }
  return layers;
}

const addTreeItem = (items, item, itemId, type, children) => {
  // const a_attr = {"class": type !== "wms_layer" ? "no_checkbox" : item.active ? "bold" : "", title: item.description};
  const a_attr = {"class": item.active ? "bold" : "", title: item.description};
  items.push({
    id: itemId,
    text: item.description,
    setting_type: item.setting_type,
    project_name: item.project_name,
    readonly: item.readonly,
    type: type,
    a_attr: a_attr,
    state: {"checked": layerIsVisible(itemId), opened: openedFolders.includes(itemId)},
    children: children,
  });
}

/**
 * WMS Layer folder tree specification
 * @type {LayerFolderTreeSpec}
 *
 * Represents the WMS layer folder tree specification for the jstree component.
 */
class LayerFolderTreeSpec {
  constructor() {
    this.type = "wms_layer_folder";
    this.icon = 'fas fa-layer-group';
    this.events = {
      'check_node.jstree': (e, data) => {
        // Hide any opened child layer from the partially opened folder.
        if (this._getCheckedChildNodeIds(data.node).length) {
          setTimeout(() => getTree().uncheck_node(data.node));
        }
        else {
          const layerIds = getDescendantLayerNodeIds(data.node);
          if (layerIds.length <= MaxLayerOpenCount) {
            setVisibilityWmsLayerGroup(data.node.id, true);
          }
          else {
            // setTimeout to ensure it happens after the check_node event has been processed.
            setTimeout(() => getTree().uncheck_node(data.node));
            this._showWarningMsg(layerIds.length, MaxLayerOpenCount);
          }
        }
      },
      'uncheck_node.jstree': (e, data) => {
        setVisibilityWmsLayerGroup(data.node.id, false);
      },
      'open_node.jstree': (e, data) => {
        setWmsLayerGroupOpened(data.node.id, true);
      },
      'close_node.jstree': (e, data) => {
        setWmsLayerGroupOpened(data.node.id, false);
      }
    };
  }

  /**
   * Returns an array of child node Ids in checked state.
   *
   * @param {Object} node jsTree node object
   * @returns {string[]} An array of checked child node Ids.
   */
  _getCheckedChildNodeIds(node) {
    const children = getTree().get_node(node).children_d;
    const checkedChildren = children.filter((childId) => getTree().is_checked(childId));
    return checkedChildren;
  }

  /**
   * Show a warning message when trying to open too many layers at once.
   *
   * @param {number} hiddenLayerCount The number of hidden layers being opened.
   * @param {number} maxLayerOpenCount The maximum number of layers can be opened at once.
   */
  _showWarningMsg(hiddenLayerCount, maxLayerOpenCount) {
    notification['warning']({
      message: 'Warning',
      description: `You are trying to open ${hiddenLayerCount} map layers. Opening more than ${maxLayerOpenCount} layers at once is not allowed, `
                    + "please open layers individually.",
      placement: 'bottomLeft',
    });
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
          let project_name;
          if (Object.hasOwn(node.original, 'project_name')) {
            project_name = node.original.project_name;
          } else {
            project_name = node.original.setting_type;
          }
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
    };
  }
}

/**
 * WMS Layer tree specification
 * @type {WmsLayerTreeSpec}
 *
 * Represents the WMS layer tree specification for the jstree component.
 */
class WmsLayerTreeSpec {
  constructor() {
    this.type = "wms_layer";
    this.icon = 'fas fa-map';
    this.max_depth = 0;
    this.events = {
      'check_node.jstree': function (e, data) {
        showWmsLayer(data.node.id);
      },
      'uncheck_node.jstree': function (e, data) {
        hideWmsLayer(data.node.id)
      },
      'move_node.jstree':function (e, data) {
        moveWmsItem(data.node.id, data.old_parent, data.node.parents[0], data.position);
      },
      'copy_node.jstree': function (e, data) {
        copyWmsItem(data.original.id, data.node.parents[0], data.position);
      },
    }
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
    this.events = {
      'check_node.jstree': function (e, data) {
        const id = data.node.id;
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
      },
      'uncheck_node.jstree': function (e, data) {
        const id = data.node.id;
        const baseLayer = getBaseLayerByLabel(id);
        hideBaseLayer(baseLayer);
      },
    }
  }
}

// eslint-disable-next-line no-unused-vars
const treeTypeSpecs = [new LayerFolderTreeSpec(), new BaseLayerTreeSpec(), new BaseLayerFolderTreeSpec(), new WmsLayerTreeSpec];

// eslint-disable-next-line no-unused-vars
const eventHandlersByName = {
  'create_node.jstree': function (e, data) {
    getTree().edit(data.node, undefined, (node, isSuccessful, isCancelled) => {
      if (isSuccessful && !isCancelled) {
        renameWmsLayerGroup(node.id, node.text);
      }
    });
  },
  'open_node.jstree': function (e, data) {
    const id = data.node.id;
    if (!openedFolders.includes(id)) {
      openedFolders.push(id);
    }
  },
  'close_node.jstree': function (e, data) {
    const id = data.node.id;
    const index = openedFolders.indexOf(id);
    if (index > -1) {
      openedFolders.splice(index, 1);
    }
  },
}

// eslint-disable-next-line no-unused-vars
const checkCallBack = (operation, node, node_parent, node_position, more) => {
  if (operation === 'move_node' || operation === 'copy_node') {
    let new_root_folder_id;
    if (node_parent.parents.length > 1) {
      new_root_folder_id = node_parent.parents[node_parent.parents.length - 2];
    } else {
      new_root_folder_id = node_parent.id;
    }
    if (node.type === 'visible_layer' || new_root_folder_id === '#' || new_root_folder_id === 'group_base_layers'
        || new_root_folder_id === 'standard_layers') {
      // don't move from visible layers or into 'root', 'Base layers' or 'Standard layers'
      return false;
    }
    if (operation === 'move_node') { // don't move read only
      if (node.original.readonly) {
        return false;
      }
    }
  }
  return true;
};

// make sure not to drag root folders

// eslint-disable-next-line no-unused-vars
const dnbIsDraggable = (nodes) => {
  return nodes[0].type !== "base_layer" && nodes[0].parent !== "#";
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
#wms_layers_view {
  overflow-y: auto;

  .text-only {
    padding-left: 8px;
  }

}

.bold {
  font-weight: bold;
}
</style>
