<template>
  <div>
    <h3 class="panel_title">
      {{ options.title }}
    </h3>
    <span class="settings" @click="showTextSettings"><i class="fas fa-edit" /></span>
  </div>
  <canvas :id="chart_id" class="sankey-chart-div" />

  <a-modal v-model:visible="sankey_settings_visible" title="Edit text" width="750px" @ok="handleOk">
    <a-row>
      <a-col :span="4">
        <span>Title:</span>
      </a-col>
      <a-col :span="20">
        <a-input v-model:value="options.title" />
      </a-col>
    </a-row>
  </a-modal>
</template>

<script setup>
import { ref, defineProps, defineEmit, onMounted } from 'vue'
import { Chart } from 'chart.js';
import { SankeyController, Flow } from 'chartjs-chart-sankey';

Chart.register(SankeyController, Flow);

const sankey_settings_visible = ref(false);

const props = defineProps({
  options: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

// Randomly create an id, so that multiple panels can be used.
const chart_id = ref('chart' + window.uuidv4().substring(0,4));

const emit = defineEmit(['updateSankeySettings']);

// eslint-disable-next-line no-unused-vars
const showSankeySettings = () => {
  sankey_settings_visible.value = true;
}

// eslint-disable-next-line no-unused-vars
const handleOk = () => {
  sankey_settings_visible.value = false;
  emit('updateSankeySettings', props.options);
}

const createSankey = () => {
  let ctx = document.getElementById(chart_id.value).getContext("2d");

  let colors = ["green", "red", "blue", "orange", "purple", "yellow", "gray", "black", "brown"];

  function getColor(nr) {
    return colors[nr % colors.length];
  }

  new Chart(ctx, {
    type: "sankey",
    data: {
      datasets: [
        {
          data: props.options.data,
          colorFrom: c => getColor(c.dataIndex),
          colorTo: c => getColor(c.dataIndex),
          colorMode: 'gradient',
        }
      ]
    }
  });
}

onMounted(() => {
  createSankey();
});

</script>

<style>

.panel_title {
    font-weight: bold;
    color: darkblue;
}

.settings {
  cursor: default;
  position: absolute;
  top: 3px;
  right: 20px;
}

.settings i {
  color: lightgrey;
}

.sankey-chart-div {
  overflow: hidden;
  object-fit: contain;
}

</style>