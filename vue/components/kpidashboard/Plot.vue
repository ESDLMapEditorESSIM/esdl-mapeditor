<template>
  <div v-show="trace.length" id="plot-container" ref="plotContainer" />
  <div v-show="trace.length === 0" class="no-data">Not configured</div>
</template>

<script setup>
import { defineProps, ref, onMounted, watch } from "vue";
import Plotly from "plotly.js-dist";

const plotContainer = ref(null);

const props = defineProps({
  trace: {
    type: Array,
    default: function () {
      return [];
    }
  },
  // TODO: rename?
  onResize: {
    type: Number,
    default: 0
  }
});

const config = { 
  responsive: true, 
  maintainAspectRatio: true,
  automargin: true,
  toImageButtonOptions: {
    format: 'png', // one of png, svg, jpeg, webp
    height: 500,
    width: 900,
    scale: 1 // Multiply title/legend/axis/canvas sizes by this factor
  }
};

const layout = {
  responsive: true,
  autosize: true,
  margin: {l: 25, t: 5, r: 25, b: 25},
  yaxis: {
    automargin: true
  },
  xaxis: {
    automargin: true
  }
};

const createPlot = () => {
  Plotly.newPlot(plotContainer.value, props.trace, layout, config);
};

const resizePlot = () => {
  Plotly.react(plotContainer.value, props.trace, layout, config);
};

// TODO: doc.
onMounted(() => {
  setTimeout(() => {
    createPlot();
  }, 10);
});

// TODO: doc.
watch(
  () => props.trace,
  () => {
    createPlot();
  }
);

// TODO: doc.
watch(
  () => props.onResize,
  () => {
    resizePlot();
  }
);
</script>

<style>
#plot-container {
  width: 100%;
  /* TODO: */
  height: 250px;
}

.no-data {
    height: 100%;
    display: flex;
    flex-grow: auto;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-size: 20pt;
    color: grey;
    font-style: italic;
    border: solid 3px lightgrey;
    border-radius: .5rem;
    margin: 1rem;
}
</style>