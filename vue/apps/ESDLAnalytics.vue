<template>
  <!-- Dialog header -->
  <a-row style="height: 60px; padding-left: 0.5em;">
    <h2 style="font-weight: bold; font-size: 2rem">ESDL Analytics</h2>
  </a-row>
  <!-- Dialog content -->
  <a-row style="height: calc(100% - 60px);">
    <div v-if="isSyncingMetaData || isDeletingMetaData" class="loading">
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
                <a-typography-title :level="5">Available variants</a-typography-title>
                <p style="font-size: small;">Select which variants need to be analysed for comparision.</p>
                <div class="variant-tree-container">
                  <vue-js-tree
                    v-if="treeData != null"
                    tree-id="analytics_variant_tree"
                    :plugins="['types', 'checkbox']"
                    :data="treeData"
                    :events="treeEventHandlers"
                    :tree-type-specs="treeTypeSpecs"
                    :checkbox="{'three_state': false, 'whole_node': false, 'tie_selection': false}"
                  />
                  <div v-else class="text-only">
                    <p>No variants available.</p>
                  </div>
                </div>
              </a-row>


              <a-col style="padding-top: 24px; padding-bottom: 16px;">
                <a-row style="padding-bottom: 8px;">
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
                <a-row style="padding-bottom: 8px;">
                  <a-button
                    :disabled="variantIdsSelected.length === 0 || isSyncingMetaData"
                    block
                    @click="onSyncBtnClick"
                  >
                    <a-tooltip
                      :title="datasetOptions.length ?
                        'Update ESDL Analytics metadata with the current ESDL(s)' :
                        'Add the select ESDL(s) to ESDL Analytics metadata'"
                    >
                      <component
                        :is="datasetOptions.length ? SyncOutlined : UploadOutlined"
                        style="vertical-align: 0.1rem"
                      />
                      {{ getAddDatasetLabel() }}
                    </a-tooltip>
                  </a-button>
                </a-row>
                <a-row style="padding-bottom: 8px;">
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

              <a-row>
                <a-typography-title :level="5">Datasets to compare</a-typography-title>
                <a-select
                  v-model:value="datasetSelected"
                  :options="datasetOptions"
                  :disabled="datasetOptions.length === 0"
                  :placeholder="datasetSelectPlaceholder"
                  mode="multiple"
                  style="width: 100%"
                  @change="onSelectDataset"
                  @mouseleave="removeTooltipPopup"
                />
              </a-row>

            </a-tab-pane>

            <!-- Tab 2: Visualization Settings -->
            <a-tab-pane key="visualization" tab="Visualization" :disabled="datasetSelected.length === 0">
              <a-row>
                <a-typography-title :level="5">Variable</a-typography-title>
                <a-select
                  v-model:value="variableSelected"
                  :options="Object.values(variableOptions)"
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
              <a-row>
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
                  :status="chartType === 'bar' && groupbySelected.length > maxGroupbySelectedCount ? 'warning' : ''"
                  allow-clear
                  mode="multiple"
                  style="width: 100%"
                  @change="onSelectGroupBy"
                  @mouseleave="removeTooltipPopup"
                />
                <span
                  v-if="chartType === 'bar' && groupbySelected.length > maxGroupbySelectedCount"
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
              </a-row>
              <br>
              <!-- Bar chart configuration -->
              <a-row v-if="datasetSelected.length && variableSelected !== null && chartType==='bar'">
                <a-typography-title :level="4">Display options</a-typography-title>
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
                          :span="2"
                          :style="{ backgroundColor: color.startsWith('#') ? color : `#${color}`, height: '10px' }"
                        />
                      </a-row>
                    </a-select-option>
                  </a-select>
                </a-row>
                <a-radio-group
                  v-model:value="dataGrouping"
                  name="groupStackRadio"
                  :options="groupStackOptions"
                  style="display: flex; flex-direction: column; padding-top: 12px;"
                  @change="onSelectDisplayOptions"
                />
                <a-checkbox
                  v-model:checked="showBarNumbers"
                  style="padding-top: 12px;"
                  @click="onSelectDisplayOptions"
                >
                  Show numbers on bar chart
                </a-checkbox>
              </a-row>
            </a-tab-pane>
          </a-tabs>
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
            <!-- Chart type buttons -->
            <a-radio-group v-model:value="chartType">
              <a-radio-button
                v-for="type in chartTypes"
                :key="type.value"
                :value="type.value"
                :disabled="datasetSelected.length === 0 || variableSelected === null"
                @click="onChartTypeBtnClick"
              >
                <component :is="type.icon" style="vertical-align: 0.05rem" />
              </a-radio-button>
            </a-radio-group>
          </a-row>
        </a-layout-header>
        <a-layout-content class="graph-content">
          <AnalyticsPlot
            :trace="currentTrace"
            :layout="currentLayout"
          />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-row>
</template>

<script setup>
import {computed, h, onMounted, onUnmounted, ref} from 'vue';
import {notification} from 'ant-design-vue';
import {
  BarChartOutlined,
  DeleteOutlined,
  EditOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SaveOutlined,
  SyncOutlined,
  TableOutlined,
  UploadOutlined
} from "@ant-design/icons-vue";
import AnalyticsPlot from '../components/esdlanalytics/AnalyticsPlot.vue';
import VueJsTree from '../components/jstree/VueJsTree.vue';
import {useESDLProjects} from "@/composables/esdlProjects";

const { esdlProject, getESDLProject } = useESDLProjects();

const collapsed = ref(false);

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: '5rem' }, spin: true
});

// to prevent stuck popup on UI
const removeTooltipPopup = () => { window.jquery(".ui-tooltip-content").parents('div').remove();};

// ------------------------------------- //
// ------------ Graph Header ----------- //
// ------------------------------------- //

const title = ref('');
const editingTitle = ref(false);
const activeTabKey = ref('data');

const minWidth = 180;
const inputWidth = ref(minWidth);

const updateTitleInputWidth = (value) => {
	const newWidth = value.target.value.length * 11;
	inputWidth.value = newWidth >= minWidth ? newWidth : minWidth;
};

const chartTypes = [
  {value: "bar", icon: BarChartOutlined},
  {value: "table", icon: TableOutlined},
];
const chartType = ref(chartTypes[0].value);

const onChartTypeBtnClick = (event) => {
  chartType.value = event.target.value;
  updateTrace();
};

// ------------------------------------- //
// -------- Graph Configuration -------- //
// ------------------------------------- //

const isSyncingMetaData = ref(false);
const isDeletingMetaData = ref(false);

const currentTrace = ref([]);
const currentLayout =  ref({});
// A list of each possible variant to select.
const variantOptions = ref([]);
// A list of selected variant IDs.
const variantIdsSelected = ref([]);
const datasetOptions = ref([]);
const datasetSelected = ref([]);
const datasetSelectPlaceholder = ref('Select a dataset');
const variableOptions = ref([]);
const variableSelected = ref(null);
const variableWarningMsg = ref("");
// TODO & WIP: Profile data visualization is not supported yet.
const isProfileVariable = ref(false);
const groupbyOptions = ref([]);
const groupbySelected = ref([]);
const maxGroupbySelectedCount = 2;
const filterOptions = ref([]);
const filterSelected = ref([]);

const groupStackOptions = [
	{ label: 'Group data', value: 0 },
	{ label: 'Stack data (totals)', value: 1 },
	{ label: 'Stack data (percentage)', value: 2 },
];
const dataGrouping = ref(1);
const showBarNumbers = ref(false);

const sampleColorCount = 12;
const colorPalettes = [
  // pie_chart_color_list is defined in area_building_layer.js
  { label: 'Default', value: 'Default', sample: pie_chart_color_list.slice(0, sampleColorCount) },
  { label: 'Qualitative', value: 'Qualitative', sample: window.palette('mpn65', sampleColorCount) },
  { label: 'Diverging', value: 'Diverging', sample: window.palette('tol-dv', sampleColorCount) },
  { label: 'Sequential', value: 'Sequential', sample: window.palette('tol-sq', sampleColorCount) },
  { label: 'Rainbow', value: 'Rainbow', sample: window.palette('tol-rainbow', sampleColorCount) }
];
const paletteSelected = ref(colorPalettes[0]);

const energyUnitOptions = [
  { label: 'PJ', value: 'PJ' },
  { label: 'TJ', value: 'TJ' },
  { label: 'GJ', value: 'GJ' },
	{ label: 'MJ', value: 'MJ' },
	{ label: 'J', value: 'J' },
	{ label: 'TWh', value: 'TWh' },
	{ label: 'GWh', value: 'GWh' },
	{ label: 'MWh', value: 'MWh' },
	{ label: 'kWh', value: 'kWh' },
	{ label: 'No conversion', value: 'None' },
];
const energyUnit = ref(energyUnitOptions[0].value );

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

onMounted(() => {
  console.info("Initializing ESDL Analytics");
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
      "checked": variantIdsSelected.value.includes(variant.id),
      "opened": children.length > 0,
    }
  };
}

// Tree type specifications
class VariantTreeSpec {
  constructor() {
    this.type = "variant";
    this.icon = 'fas fa-bezier-curve';
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
  'check_node.jstree': function(e, data) {
    if (data.node.type === 'variant') {
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
  'uncheck_node.jstree': function(e, data) {
    if (data.node.type === 'variant') {
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
  }
};


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

const getAddDatasetLabel = () => {
  if (datasetOptions.value.length) {
    return "Update dataset"
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
        esId: variant.es_id
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
const onSyncBtnClick = async() => {
  console.debug("Synchronizing ESDLs into metadata");
  isSyncingMetaData.value = true;

  const selectedVariants = [];
  if (esdlProject.value && esdlProject.value.variants) {
    findSelectedVariants(esdlProject.value.variants, variantIdsSelected.value, selectedVariants);
  }
  console.debug("Selected variants", selectedVariants);

  try {
    // Process variants sequentially
    for (const variant of selectedVariants) {
      const esId = variant.value;
      const esTitle = variant.label;

      try {
        displayNotification("info", `Adding ${esTitle} [${esId}] into the database.`);
        const reqBody = { es_id: esId, energyUnit: energyUnit.value };
        const resp = await modifyMetadata('add_update', reqBody);
        displayNotification(resp.status, resp.message);
      } catch (error) {
        console.error(error);
        displayNotification("error", `An unknown error occurred while adding ${esTitle} [${esId}] to the database`);
      }
    }
    await updateDatasets();
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
    await updateDatasets();
  } catch (error) {
    console.error(error);
    displayNotification("error", `An error occurred while deleting metadata: ${error}`);
  } finally {
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
      datasetSelectPlaceholder.value = "Select a dataset";
    } else {
      datasetOptions.value = [];
      datasetSelectPlaceholder.value = "No datasets available";
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

  if (datasetSelected.value.length === 0 || variableSelected.value === null) {
    currentTrace.value = [];
    return;
  }

  if (Object.keys(variableOptions.value).length === 0) {
    return;
  }

  // Only take the first two elements as group_by selections for a bar chart.
  const groupBySelection = chartType.value === 'bar' ? 
    groupbySelected.value.slice(0, maxGroupbySelectedCount) : groupbySelected.value;

  let filterSelection = {};
  filterSelected.value.forEach((filter) => {
    const [column, val] = filter;
    if (filterSelection[column] === undefined) {
      filterSelection[column] = [];
    }
    filterSelection[column].push(val);
  });

  const options = {
    dataset_ids: datasetSelected.value,
    variable_name: variableSelected.value,
    group_by: groupBySelection,
    filters: filterSelection,
    chart_type: chartType.value
  };

  try {
    const traces = await fetchMetadata('query', options);
    // TODO: add profile data handling with profileTraceHandler(taces) and when isProfileVariable is true
    if (chartType.value === 'table') {
      const formattedTable = tableTraceHandler(traces);
      currentTrace.value = formattedTable.traces;
      currentLayout.value = formattedTable.layout;
    }
    else {
      const formattedBarChart = barChartTraceHandler(traces);
      currentTrace.value = formattedBarChart.traces;
      currentLayout.value = formattedBarChart.layout;
    }
  } catch (error) {
    console.error(error);
    displayNotification("error", `${error}`);
  }
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
      exponentformat: "SI", // see https://github.com/plotly/plotly.py/issues/4787 for values larger than Giga...
      //ticksuffix: variableOptions.value[variableSelected.value].unit,
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

/**
 * TODO: WIP and needs refinement.
 * TODO: rename scenario to dataset
 * Configures profile traces and layout for visualization.
 */
// const profileTraceHandler = (traces) => {
//   const scenarios = [...new Set(traces.filter(trace => trace.scenario !== undefined).map(trace => trace.scenario))];
//   traces.forEach((t) => {
//     t.mode = 'lines';
//     t.type = 'scatter';
//     t.stackgroup = [1, 2].includes(dataGrouping.value) ? 0 : null,
//     t.groupnorm = dataGrouping.value === 2 ? 'percent' : '';

//     if (traces.length > 1 && t.scenario !== undefined) {
//       t.xaxis = 'x' + scenarios.indexOf(t.scenario);
//       t.yaxis = 'y' + scenarios.indexOf(t.scenario);
//     }
//   });

//   const profileLayout = {
//     xaxis: {
//       type: 'date'
//     }
//   };

//   if (scenarios.length > 1) {
//     profileLayout.grid = { rows: scenarios.length, columns: 1, pattern: 'independent' };
//     profileLayout.height =  scenarios.length * 450;  // for subplots, make graph bigger
//     profileLayout.legend = { traceorder: "normal" };
//   }

//   return {
//     traces: traces,
//     layout: profileLayout
//   };
// };

</script>

<style>

.ant-layout-header.graph-header {
	display: flex;
	align-items: center;
	padding: 12px;
	background-color: white; 
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