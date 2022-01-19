<template>
  <h3 class="panel_title">
    {{ options.title }}
  </h3>
  <div style="position: absolute; top: 3px; right: 20px;">
    <span class="settings" @click="showTextSettings"><i class="fas fa-edit" /></span>
  </div>
  <div style="position: relative; height: 90%; width: 90%;">
    <div class="chart">
      <canvas id="chart" />
    </div>
  </div>

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
import {Chart} from 'chart.js';
import {SankeyController, Flow} from 'chartjs-chart-sankey';

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
  var ctx = document.getElementById("chart").getContext("2d");

  var colors = {
    Import: "gray",
    PVInstallation: "green",
    HeatingDemand: "red",
    GenericProducer: "black",
    Battery: "blue",
    ElectricityNetwork: "orange",
    GasHeater: "purple"
  };

  function getColor(name) {
    return colors[name] || "green";
  }

  new Chart(ctx, {
    type: "sankey",
    data: {
      datasets: [
        {
          data: [
            { from: "GenericProducer", to: "GasHeater", flow: 7.5 },
            { from: "GasHeater", to: "HeatingDemand", flow: 6.7 },
            { from: "HeatPump", to: "HeatingDemand", flow: 43.3 },
            { from: "PVInstallation", to: "ElectricityNetwork", flow: 50 },
            { from: "Import", to: "ElectricityNetwork", flow: 1 },
            { from: "ElectricityNetwork", to: "Battery", flow: 40.2 },
            { from: "ElectricityNetwork", to: "HeatPump", flow: 10.8 },
          ],
          colorFrom: c => getColor(c.dataset.data[c.dataIndex].from),
          colorTo: c => getColor(c.dataset.data[c.dataIndex].to)
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
}

.settings i {
  color: lightgrey;
}

</style>