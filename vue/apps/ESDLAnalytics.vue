<template>
  <!-- Dialog header -->
  <a-row style="height: 60px; padding-left: 0.5em">
    <h2 style="font-weight: bold; font-size: 2rem">ESDL Analytics</h2>
  </a-row>
  <!-- Dialog content -->
  <a-row style="height: calc(100% - 60px)">
    <div
      v-if="isSyncingMetaData || isDeletingMetaData || isLoadingData"
      class="loading"
    >
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
          <a-tabs v-model:activeKey="activeTabKey">
            <!-- Tab 1: Variant and dataset selection -->
            <a-tab-pane key="data" tab="Data Selection">
              <a-row>
                <a-typography-title :level="5"
                  >Available variants</a-typography-title
                >
                <p style="font-size: small">
                  Select which variants need to be analysed for comparision.
                </p>
                <div class="variant-tree-container">
                  <vue-js-tree
                    v-if="treeData != null"
                    tree-id="analytics_variant_tree"
                    :plugins="['types', 'checkbox']"
                    :data="treeData"
                    :events="treeEventHandlers"
                    :tree-type-specs="treeTypeSpecs"
                    :checkbox="{
                      three_state: false,
                      whole_node: false,
                      tie_selection: false,
                    }"
                  />
                  <div v-else class="text-only">
                    <p>No variants available.</p>
                  </div>
                </div>
              </a-row>

              <a-col style="padding-top: 24px; padding-bottom: 16px">
                <a-row style="padding-bottom: 8px">
                  <a-col :span="12"><p>Target Energy Unit:</p></a-col>
                  <a-col :span="12">
                    <a-select
                      style="width: 100%"
                      size="small"
                      v-model:value="energyUnit"
                      :options="energyUnitOptions"
                    />
                  </a-col>
                </a-row>
                <a-row style="padding-bottom: 8px">
                  <a-button
                    :disabled="
                      variantIdsSelected.length === 0 || isSyncingMetaData
                    "
                    block
                    @click="onSyncBtnClick"
                  >
                    <a-tooltip
                      :title="
                        datasetOptions.length
                          ? 'Update ESDL Analytics metadata with the current ESDL(s)'
                          : 'Add the select ESDL(s) to ESDL Analytics metadata'
                      "
                    >
                      <component
                        :is="
                          datasetOptions.length ? SyncOutlined : UploadOutlined
                        "
                        style="vertical-align: 0.1rem"
                      />
                      {{ getAddDatasetLabel() }}
                    </a-tooltip>
                  </a-button>
                </a-row>
                <a-row style="padding-bottom: 8px">
                  <a-button
                    :disabled="
                      isDeletingMetaData || datasetOptions.length === 0
                    "
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

              <a-row>
                <a-typography-title :level="5"
                  >Datasets to compare</a-typography-title
                >
                <a-select
                  v-model:value="datasetSelected"
                  :options="datasetOptions"
                  :disabled="datasetOptions.length === 0"
                  :placeholder="
                    datasetOptions.length === 0
                      ? 'No datasets available'
                      : 'Select a dataset'
                  "
                  mode="multiple"
                  style="width: 100%"
                  @change="onSelectDataset"
                  @mouseleave="removeTooltipPopup"
                />
              </a-row>
            </a-tab-pane>

            <!-- Tab 2: Visualization Settings -->
            <a-tab-pane
              key="visualization"
              tab="Visualization"
              :disabled="datasetSelected.length === 0"
            >
              <a-col>
                <a-row
                  style="align-items: center; justify-content: space-between"
                >
                  <a-typography-title :level="4"
                    >Graph configuration</a-typography-title
                  >
                  <a-col>
                    <a-tooltip title="Add graph configuration to favorites">
                      <a-button
                        size="small"
                        type="text"
                        @click="() => (showSaveGraphConfigModal = true)"
                      >
                        <component
                          :is="StarOutlined"
                          style="vertical-align: 0.1rem"
                        />
                      </a-button>
                    </a-tooltip>
                    <a-tooltip title="Load graph configuration from favorites">
                      <a-button
                        size="small"
                        type="text"
                        @click="onLoadGraphConfigBtnClick"
                      >
                        <component
                          :is="FolderOpenOutlined"
                          style="vertical-align: 0.1rem"
                        />
                      </a-button>
                    </a-tooltip>
                  </a-col>
                  <!-- Modals for Load/Save Graph Configurations -->
                  <a-modal
                    v-model:open="showSaveGraphConfigModal"
                    title="Save graph configuration"
                    ok-text="Save"
                    :ok-button-props="{ disabled: !graphConfigNameInput }"
                    @ok="onSaveGraphConfigBtnClick"
                    @cancel="onCancelGraphConfigModal"
                  >
                    <a-form layout="vertical">
                      <a-form-item label="Name" required>
                        <a-input
                          v-model:value="graphConfigNameInput"
                          placeholder="Enter a name for this graph configuration"
                        />
                      </a-form-item>
                      <a-form-item label="Group">
                        <a-auto-complete
                          v-model:value="graphConfigGroupInput"
                          :options="graphConfigGroupOptions"
                          placeholder="Select an existing group or type a new one"
                          :filter-option="
                            (inputValue, option) =>
                              option.value
                                .toLowerCase()
                                .includes(inputValue.toLowerCase())
                          "
                        />
                      </a-form-item>
                    </a-form>
                  </a-modal>
                  <a-modal
                    v-model:open="showLoadGraphConfigModal"
                    title="Load graph configuration"
                    ok-text="Load"
                    :ok-button-props="{ disabled: !selectedGraphConfigKey }"
                    @ok="onLoadGraphConfigConfirm"
                    @cancel="onCancelLoadGraphConfigModal"
                  >
                    <a-empty
                      v-if="userGraphConfigs.length === 0"
                      description="No saved graph configurations yet"
                    />
                    <a-tree-select
                      v-else
                      v-model:value="selectedGraphConfigKey"
                      :tree-data="graphConfigTreeData"
                      tree-default-expand-all
                      :dropdown-match-select-width="false"
                      style="width: 100%"
                      placeholder="Select a saved graph configuration"
                      @mouseleave="removeTooltipPopup"
                    >
                      <template #title="nodeData">
                        <span
                          style="
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            width: 100%;
                          "
                        >
                          <span>{{ nodeData.title }}</span>
                          <a-button
                            type="text"
                            size="small"
                            danger
                            @click.stop="onDeleteGraphConfigNode(nodeData)"
                          >
                            <component
                              :is="DeleteOutlined"
                              style="vertical-align: 0.1rem"
                            />
                          </a-button>
                        </span>
                      </template>
                    </a-tree-select>
                    <a-typography-text
                      v-if="
                        userGraphConfigs.length > 0 && selectedGraphConfigKey
                      "
                      type="secondary"
                      style="font-size: small; margin-top: 8px; display: block"
                    >
                      After loading, verify that the saved variable, group by,
                      and filter selections are still applicable to the
                      currently selected datasets.
                    </a-typography-text>
                  </a-modal>
                </a-row>
                <a-row>
                  <a-typography-title :level="5">Variable</a-typography-title>
                  <a-select
                    v-model:value="variableSelected"
                    :options="groupOptionsByDatatype(variableOptions)"
                    :disabled="datasetSelected.length === 0"
                    :placeholder="
                      datasetSelected.length === 0
                        ? 'First select a dataset'
                        : 'Select a variable'
                    "
                    style="width: 100%"
                    @change="onSelectVariable"
                    @mouseleave="removeTooltipPopup"
                  />
                  <span
                    v-if="
                      variableSelected !== null && variableWarningMsg !== ''
                    "
                    style="color: #ffbb00; padding: 2px"
                  >
                    {{ variableWarningMsg }}
                  </span>
                </a-row>
                <a-row>
                  <a-row style="align-items: center">
                    <a-typography-title :level="5">Group by</a-typography-title>
                    <!-- Only applicable to profile variable -->
                    <a-row v-if="isProfileVariable" style="align-items: center">
                      <a-tooltip
                        title="Toggle on to display aggregated profiles in the chart. Aggregation is based on the selected group-by options and function. If no group-by option is set, profiles are aggregated across all available profiles of the selected variable."
                      >
                        <a-button size="small" type="text">
                          <component
                            :is="InfoCircleOutlined"
                            style="vertical-align: 0.1rem"
                          />
                        </a-button>
                      </a-tooltip>
                      <a-switch
                        v-model:checked="profileGroupbyEnabled"
                        size="small"
                        style="position: absolute; right: 0px"
                        @change="onProfileGroupbyEnabled"
                      />
                    </a-row>
                  </a-row>
                  <a-select
                    v-model:value="groupbySelected"
                    :options="groupbyOptions"
                    :disabled="
                      datasetSelected.length === 0 ||
                      variableSelected === null ||
                      (isProfileVariable && !profileGroupbyEnabled)
                    "
                    :placeholder="
                      datasetSelected.length === 0
                        ? 'First select a dataset'
                        : variableSelected === null
                          ? 'First select a variable'
                          : 'Select a category'
                    "
                    :max-tag-count="maxGroupbySelectedCount"
                    :status="
                      chartType === 'chart' &&
                      !isProfileVariable &&
                      groupbySelected.length > maxGroupbySelectedCount
                        ? 'warning'
                        : ''
                    "
                    allow-clear
                    mode="multiple"
                    style="width: 100%"
                    @change="onSelectGroupBy"
                    @mouseleave="removeTooltipPopup"
                  />
                  <span
                    v-if="
                      chartType === 'chart' &&
                      !isProfileVariable &&
                      groupbySelected.length > maxGroupbySelectedCount
                    "
                    style="color: #ffbb00; padding: 2px"
                  >
                    Grouping in a bar chart supports up to two selections only.
                  </span>
                  <!-- Only applicable to profile variable -->
                  <a-segmented
                    v-if="isProfileVariable"
                    v-model:value="profileGroupbyAggFuncSelected"
                    :options="profileAggFuncs"
                    style="width: 100%; margin-top: 6px"
                    size="small"
                    block
                    :disabled="isProfileVariable && !profileGroupbyEnabled"
                    @change="onSelectProfileGroupbyAggFunc"
                  />
                </a-row>
                <a-row>
                  <a-row style="align-items: center">
                    <a-typography-title :level="5">Filter</a-typography-title>
                    <a-tooltip title="Type to search filter options">
                      <a-button size="small" type="text">
                        <component
                          :is="InfoCircleOutlined"
                          style="vertical-align: 0.1rem"
                        />
                      </a-button>
                    </a-tooltip>
                  </a-row>
                  <a-cascader
                    v-model:value="filterSelected"
                    style="width: 100%"
                    :options="filterOptions"
                    :disabled="
                      datasetSelected.length === 0 || variableSelected === null
                    "
                    :placeholder="
                      datasetSelected.length === 0
                        ? 'First select a dataset'
                        : variableSelected === null
                          ? 'First select a variable'
                          : 'Select a category'
                    "
                    :show-search="true"
                    allow-clear
                    multiple
                    @change="onSelectFilters"
                    @mouseleave="removeTooltipPopup"
                  />
                  <br />
                </a-row>
                <a-col v-if="currentTrace.length > 0">
                  <br />
                  <a-typography-title :level="4">
                    Display options
                  </a-typography-title>
                  <a-row>
                    <a-segmented
                      v-model:value="chartType"
                      :options="availableChartTypes"
                      style="width: 100%"
                      size="small"
                      block
                      @change="onChartTypeBtnClick"
                    >
                      <template #label="{ payload = {} }">
                        <a-tooltip :title="payload.tooltip">
                          <div style="padding: 4px 4px">
                            <component
                              :is="payload.icon"
                              style="vertical-align: 0.05rem"
                            />
                            <div>{{ payload.label }}</div>
                          </div>
                        </a-tooltip>
                      </template>
                    </a-segmented>
                  </a-row>
                </a-col>
                <!----------------------------------------------->
                <!----- Profile variable - Display options ------>
                <!----------------------------------------------->
                <a-col v-if="isProfileVariable">
                  <a-row style="align-items: center; padding-top: 12px">
                    <a-typography-paragraph
                      style="padding-left: 8px; margin-bottom: 0px"
                    >
                      Downsampling
                      <a-tooltip :title="profileDownsampleMsg">
                        <a-button size="small" type="text">
                          <component
                            :is="InfoCircleOutlined"
                            style="vertical-align: 0.1rem"
                          />
                        </a-button>
                      </a-tooltip>
                    </a-typography-paragraph>
                    <a-switch
                      v-model:checked="profileDownsampling"
                      size="small"
                      style="position: absolute; right: 0px"
                      :disabled="profileVizTypeSelected === 'Aggregated'"
                      @change="onProfileDownsampling"
                    />
                  </a-row>
                  <a-row>
                    <a-typography-title :level="5"
                      >Date selection</a-typography-title
                    >
                    <a-range-picker
                      v-model:value="profileDataRangeSelected"
                      :disabled-date="disabledDate"
                      :show-time="{
                        hideDisabledOptions: true,
                        defaultValue: [
                          dayjs('00:00:00', 'HH:mm:ss'),
                          dayjs('11:59:59', 'HH:mm:ss'),
                        ],
                      }"
                      :format="dateTimeFormat"
                      @change="onSelectProfileDataRange"
                    />
                  </a-row>
                  <!-- Frequency histogram bin size configuration -->
                  <a-col v-if="chartType === 'hist'">
                    <a-typography-title :level="5">Bin size</a-typography-title>
                    <a-row style="align-items: center">
                      <a-typography-paragraph
                        style="padding-left: 8px; margin-bottom: 0px"
                      >
                        Auto bin size
                        <a-tooltip :title="autoBinSizeMsg">
                          <a-button size="small" type="text">
                            <component
                              :is="InfoCircleOutlined"
                              style="vertical-align: 0.1rem"
                            />
                          </a-button>
                        </a-tooltip>
                      </a-typography-paragraph>
                      <a-switch
                        v-model:checked="autoHistogramBinSize"
                        size="small"
                        style="position: absolute; right: 0px"
                        @change="onAutoHistogramBinSize"
                      />
                    </a-row>
                    <a-row
                      v-if="!autoHistogramBinSize"
                      style="align-items: center; padding-top: 8px"
                    >
                      <a-typography-paragraph
                        style="padding-left: 8px; margin-bottom: 0px"
                      >
                        Bin width
                      </a-typography-paragraph>
                      <a-input-number
                        v-model:value="histogramBinWidth"
                        :min="0"
                        :step="0.1"
                        :precision="1"
                        size="small"
                        style="position: absolute; right: 0px; width: 100px"
                        @press-enter="onHistogramBinWidthChange"
                        @blur="onHistogramBinWidthChange"
                      />
                    </a-row>
                  </a-col>
                  <a-row v-if="chartType === 'chart'">
                    <a-typography-title :level="5"
                      >Visualization type</a-typography-title
                    >
                    <a-segmented
                      v-model:value="profileVizTypeSelected"
                      :options="profileVizTypes"
                      style="width: 100%"
                      size="small"
                      block
                      @change="onSelectProfileVizType"
                    />
                  </a-row>
                  <!-- Only show subplot toggle when more than one dataset is selected and with profile data -->
                  <a-row
                    v-if="
                      chartType === 'chart' &&
                      isProfileVariable &&
                      datasetSelected.length > 1
                    "
                    style="align-items: center; padding-top: 12px"
                  >
                    <a-typography-paragraph
                      style="padding-left: 8px; margin-bottom: 0px"
                      >Display in subplots</a-typography-paragraph
                    >
                    <a-switch
                      v-model:checked="profileSubplotView"
                      size="small"
                      style="position: absolute; right: 0px"
                      @change="onProfileSubplotView"
                    />
                  </a-row>
                  <a-row v-if="profileVizTypeSelected === 'Aggregated'">
                    <a-typography-title :level="5"
                      >Aggregation interval</a-typography-title
                    >
                    <a-segmented
                      v-model:value="profileAggIntervalSelected"
                      :options="profileAggIntervals"
                      style="width: 100%"
                      size="small"
                      block
                      @change="onSelectProfileAggInterval"
                    />
                  </a-row>
                  <a-row
                    v-if="profileVizTypeSelected === 'Aggregated'"
                    style="align-items: center"
                  >
                    <a-typography-title :level="5"
                      >Aggregation function</a-typography-title
                    >
                    <a-tooltip
                      title="Aggregates data within the selected time interval using the chosen function."
                    >
                      <a-button size="small" type="text">
                        <component
                          :is="InfoCircleOutlined"
                          style="vertical-align: 0.1rem"
                        />
                      </a-button>
                    </a-tooltip>
                    <a-segmented
                      v-model:value="profileIntervalAggFuncSelected"
                      :options="profileAggFuncs"
                      style="width: 100%"
                      size="small"
                      block
                      @change="onSelectProfileIntervalAggFunc"
                    />
                  </a-row>
                </a-col>
                <!---------------------------------------------------->
                <!----- Display options for Bar / Profile chart ------>
                <!---------------------------------------------------->
                <a-col
                  v-if="
                    chartType !== 'table' &&
                    ((!isProfileVariable && variableSelected !== null) ||
                      isProfileVariable)
                  "
                >
                  <a-row style="width: 100%">
                    <a-typography-title :level="5"
                      >Color palette</a-typography-title
                    >
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
                            :span="Math.round(24 / option.sample.length)"
                            :style="{
                              backgroundColor: color.startsWith('#')
                                ? color
                                : `#${color}`,
                              height: '10px',
                            }"
                          />
                        </a-row>
                      </a-select-option>
                    </a-select>
                  </a-row>
                  <a-radio-group
                    v-if="
                      !isProfileVariable ||
                      (isProfileVariable &&
                        profileVizTypeSelected === 'Aggregated')
                    "
                    v-model:value="dataGrouping"
                    name="groupStackRadio"
                    :options="groupStackOptions"
                    style="
                      display: flex;
                      flex-direction: column;
                      padding-top: 12px;
                    "
                    @change="onSelectDisplayOptions"
                  />
                  <br />
                  <a-row style="align-items: center; padding-top: 12px">
                    <a-typography-paragraph
                      style="padding-left: 8px; margin-bottom: 0px"
                      >Show single tooltip</a-typography-paragraph
                    >
                    <a-switch
                      v-model:checked="showSingleTooltip"
                      size="small"
                      style="position: absolute; right: 0px"
                      @change="onSelectDisplayOptions"
                    />
                  </a-row>
                  <a-row
                    v-if="
                      !isProfileVariable ||
                      (isProfileVariable &&
                        profileVizTypeSelected === 'Aggregated')
                    "
                    style="align-items: center; padding-top: 12px"
                  >
                    <a-typography-paragraph
                      style="padding-left: 8px; margin-bottom: 0px"
                      >Show numbers on bar chart</a-typography-paragraph
                    >
                    <a-switch
                      v-model:checked="showBarNumbers"
                      size="small"
                      style="position: absolute; right: 0px"
                      @change="onSelectDisplayOptions"
                    />
                  </a-row>
                </a-col>
                <!------------------------------------------->
                <!------------- Dataset handler ------------->
                <!------------------------------------------->
                <a-col style="padding-top: 24px; padding-bottom: 16px">
                  <br />
                  <a-row style="padding-bottom: 8px">
                    <a-button
                      :disabled="isSyncingMetaData"
                      block
                      @click="onSyncBtnClick"
                    >
                      <a-tooltip
                        :title="
                          datasetOptions.length
                            ? 'Update ESDL Analytics metadata with the current ESDL(s)'
                            : 'Add the current ESDL(s) to ESDL Analytics metadata'
                        "
                      >
                        <component
                          :is="
                            datasetOptions.length
                              ? SyncOutlined
                              : UploadOutlined
                          "
                          style="vertical-align: 0.1rem"
                        />
                        {{
                          datasetOptions.length
                            ? "Update dataset"
                            : "Add dataset"
                        }}
                      </a-tooltip>
                    </a-button>
                  </a-row>
                  <a-row>
                    <!-- TODO & NOTE: A temporary implementation to clean up dataset -->
                    <a-button
                      :disabled="
                        isDeletingMetaData || datasetOptions.length === 0
                      "
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
            </a-tab-pane>
          </a-tabs>
        </a-col>
      </a-layout-sider>
      <a-layout>
        <a-layout-header class="graph-header">
          <a-button @click="() => (collapsed = !collapsed)">
            <component
              :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
              style="vertical-align: 0.05rem"
            />
          </a-button>
          <!-- Graph header control bar -->
          <a-row class="graph-header-control">
            <!-- Graph editable title -->
            <a-row style="align-items: center">
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
                v-if="chartType === 'table' && currentTrace.length"
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
import { computed, defineProps, h, onMounted, onUnmounted, ref } from "vue";
import {
  AreaChartOutlined,
  BarChartOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  FolderOpenOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  LineChartOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UploadOutlined,
  SaveOutlined,
  StarOutlined,
  SyncOutlined,
  TableOutlined,
} from "@ant-design/icons-vue";
import { Modal } from "ant-design-vue";
import { v4 as uuidv4 } from "uuid";
import AnalyticsPlot from "@/components/plot/AnalyticsPlot.vue";
import { fetchData } from "@/utils/api";
import {
  config,
  normalizePlotlyDateTimeStr,
} from "@/utils/profileVisualization";
import { displayNotification, NotificationType } from "@/utils/notification";
import dayjs from "dayjs";
import minMax from "dayjs/plugin/minMax";
import VueJsTree from "@/components/jstree/VueJsTree.vue";
import { useESDLProjects } from "@/composables/esdlProjects";

const { esdlProject, getESDLProject } = useESDLProjects();

dayjs.extend(minMax);

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: "5rem" },
  spin: true,
});

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const props = defineProps({
  options: {
    type: Object,
    default: null, // If null, the component is instantiated with the default initOptions settings.
  },
});

// ---------------------------------------- //
// ---------- Component options ----------- //
// ---------------------------------------- //

// payload is used by AntD segmented component to display icon
const chartTypes = [
  {
    value: "chart",
    payload: {
      label: "Chart",
      tooltip: "Default visualization chart",
      icon: AreaChartOutlined,
    },
  },
  {
    value: "ldc",
    payload: {
      label: "LDC",
      tooltip: "Load duration cruve",
      icon: LineChartOutlined,
    },
  },
  {
    value: "hist",
    payload: {
      label: "Freq.",
      tooltip: "Frequency histogram",
      icon: BarChartOutlined,
    },
  },
  {
    value: "table",
    payload: { label: "Table", tooltip: "Table", icon: TableOutlined },
  },
];

// Only expose ldc and hist for profile variables
const availableChartTypes = computed(() => {
  if (isProfileVariable.value) return chartTypes;
  return chartTypes.filter((t) => t.value !== "ldc" && t.value !== "hist");
});

const dateTimeFormat = config.dateTimeFormat;
const profileVizTypes = ["Profile", "Aggregated"];
const profileAggIntervals = ["Week", "Month", "Quarter", "Year"];
const profileAggFuncs = ["Mean", "Sum", "Max", "Min", "Count"];

const profileMaxDataPoints = config.profileMaxDataPoints;
const profileDownsampleMsg =
  "Downsampling simplifies large dataset for better chart readability and performance. " +
  "The average value is used to represent data within each interval. " +
  "Toggle it on to explore general trends or off to access the full dataset. " +
  "It is disabled by default for the aggregated visualization type.";

const autoBinSizeMsg =
  "Bin count and width are automatically determined. Switch it off to apply a custom bin width.";

const sampleColorCount = 12;
const colorPalettes = [
  // pie_chart_color_list is defined in area_building_layer.js
  {
    label: "Default",
    value: "Default",
    sample: pie_chart_color_list.slice(0, sampleColorCount),
  },
  {
    label: "Qualitative",
    value: "Qualitative",
    sample: window.palette("mpn65", sampleColorCount),
  },
  {
    label: "Diverging",
    value: "Diverging",
    sample: window.palette("tol-dv", sampleColorCount),
  },
  {
    label: "Sequential",
    value: "Sequential",
    sample: window.palette("tol-sq", sampleColorCount),
  },
  {
    label: "Rainbow",
    value: "Rainbow",
    sample: window.palette("tol-rainbow", sampleColorCount),
  },
];

const groupStackOptions = [
  { label: "Group data", value: 0 },
  { label: "Stack data (totals)", value: 1 },
  { label: "Stack data (percentage)", value: 2 },
];

const maxGroupbySelectedCount = 2;

// The initial (default) option settings of the component
const initOptions = {
  title: "",
  chartType: chartTypes[0].value,
  currentTrace: [],
  currentLayout: {},
  datasetOptions: [],
  datasetSelected: [],
  variableOptions: [],
  variableSelected: null,
  variableWarningMsg: "",
  isProfileVariable: false,
  profileDataRanges: [],
  profileDataRangeSelected: [],
  profileVizTypeSelected: profileVizTypes[0],
  profileDownsampling: true,
  profileSubplotView: false,
  profileGroupbyEnabled: false,
  profileGroupbyAggFuncSelected: profileAggFuncs[0],
  profileAggIntervalSelected: profileAggIntervals[0],
  profileIntervalAggFuncSelected: profileAggFuncs[0],
  groupbyOptions: [],
  groupbySelected: [],
  filterOptions: [],
  filterSelected: [],
  dataGrouping: 1,
  showSingleTooltip: false,
  showBarNumbers: false,
  paletteSelected: colorPalettes[0],
  autoHistogramBinSize: true,
  histogramBinWidth: null,
};

const appliedOptions = props.options === null ? initOptions : props.options;

// ----------------------------------------- //
// ------------ Component states ----------- //
// ----------------------------------------- //

const collapsed = ref(false);

const editingTitle = ref(false);
const activeTabKey = ref("data");

const minWidth = 180;
const inputWidth = ref(minWidth);

const updateTitleInputWidth = (value) => {
  const newWidth = value.target.value.length * 11;
  inputWidth.value = newWidth >= minWidth ? newWidth : minWidth;
};

const isSyncingMetaData = ref(false);
const isDeletingMetaData = ref(false);
const isLoadingData = ref(false);

const title = ref(appliedOptions.title);
const chartType = ref(appliedOptions.chartType);
const currentTrace = ref(appliedOptions.currentTrace);
const currentLayout = ref(appliedOptions.currentLayout);
// A list of selected variant IDs.
const variantIdsSelected = ref([]);
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
const profileSubplotView = ref(appliedOptions.profileSubplotView);
const profileGroupbyEnabled = ref(appliedOptions.profileGroupbyEnabled);
const profileGroupbyAggFuncSelected = ref(
  appliedOptions.profileGroupbyAggFuncSelected,
);
const profileAggIntervalSelected = ref(
  appliedOptions.profileAggIntervalSelected,
);
const profileIntervalAggFuncSelected = ref(
  appliedOptions.profileIntervalAggFuncSelected,
);
const groupbyOptions = ref(appliedOptions.groupbyOptions);
const groupbySelected = ref(appliedOptions.groupbySelected);
const filterOptions = ref(appliedOptions.filterOptions);
const filterSelected = ref(appliedOptions.filterSelected);
const dataGrouping = ref(appliedOptions.dataGrouping);
const showSingleTooltip = ref(appliedOptions.showSingleTooltip);
const showBarNumbers = ref(appliedOptions.showBarNumbers);
const paletteSelected = ref(appliedOptions.paletteSelected);
const autoHistogramBinSize = ref(appliedOptions.autoHistogramBinSize);
const histogramBinWidth = ref(appliedOptions.histogramBinWidth);

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
    profileGroupbyEnabled: profileGroupbyEnabled.value,
    profileGroupbyAggFuncSelected: profileGroupbyAggFuncSelected.value,
    profileAggIntervalSelected: profileAggIntervalSelected.value,
    profileIntervalAggFuncSelected: profileIntervalAggFuncSelected.value,
    groupbyOptions: groupbyOptions.value,
    groupbySelected: groupbySelected.value,
    filterOptions: filterOptions.value,
    filterSelected: filterSelected.value,
    dataGrouping: dataGrouping.value,
    showSingleTooltip: showSingleTooltip.value,
    showBarNumbers: showBarNumbers.value,
    paletteSelected: paletteSelected.value,
    autoHistogramBinSize: autoHistogramBinSize.value,
    histogramBinWidth: histogramBinWidth.value,
  };
};

defineExpose({
  getOptions,
});

const energyUnitOptions = [
  { label: "No conversion", value: "None" },
  { label: "PJ", value: "PJ" },
  { label: "TJ", value: "TJ" },
  { label: "GJ", value: "GJ" },
  { label: "MJ", value: "MJ" },
  { label: "J", value: "J" },
  { label: "TWh", value: "TWh" },
  { label: "GWh", value: "GWh" },
  { label: "MWh", value: "MWh" },
  { label: "kWh", value: "kWh" },
];
const energyUnit = ref(energyUnitOptions[0].value);

// -------------------------------------------------- //
// --------- Load/Save Graph Configurations --------- //
// -------------------------------------------------- //

const userGraphConfigs = ref([]);

const showSaveGraphConfigModal = ref(false);
const graphConfigNameInput = ref("");
const graphConfigGroupInput = ref(undefined);

const showLoadGraphConfigModal = ref(false);
const selectedGraphConfigKey = ref(undefined);

// A list of unique group names already used by saved graph configurations, for the Group auto-complete options.
const graphConfigGroupOptions = computed(() => {
  const groups = new Set(
    userGraphConfigs.value.map((c) => c.group).filter((g) => !!g),
  );
  return Array.from(groups).map((g) => ({ value: g }));
});

// Tree data grouping saved graph configurations by group ('folder') for the Load modal's tree select.
const graphConfigTreeData = computed(() => {
  const groups = {};
  userGraphConfigs.value.forEach((c) => {
    const groupName = c.group || "Ungrouped";
    if (!groups[groupName]) {
      groups[groupName] = [];
    }
    groups[groupName].push(c);
  });

  return Object.entries(groups).map(([groupName, configs]) => ({
    key: `group:${groupName}`,
    value: `group:${groupName}`,
    title: groupName,
    selectable: false,
    children: configs.map((c) => ({
      key: `config:${c.id}`,
      value: `config:${c.id}`,
      title: `${c.name} (${dayjs(c.lastUpdate).format(dateTimeFormat)})`,
      isLeaf: true,
    })),
  }));
});

const fetchUserGraphConfigs = async () => {
  console.debug("Fetching user graph configurations...");
  try {
    const configs = await fetchData("datamanager/get_graph_configs");
    userGraphConfigs.value = configs;
  } catch (error) {
    console.error(error);
    displayNotification(
      NotificationType.ERROR,
      "Failed to retrieve saved graph configurations.",
    );
  }
};

const resetGraphConfigModalInputs = () => {
  graphConfigNameInput.value = "";
  graphConfigGroupInput.value = undefined;
};

const onSaveGraphConfigBtnClick = async () => {
  if (!graphConfigNameInput.value) {
    return;
  }

  const graphConfig = getOptions();

  const configSetting = {
    id: uuidv4(),
    group: graphConfigGroupInput.value || "Ungrouped",
    name: graphConfigNameInput.value,
    // Used as a simple way to distinguish settings sharing the same name and group.
    lastUpdate: Date.now(),
    // Do not save trace and layout states as it should be updated when the config is applied and the chart is loaded.
    config: {
      ...graphConfig,
      currentTrace: [],
      currentLayout: {},
    },
  };

  const updatedConfigs = [...userGraphConfigs.value, configSetting];

  try {
    const savedConfigs = await fetchData("datamanager/save_graph_configs", {
      configs: updatedConfigs,
    });
    userGraphConfigs.value = savedConfigs;
    displayNotification(
      NotificationType.SUCCESS,
      `Graph configuration '${configSetting.name}' saved.`,
    );
  } catch (error) {
    // On failure the backend returns None; keep the current userGraphConfigs state unchanged.
    console.error(error);
    displayNotification(
      NotificationType.ERROR,
      `Failed to save graph configuration '${configSetting.name}'.`,
    );
  } finally {
    resetGraphConfigModalInputs();
    showSaveGraphConfigModal.value = false;
  }
};

const onCancelGraphConfigModal = () => {
  resetGraphConfigModalInputs();
};

const onLoadGraphConfigBtnClick = () => {
  selectedGraphConfigKey.value = undefined;
  showLoadGraphConfigModal.value = true;
};

/**
 * Restores the visualization settings from a previously saved graph configuration
 * and refreshes the variable/groupby/filter option lists from the backend.
 *
 * Dataset selection is intentionally not restored — the configuration applies
 * to whatever datasets are currently selected.
 *
 * @param {Object} graphConfig A graphConfig object (the .config field of a saved entry).
 */
const applyConfig = async (graphConfig) => {
  title.value = graphConfig.title;
  chartType.value = graphConfig.chartType;
  currentTrace.value = graphConfig.currentTrace;
  currentLayout.value = graphConfig.currentLayout;
  variableSelected.value = graphConfig.variableSelected;
  variableWarningMsg.value = graphConfig.variableWarningMsg;
  isProfileVariable.value = graphConfig.isProfileVariable;
  profileDataRanges.value = graphConfig.profileDataRanges;
  profileDataRangeSelected.value = graphConfig.profileDataRangeSelected;
  profileVizTypeSelected.value = graphConfig.profileVizTypeSelected;
  profileDownsampling.value = graphConfig.profileDownsampling;
  profileGroupbyEnabled.value = graphConfig.profileGroupbyEnabled;
  profileGroupbyAggFuncSelected.value =
    graphConfig.profileGroupbyAggFuncSelected;
  profileAggIntervalSelected.value = graphConfig.profileAggIntervalSelected;
  profileIntervalAggFuncSelected.value =
    graphConfig.profileIntervalAggFuncSelected;
  groupbySelected.value = graphConfig.groupbySelected;
  filterSelected.value = graphConfig.filterSelected;
  dataGrouping.value = graphConfig.dataGrouping;
  showSingleTooltip.value = graphConfig.showSingleTooltip;
  showBarNumbers.value = graphConfig.showBarNumbers;
  paletteSelected.value = graphConfig.paletteSelected;
  autoHistogramBinSize.value = graphConfig.autoHistogramBinSize;
  histogramBinWidth.value = graphConfig.histogramBinWidth;

  // Refresh variable/groupby/filter option lists based on the current dataset selection.
  // These are cleared so the UI reflects what is actually available from the live datasets.
  variableOptions.value = {};
  groupbyOptions.value = [];
  filterOptions.value = [];

  if (datasetSelected.value.length) {
    await updateVariables();
  }
  if (datasetSelected.value.length && variableSelected.value !== null) {
    await updateColumns();
  }
};

const onLoadGraphConfigConfirm = async () => {
  if (!selectedGraphConfigKey.value) {
    return;
  }

  const configId = selectedGraphConfigKey.value.slice("config:".length);
  const selectedConfig = userGraphConfigs.value.find((c) => c.id === configId);

  if (selectedConfig) {
    // Restores visualization settings and refreshes variable/groupby/filter options
    // based on the currently selected datasets.
    await applyConfig(selectedConfig.config);
    updateTrace();
  }

  selectedGraphConfigKey.value = undefined;
  showLoadGraphConfigModal.value = false;
};

const onCancelLoadGraphConfigModal = () => {
  selectedGraphConfigKey.value = undefined;
};

/**
 * Persists the updated graph configurations list to the backend.
 * If saving fails, reverts userGraphConfigs back to its previous value and notifies the user.
 *
 * @param {Array} updatedConfigs The full list of graph configurations after the deletion.
 * @param {Array} previousConfigs The full list of graph configurations before the deletion, used to revert on failure.
 */
const persistGraphConfigDeletion = async (updatedConfigs, previousConfigs) => {
  userGraphConfigs.value = updatedConfigs;
  try {
    const savedConfigs = await fetchData("datamanager/save_graph_configs", {
      configs: updatedConfigs,
    });
    userGraphConfigs.value = savedConfigs;
  } catch (error) {
    console.error(error);
    displayNotification(
      NotificationType.ERROR,
      "Failed to delete graph configuration(s). Please try again.",
    );
    userGraphConfigs.value = previousConfigs;
  }
};

/**
 * Deletes a group (and all the saved graph configurations within it) or a single saved graph
 * configuration from the Load graph configuration tree, after user confirmation, and syncs the
 * change with the backend.
 *
 * @param {Object} nodeData The tree node data of the group or saved configuration to delete.
 */
const onDeleteGraphConfigNode = (nodeData) => {
  const key = nodeData.key ?? nodeData.value;
  if (typeof key !== "string") {
    return;
  }

  if (key.startsWith("group:")) {
    const groupName = key.slice("group:".length);
    Modal.confirm({
      title: `Delete group '${groupName}'?`,
      content:
        "This will delete all saved graph configurations within this group.",
      okText: "Delete",
      okType: "danger",
      onOk: async () => {
        const previousConfigs = userGraphConfigs.value;
        const updatedConfigs = previousConfigs.filter(
          (c) => (c.group || "Ungrouped") !== groupName,
        );
        await persistGraphConfigDeletion(updatedConfigs, previousConfigs);
        if (
          selectedGraphConfigKey.value &&
          !userGraphConfigs.value.some(
            (c) => `config:${c.id}` === selectedGraphConfigKey.value,
          )
        ) {
          selectedGraphConfigKey.value = undefined;
        }
      },
    });
  } else if (key.startsWith("config:")) {
    const configId = key.slice("config:".length);
    const target = userGraphConfigs.value.find((c) => c.id === configId);
    Modal.confirm({
      title: `Delete '${target?.name ?? "this configuration"}'?`,
      okText: "Delete",
      okType: "danger",
      onOk: async () => {
        const previousConfigs = userGraphConfigs.value;
        const updatedConfigs = previousConfigs.filter((c) => c.id !== configId);
        await persistGraphConfigDeletion(updatedConfigs, previousConfigs);
        if (selectedGraphConfigKey.value === key) {
          selectedGraphConfigKey.value = undefined;
        }
      },
    });
  }
};

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
    variableWarningMsg.value =
      "The selected variable only exists in dataset: " +
      `${value.ds.map((d) => `'${d}'`).join(", ")}`;
  } else {
    variableWarningMsg.value = "";
  }

  isProfileVariable.value = value.datatype === "PROFILE";

  // falls back to default chart type if the user had ldc/hist selected and then picks a non-profile variable.
  if (
    !isProfileVariable.value &&
    (chartType.value === "ldc" || chartType.value === "hist")
  ) {
    chartType.value = "chart";
  }

  updateColumns().then(() => {
    // Retains user-applied groupbys and filters if they match the new variable options; discard otherwise.
    const appliedGroupbys = groupbySelected.value;
    const varGroupbyOptions = groupbyOptions.value.map((opt) => opt.value);
    groupbySelected.value = appliedGroupbys.filter((g) =>
      varGroupbyOptions.includes(g),
    );

    const appliedFilters = filterSelected.value;
    const varFilterOptions = [];
    filterOptions.value.forEach((opt) => {
      opt.children.forEach((c) => {
        varFilterOptions.push([opt.value, c.value]);
      });
    });
    filterSelected.value = appliedFilters.filter((f) => {
      // filter is applied at the parent level (e.g. ['region'])
      if (f.length === 1 && varFilterOptions.some((opt) => opt[0] === f[0])) {
        return f;
      }
      // filter is applied at the parent-child combined level (e.g. ['region', 'Utrecht'])
      else if (
        varFilterOptions.some((opt) => opt[0] === f[0] && opt[1] === f[1])
      ) {
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

const onChartTypeBtnClick = (value) => {
  chartType.value = value;

  // Switch off profile downsampling when chartType is not 'chart' (could be misleading)
  if (
    isProfileVariable.value &&
    profileDownsampling.value &&
    chartType.value !== "chart"
  ) {
    profileDownsampling.value = false;
    displayNotification(
      NotificationType.INFO,
      "Downsampling has been turned off for this view to avoid hiding data points. You can turn it back on anytime in the display options",
    );
  }

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
  if (profileVizTypeSelected.value !== "Profile") {
    profileDownsampling.value = false;
    displayNotification(
      NotificationType.INFO,
      "Downsampling has been turned off for this view.",
    );
  } else {
    profileDownsampling.value = true;
  }
  updateTrace();
};

const onProfileDownsampling = () => {
  updateTrace();
};

const onAutoHistogramBinSize = () => {
  if (autoHistogramBinSize.value) {
    histogramBinWidth.value = null;
  }
  updateTrace();
};

const onHistogramBinWidthChange = () => {
  updateTrace();
};

const onProfileSubplotView = () => {
  updateTrace();
};

/**
 * Triggered to update profileDataRangeSelected state when newLayoutRanges is emitted from
 * the user interaction with AnalyticsPlot (zoom in/out or pan).
 * Only updateTrace() when interacting with profile data and the chartType is 'chart'.
 *
 * @param {Object|null} newLayoutRanges An object with structure as {x: [xaxis.range[0], xaxis.range[1]], y: [yaxis.range[0], yaxis.range[1]]}
 *                                      when zoom in/out or pan event is occurred; otherwise, null is returned.
 */
const onAnalyticsPlotRelayout = (newLayoutRanges) => {
  if (!isProfileVariable.value) {
    return;
  }

  if (isProfileVariable.value && chartType.value !== "chart") {
    return;
  }

  if (profileVizTypeSelected.value !== "Profile") {
    return;
  }

  // Restore to default data range when newLayoutRanges is null.
  if (newLayoutRanges === null) {
    profileDataRangeSelected.value = [];
  }
  // Apply subset of data range for querying data.
  else {
    try {
      const normalizedDateTimeRanges = newLayoutRanges["x"].map((dt) => {
        return normalizePlotlyDateTimeStr(dt);
      });
      profileDataRangeSelected.value = dtStringsToDayJsObjects(
        normalizedDateTimeRanges,
      );
    } catch (error) {
      displayNotification(
        NotificationType.ERROR,
        `An error occurred while applying the selected data extent for querying: ${error}`,
      );
    }
  }

  updateTrace();
};

const onProfileGroupbyEnabled = () => {
  // Reset to default value when switching off
  if (profileGroupbyEnabled.value === false) {
    profileGroupbyAggFuncSelected.value =
      initOptions.profileGroupbyAggFuncSelected;
    groupbySelected.value = initOptions.groupbySelected;
  }
  updateTrace();
};

const onSelectProfileGroupbyAggFunc = () => {
  updateTrace();
};

const onSelectProfileAggInterval = () => {
  updateTrace();
};

const onSelectProfileIntervalAggFunc = () => {
  updateTrace();
};

onMounted(() => {
  console.info("Initializing ESDL Analytics");

  fetchUserGraphConfigs();

  getESDLProject(); // Get project data with variant hierarchy
  updateDatasets();
});

onUnmounted(() => {
  console.info("Unmounting ESDL Analytics");
});

// ------------------------------------- //
// ------- Variant Tree Setup ---------- //
// ------------------------------------- //

// Tree data for the variant selection
const treeData = computed(() => {
  if (esdlProject.value && esdlProject.value.variants.length > 0) {
    const rootVariants = [];

    // Process variants recursively to maintain the hierarchy
    for (const variant of esdlProject.value.variants) {
      rootVariants.push(variantToJstreeData(variant));
    }

    return rootVariants;
  }
  return null;
});

// Helper function to recursively convert variants to jstree data format
function variantToJstreeData(variant) {
  const children = [];

  // Process child variants
  for (const child of variant.children || []) {
    children.push(variantToJstreeData(child));
  }

  return {
    id: variant.id,
    esId: variant.es_id,
    text: variant.name,
    children: children,
    type: "variant",
    state: {
      checked: variantIdsSelected.value.includes(variant.id),
      opened: children.length > 0,
    },
  };
}

// Tree type specifications
class VariantTreeSpec {
  constructor() {
    this.type = "variant";
    this.icon = "fas fa-bezier-curve";
  }
}

const treeTypeSpecs = [new VariantTreeSpec()];

/**
 * Recursively collects all child node IDs from a JSTree node
 *
 * @param {Object} node - The JSTree node to get children from
 * @param {Object} treeInstance - The JSTree instance
 * @returns {Array} Array of child node IDs
 */
const getAllChildIds = (node, treeInstance) => {
  let childIds = [];
  if (node.children && node.children.length > 0) {
    // For each child, get its ID and recursively get its children's IDs
    for (const childId of node.children) {
      const childNode = treeInstance.get_node(childId);
      childIds.push(childNode.id);
      childIds = childIds.concat(getAllChildIds(childNode, treeInstance));
    }
  }
  return childIds;
};

// Tree event handlers
const treeEventHandlers = {
  "check_node.jstree": function (e, data) {
    if (data.node.type === "variant") {
      const variantId = data.node.id;
      if (!variantIdsSelected.value.includes(variantId)) {
        variantIdsSelected.value.push(variantId);
      }

      const isShiftPressed = data.event && data.event.shiftKey;
      // If shift key is pressed, select all children
      if (isShiftPressed) {
        const childIds = getAllChildIds(data.node, data.instance);
        console.log("Selected children", childIds);

        for (const childId of childIds) {
          if (!variantIdsSelected.value.includes(childId)) {
            variantIdsSelected.value.push(childId);
            data.instance.check_node(childId);
          }
        }
      }
    }
  },
  "uncheck_node.jstree": function (e, data) {
    if (data.node.type === "variant") {
      const variantId = data.node.id;
      const index = variantIdsSelected.value.indexOf(variantId);
      if (index !== -1) {
        variantIdsSelected.value.splice(index, 1);
      }

      const isShiftPressed = data.event && data.event.shiftKey;
      // If shift key is pressed, unselect all children
      if (isShiftPressed) {
        const childIds = getAllChildIds(data.node, data.instance);

        for (const childId of childIds) {
          const childIndex = variantIdsSelected.value.indexOf(childId);
          if (childIndex !== -1) {
            variantIdsSelected.value.splice(childIndex, 1);
            data.instance.uncheck_node(childId);
          }
        }
      }
    }
  },
};

// ------------------------------------- //
// --------- Component methods --------- //
// ------------------------------------- //

/**
 * Modifies DataManager metadata with specified action using a WebSocket connection.
 *
 * @param {string} action The action to be performed ("add_update", "delete").
 * @param {Object} requestBody The request body required by the specified action.
 * @returns {Promise<Object>} A promise that resolves with the parsed response object or rejects with an error.
 */
const modifyMetadata = async (action, requestBody) => {
  return new Promise((resolve, reject) => {
    const path = `datamanager/metadata/${action}`;
    window.socket.emit(path, requestBody, (response) => {
      if (response) {
        resolve(JSON.parse(response));
      } else {
        reject(
          new Error(
            `An unknown error occurred while modifying metadata from ${path}`,
          ),
        );
      }
    });
  });
};

const getAddDatasetLabel = () => {
  if (datasetOptions.value.length) {
    return "Update dataset";
  } else if (variantIdsSelected.value.length) {
    return "Add dataset from selected ESDLs";
  } else {
    return "Please select ESDLs";
  }
};

/**
 * Recursively finds selected variants in the variant hierarchy.
 *
 * @param {Array} variants - The array of variants to search through
 * @param {Array} selectedVariantIds - Array of selected variant IDs
 * @param {Array} result - Array to collect the selected variants
 */
const findSelectedVariants = (variants, selectedVariantIds, result = []) => {
  for (const variant of variants) {
    if (selectedVariantIds.includes(variant.id)) {
      result.push({
        value: variant.id,
        label: variant.name,
        esId: variant.es_id,
      });
    }

    // Process children recursively
    if (variant.children && variant.children.length > 0) {
      findSelectedVariants(variant.children, selectedVariantIds, result);
    }
  }

  return result;
};

/**
 * Adds or updates ESDLs into metadata by iterating over the list of energy systems.
 */
const onSyncBtnClick = async () => {
  console.debug("Synchronizing ESDLs into metadata");
  isSyncingMetaData.value = true;

  const selectedVariants = [];
  if (esdlProject.value && esdlProject.value.variants) {
    findSelectedVariants(
      esdlProject.value.variants,
      variantIdsSelected.value,
      selectedVariants,
    );
  }
  console.debug("Selected variants", selectedVariants);

  try {
    // Process variants sequentially
    for (const variant of selectedVariants) {
      const esId = variant.value;
      const esTitle = variant.label;

      try {
        displayNotification(
          NotificationType.INFO,
          `Adding ${esTitle} [${esId}] into the database.`,
        );
        const reqBody = { es_id: esId, energyUnit: energyUnit.value };
        const resp = await modifyMetadata("add_update", reqBody);
        displayNotification(resp.status, resp.message);
      } catch (error) {
        console.error(error);
        displayNotification(
          NotificationType.ERROR,
          `An unknown error occurred while adding ${esTitle} [${esId}] to the database`,
        );
      }
    }
    await updateDatasets();
  } catch (error) {
    console.error(error);
    displayNotification(
      NotificationType.ERROR,
      `An error occurred while synchronizing metadata: ${error}`,
    );
  } finally {
    // Reset selection
    resetMenuToDefault();

    isSyncingMetaData.value = false;
  }
};

/**
 * TODO & NOTE: A temporary implementation to clean up metadata.
 * The clean up should be a background process when the user session ends.
 */
const onDeleteBtnClick = async () => {
  console.debug("Deleting user associated metadata");
  isDeletingMetaData.value = true;
  try {
    // If dataset_name is not specified, all metadata associated with the session user will be deleted.
    const reqBody = { dataset_name: null };
    const resp = await modifyMetadata("delete", reqBody);
    displayNotification(resp.status, resp.message);
    await updateDatasets();
  } catch (error) {
    console.error(error);
    displayNotification(
      NotificationType.ERROR,
      `An error occurred while deleting metadata: ${error}`,
    );
  } finally {
    // Reset selection
    resetMenuToDefault();

    isDeletingMetaData.value = false;
  }
};

/**
 * Reset menu to the default configuration state.
 */
const resetMenuToDefault = () => {
  title.value = initOptions.title;
  chartType.value = initOptions.chartType;
  currentTrace.value = initOptions.currentTrace;
  currentLayout.value = initOptions.currentLayout;
  datasetSelected.value = initOptions.datasetSelected;
  variableSelected.value = initOptions.variableSelected;
  groupbySelected.value = initOptions.groupbySelected;
  filterSelected.value = initOptions.filterSelected;
  isProfileVariable.value = initOptions.isProfileVariable;
  profileDataRangeSelected.value = initOptions.profileDataRangeSelected;
  profileVizTypeSelected.value = initOptions.profileVizTypeSelected;
  profileDownsampling.value = initOptions.profileDownsampling;
  profileSubplotView.value = initOptions.profileSubplotView;
  profileGroupbyEnabled.value = initOptions.profileGroupbyEnabled;
  profileGroupbyAggFuncSelected.value =
    initOptions.profileGroupbyAggFuncSelected;
  profileAggIntervalSelected.value = initOptions.profileAggIntervalSelected;
  profileIntervalAggFuncSelected.value =
    initOptions.profileIntervalAggFuncSelected;
  dataGrouping.value = initOptions.dataGrouping;
  showSingleTooltip.value = initOptions.showSingleTooltip;
  showBarNumbers.value = initOptions.showBarNumbers;
  paletteSelected.value = initOptions.paletteSelected;
  autoHistogramBinSize.value = initOptions.autoHistogramBinSize;
  histogramBinWidth.value = initOptions.histogramBinWidth;
};

/**
 * Asynchronously fetches DataManager datasets and updates the dataset options.
 *
 * @returns {Promise<void>} A promise that resolves when the datasets have been fetched and the options updated.
 */
const updateDatasets = async () => {
  console.debug("Fetching DataManager datasets");
  try {
    const datasets = await fetchData("datamanager/datasets");
    if (datasets.length) {
      datasetOptions.value = datasets.map((d) => ({
        value: d.id, // This id refers to the dataset id in the database, not the es_id of the ESDL variant.
        label: `${d.name}`,
        uniqueDsId: `${d.es_id}_${d.name}`,
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
const updateVariables = async () => {
  console.debug("Fetching DataManager variables");
  if (datasetSelected.value.length) {
    try {
      const reqBody = { dataset_ids: datasetSelected.value };
      const variables = await fetchData("datamanager/variables", reqBody);

      const options = {};
      variables.forEach((v) => {
        if (!Object.keys(options).includes(v.name)) {
          // todo: distinguish between SINGLE value and PROFILE datatypes
          options[v.name] = {
            value: v.name,
            label: v.label,
            ds: [v.dataset],
            unit: v.unit,
            description: v.description,
            datatype: v.datatype,
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
    const existingGroup = acc.find((group) => group.label === datatype);
    if (existingGroup) {
      existingGroup.options.push({ ...rest, datatype });
    } else {
      acc.push({
        label: datatype,
        options: [{ ...rest, datatype }],
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
const updateColumns = async () => {
  console.debug("Fetching DataManager columns");
  if (datasetSelected.value.length && variableSelected.value !== null) {
    try {
      const reqBody = {
        dataset_ids: datasetSelected.value,
        variable_name: variableSelected.value,
      };
      const varFilterOptions = await fetchData("datamanager/columns", reqBody);

      groupbyOptions.value = Object.entries(varFilterOptions).map(
        ([name, val]) => {
          const optValue =
            val.column === "labels" ? `labels/${val.key}` : val.column;
          return {
            value: optValue,
            label: name,
          };
        },
      );

      filterOptions.value = Object.entries(varFilterOptions).map(
        ([name, val]) => {
          const optValue =
            val.column === "labels" ? `labels/${val.key}` : val.column;
          return {
            value: optValue,
            label: name,
            children: val.options.map((option) => ({
              value: option,
              label: option,
            })),
          };
        },
      );
    } catch (error) {
      console.error(error);
    }
  }
};

/**
 * Fetches metadata and updates the trace and layout configuration based on the user selections
 * such as selected datasets, variable, group by options, filter options, and chart type.
 */
const updateTrace = async () => {
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

  // Only take the first two elements as group_by selections for a bar chart visualization.
  const groupBySelection =
    chartType.value === "chart" && !queryProfileData
      ? groupbySelected.value.slice(0, maxGroupbySelectedCount)
      : groupbySelected.value;

  let filterSelection = {};
  filterSelected.value.forEach((filter) => {
    const [column, val] = filter;
    if (filterSelection[column] === undefined) {
      filterSelection[column] = [];
    }
    filterSelection[column].push(val);
  });

  let options = {
    dataset_ids: datasetSelected.value,
    variable_name: variableSelected.value,
    group_by: groupBySelection,
    filters: filterSelection,
    chart_type: chartType.value,
    profile: null,
  };

  // Conditionally updates profile data query options.
  if (queryProfileData) {
    options["profile"] = {
      viz_type: profileVizTypeSelected.value,
      data_range:
        profileDataRangeSelected.value !== null
          ? profileDataRangeSelected.value.map((dt) => formatAsDateTimeStr(dt))
          : [],
      group_by_enabled: profileGroupbyEnabled.value,
    };
    if (profileGroupbyEnabled.value) {
      options["profile"]["group_by_agg_func"] =
        profileGroupbyAggFuncSelected.value;
    }
    if (profileDownsampling.value) {
      options["profile"]["max_datapoints"] = profileMaxDataPoints;
    }
    if (profileVizTypeSelected.value === "Aggregated") {
      options["profile"]["agg_interval"] = profileAggIntervalSelected.value;
      options["profile"]["agg_func"] = profileIntervalAggFuncSelected.value;
    }
  }

  try {
    const results = await fetchData("datamanager/query", options);
    const traces = results["traces"];
    if (queryProfileData) {
      profileDataRanges.value = dtStringsToDayJsObjects(results["data_range"]);
      if (results["error_msg"] !== "") {
        displayNotification(NotificationType.ERROR, results["error_msg"]);
        console.error(results["errors"]);
      }
      if (results["warning_msg"] !== "") {
        displayNotification(NotificationType.WARNING, results["warning_msg"]);
        console.warn(results["warnings"]);
      }

      let formattedData;
      if (chartType.value === "table") {
        formattedData = tableTraceHandler(traces);
      } else if (chartType.value === "hist") {
        formattedData = histTraceHandler(traces);
      } else {
        formattedData = profileTraceHandler(traces);
      }
      currentTrace.value = formattedData.traces;
      currentLayout.value = formattedData.layout;
    } else {
      const formattedData =
        chartType.value === "table"
          ? tableTraceHandler(traces)
          : barChartTraceHandler(traces);
      currentTrace.value = formattedData.traces;
      currentLayout.value = formattedData.layout;
    }
  } catch (error) {
    console.error(error);
    displayNotification(NotificationType.ERROR, `${error}`);
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
  return dtStrings.length
    ? dtStrings.map((dt) => dayjs(dt, dateTimeFormat))
    : [];
};

const disabledDate = (current) => {
  if (profileDataRanges.value.length) {
    return (
      current < profileDataRanges.value[0] ||
      current > profileDataRanges.value[1]
    );
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
  const isGroupbyAggregated = profileGroupbyEnabled.value;
  const isAggregated = profileVizTypeSelected.value === "Aggregated";
  const displaySubplots = profileSubplotView.value;
  const subplotGroups = [...new Set(traces.map((t) => t["legendgroup"]))];

  let grid = {};
  // Display profiles in stacked subplots
  if (displaySubplots) {
    grid = {
      rows: subplotGroups.length,
      columns: 1,
      pattern: "coupled",
      roworder: "bottom to top",
    };
  }

  traces.forEach((t, idx) => {
    t.type = isAggregated ? "bar" : "scatter";
    t.mode = isAggregated ? null : "lines";
    t.text =
      isAggregated && showBarNumbers.value ? t.y.map((y) => y.toFixed(1)) : "";
    t.marker = { color: colorscale[idx % colorscale.length] };
    // Display the additional groupby aggregated profile data with dot lines
    if (isGroupbyAggregated && !isAggregated && t["isGroupbyAggregated"]) {
      t.line = { dash: "dot" };
    }

    if (t.name.length >= 25) {
      t.name = t.name.replace(new RegExp(`(.{1,${25}})`, "g"), "$1<br>");
    }

    const axisId = subplotGroups.findIndex((g) => g === t["legendgroup"]);
    if (displaySubplots && axisId >= 0) {
      t.xaxis = "x"; // share x axis
      t.yaxis = `y${axisId + 1}`;
    }
  });

  const profileLayout = {
    title: variableSelected.value,
    xaxis: { automargin: true },
    hovermode: showSingleTooltip.value ? "closest" : "x unified",
    hoversubplots: "axis",
    legend: { groupclick: "toggleitem" },
    grid: grid,
    barmode:
      isAggregated && [1, 2].includes(dataGrouping.value)
        ? "relative"
        : "group",
    barnorm: isAggregated && dataGrouping.value === 2 ? "percent" : "",
    showlegend: true,
    autosize: true,
  };

  // Define multiple y-axes dynamically
  subplotGroups.forEach((_, idx) => {
    profileLayout[`yaxis${idx + 1}`] = {
      title: variableOptions.value[variableSelected.value].unit,
      automargin: true,
      anchor: "x", // Ensure all y-axes are anchored to the same x-axis
    };
  });

  return {
    traces: traces,
    layout: profileLayout,
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
    t.type = "bar";
    t.text = showBarNumbers.value ? t.y.map((y) => y.toFixed(1)) : "";
    t.marker = { color: colorscale[idx % colorscale.length] };
    if (t.name.length >= 25) {
      t.name = t.name.replace(new RegExp(`(.{1,${25}})`, "g"), "$1<br>");
    }
  });

  const barChartLayout = {
    title: variableSelected.value,
    xaxis: {
      type: "multicategory",
      automargin: true,
    },
    yaxis: {
      title: variableOptions.value[variableSelected.value].unit,
      automargin: true,
      exponentformat: "SI", // see https://github.com/plotly/plotly.py/issues/4787 for values larger than Giga...
      //ticksuffix: variableOptions.value[variableSelected.value].unit,
    },
    hovermode: showSingleTooltip.value ? "closest" : "x unified",
    barmode: [1, 2].includes(dataGrouping.value) ? "stack" : "group",
    barnorm: dataGrouping.value === 2 ? "percent" : "",
    showlegend: true,
    autosize: true,
  };

  return {
    traces: traces,
    layout: barChartLayout,
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
    case "Qualitative":
      // The maximum number of colors: 65
      colorscale = window.palette("mpn65", numColors > 65 ? 65 : numColors);
      break;
    case "Diverging":
      colorscale = window.palette("tol-dv", numColors);
      break;
    case "Sequential":
      colorscale = window.palette("tol-sq", numColors);
      break;
    case "Rainbow":
      colorscale = window.palette("tol-rainbow", numColors);
      break;
    case "Default":
    default:
  }
  return colorscale;
};

/**
 * Configures frequency histogram traces and layout for visualization.
 *
 * @param {Array} traces An array of histogram trace objects with bin label strings as x and counts as y.
 * @returns {Object} An object containing the configured traces and layout.
 */
const histTraceHandler = (traces) => {
  const colorscale = generateColorscale(paletteSelected.value, traces.length);

  // Without an explicit start, Plotly centers bins on data values (e.g. -0.5 to 0.5) rather than
  // aligning edges to whole numbers (e.g. 0 to 1); anchor to the floored min across all traces instead.
  const allValues = traces.flatMap((t) => t.y);
  const minValue = allValues.reduce((min, v) => (v < min ? v : min), Infinity);
  const binStart = allValues.length ? Math.floor(minValue) : 0;

  traces.forEach((t, idx) => {
    t.type = "histogram";
    // bingroup forces Plotly to compute identical bin edges across all traces
    t.bingroup = "hist";
    // Plotly histogram bins t.x values; profile values are in t.y, so swap them
    t.x = t.y;
    delete t.y;
    t.xbins = { start: binStart };
    // Custom bin width: pass to Plotly's xbins if user has disabled auto
    if (!autoHistogramBinSize.value && histogramBinWidth.value !== null) {
      t.xbins.size = histogramBinWidth.value;
    }
    t.marker = { color: colorscale[idx % colorscale.length], opacity: 0.75 };
    if (t.name.length >= 25) {
      t.name = t.name.replace(new RegExp(`(.{1,${25}})`, "g"), "$1<br>");
    }
  });

  const histLayout = {
    title: variableSelected.value,
    xaxis: {
      title: variableOptions.value[variableSelected.value].unit,
      automargin: true,
    },
    yaxis: {
      title: "Frequency",
      automargin: true,
    },
    bargap: 0.1,
    hovermode: "x unified",
    barmode: "overlay",
    showlegend: true,
    autosize: true,
  };

  return {
    traces: traces,
    layout: histLayout,
  };
};

/**
 * Configures table traces and layout for visualization.
 *
 * @param {Array} traces An array containing a single object of table header and cell values.
 * @returns {Object} An object containing the formatted table trace and layout configuration.
 */
const tableTraceHandler = (traces) => {
  const formattedTableHeader = traces[0].header.values.map((col) => [
    `<b>${col[0]}</b>`,
  ]);
  const tableCellValues = traces[0].cells.values;

  const tableTrace = [
    {
      type: "table",
      header: {
        values: formattedTableHeader,
        align: "left",
        fill: { color: "#fafafa" },
        line: { width: 0.5, color: "#c4c4c4" },
        font: { size: 15, color: "black", textcase: "word caps" },
      },
      cells: {
        values: tableCellValues,
        align: "left",
        height: 25,
        line: { width: 0.5, color: "#c4c4c4" },
        font: { size: 14, color: "black" },
      },
    },
  ];
  const tableLayout = {
    title: variableSelected.value,
    autosize: true,
    margin: { l: 20, t: 65, r: 20, b: 5 },
  };

  return {
    traces: tableTrace,
    layout: tableLayout,
  };
};

const exportChartDataToCSV = () => {
  if (currentTrace.value[0] && currentTrace.value[0].type === "table") {
    try {
      const tableData = currentTrace.value[0];
      const csvFilename = variableSelected.value
        ? `${variableSelected.value}.csv`
        : `Untitled_chart_data.csv`;
      const csvHeaders = tableData.header.values.map((col) =>
        col[0].replace(/<\/?b>/g, ""),
      );
      const csvRows = [];
      const rowCounts = tableData.cells.values[0].length;
      for (let i = 0; i < rowCounts; i++) {
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
      displayNotification(NotificationType.ERROR, `${errorMsg}`);
    }
  } else {
    const errorMsg = "No data or incorrect chart type.";
    console.error(errorMsg);
    displayNotification(NotificationType.ERROR, `${errorMsg}`);
  }
};
</script>

<style scoped>
.ant-layout-header.graph-header {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: white;
}

:deep(.ant-segmented-item),
:deep(.ant-segmented-item::selection) {
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
  font-family: Arial, sans-serif;
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
  border-radius: 0.5rem;
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
  width: calc(100% - 12px);
  height: calc(100% - 60px);
  z-index: 100;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 5px;
}

.variant-tree-container {
  border: 1px solid #d9d9d9;
  border-radius: 2px;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px;
  margin-bottom: 16px;
  background-color: white;
}

.text-only {
  padding: 8px;
  color: rgba(0, 0, 0, 0.45);
}
</style>
