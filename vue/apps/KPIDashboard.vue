<template>
  <h1>
    KPI Dashboard - {{ dashboard_config.name }}
  </h1>
  <a-space>
    <load-dashboard
      :dashboards-info="dashboards_info"
      :dashboard-id="dashboard_config.id"
      @update:dashboardID="handleLoadDashboard"
    />
    <save-dashboard
      :dashboards-info="dashboards_info"
      @handle-save="handleSaveDashboard"
    />
  </a-space>
  <grid-layout
    v-model:layout="layout"
    :col-num="12"
    :row-height="30"
    is-draggable
    is-resizable
    vertical-compact
    responsive
    use-css-transforms
  >
    <grid-item
      v-for="item in layout"
      :key="item.i"
      :x="item.x"
      :y="item.y"
      :w="item.w"
      :h="item.h"
      :i="item.i"
    >
      <JSChart :chart_options_prop="item.chart_options" />
    </grid-item>
  </grid-layout>
</template>

<script setup>
import { ref, defineComponent } from 'vue'
import JSChart from '../components/kpidashboard/JSChart.vue'
import LoadDashboard from '../components/kpidashboard/LoadDashboard.vue'
import SaveDashboard from '../components/kpidashboard/SaveDashboard.vue'

const dashboards_info = ref([]);
const layout = ref([]);

const dashboard_config = ref({
  id: '',
  name: 'New dashboard',
  group: '',
  layout: layout.value,
});

const getDashboardList = async () => {
  const response = await fetch("kpi_dashboards");
  if (response.ok) {
    const data = await response.json();
    dashboards_info.value = data;
    console.log(data);
  } else {
    // TODO: Handle error
  }
};
getDashboardList();

const getAllKPIData = () => {
  let all_kpi_data = window.get_all_kpi_info();
  let kpi_data = window.kpis.preprocess_all_kpis(all_kpi_data);
  // console.log(kpi_data);

  let kpi_nr = 0;
  for (let kpi_name in kpi_data) {
    let kpi_info = kpi_data[kpi_name];
    let chart_options = window.createChartOptions(kpi_info);
    chart_options.title = kpi_name;

    layout.value.push({
      x: (kpi_nr % 3) * 3,
      y: Math.floor(kpi_nr / 3) * 5,
      w: 3,
      h: 5,
      i: kpi_nr,
      type: chart_options.type,
      chart_options: chart_options
    });

    kpi_nr = kpi_nr + 1;
  }
};
getAllKPIData();

const load_db_with_id = ref("");

const handleLoadDashboard = (dashboard_id) => {
  console.log(dashboard_id);

  window.socket.emit('kpi_dashboard_load', {dashboard_id: dashboard_id}, function(response) {
    if (response) {
      console.log(response);
      dashboard_config.value = response;
      layout.value = response.layout;       // TODO: any better way?
    } else {
      console.log('Error: empty response');
    }
  });
}

const handleSaveDashboard = (res) => {
  console.log(res);

  dashboard_config.value.id = res.id;
  dashboard_config.value.name = res.name;
  dashboard_config.value.group = res.group;

  window.socket.emit('kpi_dashboard_save', dashboard_config.value);
}

</script>

<style scoped>

.vue-grid-layout {
  background: #fff;
}

.vue-grid-item:not(.vue-grid-placeholder) {
  background: #fff;
  border: 1px solid #ccc;
  padding: 5px;
}

.vue-grid-item .resizing {
  opacity: 0.9;
}

.vue-grid-item .static {
  background: #cce;
}

.vue-grid-item .text {
  font-size: 24px;
  text-align: center;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  margin: auto;
  height: 100%;
  width: 100%;
}

.vue-grid-item .no-drag {
  height: 100%;
  width: 100%;
}

.vue-grid-item .minMax {
  font-size: 12px;
}

.vue-grid-item .add {
  cursor: pointer;
}

.vue-draggable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  top: 0;
  left: 0;
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'><circle cx='5' cy='5' r='5' fill='#999999'/></svg>")
    no-repeat;
  background-position: bottom right;
  padding: 0 8px 8px 0;
  background-repeat: no-repeat;
  background-origin: content-box;
  box-sizing: border-box;
  cursor: pointer;
}

</style>