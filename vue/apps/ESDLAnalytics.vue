<template>
  <div v-if="isSyncingMetaData || isDeletingMetaData" class="loading">
    <a-spin :indicator="loadingIcon" />
  </div>
  <!-- TODO: responsive layout -->
  <div class="dialog-content">
    <a-row>
      <a-col span="22">
        <h2 style="font-weight: bold; font-size: 2rem">ESDL Analytics (Experimental)</h2>
      </a-col>
      <a-col span="2" class="header-buttons-layout">
        <a-tooltip title="Synchronize ESDL Analytics metadata">
          <a-button
            size="large"
            :disabled="isSyncingMetaData"
            @click="onSyncBtnClick"
          >
            <template #icon>
              <component 
                :is="SyncOutlined"
                style="vertical-align: 0.1rem"
              />
            </template>
          </a-button>
        </a-tooltip>
        <!-- TODO & NOTE: A temporary implementation to clean up metadata -->
        <a-tooltip title="Delete ESDL Analytics metadata">
          <a-button
            size="large"
            :disabled="isDeletingMetaData"
            @click="onDeleteBtnClick"
          >
            <template #icon>
              <component 
                :is="DeleteOutlined"
                style="vertical-align: 0.1rem"
              />
            </template>
          </a-button>
        </a-tooltip>
      </a-col>
    </a-row>
    <br>
    <a-row style="display: flex; flex-direction: row; align-items: stretch">
      <a-col v-if="showConfig" class="graph-options" :md="24" :lg="8">
        <h2>Graph configuration</h2>
        <a-row>
          <h3>Scenario</h3>
          <a-select
            v-model:value="scenarioSelected"
            :options="scenarioOptions"
            :loading="scenarioOptions.length === 0"
            :placeholder="scenarioSelectPlaceholder"
            mode="multiple"
            style="width: 100%"
            @change="onSelectScenario"
          />
        </a-row>
        <a-row>
          <h3>Variable</h3>
          <a-select
            v-model:value="variableSelected"
            :options="Object.values(variableOptions)"
            :disabled="scenarioSelected.length === 0"
            :placeholder="scenarioSelected.length === 0 ? 'First select a scenario' : 'Select a variable'"
            style="width: 100%"
            @change="onSelectVariable"
          />
        </a-row>
        <a-row>
          <h3>Group by</h3>
          <a-select
            v-model:value="groupbySelected"
            :options="groupbyOptions"
            :disabled="scenarioSelected.length === 0 || variableSelected === null" 
            :placeholder="
              scenarioSelected.length === 0 ? 'First select a scenario'
              : variableSelected === null ? 'First select a variable'
                : 'Select a category'"
            allow-clear
            mode="multiple"
            style="width: 100%"
            @change="onSelectGroupBy"
          />
        </a-row>
        <a-row>
          <h3>Filter</h3>
          <a-cascader
            v-model:value="filterSelected"
            :options="filterOptions"
            style="width: 100%"
            :disabled="scenarioSelected.length === 0 || variableSelected === null" 
            :placeholder="
              scenarioSelected.length === 0 ? 'First select a scenario'
              : variableSelected === null ? 'First select a variable'
                : 'Select a category'" 
            allow-clear multiple
            @change="onSelectFilters"
          />
        </a-row>

        <!-- TODO -->
        <!-- <div>
          <h3>Data visualisation:</h3>
          <a-radio-group
            v-model:value="dataGrouping" name="groupStackRadio" :options="groupStackOptions"
            @change="groupstack"
          />
          <br><br>
          <a-checkbox
            v-model:checked="showBarNumbers" 
            @click="groupstack"
          >
            Show numbers on bar chart
          </a-checkbox>
        </div> -->
      </a-col>

      <!-- TODO: Plot responsive layout -->
      <a-col :md="24" :lg="16">
        <AnalyticsPlot
          :trace="currentTrace"
          :layout="currentLayout"
        />
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, h, onMounted, onUnmounted } from "vue";
import { notification } from 'ant-design-vue';
import { DeleteOutlined, LoadingOutlined, SyncOutlined } from "@ant-design/icons-vue";
import AnalyticsPlot from "../components/esdlanalytics/AnalyticsPlot.vue";

// TODOs
// Rename scenario to dataset?

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: '5rem' },
  spin: true,
});

// TODO: hide/collapse config in a small view 
const showConfig = ref(true);

const isSyncingMetaData = ref(false);
const isDeletingMetaData = ref(false);

const currentTrace = ref([]);
const currentLayout =  ref({ barmode: 'stack' });
const scenarioOptions = ref([]);
const scenarioSelected = ref([]);
const scenarioSelectPlaceholder = ref('Select a scenario');
const variableOptions = ref([]);
const variableSelected = ref(null);
const groupbyOptions = ref([]);

// TODO: default group by with year if is not profile
const groupbySelected = ref([]);
const filterOptions = ref([]);
const filterSelected = ref([]);

const showBarNumbers = ref(false);

const onSelectScenario = () => {
  updateVariables();
  updateTrace();
};

const onSelectVariable = () => {
  updateColumns();
  updateTrace();
};

const onSelectGroupBy = () => {
  updateTrace();
};

const onSelectFilters = () => {
  updateTrace();
};

onMounted(() => {
  console.info("Initializing ESDL Analytics");
  updateDatasets();
});

onUnmounted(() => {
  console.info("Unmounting ESDL Analytics");
});

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
      displayNotification("info", `Adding ${esTitle} into the database.`);
      const reqBody = { es_id: esId, scenario_name: null };
      const resp = await modifyMetadata('add_update', reqBody);
      displayNotification(resp.status, resp.message);
    } catch (error) {
      console.error(error);
      displayNotification("error", `An unknown error occurred while adding ${esTitle} to the database`);
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
    isDeletingMetaData.value = false;
  }
};

/**
 * Asynchronously fetches DataManager datasets and updates the scenario options.
 * 
 * @returns {Promise<void>} A promise that resolves when the datasets have been fetched and the options updated.
 */
const updateDatasets = async() => {
  console.debug("Fetching DataManager datasets");
  try {
    const datasets = await fetchMetadata('datasets');
    if (datasets.length) {
      scenarioOptions.value = datasets.map((d) => ({
        value: d.id, 
        label: `${d.name} (${d.scenario})`
      }));
      scenarioSelectPlaceholder.value = "Select a scenario";
    } else {
      scenarioOptions.value = [];
      scenarioSelectPlaceholder.value = "No datasets available";
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
  if (scenarioSelected.value.length) {
    try {
      const reqBody = { dataset_ids: scenarioSelected.value };
      const variables = await fetchMetadata('variables', reqBody);

      variableOptions.value = Object.fromEntries(
        variables.map(v => [
          v.name,
          { value: v.name, 
            label: v.name, 
            unit: v.unit, 
            description: v.description, 
            datatype: v.datatype 
          }
        ])
      );
      // TODO: reset groupbySelected and filterSelected is needed?
      // groupbySelected.value = [];
      // filterSelected.value = [];
    } catch (error) {
      console.error(error);
    }
  } else {
    variableOptions.value = [];
    variableSelected.value = null;
    groupbySelected.value = [];
    filterSelected.value = [];
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
  if (scenarioSelected.value.length && variableSelected.value !== null) {
    try {
      const reqBody = {
        dataset_ids: scenarioSelected.value, 
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
 * TODO
 */
const updateTrace = async() => {
  console.debug("Updating trace");

  if (scenarioSelected.value.length === 0 || variableSelected.value === null) {
    currentTrace.value = [];
    return;
  }

  if (Object.keys(variableOptions.value).length === 0) {
    return;
  }

  const isProfile = variableOptions.value[variableSelected.value].datatype === 'PROFILE';

  // If the datatype of variableSelected is not PROFILE, default group by with 'year'
  let groupBySelection = isProfile ? ['datetime'] : ['year'];
  if (groupbySelected.value.length && !isProfile ) {
    groupbySelected.value.forEach((option) => {
      if (!groupBySelection.includes(option)) {
        groupBySelection.push(option);
      }
    });
  }

  let filterSelection = {};
  filterSelected.value.forEach((filter) => {
    const [column, val] = filter;
    if (filterSelection[column] === undefined) {
      filterSelection[column] = [];
    }
    filterSelection[column].push(val);
  });

  const options = {
    dataset_ids: scenarioSelected.value,
    variable_name: variableSelected.value,
    group_by: groupBySelection,
    filters: filterSelection
  };

  try {
    const traces = await fetchMetadata('query', options);
    // TODO const scenarios = [...new Set(traces.filter(trace => trace.scenario !== undefined).map(trace => trace.scenario))];
    traces.forEach((trace) => {
      if (isProfile) {
        // TODO: implementing profile trace
        // trace.mode = 'lines';
        // trace.type = "scatter";

        // if (this.dataGrouping == 1) {
        //     trace.stackgroup = 0;
        //     // TODO: maybe also add legend group to group the legend of the different graphs
        //     trace.groupnorm = '';
        // } else if (this.dataGrouping == 2) {
        //     trace.stackgroup = 0;
        //     trace.groupnorm = 'percent';
        // } else {
        //     delete trace.stackgroup;
        //     delete trace.groupnorm;
        // }

        // // For subplots, each plot needs its own unique axis
        // if (traces.length > 1 && trace.scenario !== undefined) {
        //     trace.xaxis = 'x' + scenarios.indexOf(trace.scenario);
        //     trace.yaxis = 'y' + scenarios.indexOf(trace.scenario);
        // }

        // this.currentLayout.xaxis.type = 'date';
      } 
      else {
        trace.type = 'bar';
        currentLayout.value.xaxis.type = 'multicategory';
        if (showBarNumbers.value) {
          trace.text = trace.y.map(y => y.toFixed(1));
        } else {
          delete trace.text;
        }
      }
    });

    // TODO
    // if (is_profile) {
    //     if (scenarios.length > 1) {
    //         this.currentLayout.grid = { rows: scenarios.length, columns: 1, pattern: 'independent' };
    //         this.currentLayout.height = scenarios.length * 450;  // for subplots, make graph bigger
    //         this.currentLayout.legend = { traceorder: "normal" };
    //     } else {
    //         delete this.currentLayout.grid;
    //         this.currentLayout.height = null;
    //         this.currentLayout.legend = { traceorder: "reversed" };
    //     }
    // } else {
    //     delete this.currentLayout.grid;
    //     this.currentLayout.height = null;
    //     this.currentLayout.legend = { traceorder: "reversed" };
    // }

    currentTrace.value = traces;
    currentLayout.value = {
      ...currentLayout.value,
      title: options.variable_name,
      yaxis: {title: variableOptions.value[options.variable_name].unit},
      showlegend: true,
      autosize: true
    };
  } catch (error) {
    console.error(error);
  }
};
</script>

<style>
.graph-options {
  padding: 1rem 2rem;
  background-color: ghostwhite;
  border-radius: 1rem;
  height: fit-content;
}

.graph-options>*:not(:first-child) {
  margin-top: 1rem;
}

.header-buttons-layout {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-evenly;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  padding: 12px;
}

.loading {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: calc(100% - 36px);
  height: calc(100% - 8px);
  margin-top: 8px;
  z-index: 100;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 5px;
}

</style>