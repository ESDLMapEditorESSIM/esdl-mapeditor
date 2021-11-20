<template>
  <span>
    {{ chart_options.title }}
  </span>
  <div style="position: relative; height: 95%; width: 95%;">
    <vue3-chart-js
      :id="chart_options.id"
      :type="chart_options.type"
      :data="chart_options.data"
      :options="chart_options.options"
      @before-render="beforeRenderLogic"
    />
  </div>
</template>

<script>
import Vue3ChartJs from '@j-t-mcc/vue3-chartjs'

const default_chart_options = {
  id: 'doughnut',
  type: 'doughnut',
  data: {
    labels: ['VueJs', 'EmberJs', 'ReactJs', 'AngularJs'],
    datasets: [
      {
        backgroundColor: [
          '#41B883',
          '#E46651',
          '#00D8FF',
          '#DD1B16'
        ],
        data: [40, 20, 80, 10]
      }
    ]
  },
  options: {
    plugins: {
      legend: {
        position: 'right'
      }
    },
    maintainAspectRatio: false
  }
}

export default {
  name: 'JSChart',
  components: {
    Vue3ChartJs,
  },
  props: {
    chart_options_prop: {
      type: Object,
      default: function() {
        return {};
      }
    },
  },
  computed: {
    chart_options() {
      if (this.chart_options_prop) {
        return this.chart_options_prop;
      } else {
        return default_chart_options;
      }
    }
  },
  setup () {
    const beforeRenderLogic = (event) => {
      //...
    }

    return {
      beforeRenderLogic
    }
  },
}
</script>