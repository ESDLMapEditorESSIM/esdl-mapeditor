<template>
  <span>
    {{ chart_options.title }}
  </span>
  <div style="position: absolute; top: 3px; right: 3px;">
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
</template>

<script>
// import { ref } from 'vue'
import Vue3ChartJs from '@j-t-mcc/vue3-chartjs'

// const chartRef = ref(null);

export default {
  name: 'JSChart',
  components: {
    Vue3ChartJs,
  },
  props: {
    chartOptionsProp: {
      type: Object,
      default: function() {
        return {};
      }
    },
  },
  data() {
    return {
      chart_options: this.changeProps(this.chartOptionsProp),
      chartRef: {}
    }
  },
  methods: {
    changeProps(prop) {
      let co = prop;
      if ('options' in co) {
        co.options.maintainAspectRatio = false;
      }
      return co;
    },
    changeToPieChart() {
      this.chart_options.options.type = "pie";
      this.chartRef.update(250);
    }
  },
}
</script>