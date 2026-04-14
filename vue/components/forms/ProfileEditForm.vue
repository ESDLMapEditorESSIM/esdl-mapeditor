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
          :rules="[{ type: 'string' }]"
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
          <a-tree-select
            v-model:value="profileForm.profile"
            :tree-data="profileForm.profileClass === profileClassEnum.INFLUXDBPROFILE ? influxDBProfileOptions : profileOptions"
            show-search
            allow-clear
            :disabled="formMode === formModeEnum.UPDATE"
            :filter-tree-node="filterTreeNode"
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

        <a-form-item label="Start date">
          <a-input v-model:value="profileForm.startDate" disabled />
        </a-form-item>
        <a-form-item label="End date">
          <a-input v-model:value="profileForm.endDate" disabled />
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
        label="Quantity and unit"
        :rules="[{ required: true, type: 'object' }]"
      >
        <a-select
          v-model:value="profileForm.qau"
          :options="predefinedQaUOptions"
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
  // The container id for which the profile is attached to. e.g. Port or ProfileConstraint
  activeProfileContainerId: {
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
  // Controls how the form behaves when the user clicks "Save".
  // - If true: the component emits the constructed profile payload to the parent,
  //            and the parent decides what to do with it (e.g., store, preview, validate).
  // - If false: the component itself performs the save action by creating or updating
  //             the profile in ESDL, and still emits the payload for parent awareness.
  returnProfilePayloadOnSave: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits(["onSave", "onCancel"]);

// ----------------------------------------- //
// ---------- Component constant ----------- //
// ----------------------------------------- //

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
    startDate: null,
    endDate: null,
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
    startDate: null,
    endDate: null,
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

const profileSettings = ref([]);
const profileOptions = ref([]);
const influxDBProfileOptions = ref([]);
const predefinedQaUOptions = ref([]);

const isLoadingData = ref(false);

onMounted(async () => {
  const profiles = await getProfileSettings();  
  profileSettings.value = profiles;

  const { full, influxOnly } = await listProfileOptions(profiles);
  profileOptions.value = full;
  influxDBProfileOptions.value = influxOnly;

  predefinedQaUOptions.value = listPredefQaU();
});

watch(
  () => props.visible,
  () => {
    formMode.value = formModeEnum.CREATE;
    initForm(profileClassEnum.INFLUXDBPROFILE)

    if (props.visible && props.profileInfo) {
      // profile id is assigned when the profile is instantiated in the backend.
      // If the profile id exists, set the form to UPDATE mode.
      if (props.profileInfo.profileObj.id) {
        formMode.value = formModeEnum.UPDATE;
      }
      initializeProfileEditing(props.profileInfo);
    }
  },
);

/**
 * Initialize the profile form for editing.
 * 
 * @param {Object} profileInfo - The profileInfo object passed from the parent component to be loaded into the form.
 */
const initializeProfileEditing = (profileInfo) => {
  console.debug(profileInfo);
  
  profileForm.profileClass = profileInfo.profileClass;
  if (profileInfo.profileClass === profileClassEnum.SINGLEVALUE) {
    castSingleValueObjToFormData(profileInfo.profileObj);
  } else {
    castProfileObjToFormData(profileInfo.profileObj);
    updateTrace();
  }
}

/**
 * Cast the given profile object with SingleValue-like structure into profileForm accepted data.
 *
 * @param {Object} profileObj profile object with SingleValue-like structure.
 */
const castSingleValueObjToFormData = (profileObj) => {
  profileForm.id = profileObj.id;
  profileForm.name = profileObj.name;
  profileForm.value = profileObj.value;
  profileForm.profileType = profileObj.profileType;
  profileForm.qau = profileObj.profileQuantityAndUnit.description;

  const foundPredefQaU = predefinedQaUOptions.value.find(opt => opt.label === profileObj.profileQuantityAndUnit.description);
  if (!foundPredefQaU) {
    profileForm.qauType = qauTypeOptions[1];
  }
}

/**
 * Cast the given profile object with DataTableProfile-like structure into profileForm accepted data.
 *
 * @param {Object} profileObj profile object with DataTableProfile-like structure.
 */
const castProfileObjToFormData = (profileObj) => {
  // The displayed name follows the same pattern as defined in get_profile_settings_as_dtp_objects() in profiles.py
  let profileDisplayedName = `${profileObj.configuration.type}: ${profileObj.tableName}.${profileObj.columnName}`;

  const profileSettingsObj = getProfileSettingsObj(profileForm.profile || profileDisplayedName);
  // profile setting can't be found in setting storage, the profile is stored somewhere else.
  if (!profileSettingsObj) {
    profileForm.profileSourceTag = "External profile";
  } else {
    profileForm.profileSourceTag = profileSettingsObj.metadata.profileGroupName;
    profileDisplayedName = profileSettingsObj.metadata.profileDisplayedName;
  }

  profileForm.id = profileObj.id;
  profileForm.profile = profileDisplayedName;
  profileForm.databaseType = profileObj.configuration.type;
  profileForm.profileType = profileObj.profileType;
  profileForm.multiplier = profileObj.multiplier;
  profileForm.startDate = profileObj.startDate;
  profileForm.endDate = profileObj.endDate;
  profileForm.qau = profileObj.profileQuantityAndUnit.description;

  const foundPredefQaU = predefinedQaUOptions.value.find(opt => opt.label === profileObj.profileQuantityAndUnit.description);
  if (!foundPredefQaU) {
    profileForm.qauType = qauTypeOptions[1];
  }
};


/**
 * Fetches and updates the current profile trace data for visualization.
 *
 * This function fetches traces in two modes
 *  - UPDATE mode: retrieves traces for an existing profile referenced in the ESDL file.
 *  - CREATE mode: constructs a DataTableProfile-like object as a request payload and retrieves its trace.
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
    // CREATE mode (profile setting for querying trace is derived from profile settings storage) 
    else {
      const profileSettingsObj = getProfileSettingsObj(profileForm.profile);
      if (profileSettingsObj) {
        const profileTraceDtpRequest = {
          dtp_obj: {
            ...profileSettingsObj.profileObj,
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
        if (err.error.includes("unreachable") || err.error.includes("401")) {
          errMsg = `Unable to display profile preview due to connection error.`;
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
const addProfile = async (addProfileRequest) => {
  isLoadingData.value = true;
  try {
    const result = await fetchData("add_esdl_profile", addProfileRequest);

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
    const profileObj = props.profileInfo.profileObj;
    if (profileForm.qau !== profileObj.profileQuantityAndUnit.description) {
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
 * Construct a standardized profile payload object based on the current form inputs.
 *
 * This function converts the user‑edited form state into the backend‑compatible payload structure.
 * - For SingleValue: the payload is built directly from form fields.
 * - For DataTableProfile / InfluxDBProfile: the payload is built either from profile setting object
 *                                           or setting passed from the parent component and with form state overrides.
 *
 * @returns {Object} A fully constructed profile payload ready to be emitted or saved.
 */
const constructProfilePayloadFromFormData = () => {
  const profilePayload = {
    es_id: props.activeEsdlId,
    profile_container_id: props.activeProfileContainerId,
    profileClass: profileForm.profileClass,
    profileObj: {}
  }

  // Extend profilePayload object with profileClass specific properties
  // SingleValue profileClass
  if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
    profilePayload.profileObj = {
      name: profileForm.name,
      value: profileForm.value,
      profileType: profileForm.profileType,
      // TODO: support custom QaU
      profileQuantityAndUnit: profileQaU["predefined_qau"].find(qau => qau["description"] === profileForm.qau),
    }
  } 
  // InfluxDBProfile or DataTableProfile profileClass
  else {
    // In CREATE mode, get profile setting from setting storage;
    // otherwise, get it from the object passed from the parent component.
    const profileSettingsObj = getProfileSettingsObj(profileForm.profile);
    const profileObj = profileSettingsObj ? profileSettingsObj.profileObj : props.profileInfo.profileObj;

    profilePayload.profileObj = {
      ...profileObj,
      profileType: profileForm.profileType,
      // Overrides default multiple with form multiplier if present
      multiplier: profileForm.multiplier || profileObj.multiplier,
      // TODO: support custom QaU
      profileQuantityAndUnit: profileQaU["predefined_qau"].find(qau => qau["description"] === profileForm.qau),
    }
  }

  return profilePayload;
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

const onSelectProfile = (profileOptionValue) => {
  // Reset the form when profileOptionValue is undefined (e.g. when the selection is cleared.)
  if (profileOptionValue === undefined) {
    initForm(profileForm.profileClass);
  } else {
    const profileSettingsObj = getProfileSettingsObj(profileOptionValue);
    if (profileSettingsObj) {
      profileForm.profileSourceTag = profileSettingsObj.metadata.profileGroupName;
      profileForm.databaseType = profileSettingsObj.profileObj.configuration.type;
      profileForm.multiplier = profileSettingsObj.profileObj.multiplier;
      profileForm.startDate = profileSettingsObj.profileObj.startDate;
      profileForm.endDate = profileSettingsObj.profileObj.endDate;
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
    const profileObj = props.profileInfo.profileObj;
    if (profileForm.profileClass === profileClassEnum.SINGLEVALUE) {
      return (
        profileForm.name === profileObj.name &&
        profileForm.value === profileObj.value &&
        profileForm.profileType === profileObj.profileType &&
        profileForm.qau === profileObj.profileQuantityAndUnit.description
      )
    } else {
      return (
        profileForm.profileType === profileObj.profileType &&
        profileForm.multiplier === profileObj.multiplier &&
        profileForm.qau === profileObj.profileQuantityAndUnit.description);
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
  const profilePayload = constructProfilePayloadFromFormData();

  // If the parent does NOT want to handle saving, perform the save internally
  if (!props.returnProfilePayloadOnSave) {
    if (formMode.value === formModeEnum.UPDATE) {
      updateProfile();
    } else if (formMode.value === formModeEnum.CREATE) {
      addProfile(profilePayload);
    }
  }

  emit("onSave", {
    tag: props.profileTag,
    profileInfo: {...profilePayload},
  });
};

const onCancel = () => {
  emit("onCancel");
};

/**
 * Fetch all stored profile settings from the backend in a standardized DataTableProfile-like format.
 */
const getProfileSettings = async () => {
  isLoadingData.value = true;
  try {
    const result = await fetchData("get_profile_settings_as_dtp_objects");

    if (result.length === 0) {
      displayNotification("warning", "No profiles found in the profile database for listing.");
    }

    return result;
  } catch (e) {
    displayNotification(
      "error",
      `An unknown error occurs while listing stored profiles: ${e.message || e}`
    );
  } finally {
    isLoadingData.value = false;
  }
}

/**
 * Transform a list of normalized profile objects into a UI-friendly structure
 * suitable for tree select dropdown components.
 */
const listProfileOptions = async (profiles) => {
  if (!profiles) {
    return {
      full: [],
      influxOnly: []
    };
  }

  // Group profiles by group name
  const groupsMap = new Map();

  profiles.forEach(({ profileObj, metadata }) => {
    const groupName = metadata.profileGroupName || "Other";

    if (!groupsMap.has(groupName)) {
      groupsMap.set(groupName, []);
    }

    groupsMap.get(groupName).push({
      label: metadata.profileDisplayedName,
      value: metadata.profileSettingId,
      databaseType: profileObj.configuration.type,
    });
  });

  const full = Array.from(groupsMap.entries()).map(([groupName, children]) => ({
    title: groupName,
    value: groupName,
    selectable: false,
    children
  }));

  // Disable PostgreSQL profiles for InfluxDBProfile
  const influxOnly = full.map((group) => ({
    ...group,
    children: group.children.map((child) => ({
      ...child,
      disabled: child.databaseType === DatabaseTypeEnum.POSTGRESQL
    }))
  }));

  return { full, influxOnly };
};

/**
 * A utility function to filter tree select options.
 */
const filterTreeNode = (input, node) => {
  if (!input) return true;

  const text = node.label?.toString().toLowerCase() || "";
  const query = input.toString().toLowerCase();

  // Basic fuzzy match: allow characters in order but not necessarily adjacent
  let i = 0;
  for (const char of text) {
    if (char === query[i]) i++;
    if (i === query.length) return true;
  }

  return false;
};


/**
 * Retrieve a stored profile settings object by either:
 * - profileSettingId (when available), or
 * - profileDisplayedName (used in edit mode when only the label is available)
 *
 * @param {string|null} profileIdentifier
 *        The identifier coming from profileForm.profile — may be either
 *        the profileSettingId or the profileDisplayedName.
 */
const getProfileSettingsObj = (profileIdentifier) => {
  if (!profileIdentifier) {
    console.warn("getProfileSettingsObj called with empty identifier.");
    return null;
  }

  const matches = profileSettings.value.filter(p => {
    const idMatch = p.metadata.profileSettingId === profileIdentifier;
    const nameMatch = p.metadata.profileDisplayedName === profileIdentifier;
    return idMatch || nameMatch;
  });

  if (matches.length === 0) {
    console.warn(`No profile settings object found with identifier as "${profileIdentifier}".`);
    return null;
  }

  if (matches.length > 1) {
    console.warn(`Found ${matches.length} profile settings objects with identifier as "${profileIdentifier}". Returning the first match.`);
  }

  return matches[0];
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

:deep(.ant-form-item) {
  margin-bottom: 12px;
}

.plot {
  height: 200px;
}

</style>
