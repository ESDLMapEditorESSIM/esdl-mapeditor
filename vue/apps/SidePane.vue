<template>
  <div id="side_pane" :class="{side_pane_hidden: !showSidePane}">
    <ul class="tabs">
      <li
        v-for="tab in sidePaneTabs"
        :key="tab.key"
      >
        <a @click="clickTab(tab.key);">
          <span :class="tab.icon" />
          <span
            v-if="isActiveTab(tab.key)"
            style="font-weight:bold"
          >
            {{ tab.title }}
          </span>
          <span v-else>
            {{ tab.title }}
          </span>
        </a>
      </li>
    </ul>
    <ProjectView v-if="isActiveTab('Project')"/>
  </div>
</template>

<script setup>
import {ref} from "vue"
import {useESDLProjects} from "../composables/esdlProjects";
import {useSidePane} from "../composables/sidePane";
import ProjectView from "./ProjectView";

const {energyProject, showProjectView, toggleProjectView} = useESDLProjects();
const {showSidePane, toggleSidePaneView, initTabs, clickTab, isActiveTab} = useSidePane();

const sidePaneTabs = ref([{
    key: 'Project',
    title: 'Project',
    icon: 'fas fa-project-diagram',
    active: false
  }, {
    key: 'Workflow',
    title: 'Workflow',
    icon: 'fas fa-tasks',
    active: false
  }, {
    key: 'WMSLayers',
    title: 'WMS Layers',
    icon: 'fas fa-map',
    active: false
}]);

initTabs(sidePaneTabs);

</script>

<style scoped lang="scss">
#side_pane {
  display: flex;
  height: 100%;
  margin-right: 1px;
  border-right: 1px solid #efeff1;
  box-shadow: 0 .8px 4px rgba(0, 0, 0, .2);
  transition: max-width .2s ease-in;
  min-width: 200px;
  max-width: 500px;
  resize: both;

  &.side_pane_hidden {
    min-width: 20px;
    max-width: 20px;
  }

  ul.tabs {
    padding: 8px 0 0 0;
    margin: 0;
    // This only works in Firefox, not Chrome.
    //writing-mode: sideways-lr;
    text-align: right;
    border-right: 1px solid #efeff1;
    box-shadow: 0 .8px 4px rgba(0, 0, 0, .2);
    background-color: #ffeffe;

    li {
      display: block;
      padding: 8px 0 0 0;

      a {
        background: none;
        border: none;
        writing-mode: vertical-lr;
        -webkit-transform: rotate(180deg);
        -moz-transform: rotate(180deg);
        -ms-transform: rotate(180deg);
        -o-transform: rotate(180deg);
        transform: rotate(180deg);

        &:hover {
          cursor: pointer;
          color: slategray;
        }

        padding: 0;

        span {
          padding: 3px 0 0 0;
          -webkit-transform: rotate(180deg);
          -moz-transform: rotate(180deg);
          -ms-transform: rotate(180deg);
          -o-transform: rotate(180deg);
          transform: rotate(180deg);
        }
      }
    }
  }
}

</style>