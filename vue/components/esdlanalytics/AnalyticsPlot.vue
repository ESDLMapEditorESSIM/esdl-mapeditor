<template>
  <div v-show="trace.length === 0" class="no-data">Not configured</div>
  <div v-show="trace.length" class="with-data">
    <div id="plot" ref="plotDiv" class="plotly-plot" />
  </div>
</template>

<script setup>
import {
  ref,
  defineProps,
  onMounted,
  onUpdated,
  reactive
} from "vue";
import Plotly from "plotly.js-dist";

const props = defineProps({
	trace: {
		type: Array,
		default: function () {
			return [];
		}
	},
	layout: {
		type: Object,
		default: function () {
			return {};
		}
	}
});

const plotDiv = ref(null);

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

let resizeObserver = null;
const plotDimensions = reactive({ width: 0 });

/**
 * Resizes plot layout when the plotDiv dimensions are updated.
 */
const resizePlot = (entries) => {
	if (plotDiv.value && entries.length) {
		const entry = entries[0];
		plotDimensions.width = entry.contentRect.width;

		const layout = {
			...props.layout,
			width: plotDimensions.width
		};

		Plotly.react(plotDiv.value, props.trace, layout, config);
	}
};

onMounted(() => {
	if (resizeObserver === null) {
		resizeObserver = new ResizeObserver(resizePlot);
		resizeObserver.observe(plotDiv.value);
	}

	Plotly.newPlot(plotDiv.value, props.trace, props.layout, config);
});

onUpdated(() => {
	Plotly.react(plotDiv.value, props.trace, props.layout, config);
});

const unmountPlot = () => {
	console.debug("Clean up Plot and ResizeObserver");
	if (resizeObserver !== null) {
		resizeObserver.unobserve(plotDiv.value);
		resizeObserver = null;
	}

	if (plotDiv.value) {
		Plotly.purge(plotDiv.value);
		plotDiv.value = null;
	}
};

$(document).on('esdlAnalyticsIsClosed', (_, data) => {
	if (data) {
		unmountPlot();
	}
});
</script>

<style>
.plotly-plot {
  width: 100%;
	height: 90%;
}

.with-data {
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: space-between;
  border: 1px solid rgba(100, 100, 100, 0.15);
	border-radius: .5rem;
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
    border: 1px solid rgba(100, 100, 100, 0.15);
    border-radius: .5rem;
}
</style>