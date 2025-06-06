<template>
  <a-modal
    :open="props.visible"
    title="InfluxDB Profile"
    @cancel="onCancel"
  >
    <template #footer>
      <a-button @click="onCancel">Cancel</a-button>
      <a-button type="primary" :disabled="invalidForm" @click="onSave">Save</a-button>
    </template>
    <a-form
      ref="profileFormRef"
      layout="vertical"
      :model="profileForm"
    >
      <a-form-item label="ID">
        <a-input v-model:value="profileForm.id" disabled />
      </a-form-item>
      <a-form-item label="Class">
        <a-input v-model:value="profileForm.class" disabled />
      </a-form-item>
      <a-form-item label="Profile" required :rules="[{ required: true, type: 'object' }]">
        <a-select
          v-model:value="profileForm.uiname"
          :options="profileOptions"
          allow-clear
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>
      <!-- TODO: value or multiplier -->
      <a-form-item label="Multiplier" required :rules="[{ required: true, type: 'number' }]">
        <a-input-number v-model:value="profileForm.multiplier" style="width: 100%;" />
      </a-form-item>
      <!-- TODO: support dropdown -->
      <a-form-item label="Unit type">
        <a-input placeholder="Predefined quantity and units" disabled />
        <!-- <a-select
          v-model:value="profileForm.unitType"
          :options="unitTypeOptions"
          disabled
        /> -->
      </a-form-item>
      <a-form-item label="Quantity and unit" required :rules="[{ required: true, type: 'object' }]">
        <a-select
          v-model:value="profileForm.type"
          :options="profileQaUOptions"
          allow-clear
          @mouseleave="removeTooltipPopup"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { v4 as uuidv4 } from 'uuid';

// to prevent stuck popup on UI
const removeTooltipPopup = () => { window.jquery(".ui-tooltip-content").parents('div').remove();};

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  // Existing profile info for further editing;
  profileInfo: {
    type: Object,
    default: null
  },
});

const emit = defineEmits(["onSave", "onCancel"]);

// TODO:
// Make sure form validation is working properly


// TODO
// Global variables
const profilePlugin = window.profiles_plugin;
const profileQaU = window.quantity_and_units_info;

const profileFormRef = ref(null);

// State - Profile
const profileOptions = ref([]);
// TODO: make it dynamic
// const unitTypeOptions = ref([{value: 'Predefined quantity and units', label: 'Predefined quantity and units'}])
const profileQaUOptions = ref([]);

const initProfileForm = {
  id: '',
  class: 'InfluxDBProfile', // TODO: replace hard coded value to support other constraint
  uiname: null,
  multiplier: null,
  // unitType: unitTypeOptions.value[0], // TODO: now default to the first element; make it dynamic; name?
	type: null // TODO: rename?
};

const profileForm = reactive({ ...initProfileForm });

onMounted(() => {
	profileOptions.value = listProfileOptions();
	profileQaUOptions.value = listPredefQaU();
})

const initializeProfileForm = () => {
  if (props.profileInfo) {
    const displayedFormData = castProfileInfoToFormData(props.profileInfo);
    Object.assign(profileForm, { ...displayedFormData });
  } else {
    Object.assign(profileForm, { ...initProfileForm });
    profileForm.id = uuidv4();
  }
};

const castProfileInfoToFormData = (profileInfo) => {
  const pQaULabel = profileInfo.type;
  
  const displayedFormData = {
    id: profileInfo.id,
    class: 'InfluxDBProfile',
    uiname: getOptionObjByValue(profileOptions.value, profileInfo.uiname),
    multiplier: profileInfo.multiplier,
    // unitType: unitTypeOptions.value[0],
    type: getOptionObjByLabel(profileQaUOptions.value, pQaULabel) // TODO: rename?
  }
  console.debug(displayedFormData);
  return displayedFormData;
}


watch(() => props.visible, () => {
  if (props.visible) {
    initializeProfileForm();
  } else {
    resetForm();
  }

  console.debug(profileForm);
})

// Reset form to the initial state
const resetForm = () => {
  Object.assign(profileForm, { ...initProfileForm });
}

const invalidForm = computed(() => {
  return profileForm.uiname === null || 
         profileForm.type === null ||
         profileForm.multiplier === null
})

const onSave = () => {
  const uinameValue = profileForm.uiname.value || profileForm.uiname;
  const pQaUValue = profileForm.type.value || profileForm.type;

  const formData = {
    id: profileForm.id || uuidv4(),
    class: 'InfluxDBProfile',
    uiname: getOptionObjByValue(profileOptions.value, uinameValue),
    multiplier: profileForm.multiplier,
    // unitType: unitTypeOptions.value[0],
    type: getOptionObjByValue(profileQaUOptions.value, pQaUValue)
  }

  emit("onSave", formData);
};

const onCancel = () => {
  emit("onCancel");
};


// Util functions
const getOptionObjByValue = (optionObjs, optionValue) => {
  const optionObj = optionObjs
    .flatMap(opt => opt.options ?? [opt]) // Flatten grouped options if applicable
    .find(opt => opt.value.toLowerCase() === optionValue.toLowerCase());
  return optionObj || null;
}

// TODO: combine with above
const getOptionObjByLabel = (optionObjs, optionLabel) => {
  const optionObj = optionObjs
    .flatMap(opt => opt.options ?? [opt]) // Flatten grouped options if applicable
    .find(opt => opt.label.toLowerCase() === optionLabel.toLowerCase());
  return optionObj || null;
}

// TODO
// const validateAndSubmit = () => {
//   profileFormRef.value.validate()
//     .then(() => {
//       console.log("Form is valid, proceed with submission!");
//       // Proceed to emit or save the data
//     })
//     .catch(() => {
//       console.log("Validation failed, please fill required fields.");
//     });
// };

// TODO: clean up
const listProfileOptions = () => {
	const options = [];
	const profileGroups = profilePlugin['profiles_list']['groups'];
	const profileInfo = Object.entries(profilePlugin['profiles_list']['profiles']);
	
	profileGroups.forEach((gr) => {
		const groupLabel = gr['name'];
		let groupProfiles = []

		for (let pr=0; pr < profileInfo.length; pr++) {
			if (gr.setting_type == profileInfo[pr][1].setting_type) {
				if (
					profileInfo[pr][1].setting_type == 'project' && 
					profileInfo[pr][1].project_name != gr.project_name
				) {
						continue;
					}

				groupProfiles.push({
					value: profileInfo[pr][1].profile_uiname,
					label: profileInfo[pr][1].profile_uiname
				})
			}
		}

		options.push({
			label: groupLabel,
			options: groupProfiles
		})
	})

	return options;
}

const listPredefQaU = () => {
	const options = [];
	for (let q=0; q<profileQaU["predefined_qau"].length; q++) {
		options.push({
			value: profileQaU["predefined_qau"][q]["id"],
			label: profileQaU["predefined_qau"][q]["description"]
		})
	}
	return options;
}


</script>