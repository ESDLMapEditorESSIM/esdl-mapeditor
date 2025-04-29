<template>
  <!-- Dialog header -->
  <a-row style="height: 60px;">
    <h2 style="font-weight: bold; font-size: 2rem">ESDL Analytics</h2>
  </a-row>
  <!-- Dialog content -->
  <a-row style="height: calc(100% - 60px);">
    <div v-if="isSyncingMetaData || isDeletingMetaData || isLoadingData" class="loading">
      <a-spin :indicator="loadingIcon" />
    </div>
    <a-layout style="height: 100%">
      <a-layout-sider
        v-model:collapsed="collapsed"
        collapsible
        :trigger="null"
        :width="300"
        :collapsed-width="0"
        theme="light"
      >
        <a-col class="graph-options">
          <a-col>
            <a-typography-title :level="4">Graph configuration</a-typography-title>
            <a-row>
              <a-typography-title :level="5">Dataset</a-typography-title>
              <a-select
                v-model:value="datasetSelected"
                :options="datasetOptions"
                :disabled="datasetOptions.length === 0"
                :placeholder="datasetOptions.length === 0 ? 'No datasets available' : 'Select a dataset'"
                mode="multiple"
                style="width: 100%"
                @change="onSelectDataset"
                @mouseleave="removeTooltipPopup"
              />
            </a-row>
            <a-row>
              <a-typography-title :level="5">Variable</a-typography-title>
              <a-select
                v-model:value="variableSelected"
                :options="groupOptionsByDatatype(variableOptions)"
                :disabled="datasetSelected.length === 0"
                :placeholder="datasetSelected.length === 0 ? 'First select a dataset' : 'Select a variable'"
                style="width: 100%"
                @change="onSelectVariable"
                @mouseleave="removeTooltipPopup"
              />
              <span
                v-if="variableSelected !== null && variableWarningMsg !== ''"
                style="color: #ffbb00; padding: 2px;"
              >
                {{ variableWarningMsg }}
              </span>
            </a-row>
            <!-- TODO: support profile group by -->
            <a-row v-if="!isProfileVariable">
              <a-typography-title :level="5">Group by</a-typography-title>
              <a-select
                v-model:value="groupbySelected"
                :options="groupbyOptions"
                :disabled="datasetSelected.length === 0 || variableSelected === null" 
                :placeholder="
                  datasetSelected.length === 0 ? 'First select a dataset'
                  : variableSelected === null ? 'First select a variable'
                    : 'Select a category'"
                :max-tag-count="maxGroupbySelectedCount"
                :status="chartType === 'chart' && groupbySelected.length > maxGroupbySelectedCount ? 'warning' : ''"
                allow-clear
                mode="multiple"
                style="width: 100%"
                @change="onSelectGroupBy"
                @mouseleave="removeTooltipPopup"
              />
              <span
                v-if="chartType === 'chart' && groupbySelected.length > maxGroupbySelectedCount"
                style="color: #ffbb00; padding: 2px;"
              >
                Grouping in a bar chart supports up to two selections only.
              </span>
            </a-row>
            <a-row>
              <a-row style="align-items: center;">
                <a-typography-title :level="5">Filter</a-typography-title>
                <a-tooltip title="Type to search filter options">
                  <a-button size="small" type="text">
                    <component :is="InfoCircleOutlined" style="vertical-align: 0.1rem" />
                  </a-button>
                </a-tooltip>
              </a-row>
              <a-cascader
                v-model:value="filterSelected"
                style="width: 100%"
                :options="filterOptions"
                :disabled="datasetSelected.length === 0 || variableSelected === null" 
                :placeholder="
                  datasetSelected.length === 0 ? 'First select a dataset'
                  : variableSelected === null ? 'First select a variable'
                    : 'Select a category'" 
                :show-search="true"
                allow-clear multiple
                @change="onSelectFilters"
                @mouseleave="removeTooltipPopup"
              />
              <br>
            </a-row>
            <a-col
              v-if="currentTrace.length > 0"
            >
              <br>
              <a-typography-title
                :level="4"
              >
                Display options
              </a-typography-title>
              <a-row>
                <a-segmented
                  v-model:value="chartType"
                  :options="chartTypes"
                  style="width: 100%;"
                  size="small"
                  block
                  @change="onChartTypeBtnClick"
                >
                  <template #label="{ value: value, payload = {} }">
                    <component :is="payload.icon" style="vertical-align: 0.05rem" />
                    {{ value.charAt(0).toUpperCase() + value.slice(1) }}
                  </template>
                </a-segmented>
              </a-row>
            </a-col>
            <!----------------------------------------------->
            <!----- Profile variable - Display options ------>
            <!----------------------------------------------->
            <a-col v-if="isProfileVariable && filterSelected.length">
              <a-row>
                <a-typography-title :level="5">Date selection</a-typography-title>
                <a-range-picker
                  v-model:value="profileDataRangeSelected"
                  :disabled-date="disabledDate"
                  :show-time="{ 
                    hideDisabledOptions: true,
                    defaultValue: [dayjs('00:00:00', 'HH:mm:ss'), dayjs('11:59:59', 'HH:mm:ss')]
                  }"
                  :format="dateTimeFormat"
                  @change="onSelectProfileDataRange"
                />
              </a-row>
              <a-row>
                <a-typography-title :level="5">Visualization type</a-typography-title>
                <a-segmented
                  v-model:value="profileVizTypeSelected"
                  :options="profileVizTypes"
                  style="width: 100%;"
                  size="small"
                  block
                  @change="onSelectProfileVizType"
                />
              </a-row>
              <a-row style="align-items: center; padding-top: 12px;">
                <a-switch
                  v-model:checked="profileDownsampling"
                  size="small"
                  :disabled="profileVizTypeSelected === 'Aggregated'"
                  @change="onProfileDownsampling"
                />
                <a-typography-paragraph style="padding-left: 8px; margin-bottom: 0px;">Downsampling</a-typography-paragraph>
                <a-tooltip :title="profileDownsampleMsg">
                  <a-button size="small" type="text">
                    <component :is="InfoCircleOutlined" style="vertical-align: 0.1rem" />
                  </a-button>
                </a-tooltip>
              </a-row>
              <!-- TODO: show load duration curve -->
              <a-row v-if="profileVizTypeSelected === 'Aggregated'">
                <a-typography-title :level="5">Aggregation interval</a-typography-title>
                <a-segmented
                  v-model:value="profileAggIntervalSelected"
                  :options="profileAggIntervals"
                  style="width: 100%;"
                  size="small"
                  block
                  @change="onSelectProfileAggInterval"
                />
              </a-row>
              <a-row v-if="profileVizTypeSelected === 'Aggregated'">
                <a-typography-title :level="5">Aggregation function</a-typography-title>
                <a-segmented
                  v-model:value="profileAggFuncSelected"
                  :options="profileAggFuncs"
                  style="width: 100%;"
                  size="small"
                  block
                  @change="onSelectProfileAggFunc"
                />
              </a-row>
            </a-col>
            <!---------------------------------------------------->
            <!----- Display options for Bar / Profile chart ------>
            <!---------------------------------------------------->
            <a-col
              v-if="chartType==='chart' && 
                ((!isProfileVariable && variableSelected !== null) || (isProfileVariable && filterSelected.length))"
            >
              <a-row style="width: 100%">
                <a-typography-title :level="5">Color palette</a-typography-title>
                <a-select
                  v-model:value="paletteSelected"
                  style="width: 100%"
                  @change="onSelectPalette"
                >
                  <a-select-option
                    v-for="option in colorPalettes"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                    <a-row>
                      <a-col
                        v-for="color in option.sample"
                        :key="color"
                        :span="Math.round(24/option.sample.length)"
                        :style="{ backgroundColor: color.startsWith('#') ? color : `#${color}`, height: '10px' }"
                      />
                    </a-row>
                  </a-select-option>
                </a-select>
              </a-row>
              <a-radio-group
                v-if="!isProfileVariable || (isProfileVariable && profileVizTypeSelected === 'Aggregated')"
                v-model:value="dataGrouping" 
                name="groupStackRadio"
                :options="groupStackOptions"
                style="display: flex; flex-direction: column; padding-top: 12px;"
                @change="onSelectDisplayOptions"
              />
              <br>
              <a-row 
                v-if="!isProfileVariable || (isProfileVariable && profileVizTypeSelected === 'Aggregated')"
                style="align-items: center; padding-top: 12px;"
              >
                <a-switch
                  v-model:checked="showBarNumbers"
                  size="small"
                  @change="onSelectDisplayOptions"
                />
                <a-typography-paragraph style="padding-left: 8px; margin-bottom: 0px;">Show numbers on bar chart</a-typography-paragraph>
              </a-row>
            </a-col>
            <!------------------------------------------->
            <!------------- Dataset handler ------------->
            <!------------------------------------------->
            <a-col style="padding-top: 24px; padding-bottom: 16px;">
              <br>
              <a-row style="padding-bottom: 8px;">
                <a-button
                  :disabled="isSyncingMetaData"
                  block
                  @click="onSyncBtnClick"
                >
                  <a-tooltip 
                    :title="datasetOptions.length ? 
                      'Update ESDL Analytics metadata with the current ESDL(s)' : 
                      'Add the current ESDL(s) to ESDL Analytics metadata'"
                  >
                    <component
                      :is="datasetOptions.length ? SyncOutlined : UploadOutlined"
                      style="vertical-align: 0.1rem"
                    />
                    {{ datasetOptions.length ? 'Update dataset' : 'Add dataset' }}
                  </a-tooltip>
                </a-button>
              </a-row>
              <a-row>
                <!-- TODO & NOTE: A temporary implementation to clean up dataset -->
                <a-button
                  :disabled="isDeletingMetaData || datasetOptions.length === 0"
                  block
                  @click="onDeleteBtnClick"
                >
                  <a-tooltip title="Delete ESDL Analytics metadata">
                    <component 
                      :is="DeleteOutlined"
                      style="vertical-align: 0.1rem"
                    />
                    Delete dataset
                  </a-tooltip>
                </a-button>
              </a-row>
            </a-col>
          </a-col>
        </a-col>
      </a-layout-sider>
      <a-layout>
        <a-layout-header class="graph-header">
          <a-button
            @click="() => (collapsed = !collapsed)"
          >
            <component
              :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
              style="vertical-align: 0.05rem"
            />
          </a-button>
          <!-- Graph header control bar -->
          <a-row class="graph-header-control">
            <!-- Graph editable title -->
            <a-row style="align-items: center;">
              <a-input
                v-model:value="title" 
                :bordered="false" 
                :placeholder="'Add a graph title'"
                :disabled="!editingTitle"
                :style="{ width: `${inputWidth}px` }"
                :maxlength="50"
                class="graph-title"
                @input="updateTitleInputWidth"
              />
              <a-button
                type="text"
                style="color: rgba(100, 100, 100, 0.7)"
                @click="() => (editingTitle = !editingTitle)"
              >
                <component 
                  :is="editingTitle ? SaveOutlined : EditOutlined"
                  style="vertical-align: 0.1rem"
                />
              </a-button>
            </a-row>
            <!-- Export CSV button -->
            <a-row>
              <a-tooltip
                v-if="chartType==='table' && currentTrace.length"
                title="Export CSV"
              >
                <a-button @click="exportChartDataToCSV">
                  <component 
                    :is="DownloadOutlined"
                    style="vertical-align: 0.1rem"
                  />
                </a-button>
              </a-tooltip>
            </a-row>
          </a-row>
        </a-layout-header>
        <a-layout-content class="graph-content">
          <AnalyticsPlot
            :trace="currentTrace"
            :layout="currentLayout"
            @on-relayout="onAnalyticsPlotRelayout"
          />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-row>
</template>

<script setup>
import { defineProps, ref, h, onMounted, onUnmounted } from 'vue';
import { notification } from 'ant-design-vue';
import {
  BarChartOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
	MenuFoldOutlined,
	MenuUnfoldOutlined,
  UploadOutlined,
	SaveOutlined,
  SyncOutlined,
	TableOutlined }
from "@ant-design/icons-vue";
import { nseColorPalette } from '@/utils/spatialVisualization';
import AnalyticsPlot from '@/components/esdlanalytics/AnalyticsPlot.vue';
import dayjs from 'dayjs';
import minMax from 'dayjs/plugin/minMax';

dayjs.extend(minMax);

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: '5rem' }, spin: true
});

// to prevent stuck popup on UI
const removeTooltipPopup = () => { window.jquery(".ui-tooltip-content").parents('div').remove();};

const props = defineProps({
  options: {
    type: Object,
    default: null // If null, the component is instantiated with the default initOptions settings.
  }
});

// ---------------------------------------- //
// ---------- Component options ----------- //
// ---------------------------------------- //

// payload is used by AntD segmented component to display icon
const chartTypes = [
  {value: "chart", payload: { icon: BarChartOutlined } },
  {value: "table", payload: { icon: TableOutlined } },
];

const dateTimeFormat = "YYYY-MM-DD HH:mm:ss";
const profileVizTypes = ['Profile', 'Aggregated'];
const profileAggIntervals = ['Week', 'Month', 'Quarter', 'Year'];
const profileAggFuncs = ['Count', 'Max', 'Min', 'Sum', 'Mean'];

const profileMaxDataPoints = 100 // The value is applied in updateTrace() when profileDownsampling === true
const profileDownsampleMsg = "Downsampling simplifies large dataset for better chart readability and performance " + 
                             `by limiting visualization to approximately ${profileMaxDataPoints} data points. ` + 
                             "The average value is used to represent data within each interval. " +
                             "Toggle it on to explore general trends or off to access the full dataset." 

const sampleColorCount = 12;
const colorPalettes = [
  // pie_chart_color_list is defined in area_building_layer.js
  { label: 'Default', value: 'Default', sample: pie_chart_color_list.slice(0, sampleColorCount) },
  { label: 'Qualitative', value: 'Qualitative', sample: window.palette('mpn65', sampleColorCount) },
  { label: 'Diverging', value: 'Diverging', sample: window.palette('tol-dv', sampleColorCount) },
  { label: 'Sequential', value: 'Sequential', sample: window.palette('tol-sq', sampleColorCount) },
  { label: 'Rainbow', value: 'Rainbow', sample: window.palette('tol-rainbow', sampleColorCount) },
  // TODO: remove this quick fix (implemented to support NSE use case) 
  { label: 'Custom color palette', value: 'NSE', sample: nseColorPalette.sample },
];

const groupStackOptions = [
	{ label: 'Group data', value: 0 },
	{ label: 'Stack data (totals)', value: 1 },
	{ label: 'Stack data (percentage)', value: 2 },
];

const maxGroupbySelectedCount = 2;

// The initial (default) option settings of the component
const initOptions = {
  title: '',
  chartType: chartTypes[0].value,
  currentTrace: [],
  currentLayout: {},
  datasetOptions: [],
  datasetSelected: [],
  variableOptions: [],
  variableSelected: null,
  variableWarningMsg: '',
  isProfileVariable: false,
  profileDataRanges: [],
  profileDataRangeSelected: [],
  profileVizTypeSelected: profileVizTypes[0],
  profileDownsampling: true,
  profileAggIntervalSelected: profileAggIntervals[0],
  profileAggFuncSelected: profileAggFuncs[0],
  groupbyOptions: [],
  groupbySelected: [],
  filterOptions: [],
  filterSelected: [],
  dataGrouping: 1,
  showBarNumbers: false,
  paletteSelected: colorPalettes[0]
};

const appliedOptions = props.options === null ? initOptions : props.options;

// ----------------------------------------- //
// ------------ Component states ----------- //
// ----------------------------------------- //

const collapsed = ref(false);

const title = ref(appliedOptions.title);
const editingTitle = ref(false);

const minWidth = 180;
const inputWidth = ref(minWidth);

const updateTitleInputWidth = (value) => {
	const newWidth = value.target.value.length * 11;
	inputWidth.value = newWidth >= minWidth ? newWidth : minWidth;
};

const chartType = ref(appliedOptions.chartType);

const onChartTypeBtnClick = (value) => {
  chartType.value = value;
  updateTrace();
};

const isSyncingMetaData = ref(false);
const isDeletingMetaData = ref(false);
const isLoadingData = ref(false);

const currentTrace = ref(appliedOptions.currentTrace);
const currentLayout =  ref(appliedOptions.currentLayout);
const datasetOptions = ref(appliedOptions.datasetOptions);
const datasetSelected = ref(appliedOptions.datasetSelected);
const variableOptions = ref(appliedOptions.variableOptions);
const variableSelected = ref(appliedOptions.variableSelected);
const variableWarningMsg = ref(appliedOptions.variableWarningMsg);
const isProfileVariable = ref(appliedOptions.isProfileVariable);
const profileDataRanges = ref(appliedOptions.profileDataRanges);
const profileDataRangeSelected = ref(appliedOptions.profileDataRangeSelected);
const profileVizTypeSelected = ref(appliedOptions.profileVizTypeSelected);
const profileDownsampling = ref(appliedOptions.profileDownsampling);
const profileAggIntervalSelected = ref(appliedOptions.profileAggIntervalSelected);
const profileAggFuncSelected = ref(appliedOptions.profileAggFuncSelected);
const groupbyOptions = ref(appliedOptions.groupbyOptions);
const groupbySelected = ref(appliedOptions.groupbySelected);
const filterOptions = ref(appliedOptions.filterOptions);
const filterSelected = ref(appliedOptions.filterSelected);
const dataGrouping = ref(appliedOptions.dataGrouping);
const showBarNumbers = ref(appliedOptions.showBarNumbers);
const paletteSelected = ref(appliedOptions.paletteSelected);

/**
 * Return an object of reactive states of the component options. 
 * This can be used, together with defineExpose(), when other Vue components need to access the states of the component instance.
 */
const getOptions = () => {
  return {
    title: title.value,
    chartType: chartType.value,
    currentTrace: currentTrace.value,
    currentLayout: currentLayout.value,
    datasetOptions: datasetOptions.value,
    datasetSelected: datasetSelected.value,
    variableOptions: variableOptions.value,
    variableSelected: variableSelected.value,
    variableWarningMsg: variableWarningMsg.value,
    isProfileVariable: isProfileVariable.value,
    profileDataRanges: profileDataRanges.value,
    profileDataRangeSelected: profileDataRangeSelected.value,
    profileVizTypeSelected: profileVizTypeSelected.value,
    profileDownsampling: profileDownsampling.value,
    profileAggIntervalSelected: profileAggIntervalSelected.value,
    profileAggFuncSelected: profileAggFuncSelected.value,
    groupbyOptions: groupbyOptions.value,
    groupbySelected: groupbySelected.value,
    filterOptions: filterOptions.value,
    filterSelected: filterSelected.value,
    dataGrouping: dataGrouping.value,
    showBarNumbers: showBarNumbers.value,
    paletteSelected: paletteSelected.value
  };
};

defineExpose({
  getOptions
});

const onSelectPalette = () => {
  updateTrace();
};

const onSelectDataset = () => {
  // Resets selected variable, groupby, and filter to the default state.
  variableSelected.value = null;
  groupbySelected.value = [];
  filterSelected.value = [];

  updateVariables().then(() => {
    updateTrace();
  });
};

const onSelectVariable = (_, value) => {

  // Reminds users when the selected variable is not present in all chosen dataset.
  if (value.ds.length !== datasetSelected.value.length) {
    variableWarningMsg.value = "The selected variable only exists in dataset: " + 
                                `${value.ds.map(d => `'${d}'`).join(', ')}`;
  } else {
    variableWarningMsg.value = "";
  }

  isProfileVariable.value = value.datatype === 'PROFILE';

  updateColumns().then(() => {
    // Retains user-applied groupbys and filters if they match the new variable options; discard otherwise.
    const appliedGroupbys = groupbySelected.value;
    const varGroupbyOptions = groupbyOptions.value.map(opt => opt.value);
    groupbySelected.value = appliedGroupbys.filter((g) => varGroupbyOptions.includes(g));

    const appliedFilters = filterSelected.value;
    const varFilterOptions = [];
    filterOptions.value.forEach((opt) => {
      opt.children.forEach((c) => {
        varFilterOptions.push([opt.value, c.value]);
      });
    });
    filterSelected.value = appliedFilters.filter((f) => {
      // filter is applied at the parent level (e.g. ['region'])
      if (f.length === 1 && varFilterOptions.some(opt => opt[0] === f[0])) {
        return f;
      } 
      // filter is applied at the parent-child combined level (e.g. ['region', 'Utrecht'])
      else if (varFilterOptions.some(opt => opt[0] === f[0] && opt[1] === f[1])) {
        return f;
      }
    });

    updateTrace();
  });
};

const onSelectGroupBy = () => {
  updateTrace();
};

const onSelectFilters = () => {
  updateTrace();
};

const onSelectDisplayOptions = () => {
	updateTrace();
};

const onSelectProfileDataRange = () => {
  updateTrace();
};

const onSelectProfileVizType = () => {
  // Switch off profile downsampling when visualization type is not 'Profile' (could be misleading)
  if (profileVizTypeSelected.value !== 'Profile') {
    profileDownsampling.value = false;
  } else {
    profileDownsampling.value = true;
  }
  updateTrace();
};

const onProfileDownsampling = () => {
  updateTrace();
};

/**
 * Triggered to update profileDataRangeSelected state when newLayoutRanges is emitted from 
 * the user interaction with AnalyticsPlot (zoom in/out or pan). Only updateTrace() when interacting with profile data.
 * 
 * @param {Object|null} newLayoutRanges An object with structure as {x: [xaxis.range[0], xaxis.range[1]], y: [yaxis.range[0], yaxis.range[1]]}
 *                                      when zoom in/out or pan event is occurred; otherwise, null is returned.
 */ 
const onAnalyticsPlotRelayout = (newLayoutRanges) => {
  if (!isProfileVariable.value) {
    return;
  }

  if (profileVizTypeSelected.value !== 'Profile') {
    return;
  }

  // Restore to default data range when newLayoutRanges is null.
  if (newLayoutRanges === null) {
    profileDataRangeSelected.value = [];
  } 
  // Apply subset of data range for querying data.
  else {
    try {
      let dateTimeRanges = newLayoutRanges["x"];
      // Handling a special case that the returned datetime string in newLayoutRanges is with format: "YYYY-MM-DD HH:mm"
      newLayoutRanges["x"].forEach((dt, idx) => {
        if (dayjs(dt, "YYYY-MM-DD HH:mm", true).isValid()) {
          dateTimeRanges[idx] = `${dt}:00`;
        }
      })
      profileDataRangeSelected.value = dtStringsToDayJsObjects(dateTimeRanges);
    } catch (error) {
      displayNotification("error", `An error occurred while applying the selected data extent for querying: ${error}`);
    }
  }

  updateTrace();
};

const onSelectProfileAggInterval = () => {
  updateTrace();
};

const onSelectProfileAggFunc = () => {
  updateTrace();
};

onMounted(() => {
  console.info("Initializing ESDL Analytics");
  updateDatasets();
});

onUnmounted(() => {
  console.info("Unmounting ESDL Analytics");
});

// ------------------------------------- //
// --------- Component methods --------- //
// ------------------------------------- //

/**
 * Fetches DataManager metadata from the specified resource using a WebSocket connection.
 * 
 * @param {string} resource The name of the resource to fetch metadata from.
 * @param {Object} requestBody Optional. The request body to send with the WebSocket emit.
 * @returns {Promise<Array|Object>} A promise that resolves with the metadata response or rejects with an error.
 */
 const fetchMetadata = async(resource, requestBody) => {
  const metadataPromise = new Promise((resolve, reject) => {
    const path = `datamanager/${resource}`;
    const callback = (response) => {
      if (response) {
        resolve(response);
			} else {
				reject(new Error(`An unknown error occurred while fetching metadata from ${path}`));
			}
    };

    if (requestBody) {
      window.socket.emit(path, requestBody, callback);
    } else {
      window.socket.emit(path, callback);
    }
	});
  return metadataPromise;
};

/**
 * Modifies DataManager metadata with specified action using a WebSocket connection.
 * 
 * @param {string} action The action to be performed ("add_update", "delete").
 * @param {Object} requestBody The request body required by the specified action.
 * @returns {Promise<Object>} A promise that resolves with the parsed response object or rejects with an error.
 */
const modifyMetadata = async(action, requestBody) => {
  return new Promise((resolve, reject) => {
    const path = `datamanager/metadata/${action}`;
    window.socket.emit(path, requestBody, (response) => {
      if (response) {
        resolve(JSON.parse(response));
			} else {
				reject(new Error(`An unknown error occurred while modifying metadata from ${path}`));
			}
    });
	});
};

/**
 * Displays a notification with the specified level and description.
 * 
 * @param {string} level The level of the notification ("info", "warning", "error").
 * @param {string} description The description text of the notification.
 */
const displayNotification = (level, description) => {
  notification[level.toLowerCase()]({
    message: level.toUpperCase(),
    description: description,
    placement: "bottomRight",
    duration: 8
  });
};

/**
 * Adds or updates ESDLs into metadata by iterating over the list of energy systems.
 */
const onSyncBtnClick = async() => {
  console.debug("Synchronizing ESDLs into metadata");
  isSyncingMetaData.value = true;

  const esObjects = window.esdl_list;
  const promises = Object.keys(esObjects).map(async(esId) => {
    const esTitle = esObjects[esId].title;
    try {
      displayNotification("info", `Adding ${esTitle} [${esId}] into the database.`);
      const reqBody = { es_id: esId };
      const resp = await modifyMetadata('add_update', reqBody);
      displayNotification(resp.status, resp.message);
    } catch (error) {
      console.error(error);
      displayNotification("error", `An unknown error occurred while adding ${esTitle} [${esId}] to the database`);
    }
  });

  try {
    await Promise.all(promises);
    updateDatasets();
  } catch (error) {
    console.error(error);
    displayNotification("error", `An error occurred while synchronizing metadata: ${error}`);
  } finally {
    isSyncingMetaData.value = false;
  }  
};

/**
 * TODO & NOTE: A temporary implementation to clean up metadata. 
 * The clean up should be a background process when the user session ends.
 */
const onDeleteBtnClick = async() => {
  console.debug("Deleting user associated metadata");
  isDeletingMetaData.value = true;
  try {
    // If dataset_name is not specified, all metadata associated with the session user will be deleted.
    const reqBody = { dataset_name: null };
    const resp = await modifyMetadata('delete', reqBody);
    displayNotification(resp.status, resp.message);
    updateDatasets();
  } catch (error) {
    console.error(error);
    displayNotification("error", `An error occurred while deleting metadata: ${error}`);
  } finally {
    // TODO: rest all to default
    // Reset selection
    datasetSelected.value = [];
    variableSelected.value = null;
    groupbySelected.value = [];
    filterSelected.value = [];
    currentTrace.value = [];
    currentLayout.value = {};

    isDeletingMetaData.value = false;
  }
};

/**
 * Asynchronously fetches DataManager datasets and updates the dataset options.
 * 
 * @returns {Promise<void>} A promise that resolves when the datasets have been fetched and the options updated.
 */
const updateDatasets = async() => {
  console.debug("Fetching DataManager datasets");
  try {
    const datasets = await fetchMetadata('datasets');
    if (datasets.length) {
      datasetOptions.value = datasets.map((d) => ({
        value: d.id,
        label: `${d.name}`
      }));
    } else {
      datasetOptions.value = [];
    }
  } catch (error) {
    console.error(error);
  }
};

/**
 * Asynchronously fetches DataManager variables and updates the variable options.
 * 
 * @returns {Promise<void>} A promise that resolves when the variables have been fetched and the options updated.
 */
const updateVariables = async() => {
  console.debug("Fetching DataManager variables");
  if (datasetSelected.value.length) {
    try {
      const reqBody = { dataset_ids: datasetSelected.value };
      const variables = await fetchMetadata('variables', reqBody);

      const options = {};
      variables.forEach((v) => {
        if (!Object.keys(options).includes(v.name)) {
          options[v.name] = {
            value: v.name,
            label: v.label,
            ds: [v.dataset],
            unit: v.unit, 
            description: v.description, 
            datatype: v.datatype 
          };
        } else {
          options[v.name].ds.push(v.dataset);
        }
      });

      variableOptions.value = options;
    } catch (error) {
      console.error(error);
    }
  }
};

// A helper function to turn variableOptions into a list of datatype labeled options.
const groupOptionsByDatatype = (variableOptions) => {
  const groupedOptions = Object.values(variableOptions).reduce((acc, obj) => {
    const { datatype, ...rest } = obj;
    const existingGroup = acc.find(group => group.label === datatype);
    if (existingGroup) {
      existingGroup.options.push({ ...rest, datatype });
    } else {
      acc.push({
        label: datatype,
        options: [{ ...rest, datatype }]
      });
    }
    return acc;
  }, []);
  return groupedOptions;
};

/**
 * Asynchronously fetches DataManager columns and updates the groupby and filter options.
 * 
 * @returns {Promise<void>} A promise that resolves when the columns have been fetched 
 *                          and the groupby and filter options updated.
 */
const updateColumns = async() => {
  console.debug("Fetching DataManager columns");
  if (datasetSelected.value.length && variableSelected.value !== null) {
    try {
      const reqBody = {
        dataset_ids: datasetSelected.value, 
        variable_name: variableSelected.value
      };
      const varFilterOptions = await fetchMetadata('columns', reqBody);

      groupbyOptions.value = Object.entries(varFilterOptions).map(([name, val]) => {
        const optValue = val.column === 'labels' ? `labels/${val.key}` : val.column;
        return { 
          value: optValue, 
          label: name 
        };
      });

      filterOptions.value = Object.entries(varFilterOptions).map(([name, val]) => {
        const optValue = val.column === 'labels' ? `labels/${val.key}` : val.column;
        return {
          value: optValue,
          label: name,
          children: val.options.map((option) => ({
            value: option,
            label: option
          }))
        };
      });
    } catch (error) {
      console.error(error);
    }
  }
};

/**
 * Fetches metadata and updates the trace and layout configuration based on the user selections
 * such as selected datasets, variable, group by options, filter options, and chart type.
 */
const updateTrace = async() => {
  console.debug("Updating trace");
  isLoadingData.value = true;

  const queryProfileData = isProfileVariable.value;

  if (datasetSelected.value.length === 0 || variableSelected.value === null) {
    currentTrace.value = [];
    isLoadingData.value = false;
    return;
  }

  if (Object.keys(variableOptions.value).length === 0) {
    isLoadingData.value = false;
    return;
  }

  // Only take the first two elements as group_by selections for a chart visualization.
  const groupBySelection = chartType.value === 'chart' ? 
    groupbySelected.value.slice(0, maxGroupbySelectedCount) : groupbySelected.value;

  let filterSelection = {};
  filterSelected.value.forEach((filter) => {
    const [column, val] = filter;
    if (filterSelection[column] === undefined) {
      filterSelection[column] = [];
    }
    filterSelection[column].push(val);
  });

  // Continue to query profile only when the filter is selected;
  // Otherwise, it could lead to too many profile queries and can be slow.
  if (queryProfileData && Object.keys(filterSelection).length === 0) {
    currentTrace.value = [];
    isLoadingData.value = false;
    return;
  }

  let options = {
    dataset_ids: datasetSelected.value,
    variable_name: variableSelected.value,
    group_by: groupBySelection,
    filters: filterSelection,
    chart_type: chartType.value,
    profile: null
  };

  // Conditionally updates profile data query options.
  if (queryProfileData) {
    options['profile'] = {
        data_range: profileDataRangeSelected.value !== null ? 
          profileDataRangeSelected.value.map(dt => formatAsDateTimeStr(dt)) : [],
        viz_type: profileVizTypeSelected.value,
      };
    if (profileDownsampling.value) {
      options['profile']['max_datapoints'] = profileMaxDataPoints;
    }
    if (profileVizTypeSelected.value === 'Aggregated') {
      options['profile']['agg_interval'] = profileAggIntervalSelected.value;
      options['profile']['agg_func'] = profileAggFuncSelected.value;
    }
  }

  try {
    const results = await fetchMetadata('query', options);
    const traces = results['traces'];
    if (queryProfileData) {
      profileDataRanges.value = dtStringsToDayJsObjects(results['data_range']);
      if (results['error_msg'] !== '') {
        displayNotification('error', results['error_msg']);
        console.error(results['errors']);
      }
      const formattedData = chartType.value === 'table' ? 
        tableTraceHandler(traces) : profileTraceHandler(traces);
      currentTrace.value = formattedData.traces;
      currentLayout.value = formattedData.layout;
    }
    else {
      const formattedData = chartType.value === 'table' ? 
        tableTraceHandler(traces) : barChartTraceHandler(traces);
      currentTrace.value = formattedData.traces;
      currentLayout.value = formattedData.layout;
    }
  } catch (error) {
    console.error(error);
    displayNotification("error", `${error}`);
  }
  isLoadingData.value = false;
};

// A helper function to format a DayJs object and return a datetime string that can be parsed by the backend. 
const formatAsDateTimeStr = (obj) => {
  if (!obj) {
    return;
  }
  return obj.format(dateTimeFormat);
};

// A helper function to cast datetime strings array into dayjs objects array.
const dtStringsToDayJsObjects = (dtStrings) => {
  return dtStrings.length ? dtStrings.map(dt => dayjs(dt, dateTimeFormat)) : [];
};

const disabledDate = (current) => {
  if (profileDataRanges.value.length) {
    return current < profileDataRanges.value[0] || current > profileDataRanges.value[1];
  } else {
    return false;
  }
};

/**
 * Configures profile line chart traces and layout for visualization.
 * 
 * @param {Array} traces An array of trace objects to be configured for profile line chart visualization.
 * @returns {Object} An object containing the configured traces and layout for the profile line chart.
 */
 const profileTraceHandler = (traces) => {
  const colorscale = generateColorscale(paletteSelected.value, traces.length);
  const isAggregated = profileVizTypeSelected.value === 'Aggregated';
  traces.forEach((t, idx) => {
    t.type = isAggregated ? 'bar' : 'scatter';
    t.mode = isAggregated ? null : 'lines';
    t.text = (isAggregated && showBarNumbers.value) ? t.y.map(y => y.toFixed(1)) : "";
    t.marker = {color: colorscale[idx % colorscale.length]};
  });

  const profileLayout = {
    title: variableSelected.value,
    xaxis: {
      automargin: true,
    },
    yaxis: {
      title: variableOptions.value[variableSelected.value].unit,
      automargin: true,
    },
    legend: {
      groupclick: 'toggleitem',
    },
    barmode: (isAggregated && [1, 2].includes(dataGrouping.value))? 'relative' : 'group',
    barnorm: (isAggregated && dataGrouping.value === 2) ? 'percent' : '',
    showlegend: true,
    autosize: true,
  };

  return {
    traces: traces,
    layout: profileLayout
  };
};

/**
 * Configures bar chart traces and layout for visualization.
 * 
 * @param {Array} traces An array of trace objects to be configured for bar chart visualization.
 * @returns {Object} An object containing the configured traces and layout for the bar chart.
 */
const barChartTraceHandler = (traces) => {
  const colorscale = generateColorscale(paletteSelected.value, traces.length);
  traces.forEach((t, idx) => {
    t.type = 'bar';
    t.text = showBarNumbers.value ? t.y.map(y => y.toFixed(1)) : "";
    t.marker = {color: colorscale[idx % colorscale.length]};
  });

  const barChartLayout = {
    title: variableSelected.value,
    xaxis: {
      type: 'multicategory',
      automargin: true,
    },
    yaxis: {
      title: variableOptions.value[variableSelected.value].unit,
      automargin: true,
    },
    barmode: [1, 2].includes(dataGrouping.value) ? 'stack' : 'group',
    barnorm: dataGrouping.value === 2 ? 'percent' : '',
    showlegend: true,
    autosize: true
  };

  return {
    traces: traces,
    layout: barChartLayout
  };
};

/**
 * Generates a colorscale based on the specified palette and number of colors.
 * 
 * @param {string} palette The type of color palette to use. Options include:
 *                         'Qualitative', 'Diverging', 'Sequential', 'Rainbow', and 'Default'.
 * @param {number} numColors The number of colors to generate in the colorscale.
 * @returns {Array} An array of colorscale values.
 */
 const generateColorscale = (palette, numColors) => {
  // Default colorscale to pie_chart_color_list
  let colorscale = pie_chart_color_list;
  switch (palette) {
    case 'Qualitative':
      // The maximum number of colors: 65
      colorscale = window.palette('mpn65', numColors > 65 ? 65 : numColors);
      break;
    case 'Diverging': 
      colorscale = window.palette('tol-dv', numColors);
      break;
    case 'Sequential':
      colorscale = window.palette('tol-sq', numColors);
      break;
    case 'Rainbow':
      colorscale = window.palette('tol-rainbow', numColors);
      break;
    // TODO: remove this quick fix (implemented to support NSE use case)
    case 'NSE':
      colorscale = nseColorPalette.sample;
      break;
    case 'Default':
    default:
  }
  return colorscale;
};

/**
 * Configures table traces and layout for visualization.
 * 
 * @param {Array} traces An array containing a single object of table header and cell values.
 * @returns {Object} An object containing the formatted table trace and layout configuration.
 */
const tableTraceHandler = (traces) => {
  const formattedTableHeader = traces[0].header.values.map((col) => ([`<b>${col[0]}</b>`]));
  const tableCellValues = traces[0].cells.values;
  
  const tableTrace = [{
    type: 'table',
    header: {
      values: formattedTableHeader,
      align: 'left',
      fill: {color: "#fafafa"},
      line: {width: 0.5, color: "#c4c4c4"},
      font: {size: 15, color: "black", textcase: "word caps"}
    },
    cells: {
      values: tableCellValues,
      align: "left",
      height: 25,
      line: {width: 0.5, color: "#c4c4c4"},
      font: {size: 14, color: "black"},
    },
  }];
  const tableLayout = {
    title: variableSelected.value,
    autosize: true,
    margin: {l: 20, t: 65, r: 20, b: 5},
  };

  return {
    traces: tableTrace,
    layout: tableLayout
  };
};

const exportChartDataToCSV = () => {
  if (currentTrace.value[0] && currentTrace.value[0].type === 'table') {
    try {
      const tableData = currentTrace.value[0];
      const csvFilename = variableSelected.value ? `${variableSelected.value}.csv` : `Untitled_chart_data.csv`;
      const csvHeaders = tableData.header.values.map((col) => col[0].replace(/<\/?b>/g, ""));
      const csvRows = [];
      const rowCounts = tableData.cells.values[0].length;
      for (let i = 0; i < rowCounts ; i++) {
        const row = tableData.cells.values.map((array) => array[i]).join(",");
        csvRows.push(row);
      }
      const csvContent = [csvHeaders, ...csvRows].join("\n");

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = csvFilename;
      document.body.appendChild(link);
      link.click();

      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      const errorMsg = `Error exporting CSV: ${error}`;
      console.error(errorMsg);
      displayNotification("error", `${errorMsg}`);
    }
  } else {
    const errorMsg = "No data or incorrect chart type.";
    console.error(errorMsg);
    displayNotification("error", `${errorMsg}`);
  }
};

</script>

<style>

.ant-layout-header.graph-header {
	display: flex;
	align-items: center;
	padding: 12px;
	background-color: white; 
}

.ant-segmented-item,
.ant-segmented-item::selection {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.graph-header-control {
	width: 100%;
	justify-content: space-between;
	padding-left: 8px;
}

.graph-title {
	font-size: 1.3rem;
	font-family: Arial,sans-serif;
	font-style: italic;
	color: gray;
	margin-left: 8px;
	margin-right: 8px;
	min-width: 180px;
	max-width: 400px;
	border-bottom: 1px solid;
	border-radius: 0px;
}

.graph-title:disabled {
	color: black;
	font-style: normal;
}

.graph-options {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	overflow-y: auto;
  padding: 16px;
  height: 100%;
	border: 1px solid rgba(100, 100, 100, 0.15);
	border-radius: .5rem;
}

.graph-content {
	background-color: white;
	padding-left: 12px;
	padding-right: 12px;
}

.loading {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: calc(100% - 52px);
  height: calc(100% - 60px);
  z-index: 100;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 5px;
}

</style>