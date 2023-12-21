<template>
  <h3 class="panel_title">
    {{ chart_options.title }}
  </h3>
  <div style="position: absolute; top: 3px; right: 20px;">
    <span v-if="chart_options.type != 'table'" class="chart-icon" @click="changeChartType('table')"><i class="fas fa-table" /></span>
    <span v-if="chart_options.type != 'pie'" class="chart-icon" @click="changeChartType('pie')"><i class="fas fa-chart-pie" /></span>
    <span v-if="chart_options.type != 'bar'" class="chart-icon" @click="changeChartType('bar')"><i class="fas fa-chart-bar" /></span>
  </div>

  <vue3-chart-js
    v-if="chart_options.type != 'table'"
    :id="chart_options.id"
    ref="chartRef"
    :key="chart_options.type"
    class="chart-or-table"
    :type="chart_options.type"
    :data="chart_options.data"
    :options="chart_options.options"
  />
  <a-table
    v-else
    class="chart-or-table"
    :columns="table_columns"
    :data-source="table_data"
    size="middle"
    style="width: 100%"
  />
</template>

<script>
import Vue3ChartJs from '@j-t-mcc/vue3-chartjs'

export default {
  name: 'KPIChartOrTable',
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
    kpiName: String,
    kpiType: String,
  },
  data() {
    return {
      chart_options: this.changeProps(this.chartOptionsProp),
      chartRef: {},
      table_data: [],
      table_columns: [],
    }
  },
  mounted() {
    this.createTableData();
  },
  methods: {
    changeProps(prop) {
      let co = prop;
      if ('options' in co) {
        co.options.maintainAspectRatio = false;
      }
      return co;
    },
    createTableData() {
      this.table_columns = [];
      this.table_data = [];

      this.table_columns.push({
        title: 'Parameter',
        dataIndex: 'param',
      }, {
        title: 'Value',
        dataIndex: 'value',
      });

      let data = this.chart_options.data;
      for (let i=0; i<data.labels.length; i++) {
        this.table_data.push({
          key: i,
          param: data.labels[i],
          value: data.datasets[0].data[i]
        });
      }
    },
    changeChartType(type) {
      this.createTableData();
      if (type == 'pie' || type == 'doughnut') {
        // for a pie or doughnut chart remove the axis and scales
        delete(this.chart_options.options.scales);
      } else {
        // restore original properties, such that axis and scales can be rendered again
        this.chart_options = this.changeProps(this.chartOptionsProp);
      }
      this.chart_options.type = type;

      // The :key="chart_options.type" has been added to the vue component.
      // The component re-renders when its key changes.
    },
  },
}
</script>

<style>

.panel_title {
    font-weight: bold;
    color: darkblue;
}

.chart-icon i {
  cursor: default;
  color: lightgrey;
  margin: 0px 3px 0px 3px;
}

.chart-or-table {
  overflow: hidden;
  object-fit: contain;
}

</style>