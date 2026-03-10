<template>
  <a-modal
    :open="props.visible"
    :title="`Profile Editor${props.profileTag ? ` - ${props.profileTag}` : ''}`"
    width="40%"
    @cancel="onCancel"
  >
    <template #footer>
      <a-button @click="onCancel">Cancel</a-button>
      <a-button type="primary" :disabled="invalidForm || noChangeDetected" @click="onSave">Save</a-button>
    </template>
    <a-form ref="profileFormRef" layout="vertical" :model="profileForm">
      <br>
      <a-row>
        <a-typography-text style="padding-bottom: 8px;">
          Profile class
          <a-tooltip
            v-if="formMode === formModeEnum.CREATE" 
            title="Choose the ESDL profile class to save this profile as."
          >
            <a-button size="small" type="text">
              <component
                :is="InfoCircleOutlined"
                style="vertical-align: 0.1rem"
              />
            </a-button>
          </a-tooltip>
        </a-typography-text>
        <a-segmented
          v-model:value="profileForm.profileClass"
          :options="profileClassOptions"
          :disabled="formMode === formModeEnum.UPDATE"
          style="width: 100%"
          block
          @change="onSelectProfileClass"
        />
      </a-row>
      <br>
      <a-form-item label="ID">
        <a-input v-model:value="profileForm.id" disabled />
      </a-form-item>

      <!-- SINGLE VALUE profile -->
      <div v-if="profileForm.profileClass === profileClassEnum.SINGLEVALUE">
        <a-form-item 
          label="Name"
          :rules="[{ required: true, type: 'string' }]"
        >
          <a-input v-model:value="profileForm.name" />
        </a-form-item>
        <a-form-item
          label="Value"
          :rules="[{ required: true, type: 'number' }]"
        >
          <a-input-number
            v-model:value="profileForm.value"
            style="width: 100%"
          />
        </a-form-item>
      </div>

      <!-- InfluxDBProfile or DataTableProfile -->
      <div v-if="profileForm.profileClass !== profileClassEnum.SINGLEVALUE">
        <a-form-item
          :rules="[{ required: true, type: 'object' }]"
        >
          <template #label>
            <span>Profile</span>
            <a-tooltip
              v-if="formMode === formModeEnum.CREATE"
              :title="profileForm.profileClass === profileClassEnum.INFLUXDBPROFILE ? influxDBProfileTooltip : profileTooltip"
            >
              <a-button size="small" type="text" style="vertical-align: top; margin-left: 4px;">
                <component :is="InfoCircleOutlined" style="vertical-align: 0.1rem" />
              </a-button>
            </a-tooltip>
            <a-tag v-if="profileForm.profileSourceTag" color="blue" style="margin-left: 8px;">
              {{ profileForm.profileSourceTag }}
            </a-tag>
          </template>
          <a-select
            v-model:value="profileForm.profile"
            :options="profileForm.profileClass === profileClassEnum.INFLUXDBPROFILE ? influxDBProfileOptions : profileOptions"
            show-search
            allow-clear
            :disabled="formMode === formModeEnum.UPDATE"
            @change="onSelectProfile"
            @mouseleave="removeTooltipPopup"
          />
        </a-form-item>

        <a-form-item
          v-if="profileForm.profileClass === profileClassEnum.DATATABLEPROFILE"
          label="Database Type"
        >
          <a-input v-model:value="profileForm.databaseType" disabled />
        </a-form-item>

        <a-form-item
          label="Multiplier"
          :rules="[{ required: true, type: 'number' }]"
        >
          <a-input-number
            v-model:value="profileForm.multiplier"
            :disabled="isLoadingData"
            style="width: 100%"
            @change="onUpdateMultiplier"
          />
        </a-form-item>
      </div>

      <a-form-item
        label="Profile type"
        :rules="[{ type: 'object' }]"
      >
        <a-select
          v-model:value="profileForm.profileType"
          :options="profileTypeOptions"
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>

      <a-form-item label="Quantity and unit type">
        <a-select
          v-model:value="profileForm.qauType"
          :options="qauTypeOptions"
          disabled
        />
      </a-form-item>

      <a-form-item
        label="Predefined quantity and unit"
        :rules="[{ required: true, type: 'object' }]"
      >
        <a-select
          v-model:value="profileForm.qau"
          :options="profileQaUOptions"
          allow-clear
          :disabled="isLoadingData"
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>

      <a-row 
        v-if="profileForm.profileClass !== profileClassEnum.SINGLEVALUE"
        class="plot"
      >
        <a-typography-text style="padding-bottom: 8px;">
          Preview
          <a-tooltip :title="previewTooltip">
            <a-button size="small" type="text">
              <component
                :is="InfoCircleOutlined"
                style="vertical-align: 0.1rem"
              />
            </a-button>
          </a-tooltip>
          <span v-if="isLoadingData" style="padding-left: 8px;">
            <a-spin :indicator="loadingIcon" />
          </span>
        </a-typography-text>
        <AnalyticsPlot
          :trace="profileForm.currentTrace"
          :layout="profileForm.currentLayout"
        />
      </a-row>
      <br>
      <br>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, h } from "vue";
import { LoadingOutlined, InfoCircleOutlined } from "@ant-design/icons-vue";

import AnalyticsPlot from "@/components/plot/AnalyticsPlot.vue";
import { config } from "@/utils/profileVisualization";
import { fetchData } from "@/utils/api";
import { displayNotification } from "@/utils/notification";

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const loadingIcon = h(LoadingOutlined, {
  spin: true,
});

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  activeEsdlId: {
    type: String,
    default: ""
  },
  activePortId: {
    type: String,
    default: ""
  },
  profileTag: {
    type: String,
    default: null,
  },
  // Existing profile info for further editing;
  profileInfo: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["onSave", "onCancel"]);

// ----------------------------------------- //
// ---------- Component constant ----------- //
// ----------------------------------------- //

const profilePlugin = window.profiles_plugin;
const profileQaU = window.quantity_and_units_info;

const formModeEnum = Object.freeze({
  CREATE: "Create",
  UPDATE: "Update",
})

// See reference at: https://energytransition.github.io/#router/doc-content/687474703a2f2f7777772e746e6f2e6e6c2f6573646c/ExternalProfile.html
// NOTE: INFLUXDBPROFILE will be phased out in the future.
const profileClassEnum = Object.freeze({
  SINGLEVALUE: "SingleValue",
  INFLUXDBPROFILE: "InfluxDBProfile",
  DATATABLEPROFILE: "DataTableProfile"
})

const profileClassOptions = Object.entries(profileClassEnum).map(([_, label]) => ({
  value: label,
  label: label,
}));

const DatabaseTypeEnum = Object.freeze({
  INFLUXDB: "INFLUXDB",
  POSTGRESQL: "POSTGRESQL",
});

const QaUType = Object.freeze({
  PREDEFINED: "Predefined quantity and units",
  CUSTOM: "Custom quantity and units"
});

const qauTypeOptions = Object.entries(QaUType).map(([_, label]) => ({
  value: label,
  label: label,
}));

// NOTE: ProfileTypeEnum from https://energytransition.github.io/index.html
// NICE TO HAVE: fetch this from backend to ensure a single source of truth.
const profileTypeEnum = Object.freeze({
  UNDEFINED: "UNDEFINED",
  INPUT: "INPUT",
  OUTPUT: "OUTPUT",
});

const profileTypeOptions = Object.entries(profileTypeEnum).map(([_, label]) => ({
  value: label,
  label: label,
}));

const profileBase = {
  id: null,
  profileType: profileTypeOptions[1].value,   // Default INPUT
  qauType: qauTypeOptions[0].value,           // Default predefined quantity and units type
  qau: null,
};

const profileDefaults = {
  SingleValue: {
    ...profileBase,
    profileClass: profileClassEnum.SINGLEVALUE,
    name: null,
    value: null,
  },
  InfluxDBProfile: {
    ...profileBase,
    profileClass: profileClassEnum.INFLUXDBPROFILE,
    profile: null,
    profileSourceTag: "",
    multiplier: null,
    currentTrace: [],
    currentLayout: {},
  },
  DataTableProfile: {
    ...profileBase,
    profileClass: profileClassEnum.DATATABLEPROFILE,
    profile: null,
    profileSourceTag: "",
    databaseType: null,
    multiplier: null,
    currentTrace: [],
    currentLayout: {},
  },
};

// Initialize a default form
const initForm = (type) => {
  // Remove all existing keys
  for (const key in profileForm) {
    delete profileForm[key];
  }
  
  // Assign new defaults
  Object.assign(profileForm, {
    ...profileDefaults[type],
  });
}

const profileTooltip = "Type to search profile.";
const influxDBProfileTooltip = profileTooltip + " PostgreSQL profiles are unavailable with InfluxDBProfile, please use DataTableProfile instead.";
const previewTooltip = "The preview displays a downsampled profile for improved chart readability and performance. "
                       + "To view the full profile data, use ESDL Analytics or Port Profile Viewer.";

// ----------------------------------------- //
// ------------ Component states ----------- //
// ----------------------------------------- //

const formMode = ref(formModeEnum.CREATE);

const profileFormRef = ref(null);
const profileForm = reactive({});

const profileOptions = ref([]);
const influxDBProfileOptions = ref([]);
const profileQaUOptions = ref([]);

const isLoadingData = ref(false);

onMounted(() => {
  const fullProfileOptions = listProfileOptions();
  profileOptions.value = fullProfileOptions;
  // Disable PostgreSQL profiles for InfluxDBProfile profile options.
  influxDBProfileOptions.value = fullProfileOptions.map((gr) => {
    return {
      ...gr,
      options: gr.options.map((p) => {
        if (p.databaseType === DatabaseTypeEnum.POSTGRESQL) {
          return {
            ...p,
            disabled: true
          };
        }
        return p;
      })
    };
  });
  profileQaUOptions.value = listPredefQaU();
});

watch(
  () => props.visible,
  () => {
    formMode.value = formModeEnum.CREATE;
    initForm(profileClassEnum.INFLUXDBPROFILE)

    if (props.visible && props.profileInfo) {
      formMode.value = formModeEnum.UPDATE;
      initializeProfileEditing(props.profileInfo);
    }
  },
);

/**
 * Initializes the profile form for editing.
 * 
 * @param {Object} profileInfo - The existing profile object to be loaded into the form.
 */
const initializeProfileEditing = (profileInfo) => {
  console.debug(profileInfo);
  if (profileInfo.profileClass === profileClassEnum.SINGLEVALUE) {
    castSingleValueObjToFormData(profileInfo);
  } else {
    castExternalProfileObjToFormData(profileInfo);

    // Check if profile can be found from profile plugin and update profileSourceTag accordingly.
    const profilePluginObj = getProfileInfoFromProfilePlugin(profileInfo.columnName);
    profileForm.profileSourceTag = profilePluginObj ? profilePluginObj["profileGroupName"] : "Custom profile";

    updateTrace();
  }
}

/**
 * Cast the given SingleValue object into profileForm accepted data.
 *
 * @param {Object} svInfo existing SingleValue profile object passed from the parent component.
 */
const castSingleValueObjToFormData = (svInfo) => {
  profileForm.id = svInfo.id;
  profileForm.name = svInfo.name;
  profileForm.value = svInfo.value;
  profileForm.profileClass = svInfo.profileClass;
  profileForm.profileType = svInfo.profileType;
  profileForm.qau = svInfo.profileQuantityAndUnit.description;

  if (!svInfo.profileQuantityAndUnit["_isPredefinedQaU"]) {
    profileForm.qauType = qauTypeOptions[1];
  }
}

/**
 * Cast the given ExteranlProfile e.g., InfluxDBProfile or DataTableProfile object into profileForm accepted data.
 *
 * @param {Object} profileInfo existing profile object passed from the parent component.
 */
const castExternalProfileObjToFormData = (profileInfo) => {
  profileForm.id = profileInfo.id;
  profileForm.profile = profileInfo.columnName;
  profileForm.profileClass = profileInfo.profileClass;
  profileForm.databaseType = profileInfo.configuration.type;
  profileForm.profileType = profileInfo.profileType;
  profileForm.multiplier = profileInfo.multiplier;
  profileForm.qau = profileInfo.profileQuantityAndUnit.description;

  if (!profileInfo.profileQuantityAndUnit["_isPredefinedQaU"]) {
    profileForm.qauType = qauTypeOptions[1];
  }
};


/**
 * Fetches and updates the current profile trace data for visualization.
 *
 * This function handles two modes:
 *  - UPDATE mode: retrieves traces for an existing profile referenced in the ESDL file.
 *  - CREATE mode: constructs a DataTableProfileObject from a profile plugin and retrieves its trace
 */
const updateTrace = async () => {
  isLoadingData.value = true;
  try {
    let results = null;
    // UPDATE mode (profile is referenced in the ESDL file)
    if (formMode.value === formModeEnum.UPDATE) {
      const profileTracesRequest = {
        es_id: props.activeEsdlId,
        profile_ids: [profileForm.id],
        viz_options: {
          multiplier: profileForm.multiplier,
          max_datapoints: config.profileMaxDataPoints,
        }
      };
      results = await fetchData("get_profile_traces", profileTracesRequest);
    }
    // CREATE mode (profile to be retrieved from, e.g. EDR) 
    else {
      const profilePluginObj = getProfileInfoFromProfilePlugin(profileForm.profile);
      if (profilePluginObj) {
        const profileTraceDtpRequest = {
          dtp_obj: {
            tableName: profilePluginObj.measurement,
            columnName: profilePluginObj.field,
            startDate: profilePluginObj.startDatetime,
            endDate: profilePluginObj.endDatetime,
            multiplier: profilePluginObj.multiplier * 1.0,
            configuration: {
              type: profilePluginObj.databaseType,
              database: profilePluginObj.database,
              host: profilePluginObj.host,
              port: profilePluginObj.port,
            }
          },
          viz_options: {
            multiplier: profileForm.multiplier,
            max_datapoints: config.profileMaxDataPoints,
          }
        }
        results = await fetchData("get_profile_trace_from_dtp_obj", profileTraceDtpRequest);
      }
    }

    // Handle errors per profile
    if (results.errors && results.errors.length > 0) {
      results.errors.forEach((err) => {
        let errMsg = "Error retrieving profile";
        if (err.profile_id) {
          errMsg += ` (id=${err.profile_id})`
        }
        if (err.error.includes("unreachable")) {
          errMsg = `Unable to display profile preview due to database connection error.`;
        }
        displayNotification("error", errMsg);
        console.error(err);
      });
    }

    const profileTraces = results.traces.map((t) => t.trace);
    const formattedData = profileTraceHandler(profileTraces);
    profileForm.currentTrace = formattedData.traces;
    profileForm.currentLayout = formattedData.layout;
  } catch (e) {
    displayNotification(
      "error",
      `An unknown error occurs while fetching profile: ${e.message || e}`
    );
    profileForm.currentTrace = [];
    profileForm.currentLayout = {};
  } finally {
    isLoadingData.value = false;
  }
}

/**
 * Add new profile to ESDL with addProfileRequest payload.
 */
const addProfile = async () => {
  isLoadingData.value = true;
  try {
    let result = null;
    const addProfileRequest = {
      es_id: props.activeEsdlId,
      // Port to attach the profile to.
      port_id: props.activePortId,
      profileClass: profileForm.profileClass,
      profile_obj: {}
    }

    // Extend addProfileRequest object with profileClass specific properties
    // SingleValue profileClass
    if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
      addProfileRequest["profile_obj"] = {
        name: profileForm.name,
        value: profileForm.value,
        profileType: profileForm.profileType,
        // TODO: support custom QaU
        profileQuantityAndUnit: profileQaU["predefined_qau"].find(qau => qau["description"] === profileForm.qau),
      }
    } 
    // InfluxDBProfile or DataTableProfile profileClass
    else {
      const profilePluginObj = getProfileInfoFromProfilePlugin(profileForm.profile);
      addProfileRequest["profile_obj"] = {
        tableName: profilePluginObj.measurement,
        columnName: profilePluginObj.field,
        startDate: profilePluginObj.startDatetime,
        endDate: profilePluginObj.endDatetime,
        // Overrides default multiple with form multiplier if present
        multiplier: profileForm.multiplier ? profileForm.multiplier * 1.0 : profilePluginObj.multiplier * 1.0,
        profileType: profileForm.profileType,
        // TODO: support custom QaU
        profileQuantityAndUnit: profileQaU["predefined_qau"].find(qau => qau["description"] === profileForm.qau),
        configuration: {
          type: profilePluginObj.databaseType,
          database: profilePluginObj.database,
          host: profilePluginObj.host,
          port: profilePluginObj.port,
        }
      }
    }

    result = await fetchData("add_esdl_profile", addProfileRequest);

    if (result.success) {
      displayNotification("success", result.message);
    } else {
      displayNotification("error", result.message);
      console.error(result.message);
    }
  } catch (e) {
    displayNotification(
      "error",
      `An unknown error occurs while adding profile: ${e.message || e}.`
    );
  } finally {
    isLoadingData.value = false;
  }
}

/**
 * Update existing ESDL profile with updateProfileRequest payload.
 */
const updateProfile = async () => {
  isLoadingData.value = true;
  try {    
    const updateProfileRequest = {
      es_id: props.activeEsdlId,
      profile_id: profileForm.id,
      profileClass: profileForm.profileClass,
      updates: {}
    };

    // Extend updateProfileRequest object with profileClass specific properties
    // SingleValue profileClass
    if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
      updateProfileRequest["updates"] = {
        name: profileForm.name,
        value: profileForm.value,
        profileType: profileForm.profileType,
      }
    }
    // InfluxDBProfile or DataTableProfile profileClass
    else {
      updateProfileRequest["updates"] = {
        multiplier: profileForm.multiplier,
        profileType: profileForm.profileType,
      }
    }

    // Only include profileQuantityAndUnit in request payload if it is modified.
    // TODO: support custom QaU
    if (profileForm.qau !== props.profileInfo.profileQuantityAndUnit.description) {
      updateProfileRequest.updates["profileQuantityAndUnit"] = profileQaU["predefined_qau"].find(qau => qau["description"] === profileForm.qau);
    }
    const result = await fetchData("update_esdl_profile", updateProfileRequest);

    if (result.success) {
      displayNotification("success", result.message);
    } else {
      displayNotification("error", result.message);
      console.error(result.message);
    }
  } catch (e) {
    displayNotification(
      "error",
      `An unknown error occurs while updating profile: ${e.message || e}. Changes will not be saved.`
    );
  } finally {
    isLoadingData.value = false;
  }
}

/**
 * TODO: clean up
 * @param profileName 
 */
const getProfileInfoFromProfilePlugin = (profileName) => {
  let result = null;

  const profiles = profilePlugin["profiles_list"]["profiles"];
  const groups = profilePlugin["profiles_list"]["groups"];

  // TODO: this could miss some profile
  const profile = Object.values(profiles).find(p => p["profile_uiname"] === profileName);

  if (profile) {
    const settingType = profile["setting_type"];
    const profileGroupName = groups.find(g => g["setting_type"] === settingType)["name"];
    const databaseType = deriveProfileDatabaseType(profile);

    let tableName;
    let columnName;
    if (databaseType === DatabaseTypeEnum.INFLUXDB) {
      tableName = profile["measurement"];
      columnName = profile["field"];
    } else if (databaseType === DatabaseTypeEnum.POSTGRESQL) {
      tableName = profile["table"];
      columnName = profile["column"];
    }

    // TODO: proper handling of host, port, and database when not given as profile properties.
    // TODO: maybe the object should follow DTP structure?
    // TODO: properly handle personl, system, project profile connection info.
    // TODO: profileQaU?
    result = {
      host: profile["host"] || "localhost",
      port: profile["port"] || 8086,
      database: profile["database"] || null,
      measurement: tableName,
      field: columnName,
      multiplier: profile["multiplier"],
      startDatetime: profile["start_datetime"],
      endDatetime: profile["end_datetime"],
      databaseType: databaseType,
      profileGroupName: profileGroupName
    }
  }
  
  return result;
}

/**
 * Configures profile chart traces and layout for visualization.
 *
 * @param {Array} traces An array of trace objects to be configured for profile visualization.
 * @returns {Object} An object containing the configured traces and layout for the profile chart.
 */
const profileTraceHandler = (traces) => {
  traces.forEach((t) => {
    t.type = "scatter";
    t.mode = "lines";
  });

  const profileLayout = {
    autosize: true,
    margin: { t: 20, b: 20, l: 32, r: 32 },
  };

  return {
    traces: traces,
    layout: profileLayout,
  };
};

const onSelectProfileClass = (type) => {
  initForm(type);
};

const onSelectProfile = (profile) => {
  // Reset the form when profile is undefined (e.g. when the selection is cleared.)
  if (profile === undefined) {
    initForm(profileForm.profileClass);
  } else {
    const profilePluginObj = getProfileInfoFromProfilePlugin(profile);
    if (profilePluginObj) {
      profileForm.profileSourceTag = profilePluginObj["profileGroupName"] || "";
      profileForm.databaseType = profilePluginObj["databaseType"];
      profileForm.multiplier = profilePluginObj["multiplier"];
    }
    updateTrace();
  }  
}

const onUpdateMultiplier = (value) => {
  if (value !== null) {
    // Wait for 0.5 sec before updating the trace.
    setTimeout(() => {
      updateTrace();
    }, 500);
  }
}

// Disable form save button when no changes are made in the UPDATE mode.
const noChangeDetected = computed(() => {
  if (formMode.value === formModeEnum.UPDATE) {
    if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
      return (
        profileForm.name === props.profileInfo.name &&
        profileForm.value === props.profileInfo.value &&
        profileForm.profileType === props.profileInfo.profileType &&
        profileForm.qau === props.profileInfo.profileQuantityAndUnit.description
      )
    } else {
      return (
        profileForm.profileType === props.profileInfo.profileType &&
        profileForm.multiplier === props.profileInfo.multiplier &&
        profileForm.qau === props.profileInfo.profileQuantityAndUnit.description);
      }
  } else {
    return false;
  }
});

const invalidForm = computed(() => {
  if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
      return (
        profileForm.name === null ||
        profileForm.value === null ||
        (profileForm.qau === null || profileForm.qau === undefined)
      );
  } else {
    return (
      profileForm.profile === null ||
      profileForm.multiplier === null ||
      (profileForm.qau === null || profileForm.qau === undefined)
    );
  }
});

const onSave = () => {
  if (formMode.value === formModeEnum.UPDATE) {
    updateProfile();
  } else if (formMode.value === formModeEnum.CREATE) {
    addProfile();
  }
  emit("onSave");
};

const onCancel = () => {
  emit("onCancel");
};

// ------------------------------------------- //
// -------------- Util functions ------------- //
// ------------------------------------------- //

// TODO: pay attention to profiles with the same name
const listProfileOptions = () => {
  const options = [];

  const profileGroups = profilePlugin["profiles_list"]["groups"];
  const profileInfo = Object.entries(
    profilePlugin["profiles_list"]["profiles"],
  );

  profileGroups.forEach((gr) => {
    const groupLabel = gr["name"];
    const groupProfiles = [];

    for (let pr = 0; pr < profileInfo.length; pr++) {
      if (gr.setting_type == profileInfo[pr][1].setting_type) {
        if (
          profileInfo[pr][1].setting_type == "project" &&
          profileInfo[pr][1].project_name != gr.project_name
        ) {
          continue;
        }

        groupProfiles.push({
          value: profileInfo[pr][1]["profile_uiname"],
          label: profileInfo[pr][1]["profile_uiname"], // TODO: replace this with profile id?
          databaseType: deriveProfileDatabaseType(profileInfo[pr][1])
        });
      }
    }

    options.push({
      label: groupLabel,
      options: groupProfiles,
    });
  });

  return options;
};

/**
 * An until function to derive profile database type from a profilePlugin profile record.
 * 
 * @param profileInfo {Object} A profile object stored in the profilePlugin profiles list.
 */
const deriveProfileDatabaseType = (profileInfo) => {
  let databaseType = "Unknown";
  if (profileInfo["type"]) {
    databaseType = DatabaseTypeEnum[profileInfo["type"]];
  } // To handle a record without 'type' attribute (introduced in esdl.DatabaseConfiguration)  
  else if (profileInfo["item_type"] && profileInfo["item_type"] === "InfluxDBProfile") {
    databaseType = DatabaseTypeEnum.INFLUXDB;
  }
  return databaseType;
} 

const listPredefQaU = () => {
  const options = [];

  for (let q = 0; q < profileQaU["predefined_qau"].length; q++) {
    options.push({
      value: profileQaU["predefined_qau"][q]["description"],
      label: profileQaU["predefined_qau"][q]["description"],
    });
  }
  return options;
};

</script>

<style scoped>

:deep(.ant-segmented-item),
:deep(.ant-segmented-item::selection) {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.plot {
  height: 200px;
}

</style>
