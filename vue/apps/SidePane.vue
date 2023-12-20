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
    <div id="tab_area">
      <LayersView v-if="isActiveTab('Maps')" />
    </div>
  </div>
</template>

<script setup>
import {ref} from "vue"
import {useSidePane} from "../composables/sidePane";
// eslint-disable-next-line no-unused-vars
import LayersView from "./LayersView.vue";

// eslint-disable-next-line no-unused-vars
const {showSidePane, initTabs, clickTab, isActiveTab} = useSidePane();

const sidePaneTabs = ref([{
  key: 'Maps',
  title: 'Maps',
  icon: 'far fa-map',
  active: false
}]);

initTabs(sidePaneTabs);

</script>

<style scoped lang="scss">
#side_pane {
  display: flex;
  margin-right: 1px;
  border-right: 1px solid #efeff1;
  box-shadow: 0 .8px 4px rgba(0, 0, 0, .2);
  transition: max-width .2s ease-in;
  min-width: 200px;
  max-width: 500px;
  resize: horizontal;

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
