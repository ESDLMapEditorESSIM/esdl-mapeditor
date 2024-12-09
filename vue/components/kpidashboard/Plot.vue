<template>
  <div v-if="trace.length" :id="plotId" ref="plotDiv" class="plot-div" />
  <div v-else class="no-data">Not configured</div>
</template>

<script setup>
import { defineProps, ref, onMounted, onUnmounted, watch } from "vue";
import Plotly from "plotly.js-dist";

const props = defineProps({
  title: {
    type: String,
    default: "Undefined plot title"
  },
  trace: {
    type: Array,
    default: function () {
      return [];
    }
  },
  onResize: {
    type: Number,
    default: 0
  }
});

const plotDiv = ref(null);
const plotIsMounted = ref(false);

const plotId = `plot-${props.title}`;

const layout = {
  responsive: true,
  autosize: true,
  margin: {l: 25, t: 20, r: 25, b: 25},
  yaxis: {
    automargin: true
  },
  xaxis: {
    automargin: true
  }
};

const config = { 
  toImageButtonOptions: {
    format: 'png', // one of png, svg, jpeg, webp
    filename: props.title,
    height: 500,
    width: 900,
    scale: 1 // Multiply title/legend/axis/canvas sizes by this factor
  }
};

/**
 * Creates a new plot in the plotDiv container.
 */
const createPlot = () => {
  Plotly.newPlot(plotDiv.value, props.trace, layout, config);
};

/**
 * Initializes the plot and updates plotIsMounted state.
 */
onMounted(() => {
  createPlot();
  plotIsMounted.value = true;
});

/**
 * Listens to the trace prop state update (e.g. switching between plot types) 
 * and triggers createPlot().
 */
watch(
  () => props.trace,
  () => {
    if (plotIsMounted.value) {
      createPlot();
    }
  }
);

/**
 * Triggers Plotly react method to update the existing plot using the new plot parent container height.
 */
 const resizePlot = () => {
  if (plotIsMounted.value) {
    const newPlotContainerHeight = document.getElementById(plotId).parentElement.offsetHeight;
    layout.height = newPlotContainerHeight;
    Plotly.react(plotDiv.value, props.trace, layout, config);
  }
};

/**
 * Listens to the onResize prop state update and triggers resizePlot().
 */
watch(
  () => props.onResize,
  () => resizePlot()
);

/**
 * Reset to the default state when onUnmounted.
 */
onUnmounted(() => {
  plotDiv.value = null;
  plotIsMounted.value = false;
});

// Listens to the kpiDashboardIsClosed event emitted from KPIDashboard.js
// to ensure the Plotly plot is cleaned up after the kpi_dashboard_window div closed 
// instead of only becoming invisible (default behavior of the Leaflet Control Dialog).
$(document).on('kpiDashboardIsClosed', (_, data) => {
  if (data && plotIsMounted.value) {
    Plotly.purge(document.getElementById(plotId));
    plotIsMounted.value = false;
  }
});

</script>

<style>
.plot-div {
  width: 100%;
}

.no-data {
  width: 100%;
  height: 90%;
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