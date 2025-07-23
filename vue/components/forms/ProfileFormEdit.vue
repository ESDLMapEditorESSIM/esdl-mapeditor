<template>
  <a-modal
    :open="props.visible"
    :title="`Profile Editor${props.profileTag ? ` - ${props.profileTag}` : ''}`"
    @cancel="onCancel"
  >
    <template #footer>
      <a-button @click="onCancel">Cancel</a-button>
      <a-button type="primary" :disabled="invalidForm" @click="onSave">Save</a-button>
    </template>
    <a-form ref="profileFormRef" layout="vertical" :model="profileForm">
      <a-form-item label="ID">
        <a-input v-model:value="profileForm.id" disabled />
      </a-form-item>
      <a-form-item label="Class">
        <a-input v-model:value="profileForm.class" disabled />
      </a-form-item>
      <a-form-item
        label="Profile"
        required
        :rules="[{ required: true, type: 'object' }]"
      >
        <a-select
          v-model:value="profileForm.profile"
          :options="profileOptions"
          allow-clear
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>
      <a-form-item
        label="Multiplier"
        required
        :rules="[{ required: true, type: 'number' }]"
      >
        <a-input-number
          v-model:value="profileForm.multiplier"
          style="width: 100%"
        />
      </a-form-item>
      <a-form-item label="Unit type">
        <a-select
          v-model:value="profileForm.unitType"
          :options="unitTypeOptions"
          disabled
        />
      </a-form-item>
      <a-form-item
        label="Quantity and unit"
        required
        :rules="[{ required: true, type: 'object' }]"
      >
        <a-select
          v-model:value="profileForm.qau"
          :options="profileQaUOptions"
          allow-clear
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from "vue";
import { v4 as uuidv4 } from "uuid";

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
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

const ProfileClass = Object.freeze({
  INFLUXDB: "InfluxDBProfile",
});

const UnitType = Object.freeze({
  PREDEFINED: "Predefined quantity and units",
});

const unitTypeOptions = Object.entries(UnitType).map(([_, label]) => ({
  value: label,
  label: label,
}));

const profileFormRef = ref(null);

const profileOptions = ref([]);
const profileQaUOptions = ref([]);

const initProfileForm = {
  id: null,
  class: ProfileClass.INFLUXDB,
  profile: null,
  multiplier: null,
  // default to the predefined unit type until other types are supported in the future
  unitType: unitTypeOptions[0],
  qau: null,
};

const profileForm = reactive({ ...initProfileForm });

onMounted(() => {
  profileOptions.value = listProfileOptions();
  profileQaUOptions.value = listPredefQaU();
});

// Reset form to the initial state
const resetForm = () => {
  Object.assign(profileForm, { ...initProfileForm });
  profileForm.id = uuidv4();
};

/**
 * Cast the given profileInfo object into profileForm accepted data.
 *
 * @param {Object} profileInfo profile object passed from the parent component.
 */
const castProfileInfoToFormData = (profileInfo) => {
  profileForm.id = profileInfo.id;
  profileForm.profile = profileInfo.displayed_name;
  profileForm.multiplier = profileInfo.multiplier;
  profileForm.qau = profileInfo.qau_description;
};

watch(
  () => props.visible,
  () => {
    // Reset form to ensure no existing data is left on dialog open and close.
    resetForm();

    if (props.visible && props.profileInfo) {
      castProfileInfoToFormData(props.profileInfo);
    }
  },
);

const invalidForm = computed(() => {
  return (
    profileForm.profile === null ||
    profileForm.multiplier === null ||
    profileForm.qau === null
  );
});

const onSave = () => {
  const formData = {
    id: profileForm.id,
    profile_class: profileForm.class,
    displayed_name: profileForm.profile,
    multiplier: profileForm.multiplier,
    qau_description: profileForm.qau,
  };

  emit("onSave", {
    tag: props.profileTag,
    data: formData,
  });
};

const onCancel = () => {
  emit("onCancel");
};

// ------------------------------------------- //
// -------------- Util functions ------------- //
// ------------------------------------------- //

const listProfileOptions = () => {
  const options = [];

  const profilePlugin = window.profiles_plugin;
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
          label: profileInfo[pr][1]["profile_uiname"],
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

const listPredefQaU = () => {
  const options = [];
  const profileQaU = window.quantity_and_units_info;

  for (let q = 0; q < profileQaU["predefined_qau"].length; q++) {
    options.push({
      value: profileQaU["predefined_qau"][q]["description"],
      label: profileQaU["predefined_qau"][q]["description"],
    });
  }
  return options;
};
</script>
