<template>
  <a-row class="dashboard-header">
    <a-col>
      <h2 style="font-weight: bold; font-size: 2rem">
        {{ `KPI Dashboard - ${dashboard_config.name.value}` }}
      </h2>
    </a-col>
    <a-col>
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
        <a-dropdown>
          <a-button type="primary">
            <i class="fas fa-plus" />
          </a-button>
          <template #overlay>
            <a-menu
              @click="handleAddPanel"
            >
              <a-menu-item :key="GridItemTypes.TITLE">
                Add Title panel
              </a-menu-item>
              <a-menu-item :key="GridItemTypes.TEXT">
                Add Text panel
              </a-menu-item>
              <a-menu-item :key="GridItemTypes.IMAGE">
                Add Image panel
              </a-menu-item>
              <a-menu-item :key="GridItemTypes.ANALYTICS">
                Add ESDL Analytics
              </a-menu-item>
              <!-- <a-menu-item :key="GridItemTypes.SANKEY">
                Add Sankey panel
              </a-menu-item> -->
            </a-menu>
          </template>
        </a-dropdown>
      </a-space>
    </a-col>
  </a-row>
  <div v-if="selectorOptionsKpiScope.length">
    <a-row>
      <a-typography-title :level="5" style="padding-right: 8px;">KPI Scope</a-typography-title>
      <a-select
        v-model:value="selectedKPIScope"
        placeholder="Please select a KPI scope"
        style="width: 50%; display: flex; align-items: center;"
        @change="onSelectKPIScope"
      >
        <a-select-opt-group
          v-for="optGroup in selectorOptionsKpiScope"
          :key="optGroup.label"
          :label="formatSelectorOptGroupLabel(optGroup.label)"
        >
          <a-select-option
            v-for="option in optGroup.options"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </a-select-option>
        </a-select-opt-group>
      </a-select>
    </a-row>
  </div>
  <div
    v-if="layout.length"
  >
    <grid-layout
      :key="dashboard_config.id.value"
      :layout="layout"
      :col-num="12"
      :row-height="30"
      is-draggable
      is-resizable
      vertical-compact
      responsive
      use-css-transforms
      @breakpoint-changed="onBreakpointChanged"
    >
      <!-- drag-ignore-from is required to avoid dragging the grid item 
       when the user is interacting with the PlotPanel Plot.
       https://jbaysolutions.github.io/vue-grid-layout/guide/04-allow-ignore.html -->
      <grid-item
        v-for="item in layout"
        :key="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :i="item.i"
        :is-resizable="item.isResizable"
        drag-ignore-from=".no-drag"
      >
        <TitlePanel
          v-if="item.type === GridItemTypes.TITLE"
          :options="item.options"
          @on-remove="onRemovePanel(item.i)"
        />
        <TextPanel
          v-if="item.type === GridItemTypes.TEXT"
          :options="item.options"
          @on-remove="onRemovePanel(item.i)"
        />
        <ImagePanel
          v-if="item.type === GridItemTypes.IMAGE"
          :options="item.options"
          @on-edit-save="(options) => onImageEditSave(item.i, options)"
          @on-remove="onRemovePanel(item.i)"
        />
        <PlotPanel
          v-if="item.type === GridItemTypes.PLOT"
          :options="item.options"
          :panel-dimension="{
            x: item.x, 
            y: item.y, 
            w: item.w, 
            h: item.h}"
          @on-remove="onRemovePanel(item.i)"
        />
        <AnalyticsPanel
          v-if="item.type === GridItemTypes.ANALYTICS"
          :options="item.options"
          @on-edit="onEditAnalyticsPanel(item.i)"
          @on-remove="onRemovePanel(item.i)"
        />
        <!-- <SankeyPanel
          v-if="item.type === GridItemTypes.SANKEY"
          :options="item.options"
        /> -->
      </grid-item>
    </grid-layout>
  </div>
  <div v-else>
    <a-empty 
      :description="false"
      :image-style="{
        height: '200px',
      }"
    >
      <h5>No dashboard loaded yet</h5>
    </a-empty>
  </div>
  <!-- Opens a modal to add or edit ESDL Analytics -->
  <a-modal
    v-model:open="esdlAnalyticsModalOpen"
    width="75%"
    :body-style="{height: '60vh'}"
    :destroy-on-close="true"
    :ok-text="esdlAnalyticsEditingId !== null ? 'Update' : 'Add'"
    @ok="esdlAnalyticsEditingId !== null ? addUpdatedAnalyticsPanelToDash() : addNewAnalyticsPanelToDash()"
    @cancel="closeESDLAnalyticsModal"
  >
    <ESDLAnalytics
      ref="refEsdlAnalytics"
      :options="esdlAnalyticsOptions"
    />
  </a-modal>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import ESDLAnalytics from './ESDLAnalytics.vue';
import TextPanel from '../components/kpidashboard/TextPanel.vue';
import TitlePanel from '../components/kpidashboard/TitlePanel.vue';
import ImagePanel from '../components/kpidashboard/ImagePanel.vue';
// import SankeyPanel from '../components/kpidashboard/SankeyPanel.vue';
import LoadDashboard from '../components/kpidashboard/LoadDashboard.vue';
import SaveDashboard from '../components/kpidashboard/SaveDashboard.vue';
import PlotPanel from "../components/kpidashboard/PlotPanel.vue";
import AnalyticsPanel from '../components/kpidashboard/AnalyticsPanel.vue';

const GridItemTypes = Object.freeze({
  ANALYTICS: 'analyticspanel',
  IMAGE: 'imagepanel',
  TEXT: 'textpanel',
  TITLE: 'titlepanel',
  PLOT: 'charttable',
  SANKEY: 'sankeypanel'
});

const dashboards_info = ref([]);
const layout = ref([]);     // this is the information used (and changed!) in the vue components

// Change in breakpoint will update layout accordingly.
const currentBreakpoint = ref("lg");

var new_panel_id = 0;  // to store the id that new panels should use

const dashboard_config = {
  id: ref(''),
  name: ref('New dashboard'),
  group: ref(''),
  layout: ref([]),     // this is the information stored as settings in the database
};

const esKPIs = window.get_all_kpi_info();
const esIds = Object.keys(esKPIs);

// Create the option group array for the UI Selector component.
const selectorOptionsKpiScope = esIds.map((esId) => (
  {
    label: esId,
    options: Object.keys(esKPIs[esId]).map((scope) => 
      // Prefix value with esId to differentiate scope (in case the different ES has the same scope name).
      ({value: `${esId}-${scope}`, label: scope}))
  }
));
const selectedKPIScope = ref({});

/**
 * Initialize dashboard contents based on the active ESDL and the first KPI scope.
 */
const initDashboard = () => {
  const activeEsdlId = window.active_layer_id;
  const activeEsdlKPIScope = selectorOptionsKpiScope.find(obj => obj.label === activeEsdlId);

  if (activeEsdlKPIScope) {
    const initSelectedKPIScope = activeEsdlKPIScope.options[0];
    selectedKPIScope.value = initSelectedKPIScope;

    updateDashboard(activeEsdlId, initSelectedKPIScope.label);
  } else {
    console.error(`Unable to find KPI scope of ESDL: ${activeEsdlId}`);
  }
};

if (Object.keys(esKPIs).length) {
  console.info("Initializing KPI dashboard contents");
  initDashboard();
}

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

/**
 * Handler to call when the user selects a different KPI scope from the Selector component.
 * 
 * @param {string} value User selected option value. Be noted that the value has been formatted as {edId}-{option label}.
 */
const onSelectKPIScope = (value) => {
  // Apply reverse search to return the corresponding ESId, and KPI Scope from the user selected value.
  const selectedOptionGroup = selectorOptionsKpiScope.filter((optGroup) => (
    optGroup.options.map((opt) => (opt.value)).includes(value)
  ))[0];
  const associatedESId = selectedOptionGroup.label;
  const selectedKPIScopeObj = selectedOptionGroup.options.filter(
    (opt) => (opt.value === value))[0];

  selectedKPIScope.value = selectedKPIScopeObj;

  updateDashboard(associatedESId, selectedKPIScopeObj.label);
};

/**
 * The utility function formats the displayed label of the selector option group.
 * 
 * @param {string} esId Energy system id.
 * @returns {string} Formatted selector option group label.
 */
const formatSelectorOptGroupLabel = (esId) => {
  return `${window.get_es_title(esId)} [${esId}]`;
};

/**
 * Calculate the grid item layout according to the current breakpoint.
 * 
 * @param {string} breakpoint The current breakpoint.
 * @param {number} itemNr Grid item number used for positing the grid item in the dashboard.
 * @param {number} itemHeight Default grid item height to 8
 */
function calGridItemLayout(breakpoint, itemNr, itemHeight=8) {
  // Vue Grid Layout library has the default number of columns for each breakpoint defined. 
  // Apply the default cols per breakpoint below.
  // https://jbaysolutions.github.io/vue-grid-layout/guide/properties.html#gridlayout
  let cols = 12;
  // Dynamically adjust colNum according to the current breakpoint.
  let colNum = 3;
  switch (breakpoint) {
    case 'lg':
      cols = 12;
      colNum = 3;
      break;
    case 'md':
      cols = 10;
      colNum = 2;
      break;
    case 'sm':
      cols = 6;
      colNum = 2;
      break;
    case 'xs':
      cols = 4;
      colNum = 1;
      break;
    case 'xxs':
      cols = 2;
      colNum = 1;
      break;
  }
  const w = cols / colNum;
  const h = itemHeight;
  const x = (itemNr % colNum) * w;
  const y = Math.floor(itemNr / colNum) * h;
  return [x, y, w, h];
}

/**
 * Updates the currentBreakpoint value and recalculates the grid layout accordingly.
 * 
 * @param {string} breakpoint The current breakpoint.
 */
 const onBreakpointChanged = (breakpoint) => {
  currentBreakpoint.value = breakpoint;

  // Sort and recalculate layout due to breakpoint change.
  const sortedLayout = sortLayoutItems(layout.value);
  const newLayout = sortedLayout.map((item, itemNr) => {
    const [x, y, w, h] = calGridItemLayout(currentBreakpoint.value, itemNr);
    if (item.isResizable === false) {
      return {
        ...item,
        x: x,
        y: y,
      };
    } else {
      return {
        ...item,
        x: x,
        y: y,
        w: w,
        h: h
      };
    }
  });
  layout.value = [...newLayout];
  dashboard_config.layout.value = [...newLayout];
};

/**
 * Returns an item layout list which will append the new grid item
 * at the end of the dashboard.
 */
 const findNewGridItemLocation = () => {
  // This updates the new_panel_id
  findNewPanelId();
  const newItemNr = layout.value.length;
  const [x, y, w, h] = calGridItemLayout(currentBreakpoint.value, newItemNr);
  return [new_panel_id, x, y, w, h];
};

/**
 * Remove the dashboard item with the given gridItemId.
 * 
 * @param {number} gridItemId Grid item id to be removed.
 */
const onRemovePanel = (gridItemId) => {
  const newLayout = layout.value.filter(item => gridItemId !== item.i);
  layout.value = [...newLayout];
  dashboard_config.layout.value = [...newLayout];
};

/**
 * Sort the given dashboard layout array based on the x + y value of the grid item
 * and return the sorted layout array.
 * 
 * @param {Array<Object>} layout An array of grid item objects to be sorted.
 * @return {Array<Object>} sortedLayout An array of sorted grid item objects.
 */
const sortLayoutItems = (layout) => {
  const sortedLayout = JSON.parse(JSON.stringify(layout));
  sortedLayout.sort((a, b) => ((a.x + a.y) - (b.x + b.y)));
  return sortedLayout;
};


/**
 * Append and synchronize a panel object to the layout and dashboard_config.layout array.
 * 
 * @param panelObj A panel object to be appended to the layout array.
 */
const appendAndSyncPanelToLayout = (panelObj) => {
  layout.value.push(panelObj);
  dashboard_config.layout.value = [...layout.value];
};

/**
 * Reset and empty the layout references.
 */
 function emptyLayout() {
  layout.value = [];
  dashboard_config.layout.value = [];
}

/**
 * Update dashboard contents according to the given esId and kpiScope.
 * 
 * @param {string} esId Energy system Id.
 * @param {string} kpiScope KPI scope of the associated energy system.
 */
function updateDashboard(esId, kpiScope) {
  console.debug(`Updating KPI dashboard for ES: ${esId} and scope: ${kpiScope}`);

  emptyLayout();

  // Preprocessing KPIs data
  const scopeKPIs = esKPIs[esId][kpiScope];
  const esScopeKPIs = {[esId]: scopeKPIs};
  const scopeKPIsData = window.kpis.preprocess_all_kpis(esScopeKPIs);
  const refKPIs = window.get_area_kpi_list(esId);
  const kpiData = window.syncScopeKPIsWithRefKPIs(scopeKPIsData, refKPIs);

  let kpi_nr = 0;     // TODO: do we need to seperate kpi_nr and new_panel_id? Add panels to existing dashboard?
  for (let kpi_name in kpiData) {
    let kpi_info = kpiData[kpi_name];
    const [x, y, w, h] = calGridItemLayout(currentBreakpoint.value, kpi_nr);
    if (kpi_info[0]['type'] == 'Sankey') {
      layout.value.push({
        x: x,
        y: y,
        w: w,
        h: h,
        i: new_panel_id,
        type: 'sankeypanel',
        options: {
          'title': kpi_name,
          'data': kpi_info[0]['flows'],
        },
      });
    } 
    else {
      let chart_options = window.createChartOptions(kpi_info);
      chart_options.title = kpi_name;
      // console.log(chart_options);

      layout.value.push({
        x: x,
        y: y,
        w: w,
        h: h,
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
}

const findNewPanelId = () => {
  new_panel_id = 0;
  for (let i=0; i<layout.value.length; i++) {
    if (layout.value[i].i >= new_panel_id) {
      new_panel_id = layout.value[i].i + 1;
    }
  }
};

// eslint-disable-next-line no-unused-vars
const handleLoadDashboard = (dashboard_id) => {
  window.socket.emit('kpi_dashboard_load', {dashboard_id: dashboard_id}, function(response) {
    if (response) {
      emptyLayout();

      layout.value = response.layout;
      dashboard_config.id.value = response.id;
      dashboard_config.name.value = response.name;
      dashboard_config.group.value = response.group;
      dashboard_config.layout.value = response.layout;

      findNewPanelId();
    } else {
      console.log('Error: empty response');
    }
  });
};

const applyTemplatePanelToDashbaordPanel = (template_panel, layout) => {
  for (let i in layout.value) {
    let panel = layout.value[i];
    if ('kpi_name' in panel && 'kpi_name' in template_panel && panel['kpi_name'] == template_panel['kpi_name']) {
      panel.x = template_panel.x;
      panel.y = template_panel.y;
      panel.w = template_panel.w;
      panel.h = template_panel.h;
      panel.type = template_panel.type;  // panel type (charttable/textpanel/titlepanel/imagepanel)

      if (template_panel.type == "charttable") {
        // console.log('Adjusting scales...', template_panel.options.options.scales);
        panel.options.options.scales = template_panel.options.options.scales;  // chart scales (x/y)
        if (template_panel.options.type == 'pie' || template_panel.options.type == 'doughnut') {
          // for a pie or doughnut chart remove the axis and scales
          panel.options.options.scales = {};
        }
        // console.log('Adjusting chart type to ' + template_panel.options.type);
        // This should trigger a re-render of the jschart
        panel.options.type = template_panel.options.type;  // chart type (pie/bar/...)
      }

      // This doesn't work yet
      panel.type = '';
      panel.options.type = '';
      nextTick();
      panel.type = template_panel.type;  // panel type (charttable/textpanel/titlepanel/imagepanel)
      panel.options.type = template_panel.options.type;

      // console.log("Applying template to existing panel " + panel['kpi_name']);
      // console.log("Dashboard panel:");
      // console.log(panel);
      // console.log("Template panel:");
      // console.log(template_panel);

      return true;
    }
  }
  return false;
};

const addTemplatePanelToDashboard = (template_panel, layout) => {
  // console.log("Adding template panel to dashboard");
  // console.log(template_panel);
  // console.log(layout.value);
  layout.value.push(template_panel);
};

// eslint-disable-next-line no-unused-vars
const handleLoadDashboardTemplate = (dashboard_id) => {
  window.socket.emit('kpi_dashboard_load', {dashboard_id: dashboard_id}, function(response) {
    if (response) {
      let template_layout = response.layout;

      for (let i in template_layout) {
        let template_panel = template_layout[i];
        let found = applyTemplatePanelToDashbaordPanel(template_panel, layout);
        if (!found) {
          addTemplatePanelToDashboard(template_panel, layout);
        }
      }

      findNewPanelId();
      dashboard_config.layout.value = [...layout.value];
    } else {
      console.log('Error: empty response');
    }
  });
};

// eslint-disable-next-line no-unused-vars
const handleSaveDashboard = (res) => {
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
};

const handleAddPanel = (e) => {
  switch (e.key) {
    case GridItemTypes.TITLE:
      addTitlePanel();
      break;
    case GridItemTypes.TEXT:
      addTextPanel();
      break;
    case GridItemTypes.IMAGE:
      addImagePanel();
      break;
    case GridItemTypes.ANALYTICS:
      // Opens an empty (default) ESDL Analytics modal
      openESDLAnalyticsModal(null);
      break;
    // TODO: fix SankeyPanel when ready
    // case GridItemTypes.SANKEY:
    //   addSankeyPanel();
    //   break;
    default:
      console.debug(`Unknown key: ${e.key}`);
  }
};

const addTitlePanel = () => {
  const [i, x, y, w, h] = findNewGridItemLocation();
  const titlePanelConfig = {
    x: x,
    y: y,
    w: 12,
    h: 2,
    i: i,
    isResizable: false,
    type: GridItemTypes.TITLE,
    options: {
      'title': 'New title',
    }
  };
  appendAndSyncPanelToLayout(titlePanelConfig);
};

const addTextPanel = () => {
  const [i, x, y, w, h] = findNewGridItemLocation();
  const textPanelConfig = {
    x: x,
    y: y,
    w: w,
    h: h,
    i: i,
    type: GridItemTypes.TEXT,
    options: {
      'title': 'New title',
      'text': 'New text',
    }
  };
  appendAndSyncPanelToLayout(textPanelConfig);
};

/**
 * Update the corresponding image panel options after receiving the emitted editedOptions.
 * 
 * @param {number} gridItemId The target grid item id.
 * @param {Object} editedOptions An object contains the edited image panel title and base64_image_data. 
 */
 const onImageEditSave = (gridItemId, editedOptions) => {
  layout.value.find(item => item.i === gridItemId).options = editedOptions;
};

const addImagePanel = () => {
  const [i, x, y, w, h] = findNewGridItemLocation();
  const imagePanelConfig = {
    x: x,
    y: y,
    w: w,
    h: h,
    i: i,
    type: GridItemTypes.IMAGE,
    options: {
      'title': 'New title',
      'base64_image_data': '',
    }
  };
  appendAndSyncPanelToLayout(imagePanelConfig);
};

// TODO: fix SankeyPanel when ready
// const addSankeyPanel = () => {
//   const [i, x, y, w, h] = findNewGridItemLocation();
//   const sankeyPanelConfig = {
//     x: x,
//     y: y,
//     w: w,
//     h: h,
//     i: i,
//     type: GridItemTypes.SANKEY,
//     options: {
//       'title': 'New title',
//     }
//   };
//   appendAndSyncPanelToLayout(sankeyPanelConfig);
// };


// -------------------------------------------- //
// ---- ESDL Analytics states & functions ----- //
// -------------------------------------------- //

const refEsdlAnalytics = ref(null);
const esdlAnalyticsModalOpen = ref(false);
const esdlAnalyticsEditingId = ref(null);

// Configures the ESDL Analytics modal states. 
// If null, ESDL Analytics modal is opened with the default (empty) settings;
const esdlAnalyticsOptions = ref(null);

/**
 * Opens ESDL Analytics modal with options setting
 *  
 * @param {Object|null} options Configures the ESDL Analytics modal states; 
 *                              If null, the modal is opened with a default state.
 */
const openESDLAnalyticsModal = (options) => {
  console.debug(`Open ESDL Analytics modal with options as ${options}`);
  esdlAnalyticsOptions.value = options;
  esdlAnalyticsModalOpen.value = true;
};

const closeESDLAnalyticsModal = () => {
  console.debug("Close ESDL Analytics modal");
  esdlAnalyticsEditingId.value = null;
  esdlAnalyticsModalOpen.value = false;
};

/**
 * Opens ESDL Analytics modal from the given gridItemId for further editing.
 * 
 * @param {number} gridItemId Layout grid item id
 */
 const onEditAnalyticsPanel = (gridItemId) => {
  esdlAnalyticsEditingId.value = gridItemId;
  const analyticsPanelOptions = layout.value.find(item => item.i === gridItemId).options;
  openESDLAnalyticsModal(analyticsPanelOptions);
};

/**
 * Adds a new ESDL Analytics panel to the dashboard.
 */
const addNewAnalyticsPanelToDash = () => {
  const [i, x, y, w, h] = findNewGridItemLocation();
  const analyticsPanelOptions = refEsdlAnalytics.value.getOptions();
  const analyticsPanelConfig = {
    x: x,
    y: y,
    w: w,
    h: h,
    i: i,
    type: GridItemTypes.ANALYTICS,
    options: analyticsPanelOptions
  };
  appendAndSyncPanelToLayout(analyticsPanelConfig);

  closeESDLAnalyticsModal();
};

/**
 * Updates the dashboard ESDL Analytics panel with the latest configured options.
 */
const addUpdatedAnalyticsPanelToDash = () => {
  const gridItemId = esdlAnalyticsEditingId.value;
  layout.value.find(item => item.i === gridItemId).options = refEsdlAnalytics.value.getOptions();
  dashboard_config.layout.value = [...layout.value];
  closeESDLAnalyticsModal();
};

</script>

<style scoped>

.dashboard-header {
  height: 60px;
  align-items: center;
  justify-content: space-between;
}

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