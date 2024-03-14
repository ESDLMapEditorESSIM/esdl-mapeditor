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
  <div id="side_pane">
    <ul class="tabs">
      <li
        v-for="tab in sidePaneTabs"
        :key="tab.key"
      >
        <a @click="clickTab(tab.key);">
          <span :class="tab.icon" />
          <span
            v-if="isActiveTab(tab.key) && showSidePane"
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
    <div id="tab-content" :class="{side_pane_hidden: !showSidePane}">
      <LayersView v-if="isActiveTab('WMS_Layers')" />
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
  key: 'WMS_Layers',
  title: 'WMS Layers',
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

  #tab-content {
    &.side_pane_hidden {
      min-width: 0;
      max-width: 0;
    }
    min-width: 200px;
    max-width: 500px;
    transition: max-width .2s ease-in;
    overflow: auto;
    resize: horizontal;
  }

  ul.tabs {
    min-width: 20px;
    max-width: 20px;
    padding: 8px 0 0 0;
    margin: 0;
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
