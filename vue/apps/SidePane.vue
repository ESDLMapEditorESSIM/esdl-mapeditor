<template>
  <div id="side_pane" :class="{side_pane_hidden: !showProjectView}">
    <ul class="tabs">
      <li>
        <a @click="toggleProjectView">
          <span class="fas fa-project-diagram" />
          Project
        </a>
      </li>
    </ul>
    <ProjectView />
  </div>
</template>

<script setup>
import {useESDLProjects} from "../composables/esdlProjects";
import ProjectView from "./ProjectView";

const {energyProject, showProjectView, toggleProjectView} = useESDLProjects();
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
      }
    }
  }
}

</style>