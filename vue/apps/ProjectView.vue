<template>
  <div id="project_view" :class="{project_view_hidden: !showProjectView}">
    <ul class="tabs">
      <li>
        <button @click="toggleProjectView">
          <span class="fas fa-project-diagram" />
          Project
        </button>
      </li>
    </ul>
    <div id="project_view_contents">
      <div id="project_tree" />
      <vue-js-tree v-if="treeData != null" tree-id="project_tree" :data="treeData"
                   :contextmenus-by-type="contextmenusByType" :type-settings="treeTypeSettings"
      />
      <p v-else class="text-only">No project loaded.</p>
    </div>
  </div>
</template>

<script setup>
import {onMounted, computed} from 'vue'
import VueJsTree from "../components/jstree/VueJsTree";
import {useEnergyProjects} from "../composables/energyProjects";

const {energyProject, getActiveEnergyProject, showProjectView, toggleProjectView} = useEnergyProjects();

// onMounted(() => {
//   getActiveEnergyProject();
// })

function variantToJstreeData(variant) {
  const children = [];
  for (const child of variant.children) {
    const variantTreeData = variantToJstreeData(child);
    children.push(variantTreeData);
  }
  console.log(variant.changes);
  for (const change of variant.changes) {
    const changeTreeData = changeToJstreeData(change);
    children.push(changeTreeData);
  }
  return {
    text: variant.name,
    children: children,
    type: "variant",
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

const treeData = computed(() => {
  if (energyProject.value) {
    console.log(energyProject.value);
    const baseVariant = energyProject.value.base_variant;
    console.log(baseVariant);
    // const variants = baseVariant.children;
    const variantJstreeData = variantToJstreeData(baseVariant);
    return [
      {text: energyProject.value.name, type: 'project'},
      variantJstreeData
      // {
      //   'text': baseVariant.name,
      //   'state': {
      //     'opened': true,
      //   },
      //   'children': [
      //     {'text': 'Child 1'},
      //     'Child 2'
      //   ]
      // }
    ];
  } else {
    return null;
  }
});

const treeTypeSettings = {
  variant: {
    icon: 'fas fa-bezier-curve'
  },
  project: {
    icon: 'fas fa-project-diagram'
  },
}

const contextmenusByType = {
  "project": (node, tree) => {
    return {
      'rename': {
        'label': 'Rename Energy Project',
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
          window.socket.emit('activate_project_variant', {id: node.original.text}, () => {
            window.socket.emit('process_loaded_energysystems');
          });
        }
      },
      'create': {
        'label': 'Create new Variant',
        'icon': 'fas fa-plus',
        'action': function () {
          tree.create_node(node.id, {
            text: "New variant",
            type: "variant",
          }, "last", () => tree.open_node(node));
        }
      },
      'rename': {
        'label': 'Rename Variant',
        'icon': 'far fa-edit',
        'action': function () {
          tree.edit(node);
        }
      },
      'delete' : {
        'label' : 'Remove Variant',
        'icon': 'fa fa-trash-o',
        'action' : function () {
          tree.delete_node(node.id);
        }
      },
    }
  },
}
</script>

<style lang="scss">
#project_view {
  display: flex;
  height: 100%;
  margin-right: 1px;
  border-right: 1px solid #efeff1;
  box-shadow: 0 .8px 4px rgba(0, 0, 0, .2);
  transition: max-width .2s ease-in;
  min-width: 200px;
  max-width: 500px;
  resize: both;

  &.project_view_hidden {
    min-width: 20px;
    max-width: 20px;
  }

  ul.tabs {
    padding: 8px 0 0 0;
    margin: 0;
    writing-mode: sideways-lr;
    text-align: right;
    border-right: 1px solid #efeff1;
    box-shadow: 0 .8px 4px rgba(0, 0, 0, .2);
    background-color: #ffeffe;

    li {
      display: block;

      button {
        background: none;
        border: none;

        &:hover {
          cursor: pointer;
        }

        padding: 0;
      }
    }
  }

  #project_view_contents {
    padding: 8px 5px 8px 2px;
    overflow: scroll;
    width: 100%;
    resize: horizontal;

    .text-only {
      padding-left: 8px;
    }
  }
}

</style>