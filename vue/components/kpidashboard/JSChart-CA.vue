<template>
  <div v-if="chart_options">
    <h3>
      {{ chart_options.title }}
    </h3>
    <div style="position: absolute; top: 3px; right: 20px;">
      <a-button @click="changeToPieChart">Pie</a-button>
    </div>
    <div style="position: relative; height: 90%; width: 90%;">
      <vue3-chart-js
        :id="chart_options.id"
        ref="chartRef"
        :type="chart_options.type"
        :data="chart_options.data"
        :options="chart_options.options"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, watch } from 'vue'
import Vue3ChartJs from '@j-t-mcc/vue3-chartjs'

const chartRef = ref(null);

const props = defineProps({
  chartOptionsProp: {
    type: Object,
    default: function() {
      return {};
    }
  },
});

const changeProps = (prop) => {
  if ('options' in prop) {
    prop.options.maintainAspectRatio = false;
  }
  return prop;
}
var chart_options = ref({});

watch(() => props.chartOptionsProp, (prop_value, prev_prop_value) => {
  chart_options.value = changeProps(prop_value);
});

const changeToPieChart = () => {
  chart_options.value.type = "pie";
  chartRef.value.update(250);
}

</script>