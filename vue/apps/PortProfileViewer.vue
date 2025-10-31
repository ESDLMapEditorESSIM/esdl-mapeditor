<template>
  <div v-if="isLoadingData" class="loading">
    <a-spin :indicator="loadingIcon" />
  </div>
  <a-col style="height: 100%">
    <a-row class="header">
      <a-typography-title :level="4"> Port Profile Viewer </a-typography-title>
      <a-space direction="horizontal" size="large" style="padding-left: 32px">
        <a-row style="width: 450px; align-items: center">
          <a-select
            v-model:value="selectedProfiles"
            :options="profileOptions"
            style="width: 400px"
            mode="multiple"
            max-tag-count="responsive"
            :placeholder="
              selectedProfiles.length === 0 ? 'Select profiles' : ''
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
        @on-relayout="onPlotRelayout"
      />
    </a-col>
  </a-col>
</template>

<script setup>
import { ref, h, onMounted, onUnmounted } from "vue";
import { LoadingOutlined, InfoCircleOutlined } from "@ant-design/icons-vue";
import dayjs from "dayjs";

import { fetchData } from "@/utils/api";
import { config } from "@/utils/profileVisualization";
import { displayNotification } from "@/utils/notification";
import { useObject } from "@/composables/ObjectID";
import { useEsdlLayers } from "@/composables/esdlLayers";
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
  "Tip: To view port profiles for multiple assets, hold down the Ctrl key while selecting assets on the map. " +
  "Then open the Port Profile Viewer to explore asset port profiles from the dropdown.";

const profileMaxDataPoints = config.profileMaxDataPoints;
const profileDownsampleMsg =
  "Downsampling simplifies large dataset for better chart readability and performance. " +
  "The average value is used to represent data within each interval. " +
  "Toggle it on to explore general trends or off to access the full dataset.";

onMounted(() => {
  console.debug("Port profile viewer component mounted");
  resetState();

  activeEsdlId.value = getActiveEsdlLayerId().value;
  assetId.value = currentObjectID.value;

  const selectedAssetIds = getSelectedAssetIds();
  getProfileOptions(activeEsdlId.value, selectedAssetIds);
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

// Get profile options from a list of selectedAssetIds
const getProfileOptions = async (esId, selectedAssetIds) => {
  isLoadingData.value = true;

  const assetsProfilesOptions = await fetchAssetsProfiles(
    esId,
    selectedAssetIds
  );
  if (assetsProfilesOptions) {
    // assetsProfilesOptions has structure as [ { asset_id: str, asset_name: str, profiles: [ {id: str, name: str} ] } ]
    // cast it to AntDV optionGroup object for selector UI
    const optionGroup = assetsProfilesOptions.map((obj) => {
      const assetName = obj.asset_name;
      const assetProfiles = obj.profiles;
      return {
        label: assetName,
        options: assetProfiles.map((p) => ({
          label: p.name,
          value: p.id,
        })),
      };
    });
    profileOptions.value = optionGroup;
  }

  isLoadingData.value = false;
};

const fetchAssetsProfiles = async (esId, assetIds) => {
  const reqBody = {
    es_id: esId,
    asset_ids: assetIds,
  };
  const assetsProfiles = await fetchData(
    "port_profile_viewer/assets_profiles",
    reqBody
  );
  return assetsProfiles;
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
    profileDateTimeRange.value = newLayoutRanges["x"].map((dt) =>
      formatAsDateTimeStr(dt, dateTimeFormat)
    );
  }
  updateTrace();
};

const updateTrace = async () => {
  isLoadingData.value = true;
  try {
    const reqBody = {
      es_id: activeEsdlId.value,
      profile_ids: selectedProfiles.value,
      dt_range: profileDateTimeRange.value,
      max_datapoints: profileDownsampling.value ? profileMaxDataPoints : null,
    };

    const results = await fetchData(
      "port_profile_viewer/profile_traces",
      reqBody
    );

    // Handle errors per profile
    if (results.errors && results.errors.length > 0) {
      results.errors.forEach((err) => {
        displayNotification(
          "error",
          `Error retrieving profile [${err.profile_id}]`
        );
        console.error(err);
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

::v-deep(.with-data) {
  overflow-y: scroll;
}

::v-deep(.plotly-plot) {
  height: 100%;
}
</style>
