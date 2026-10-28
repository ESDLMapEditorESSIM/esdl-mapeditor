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
    <div id="tab-content" :class="{side_pane_hidden: !showSidePane}" :style="{width: paneWidth + 'px'}">
      <div class="pane-header">
        <h4>{{ activeTab?.title }}</h4>
        <a-button
          type="default"
          size="small"
          title="Collapse side pane"
          aria-label="Collapse side pane"
          @click="toggleSidePaneView"
        >
          <template #icon>
            <i class="fas fa-chevron-left" />
          </template>
        </a-button>
      </div>
      <div class="pane-content">
        <LayersView v-show="isActiveTab('WMS_Layers')" />
        <!-- v-show keeps LayerStyleEditor mounted across tab switches, so LayerStyleEditor inside it can stay mounted. -->
        <VisibleLayersView v-show="isActiveTab('visible_layers')" />
        <ProjectView v-if="isActiveTab('Project')" />
        <LiveModelInterfaceView v-show="isActiveTab('live_model_interfaces')" />
      </div>
    </div>
    <div
      v-if="showSidePane"
      class="pane-divider"
      :class="{resizing: isResizing}"
      role="separator"
      aria-label="Resize side pane"
      aria-orientation="vertical"
      aria-controls="tab-content"
      aria-valuemin="200"
      aria-valuemax="500"
      :aria-valuenow="paneWidth"
      tabindex="0"
      @pointerdown="startResize"
      @pointermove="resizePane"
      @pointerup="stopResize"
      @pointercancel="stopResize"
      @lostpointercapture="stopResize"
      @keydown.left.prevent="paneWidth = Math.max(200, paneWidth - 10)"
      @keydown.right.prevent="paneWidth = Math.min(500, paneWidth + 10)"
      @keydown.home.prevent="paneWidth = 200"
      @keydown.end.prevent="paneWidth = 500"
    />
  </div>
</template>

<script setup>
import {computed, ref} from "vue"
import {useSidePane} from "../composables/sidePane";
import ProjectView from "../components/sidepane/ProjectView.vue";
import LayersView from "../components/sidepane/WMSLayersView.vue";
import LiveModelInterfaceView from "../components/sidepane/LiveModelInterfaceView.vue";
import VisibleLayersView from "@/components/sidepane/VisibleLayersView.vue";

// eslint-disable-next-line no-unused-vars
const {showSidePane, initTabs, clickTab, isActiveTab, toggleSidePaneView} = useSidePane();

const sidePaneTabs = ref([{
  key: 'Project',
  title: 'Project',
  icon: 'fas fa-project-diagram',
  active: false
}, {
  key: 'visible_layers',
  title: 'Layers',
  icon: 'far fa-map',
  active: false
}, {
  key: 'WMS_Layers',
  title: 'WMS Layers',
  icon: 'far fa-map',
  active: false
}, {
  key: 'live_model_interfaces',
  title: 'Live Model Interfaces',
  icon: 'fas fa-cogs',
  active: false
}]);

initTabs(sidePaneTabs);

const activeTab = computed(() => sidePaneTabs.value.find(tab => isActiveTab(tab.key)));

const paneWidth = ref(300);
const isResizing = ref(false);
let resizeStartX = 0;
let resizeStartWidth = 0;

function startResize(event) {
  if (event.button !== 0) {
    return;
  }
  resizeStartX = event.clientX;
  resizeStartWidth = paneWidth.value;
  isResizing.value = true;
  event.currentTarget.setPointerCapture(event.pointerId);
  event.preventDefault();
}

function resizePane(event) {
  if (!isResizing.value) {
    return;
  }
  paneWidth.value = Math.min(500, Math.max(200, resizeStartWidth + event.clientX - resizeStartX));
}

function stopResize() {
  isResizing.value = false;
}

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
      padding: 0;
    }
    display: flex;
    flex-direction: column;
    min-height: 0;
    box-sizing: border-box;
    flex-shrink: 0;
    min-width: 200px;
    max-width: 500px;
    transition: max-width .2s ease-in;
    overflow: hidden;
  }

  .pane-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-shrink: 0;
    padding: 8px;
    border-bottom: 1px solid #efeff1;

    h4 {
      margin: 0;
    }
  }

  .pane-content {
    flex: 1;
    min-height: 0;
    padding: 8px;
    overflow: auto;
  }

  .pane-divider {
    flex: 0 0 5px;
    background-color: #efeff1;
    cursor: col-resize;
    touch-action: none;
    user-select: none;

    &:hover, &:focus-visible, &.resizing {
      background-color: slategray;
    }
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
