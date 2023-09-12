<template>
  <a-row>
    <a-col span="20">
      <h1>
        KPI Dashboard - {{ dashboard_config.name.value }}
      </h1>
    </a-col>
    <a-col span="4">
      <a-space style="float: right">
        <load-dashboard
          :dashboards-info="dashboards_info"
          :dashboard-id="dashboard_config.id.value"
          @update:dashboardId="handleLoadDashboard"
        />
        <load-dashboard
          :dashboards-info="dashboards_info"
          :dashboard-id="dashboard_config.id.value"
          load-dashboard-icon="fas fa-paint-brush"
          load-dashboard-title="Load dashboard template"
          load-dashboard-text="Select the existing dashboard configuration that is used as a template for the current data"
          @update:dashboardId="handleLoadDashboardTemplate"
        />
        <save-dashboard
          :dashboards-info="dashboards_info"
          :dashboard-id="dashboard_config.id.value"
          @handle-save="handleSaveDashboard"
        />

        <div class="demo-dropdown-wrap">
          <a-dropdown :trigger="['click']" placement="bottomRight">
            <a-button type="primary">
              <i class="fas fa-plus" />
            </a-button>
            <template #overlay>
              <a-menu @click="handleAddPanel">
                <a-menu-item key="Text">
                  Add Text panel
                </a-menu-item>
                <a-menu-item key="Image">
                  Add Image panel
                </a-menu-item>
                <a-menu-item key="Title">
                  Add Title panel
                </a-menu-item>
                <a-menu-item key="Sankey">
                  Add Sankey panel
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-space>
    </a-col>
  </a-row>
  <div
    v-if="layout.length"
  >
    <grid-layout
      :key="dashboard_config.id.value"
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
        <span class="remove" @click="removeItem(item.i)"><i class="fas fa-times" /></span>
        <KPIChartOrTable
          v-if="item.type == 'charttable'"
          :key="item.kpi_type"
          :chart-options-prop="item.options"
          :kpi-name="item.kpi_name"
          :kpi-type="item.kpi_type"
        />
        <TextPanel
          v-if="item.type == 'textpanel'"
          :options="item.options"
        />
        <ImagePanel
          v-if="item.type == 'imagepanel'"
          :options="item.options"
        />
        <TitlePanel
          v-if="item.type == 'titlepanel'"
          :options="item.options"
        />
        <SankeyPanel
          v-if="item.type == 'sankeypanel'"
          :options="item.options"
        />
      </grid-item>
    </grid-layout>
  </div>
  <div v-else>
    <a-card>
      No dashboard loaded yet
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
// eslint-disable-next-line no-unused-vars
import KPIChartOrTable from '../components/kpidashboard/KPIChartOrTable.vue'
// eslint-disable-next-line no-unused-vars
import TextPanel from '../components/kpidashboard/TextPanel.vue'
// eslint-disable-next-line no-unused-vars
import TitlePanel from '../components/kpidashboard/TitlePanel.vue'
// eslint-disable-next-line no-unused-vars
import ImagePanel from '../components/kpidashboard/ImagePanel.vue'
// eslint-disable-next-line no-unused-vars
import SankeyPanel from '../components/kpidashboard/SankeyPanel.vue'
// eslint-disable-next-line no-unused-vars
import LoadDashboard from '../components/kpidashboard/LoadDashboard.vue'
// eslint-disable-next-line no-unused-vars
import SaveDashboard from '../components/kpidashboard/SaveDashboard.vue'

const dashboards_info = ref([]);
const layout = ref([]);     // this is the information used (and changed!) in the vue components

var new_panel_id = 0;  // to store the id that new panels should use

const dashboard_config = {
  id: ref(''),
  name: ref('New dashboard'),
  group: ref(''),
  layout: ref([]),     // this is the information stored as settings in the database
};

const getDashboardList = async () => {
  const response = await fetch("kpi_dashboards");
  if (response.ok) {
    const data = await response.json();
    dashboards_info.value = data;
  } else {
    // TODO: Handle error
  }
};
getDashboardList();

const getAllKPIData = () => {
  let all_kpi_data = window.get_all_kpi_info();
  let kpi_data = window.kpis.preprocess_all_kpis(all_kpi_data);
  console.log(kpi_data);

  let kpi_nr = 0;     // TODO: do we need to seperate kpi_nr and new_panel_id? Add panels to existing dashboard?
  for (let kpi_name in kpi_data) {
    let kpi_info = kpi_data[kpi_name];
    if (kpi_info[0]['type'] == 'Sankey') {
      layout.value.push({
        x: (kpi_nr % 3) * 3,
        y: Math.floor(kpi_nr / 3) * 5,
        w: 3,
        h: 5,
        i: new_panel_id,
        type: 'sankeypanel',
        options: {
          'title': kpi_name,
          'data': kpi_info[0]['flows'],
        },
      });
    } else {
        let chart_options = window.createChartOptions(kpi_info);
        chart_options.title = kpi_name;

        layout.value.push({
          x: (kpi_nr % 3) * 3,
          y: Math.floor(kpi_nr / 3) * 5,
          w: 3,
          h: 5,
          i: new_panel_id,
          type: 'charttable',
          options: chart_options,
          kpi_name: kpi_name,
          kpi_type: kpi_info.type
        });
    }

    kpi_nr = kpi_nr + 1;
    new_panel_id = new_panel_id + 1;
  }
  dashboard_config.layout.value = [...layout.value];
};
getAllKPIData();

// eslint-disable-next-line no-unused-vars
const handleLoadDashboard = (dashboard_id) => {
  window.socket.emit('kpi_dashboard_load', {dashboard_id: dashboard_id}, function(response) {
    if (response) {
      layout.value = [];
      layout.value = response.layout;
      dashboard_config.id.value = response.id;
      dashboard_config.name.value = response.name;
      dashboard_config.group.value = response.group;
      dashboard_config.layout.value = response.layout;

      for (let i=0; i<layout.value.length; i++) {
        if (layout.value[i].i >= new_panel_id) {
          new_panel_id = layout.value[i].i + 1;
        }
      }
    } else {
      console.log('Error: empty response');
    }
  });
}

const findTemplatePanelInData = (template_panel, layout) => {
  for (let i in layout) {
    let panel = layout[i];
    if ('kpi_name' in panel && 'kpi_name' in template_panel && panel['kpi_name'] == template_panel['kpi_name']) {
      panel.x = template_panel.x;
      panel.y = template_panel.y;
      panel.w = template_panel.w;
      panel.h = template_panel.h;
      panel.type = template_panel.type;
      panel.chart_options = template_panel.chart_options; // TODO: chart type doesn't seem to work yet
      return true;
    }
  }
  return false;
}

const addTemplatePanelToDashboard = (template_panel, layout) => {
  console.log(template_panel);
}

const handleLoadDashboardTemplate = (dashboard_id) => {
  window.socket.emit('kpi_dashboard_load', {dashboard_id: dashboard_id}, function(response) {
    if (response) {
      // layout.value = [];
      // layout.value = response.layout;
      // dashboard_config.id.value = response.id;
      // dashboard_config.name.value = response.name;
      // dashboard_config.group.value = response.group;
      // dashboard_config.layout.value = response.layout;

      // for (let i=0; i<layout.value.length; i++) {
      //   if (layout.value[i].i >= new_panel_id) {
      //     new_panel_id = layout.value[i].i + 1;
      //   }
      // }

      let template_layout = response.layout;

      for (let i in template_layout) {
        let template_panel = template_layout[i];
        let found = findTemplatePanelInData(template_panel, layout.value);
        if (!found) {
          addTemplatePanelToDashboard(template_panel, layout.value);
        }
      }

    } else {
      console.log('Error: empty response');
    }
  });
}

// To keep the dashboard information in the vue component and in the database settings in sync
// Assume order in layout array doesn't change...     Maybe add id to panel data, use i attribute?
const copyDashboardLayoutToSettings = () => {
  for (let i=0; i<layout.value.length; i++) {
    if (dashboard_config.layout.value[i].i != layout.value[i].i) {
      console.log('ERROR: Dashboard panel IDs are not the same!');
    } else {
      // Why is the following true???
      // dashboard_config.layout.value[i] contains changes in options (for the jschart component)
      // layout.value[i] contains changes in basic attributes (x, y, w, h, ...)
      dashboard_config.layout.value[i].x = layout.value[i].x;
      dashboard_config.layout.value[i].y = layout.value[i].y;
      dashboard_config.layout.value[i].w = layout.value[i].w;
      dashboard_config.layout.value[i].h = layout.value[i].h;
      dashboard_config.layout.value[i].type = layout.value[i].type;
      if (dashboard_config.layout.value[i].type != 'charttable') {
        // Don't copy JSChart config as JSChart completely changes the config during visualisation
        dashboard_config.layout.value[i].options = layout.value[i].options;
      } else {
        // Only copy the chart/table type
        // dashboard_config.layout.value[i].options.type = layout.value[i].options.type;
        // copy the other way around???
        layout.value[i].options.type = dashboard_config.layout.value[i].options.type;
      }
    }
  }
}

// eslint-disable-next-line no-unused-vars
const handleSaveDashboard = (res) => {
  copyDashboardLayoutToSettings();

  dashboard_config.id.value = res.id;
  dashboard_config.name.value = res.name;
  dashboard_config.group.value = res.group;

  let message = {
    id: res.id,
    name: res.name,
    group: res.group,
    layout: dashboard_config.layout.value
  };

  window.socket.emit('kpi_dashboard_save', message);
}

// eslint-disable-next-line no-unused-vars
const removeItem = (item_index) => {
  // Note: the item.i doesn't necessarily
  const index = layout.value.map(item => item.i).indexOf(item_index);
  layout.value.splice(index, 1);

  const db_index = dashboard_config.layout.value.map(item => item.i).indexOf(item_index);
  dashboard_config.layout.value.splice(db_index, 1);
}

const findFreeRow = () => {
  let free_row_nr = 0;
  for (let i=0; i<layout.value.length; i++) {
    if (layout.value[i].y + layout.value[i].h > free_row_nr) {
      free_row_nr = layout.value[i].y + layout.value[i].h;
    }
  }
  return free_row_nr;
}

const addTextPanel = () => {
  let panel_config = {
    x: 0,
    y: findFreeRow(),
    w: 3,
    h: 5,
    i: new_panel_id,
    type: 'textpanel',
    options: {
      'title': 'New title',
      'text': 'New text',
    }
  };
  layout.value.push(panel_config);
  dashboard_config.layout.value.push(panel_config);

  new_panel_id = new_panel_id + 1;
}

const addImagePanel = () => {
  let panel_config = {
    x: 0,
    y: findFreeRow(),
    w: 3,
    h: 5,
    i: new_panel_id,
    type: 'imagepanel',
    options: {
      'title': 'New title',
      'base64_image_data': '',
    }
  };
  layout.value.push(panel_config);
  dashboard_config.layout.value.push(panel_config);

  new_panel_id = new_panel_id + 1;
}

const addTitlePanel = () => {
  let panel_config = {
    x: 0,
    y: findFreeRow(),
    w: 12,
    h: 2,
    i: new_panel_id,
    type: 'titlepanel',
    options: {
      'title': 'New title',
    }
  };
  layout.value.push(panel_config);
  dashboard_config.layout.value.push(panel_config);

  new_panel_id = new_panel_id + 1;
}

const addSankeyPanel = () => {
  let panel_config = {
    x: 0,
    y: findFreeRow(),
    w: 12,
    h: 8,
    i: new_panel_id,
    type: 'sankeypanel',
    options: {
      'title': 'New title',
    }
  };
  layout.value.push(panel_config);
  dashboard_config.layout.value.push(panel_config);

  new_panel_id = new_panel_id + 1;
}

// eslint-disable-next-line no-unused-vars
const handleAddPanel = (e) => {
  if (e.key == "Text") addTextPanel();
  if (e.key == "Image") addImagePanel();
  if (e.key == "Title") addTitlePanel();
  if (e.key == "Sankey") addSankeyPanel();
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
  display: flex;
  flex-direction: column;
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

.vue-grid-item .remove {
    position: absolute;
    right: 2px;
    top: 0;
    cursor: pointer;
    color: lightgrey;
}

</style>