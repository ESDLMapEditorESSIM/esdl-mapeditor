<template>
  <div v-show="trace.length === 0" class="no-analytics-data">{{ props.plotMessage || "Not configured" }}</div>
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
	},
	plotMessage: {
		type: String,
		default: ""
	}
});

const emit = defineEmits(['onRelayout']);

const plotDiv = ref(null);

const config = { 
	responsive: true,
	maintainAspectRatio: true,
	automargin: true,
	toImageButtonOptions: {
		format: 'svg', // one of png, svg, jpeg, webp
		// height: 500,
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
	config.toImageButtonOptions['filename'] = props.layout?.title?.text || "Untitled chart";
	Plotly.newPlot(plotDiv.value, props.trace, props.layout, config);

	plotDiv.value.on('plotly_relayout', (eventData) => {
		// Only update newLayoutRanges when zoom in/out or pan on subset of data
		let newLayoutRanges = null;

		if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
			newLayoutRanges = { x: [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']] };

			// Check for any y-axis ranges dynamically; and optionally add y ranges
			const yRanges = Object.keys(eventData).filter(key => key.startsWith('yaxis') && key.includes('range'));
			if (yRanges.length > 1) {
				newLayoutRanges['y'] = yRanges.map(rangeKey => eventData[rangeKey]);
			}
		}
		emit('onRelayout', newLayoutRanges)
	})
});

onUpdated(() => {
	config.toImageButtonOptions['filename'] = props.layout?.title || "Untitled chart";
	Plotly.react(plotDiv.value, props.trace, props.layout, config);
});

const unmountPlot = () => {
	console.debug("Clean up Plot and ResizeObserver");
	if (resizeObserver !== null) {
		if (plotDiv.value) {
			resizeObserver.unobserve(plotDiv.value);
			Plotly.purge(plotDiv.value);
			plotDiv.value = null;
		}
		resizeObserver = null;
	}
};

// Listens to esdlAnalyticsIsClosed or kpiDashboardIsClosed events emitted from esdl_analytics.js or KPIDashboard.js
// to ensure the Plotly plot is properly cleaned up after closing instead of only becoming invisible 
// (default behavior of the Leaflet Control Dialog).
$(document).on("esdlAnalyticsIsClosed kpiDashboardIsClosed", (_, data) => {
	if (data) {
		unmountPlot();
	}
});
</script>

<style>
.plotly-plot {
	height: 90%;
}

.with-data {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  justify-content: space-between;
  border: 1px solid rgba(100, 100, 100, 0.15);
	border-radius: .5rem;
}

.no-analytics-data {
	height: 100%;
	width: 100%;
	display: flex;
	flex-grow: auto;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	font-size: 16pt;
	color: grey;
	border: 1px solid rgba(100, 100, 100, 0.15);
	border-radius: .5rem;
}
</style>