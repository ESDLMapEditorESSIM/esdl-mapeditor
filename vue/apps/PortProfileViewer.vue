<template>
  <div v-if="isLoadingData" class="loading">
    <a-spin :indicator="loadingIcon" />
  </div>
  <a-col style="height: 100%">
    <a-row class="header">
      <a-typography-title :level="4"> Port Profile Viewer </a-typography-title>
      <a-space direction="horizontal" size="large" style="padding-left: 32px">
        <a-row style="width: 500px; align-items: center">
          <a-tree-select
            v-model:value="selectedProfiles"
            :tree-data="profileOptions"
            style="width: 450px"
            allow-clear
            tree-checkable
            tree-default-expand-all
            max-tag-count="responsive"
            :placeholder="
              selectedProfiles.length === 0 ? 'Select asset profiles' : ''
            "
            :disabled="isLoadingData"
            @change="onSelectProfiles"
            @mouseleave="removeTooltipPopup"
          />
          <a-tooltip :title="profileSelectorMsg">
            <a-button size="small" type="text">
              <component
                :is="InfoCircleOutlined"
                style="vertical-align: 0.1rem"
              />
            </a-button>
          </a-tooltip>
        </a-row>
        <a-row style="width: 200px; padding-left: 24px; align-items: center">
          <a-switch
            v-model:checked="profileDownsampling"
            size="small"
            :disabled="isLoadingData"
            @change="onProfileDownsampling"
          />
          <a-typography-paragraph style="padding-left: 8px; margin-bottom: 0px">
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
        </a-row>
      </a-space>
    </a-row>
    <a-col class="content">
      <AnalyticsPlot
        :trace="currentTrace"
        :layout="currentLayout"
        :plot-message="profileOptions.length > 0 && selectedProfiles.length === 0 ? 'Select one or more profiles from the menu to visualize' : ''"
        @on-relayout="onPlotRelayout"
      />
    </a-col>
  </a-col>
</template>

<script setup>
import {h, onMounted, onUnmounted, ref} from "vue";
import {InfoCircleOutlined, LoadingOutlined} from "@ant-design/icons-vue";
import dayjs from "dayjs";

import {fetchData} from "@/utils/api";
import {config, normalizePlotlyDateTimeStr} from "@/utils/profileVisualization";
import {displayNotification} from "@/utils/notification";
import {useObject} from "@/composables/ObjectID";
import {useEsdlLayers} from "@/composables/esdlLayers";
import AnalyticsPlot from "@/components/plot/AnalyticsPlot.vue";

const { currentObjectID } = useObject();
const { getActiveEsdlLayerId } = useEsdlLayers();

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const loadingIcon = h(LoadingOutlined, {
  style: { fontSize: "5rem" },
  spin: true,
});

// ----------------------------------------- //
// ------------ Component states ----------- //
// ----------------------------------------- //

const isLoadingData = ref(false);

const activeEsdlId = ref(null);
const assetId = ref(null);

const profileOptions = ref([]);
const selectedProfiles = ref([]);
const profileDateTimeRange = ref(null);
const profileDownsampling = ref(true);

const currentTrace = ref([]);
const currentLayout = ref({});

// ----------------------------------------- //
// ---------- Component constant ----------- //
// ----------------------------------------- //

const dateTimeFormat = config.dateTimeFormat;

const profileSelectorMsg =
  "Tip: To view port profiles for multiple assets, hold down the CTRL key while selecting assets on the map. " +
  "Then open the Port Profile Viewer to explore asset port profiles from the dropdown.";

const profileMaxDataPoints = config.profileMaxDataPoints;
const profileDownsampleMsg =
  "Downsampling simplifies large dataset for better chart readability and performance. " +
  "The average value is used to represent data within each interval. " +
  "Toggle it on to explore general trends or off to access the full dataset.";

onMounted(() => {
  console.debug("Port profile viewer component mounted");
  resetState();

  activeEsdlId.value = currentObjectID.value["es_id"] ? currentObjectID.value["es_id"] : getActiveEsdlLayerId().value;
  assetId.value = currentObjectID.value["object_id"] ? currentObjectID.value["object_id"] : null;

  const selectedAssetIds = getSelectedAssetIds();
  listProfileOptions(activeEsdlId.value, selectedAssetIds);
});

onUnmounted(() => {
  resetState();
  console.debug("Port profile viewer component unmounted");
});

// Reset to default state.
const resetState = () => {
  activeEsdlId.value = null;
  assetId.value = null;

  profileOptions.value = [];
  selectedProfiles.value = [];
  profileDateTimeRange.value = null;

  currentTrace.value = [];
  currentLayout.value = {};
};

// Return a list of selected asset ids.
const getSelectedAssetIds = () => {
  let activeAssetIds = [];
  if (assetId.value !== null) {
    activeAssetIds = [assetId.value];
  }
  // One or more assets have been selected
  if (window.select_assets.is_select_mode()) {
    activeAssetIds = window.select_assets.get_selected_assets();
  }
  return activeAssetIds;
};

// List profile options for a given list of selectedAssetIds
const listProfileOptions = async (esId, selectedAssetIds) => {
  isLoadingData.value = true;

  // assetsPortsProfiles has structure as
  // [ { asset_id: str, asset_name: str, ports_profiles: [ { port_id: str, port_name: str, port_profiles: [ {id: str, name: str, ...} ] } ] } ]
  const assetsPortsProfiles = await fetchAssetsPortsProfiles(
    esId,
    selectedAssetIds
  );

  if (assetsPortsProfiles) {
    const optionGroup = assetsPortsProfiles.map((asset) => {   
      if (asset.ports_profiles.length === 0) {
        return {
          title: `${asset.asset_name} (No profile found)`,
          value: asset.asset_id,
          checkable: false,
          disabled: true,
          children: []   // explicitly empty
        };
      }

      // Build port nodes
      const portsProfiles = [];
      asset.ports_profiles.forEach((port) => {
        portsProfiles.push({
          title: `Port - ${port.port_name}`,
          value: `${asset.asset_id}-${port.port_name}`,
          checkable: false,
          children: port.port_profiles.map((p) => {
            if (p["profileClass"] == "InfluxDBProfile" || p["profileClass"] == "DataTableProfile" ) {
              const profileDisplayedName = `${p.columnName} [${p.profileQuantityAndUnit?.description?.split(" ").at(-1) ?? "Unknown"}]`;
              return {
                title: profileDisplayedName,
                value: p.id,
                checkable: true,
              }
            } else if (p["profileClass"] == "TimeSeriesProfile") {
              const profileDisplayedName = `${p.name} [${p.profileQuantityAndUnit?.description?.split(" ").at(-1) ?? "Unknown"}]`;
              return {
                title: profileDisplayedName,
                value: p.id,
                checkable: true,
              }
            } else {
              const profileDisplayedName = `${p.name || p.id} [${p.profileQuantityAndUnit?.description?.split(" ").at(-1) ?? "Unknown"}]`;
              displayNotification(
                "warning",
                `${p["profileClass"]} profile ${profileDisplayedName} is not supported for visualization in Port Profile Viewer.`
              );
              return {
                title: profileDisplayedName,
                value: p.id,
                checkable: true,
                disabled: true
              }
            }
          }),
        });
      })

      // Build asset node
      return {
        title: asset.asset_name,
        value: asset.asset_id,
        checkable: false,
        children: portsProfiles,
      };
    });

    profileOptions.value = optionGroup;
  }

  isLoadingData.value = false;
};

/**
 * Fetches ports profiles for a given list of assetIds.
 */
const fetchAssetsPortsProfiles = async (esId, assetIds) => {
  const assetsPortsProfilesRequest = {
    es_id: esId,
    asset_ids: assetIds,
  };
  try {
    const assetsProfiles = await fetchData("port_profile_viewer/assets_ports_profiles", assetsPortsProfilesRequest);
    return assetsProfiles;
  } catch (e) {
    console.error(e);
    displayNotification(
      "error",
      `Error listing port profiles from the active ESDL (id=${esId}) and selected assets with Ids [${assetIds}].`
    );
  }
};

const onSelectProfiles = () => {
  updateTrace();
};

const onProfileDownsampling = () => {
  updateTrace();
};

/**
 * Triggered to update profileDateTimeRange state when newLayoutRanges is emitted from
 * the user interaction with AnalyticsPlot (zoom in/out or pan).
 *
 * @param {Object|null} newLayoutRanges An object with structure as {x: [xaxis.range[0], xaxis.range[1]], y: [yaxis.range[0], yaxis.range[1]]}
 *                                      when zoom in/out or pan event is occurred; otherwise, null is returned.
 */
const onPlotRelayout = (newLayoutRanges) => {
  // Restore to default.
  if (newLayoutRanges === null) {
    profileDateTimeRange.value = null;
  } else {
    profileDateTimeRange.value = newLayoutRanges["x"].map((dt) => {
      const normalizedDt = normalizePlotlyDateTimeStr(dt);
      return formatAsDateTimeStr(normalizedDt, dateTimeFormat);
    });
  }
  updateTrace();
};

const updateTrace = async () => {
  isLoadingData.value = true;
  try {
    const profileTracesRequest = {
      es_id: activeEsdlId.value,
      profile_ids: selectedProfiles.value,
      viz_options: {
        max_datapoints: profileDownsampling.value ? profileMaxDataPoints : null
      }
    };
    if (profileDateTimeRange.value) {
      profileTracesRequest.viz_options["start_datetime"] = profileDateTimeRange.value[0];
      profileTracesRequest.viz_options["end_datetime"] = profileDateTimeRange.value[1];
    }
    const results = await fetchData("port_profile_viewer/profile_traces", profileTracesRequest);


    // Handle warning per profile
    if (results.warnings && results.warnings.length > 0) {
      results.warnings.forEach((warningObj) => {
        displayNotification(
          "warning",
          `${warningObj.warning}`
        );
        console.warn(warningObj)
      });
    }

    // Handle error per profile
    if (results.errors && results.errors.length > 0) {
      results.errors.forEach((errObj) => {
        let errMsg = "Error retrieving profile";
        if (errObj.profile_id) {
          errMsg += ` (id=${errObj.profile_id})`
        }
        if (errObj.error.includes("unreachable")) {
          errMsg = `Unable to display profile (id=${errObj.profile_id}) due to database connection error.`;
        }
        displayNotification("error", errMsg);
        console.error(errObj);
      });
    }

    const profileTraces = results.traces.map((t) => t.trace);
    const formattedData = profileTraceHandler(profileTraces);
    currentTrace.value = formattedData.traces;
    currentLayout.value = formattedData.layout;
  } catch (e) {
    displayNotification(
      "error",
      `Failed to fetch profile traces: ${e.message || e}`
    );
    console.error(e);
    currentTrace.value = [];
    currentLayout.value = {};
  } finally {
    isLoadingData.value = false;
  }
};

/**
 * Configures profile chart traces and layout for visualization.
 *
 * @param {Array} traces An array of trace objects to be configured for profile visualization.
 * @returns {Object} An object containing the configured traces and layout for the profile chart.
 */
const profileTraceHandler = (traces) => {
  const subplotgroupKey = "subplotgroup";
  const subplotGroups = [...new Set(traces.map((t) => t[subplotgroupKey]))];
  const displaySubplots = subplotGroups.length > 1;

  let grid = {};
  if (displaySubplots) {
    grid = {
      rows: subplotGroups.length,
      columns: 1,
      pattern: "coupled",
      roworder: "bottom to top",
    };
  }

  traces.forEach((t) => {
    t.type = "scatter";
    t.mode = "lines";
    // Limit legend group title and legend name legth.
    if (t.name.length >= 25) {
      t.name = t.name.replace(new RegExp(`(.{1,${25}})`, "g"), "$1<br>");
    }
    if (t.legendgrouptitle.text.length >= 50) {
      t.legendgrouptitle.text = t.legendgrouptitle.text.replace(
        new RegExp(`(.{1,${50}})`, "g"),
        "$1<br>"
      );
    }

    const axisId = subplotGroups.findIndex((g) => g === t[subplotgroupKey]);
    if (displaySubplots && axisId >= 0) {
      t.xaxis = "x"; // share x axis
      t.yaxis = `y${axisId + 1}`;
    }
  });

  const plotHeight = 330;
  const profileLayout = {
    xaxis: { automargin: true },
    hovermode: "x unified",
    hoversubplots: "axis",
    legend: {
      groupclick: "toggleitem",
    },
    grid: grid,
    showlegend: true,
    autosize: true,
    margin: { t: 35, b: 35 },
    height: plotHeight * subplotGroups.length,
  };

  // Define multiple y-axes dynamically
  subplotGroups.forEach((_, idx) => {
    profileLayout[`yaxis${idx + 1}`] = {
      title: subplotGroups[idx],
      automargin: true,
      anchor: "x", // Ensure all y-axes are anchored to the same x-axis
    };
  });

  return {
    traces: traces,
    layout: profileLayout,
  };
};

// A helper function to format a dtString to the specified datetimeFormat
const formatAsDateTimeStr = (dtString, datetimeFormat) => {
  return dayjs(dtString, dateTimeFormat).format(datetimeFormat);
};
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  align-content: center;
  height: 48px;
  padding: 12px;
  padding-top: 16px;
  background-color: white;
}

.content {
  background-color: white;
  height: calc(100% - 60px);
  padding: 12px;
}

.loading {
  position: absolute;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: calc(100% - 52px);
  height: calc(100% - 24px);
  z-index: 100;
}

:v-deep(.with-data) {
  overflow-y: scroll;
}

:v-deep(.plotly-plot) {
  height: 100%;
}
</style>
