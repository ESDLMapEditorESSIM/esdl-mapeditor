<template>
  <h1>
    KPI Dashboard
  </h1>

  <grid-layout
    v-model:layout="layout"
    :col-num="12"
    :row-height="30"
    is-draggable
    is-resizable
    vertical-compact
    responsive
    use-css-transforms
  >
    <grid-item
      v-for="item in layout"
      :key="item.i"
      :static="item.static"
      :x="item.x"
      :y="item.y"
      :w="item.w"
      :h="item.h"
      :i="item.i"
    >
      <span class="text">{{ itemTitle(item) }}</span>
      <DChart />
    </grid-item>
  </grid-layout>
</template>

<script setup>
import { ref, defineComponent } from 'vue'
import DChart from '../components/kpipanels/DChart.vue'

const layout = ref([
    {"x":0,"y":0,"w":3,"h":5,"i":"0", static: false},
    {"x":3,"y":0,"w":3,"h":5,"i":"1", static: false},
    {"x":6,"y":0,"w":3,"h":5,"i":"2", static: false},
    {"x":0,"y":5,"w":3,"h":5,"i":"3", static: false},
    {"x":3,"y":5,"w":3,"h":5,"i":"4", static: false},
    {"x":6,"y":5,"w":3,"h":5,"i":"5", static: false},
    {"x":0,"y":10,"w":3,"h":5,"i":"6", static: false},
    {"x":3,"y":10,"w":3,"h":5,"i":"7", static: false},
    {"x":6,"y":10,"w":3,"h":5,"i":"8", static: false},
    {"x":0,"y":15,"w":3,"h":5,"i":"9", static: false},
    {"x":3,"y":15,"w":3,"h":5,"i":"10", static: false},
    {"x":6,"y":15,"w":3,"h":5,"i":"11", static: false},
    {"x":0,"y":20,"w":3,"h":5,"i":"12", static: false},
    {"x":3,"y":20,"w":3,"h":5,"i":"13", static: false},
    {"x":6,"y":20,"w":3,"h":5,"i":"14", static: false},
    {"x":0,"y":25,"w":3,"h":5,"i":"15", static: false},
    {"x":3,"y":25,"w":3,"h":5,"i":"16", static: false},
    {"x":6,"y":25,"w":3,"h":5,"i":"17", static: false},
    {"x":0,"y":30,"w":3,"h":5,"i":"18", static: false},
    {"x":3,"y":30,"w":3,"h":5,"i":"19", static: false}
])

const itemTitle = (item) => {
  let result = item.i;
  if (item.static) {
      result += " - Static";
  }
  return result;
}

</script>

<style scoped>

.vue-grid-layout {
  background: #eee;
}

.vue-grid-item:not(.vue-grid-placeholder) {
  background: #ccc;
  border: 1px solid black;
  padding: 5px;
}

.vue-grid-item .resizing {
  opacity: 0.9;
}

.vue-grid-item .static {
  background: #cce;
}

.vue-grid-item .text {
  font-size: 24px;
  text-align: center;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  margin: auto;
  height: 100%;
  width: 100%;
}

.vue-grid-item .no-drag {
  height: 100%;
  width: 100%;
}

.vue-grid-item .minMax {
  font-size: 12px;
}

.vue-grid-item .add {
  cursor: pointer;
}

.vue-draggable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  top: 0;
  left: 0;
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><circle cx='5' cy='5' r='5' fill='#999999'/></svg>")
    no-repeat;
  background-position: bottom right;
  padding: 0 8px 8px 0;
  background-repeat: no-repeat;
  background-origin: content-box;
  box-sizing: border-box;
  cursor: pointer;
}

</style>