<template>
  <div style="width: 100%; height: 100%;">
    <a-row class="panel-header vue-draggable-handle">
      <h5 class="panel-title">{{ plot.title }}</h5>
      <a-button 
        type="text"
        class="panel-header-icon-btn"
        @click="onPlotTypeBtnClick"
      >
        <template #icon>
          <component :is="plotTypeIcon" />
        </template>
      </a-button>
      <a-button 
        type="text" 
        class="panel-header-icon-btn"
        @click="emit('onRemove')"
      >
        <template #icon>
          <CloseOutlined />
        </template>
      </a-button>
    </a-row>
    <a-row class="panel-plot-container no-drag">
      <Plot
        :title="plot.title"
        :trace="plot.trace"
        :layout="plotLayout"
        :on-resize="resizeEventCounter"
      />
    </a-row>
  </div>
</template>
  
<script setup>
import { defineProps, ref, computed, watch } from "vue";
import Plot from "./Plot.vue";
import { CloseOutlined, PieChartOutlined, BarChartOutlined, TableOutlined } from "@ant-design/icons-vue";

const plotTypes = ["bar", "pie", "table"];

// Initialize the plot panel with the bar chart type.
const plotType = ref(plotTypes[0]);
const plotTypeIcon = ref(PieChartOutlined);

const props = defineProps({
  // config of the graph with structure as
  // {title: string, type: string, options: Object, data: Object}
  options: {
    type: Object,
    default: function () {
      return {};
    }
  },
  panelDimension: {
    type: Object,
    default: function () {
      return {};
    }
  },
});

const resizeEventCounter = ref(0);

const emit = defineEmits(["onRemove"]);

/**
 * Listens to the panelDimension prop state update
 * and triggers the child Plot component to resize the chart.
 */
watch(
  () => props.panelDimension,
  () => {
    resizeEventCounter.value += 1;
  }
);

/**
 * Handles the click event for the plot type button.
 */
const onPlotTypeBtnClick = () => {
  switch (plotType.value) {
    default:
    case "bar":
      plotType.value = "pie";
      plotTypeIcon.value = TableOutlined;
      break;
    case "pie":
      plotType.value = "table";
      plotTypeIcon.value = BarChartOutlined;
      break;
    case "table":
      plotType.value = "bar";
      plotTypeIcon.value = PieChartOutlined;
      break;
  }
};

/**
 * Sorts data object alphabetically by data.labels and returns a new data object.
 * 
 * @param {Object} data Plot data object.
 * @returns {Object} Sorted plot data object.
 */
const sortDataAlphabetically = (data) => {
  const combined = data.labels.map((label, index) => (
    {
      label: label,
      data: data.datasets.map(d => d.data[index])
    }
  ));

  // Sort the combined array alphabetically by label
  combined.sort((a, b) => String(a.label).localeCompare(String(b.label)));

  // Deepy copy data object
  const sortedData = JSON.parse(JSON.stringify(data));
  sortedData.labels = combined.map(item => item.label);
  sortedData.datasets.forEach((dataset, dIndex) => {
    dataset.data = combined.map(item => item.data[dIndex]);
  });

  return sortedData;
};

/**
 * Create a Plot properties object required by the Plot component.
 * 
 * @param {string} plotType Plot type.
 * @param {string} title Plot title.
 * @param {Object} data Plot data object.
 * @returns {Object} Plot properties object required by the Plot component.
 */
const createPlotProps = (plotType, title, data) => {
  // TODO: use the config setting to enable/disable sorting on data labels.
  // const sortedData = sortDataAlphabetically(data);

  let trace = [];
  switch (plotType) {
    default:
    case "bar":
      trace = createBarChartTrace(data);
      break;
    case "pie":
      trace = createPieChartTrace(data);
      break;
    case "table":
      trace = createTableTrace(data);
      break;
  }

  return {
    title: title,
    trace: trace,
  };
};

const plotLayout = computed(() => {
  if (plotType.value === 'bar') {
    const yTitle = props.options.options?.scales?.y?.title;
    if (yTitle?.display && yTitle?.text) {
      return { yaxis: { title: yTitle.text } };
    }
  }
  return {};
});

const plot = computed(() => {
  if (Object.keys(props.options).length && 
      props.options.title && 
      Object.keys(props.options.data).length) {
    return createPlotProps(plotType.value, props.options.title, props.options.data);
  } else {
    console.error("Error while creating a plot, default setting will be applied.");
    return {
      title: "Undefined plot title",
      trace: []
    };
  }
});

// NOTE: The three create{PlotType}Trace functions below 
// only support creating a single data-trace at the moment.
const createBarChartTrace = (data) => {
  return [{
    type: "bar",
    name: data.datasets[0].label,
    x: data.labels,
    y: data.datasets[0].data
  }];
};

const createPieChartTrace = (data) => {
  // pie_chart_color_list is defined in area_building_layer.js
  const pieChartColors = pie_chart_color_list;

  return [{
    type: "pie",
    name: data.datasets[0].label,
    labels: data.labels,
    values: data.datasets[0].data,
    automargin: true,
    sort: false,
    direction: "clockwise",
    marker: {
      colors: pieChartColors
    },
    opacity: 0.9
  }];
};

const createTableTrace = (data) => {
  const headerValues = [["<b>Parameter</b>"], ["<b>Value</b>"]];
  const cellValues = [data.labels, data.datasets[0].data.map((d) => [d])];

  return [{
    type: "table",
    header: {
      values: headerValues,
      align: "left",
      fill: {color: "#fafafa"},
      line: {width: 0.5, color: "#c4c4c4"},
      font: {size: 14, color: "black"}
    },
    cells: {
      values: cellValues,
      align: "left",
      height: 25,
      line: {width: 0.5, color: "#c4c4c4"},
      font: {size: 14, color: "black"}
    }
  }];
};

</script>

<style>
.panel-header {
  margin: 0;
  height: 35px;
  width: 100%;
  flex-direction: row;
  background-color: #f1f1f196;
}

.panel-header:hover {
  background-color: #f5f5f5e8;
}

.panel-plot-container {
  /* height of the plot container = 100% - panel-header height (35px) */
  height: calc(100% - 35px);
}

.panel-header-icon-btn {
  right: 5px;
  color: #363636;
}

.panel-title {
  font-size: 1.1em;
  width: 70%;
  margin: 0;
  padding: 0.5rem;
  color: #363636;
  font-weight: bolder;
  flex-grow: 1;
}
</style>