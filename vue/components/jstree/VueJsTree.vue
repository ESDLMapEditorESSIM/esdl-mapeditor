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
  <div :id="props.treeId" />
</template>

<script setup="props">
import {defineProps, onMounted, watchEffect} from "vue";

const props = defineProps({
  treeId: String,
  data: Object,
  plugins: Array,
  checkbox: Object, // checkbox config for checkbox plugin
  treeTypeSpecs: Array,
  // Tree-level events.
  events: Object,
  checkCallBack: {
    type: Function,
    required: false,
    default: () => true,
  },
  dndIsDraggable: {
    type: Function,
    required: false,
    default: () => true,
  },
});

const $ = window.$;

/// Get the tree element from the treeId.
const getTreeElement = () => $('#' + props.treeId);
/// Get the jstree object from the tree element.
const getTree = () => getTreeElement().jstree(true);

const types = {};
const contextMenusByType = {};
const eventsByEventName = {};

/**
 * Process the treeTypeSpecs to create the types object and the contextMenusByType object.
 *
 * The treeTypeSpecs object is a list of tree type specifications. Each tree type specification
 * is a dictionary with the following keys
 *
 * - type: the type of the tree node.
 * - icon: the icon to use for the tree node.
 * - max_depth: the maximum depth of the tree node.
 * - contextMenus: a dictionary of context menu items for the tree node type.
 * - events: a dictionary of event handlers for the tree node type.
 *
 * The contextMenus object is a dictionary of context menu items for the tree node type. Each
 * context menu item is a dictionary with the following keys:
 *
 * - label: the label of the context menu item.
 * - action: the action to perform when the context menu item is clicked.
 *
 * The events object is a dictionary of event handlers for the tree node type. Each event handler
 * is a function that is called with the following parameters:
 *
 * - e: the event object.
 * - data: the data object.
 * - tree: the tree object.
 *
 * The tree object is the jstree object.
 */
function initTreeTypeSpecs() {
  for (const treeTypeSpec of props.treeTypeSpecs) {
    types[treeTypeSpec.type] = {
      icon: treeTypeSpec.icon,
      max_depth: treeTypeSpec.max_depth,
    }

    if (treeTypeSpec.contextMenus) {
      contextMenusByType[treeTypeSpec.type] = treeTypeSpec.contextMenus
    }

    if (treeTypeSpec.events) {
      for (const [event, handler] of Object.entries(treeTypeSpec.events)) {
        const typeHandler = (e, data, tree) => {
          const type = data.node.type
          if (type === treeTypeSpec.type) {
            handler(e, data, tree)
          }
        }
        if (!eventsByEventName[event]) {
          eventsByEventName[event] = typeHandler
        } else {
          const existingHandler = eventsByEventName[event];
          eventsByEventName[event] = (e, data, tree) => {
            existingHandler(e, data, tree)
            typeHandler(e, data, tree)
          }
        }
      }
    }
  }
}
initTreeTypeSpecs()

/**
 * Process the eventHandlersByName to create the eventsByType object.
 *
 * The eventHandlersByName object is a dictionary of event names to event handlers. The event
 * handlers are called with the following parameters:
 *
 * - e: the event object.
 * - data: the data object.
 * - tree: the tree object.
 */
function initTreeEvents() {
  for (const [eventName, handler] of Object.entries(props.events)) {
    if (!eventsByEventName[eventName]) {
      eventsByEventName[eventName] = handler;
    } else {
      const existingHandler = eventsByEventName[eventName];
      eventsByEventName[eventName] = (e, data, tree) => {
        existingHandler(e, data, tree);
        handler(e, data, tree);
      }
    }
  }
}
initTreeEvents()

onMounted(() => {
  const treeElement = getTreeElement();
  // Add event handlers to the tree element.
  for (const [event, handler] of Object.entries(eventsByEventName)) {
    // Add tree element as extra parameter.
    treeElement.on(event, (e, data) => handler(e, data, getTreeElement()));
  }
  // Create the tree.
  treeElement.jstree({
    core: {
      data: props.data,
      check_callback: (operation, node, node_parent, node_position, more) =>
          props.checkCallBack(operation, node, node_parent, node_position, more),
      animation: 200,
      multiple: false,
      expand_selected_onload : false,
    },
    plugins: props.plugins,
    checkbox: props.checkbox || {
      "three_state": true,
      "whole_node": false,
      // uncouple selecting and checking
      "tie_selection": false
    },
    contextmenu: {
      items: (node) => {
        // Get the context menu for the node type.
        const nodeContextMenu = contextMenusByType[node.type];
        if (nodeContextMenu) {
          return nodeContextMenu(node, getTree());
        }
        return {};
      },
      select_node: true,
    },
    dnd: {
      inside_pos: "first",
      is_draggable: (node) => props.dndIsDraggable(node),
    },
    types: types,
  });
});

watchEffect(() => {
  // Refresh tree with new data.
  if (props.data && getTree() && getTree().refresh) {
    getTree().settings.core.data = props.data;
    console.log("Refreshing tree with new data");
    getTree().refresh(true, true);
  }
});

</script>

<style>
.no_checkbox > i.jstree-checkbox {
  display: none;
}
</style>
