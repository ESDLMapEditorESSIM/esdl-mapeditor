<template>
  <a-space
    id="asset-constraint"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%"
  >
    <!-- Header -->
    <a-row v-if="!props.embeddedView">
      <a-typography-title :level="3">
        <img
          src="/static/icons/Chain.png"
          alt="Asset Constraint Icon"
          style="width: 24px; height: 24px"
        >
        Asset Constraint
      </a-typography-title>
    </a-row>

    <!----------------------------------->
    <!------------- Content ------------->
    <!----------------------------------->
    <a-col style="height: 100%">
      <a-segmented
        v-model:value="activeSegment"
        :options="segmentedOptions"
        style="width: 100%"
        block
        @change="onSelectSegment"
      />
      <br>
      <!------------- LIST CONSTRAINTS ------------->
      <div
        v-if="activeSegment === SegmentOptions.CONSTRAINTS"
        style="width: 100%"
      >
        <a-col v-if="constraints.length">
          <a-table
            :data-source="constraints"
            :columns="columns"
            :pagination="false"
            size="middle"
            table-layout="fixed"
            :scroll="{ y: 'calc(100vh - 180px)' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div class="cell-ellipsis" :title="record.name">
                  {{ record.name }}
                </div>
                <a-tag
                  :color="constraintTypeColor[record.type]"
                  class="type-tag"
                  :title="record.type"
                >
                  {{ record.type?.replace(/Constraint$/, "") }}
                </a-tag>
              </template>

              <template v-if="column.key === 'value'">
                <div
                  v-for="item in getConstraintValues(record)"
                  :key="item.label"
                  class="cell-ellipsis"
                  :title="`${item.label}: ${item.text}`"
                >
                  <span class="value-label">{{ item.label }}:</span> {{ item.text }}
                </div>
                <span v-if="!getConstraintValues(record).length" class="value-label">–</span>
              </template>

              <template v-if="column.key === 'action'">
                <div class="action-buttons action-buttons-vertical">
                  <a-button
                    type="text"
                    size="small"
                    @click="onEditConstraint(record)"
                  >
                    <edit-outlined />
                  </a-button>
                  <a-button
                    type="text"
                    size="small"
                    danger
                    @click="onDeleteConstraint(record.id)"
                  >
                    <delete-outlined />
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>
        </a-col>

        <!-- Empty state: no constraints -->
        <a-col v-else>
          <a-empty
            :description="'No constraints defined'"
            :image-style="{ height: '150px' }"
          />
        </a-col>
      </div>

      <!------------- ADD CONSTRAINT ------------->
      <div
        v-if="activeSegment === SegmentOptions.ADD_CONSTRAINT"
        style="width: 100%"
      >
        <a-card>
          <a-form layout="vertical">
            <a-form-item label="Constraint Type">
              <a-select
                v-model:value="formData.type"
                :options="
                  availableConstraintTypes.map((ct) => ({
                    value: ct,
                    label: ct,
                  }))
                "
                :disabled="currentConstraint !== null"
                @change="onSelectConstraintType"
              />
            </a-form-item>

            <!------------- Constraint base properties ------------->
            <a-form-item label="ID">
              <a-input v-model:value="formData.id" disabled />
            </a-form-item>
            <a-form-item label="Name">
              <a-input
                v-model:value="formData.name"
                placeholder="Constraint name"
              />
            </a-form-item>
            <a-form-item label="Description">
              <a-input
                v-model:value="formData.description"
                placeholder="Describe the purpose of this constraint"
              />
            </a-form-item>
            <a-form-item label="Attribute Reference">
              <a-select
                v-model:value="formData.attributeReference"
                :options="attributeReferenceOptions"
                allow-clear
              />
            </a-form-item>

            <!-------- Profile constraint specific UI --------->
            <a-col v-if="formData.type === ConstraintType.PROFILE">
              <a-form-item label="Maximum">
                <a-row v-if="formData.maximum !== null">
                  <a-col :span="20">
                    <p>{{ constructProfileDisplayedName(formData.maximum.profileObj) }}</p>
                  </a-col>
                  <a-col :span="4">
                    <div class="action-buttons">
                      <a-button type="text" size="small">
                        <edit-outlined
                          @click="onEditConstraintMinMax(ProfileTag.MAX)"
                        />
                      </a-button>
                      <a-button
                        type="text"
                        size="small"
                        danger
                        @click="onDeleteConstraintMinMax(ProfileTag.MAX)"
                      >
                        <delete-outlined />
                      </a-button>
                    </div>
                  </a-col>
                </a-row>
                <a-button
                  v-else
                  block
                  :disabled="isFieldDisabled('maximum')"
                  @click="openProfileModal(ProfileTag.MAX)"
                >
                  Add maximum
                </a-button>
              </a-form-item>
              <a-form-item label="Minimum">
                <a-row v-if="formData.minimum !== null">
                  <a-col :span="20">
                    <p>{{ constructProfileDisplayedName(formData.minimum.profileObj) }}</p>
                  </a-col>
                  <a-col :span="4">
                    <div class="action-buttons">
                      <a-button type="text" size="small">
                        <edit-outlined
                          @click="onEditConstraintMinMax(ProfileTag.MIN)"
                        />
                      </a-button>
                      <a-button
                        type="text"
                        size="small"
                        danger
                        @click="onDeleteConstraintMinMax(ProfileTag.MIN)"
                      >
                        <delete-outlined />
                      </a-button>
                    </div>
                  </a-col>
                </a-row>
                <a-button
                  v-else
                  block
                  :disabled="isFieldDisabled('minimum')"
                  @click="openProfileModal(ProfileTag.MIN)"
                >
                  Add minimum
                </a-button>
              </a-form-item>
              <ProfileEditForm
                :visible="profileModalVisible"
                :active-esdl-id="activeEsdlId"
                :active-profile-container-id="null"
                :profile-tag="activeProfileTag"
                :profile-info="activeProfile"
                :return-profile-payload-on-save="true"
                @on-save="onSaveProfileFormData"
                @on-cancel="onCancelProfileFormData"
              />
            </a-col>

            <!-------- Ranged constraint specific UI --------->
            <a-col v-if="formData.type === ConstraintType.RANGED">
              <a-typography-title :level="5">Range values</a-typography-title>
              <a-form-item label="ID">
                <a-input v-model:value="formData.range.id" disabled />
              </a-form-item>
              <a-form-item label="Name">
                <a-input v-model:value="formData.range.name" />
              </a-form-item>
              <a-row>
                <a-space direction="horizontal" style="width: 100%">
                  <a-form-item label="Minimum">
                    <a-input-number
                      v-model:value="formData.range.min_value"
                      style="width: 100%"
                      :step="0.1"
                      :disabled="isFieldDisabled('range.min_value')"
                    />
                  </a-form-item>
                  <a-form-item label="Mid-value">
                    <a-input-number
                      v-model:value="formData.range.mid_value"
                      style="width: 100%"
                      :step="0.1"
                      :disabled="isFieldDisabled('range.mid_value')"
                    />
                  </a-form-item>
                  <a-form-item label="Maximum">
                    <a-input-number
                      v-model:value="formData.range.max_value"
                      style="width: 100%"
                      :step="0.1"
                      :disabled="isFieldDisabled('range.max_value')"
                    />
                  </a-form-item>
                </a-space>
              </a-row>
            </a-col>

            <!-------- PipeDiameterConstraint specific UI --------->
            <a-col v-if="formData.type === ConstraintType.PIPEDIAMETER">
              <a-form-item label="Maximum">
                <a-select
                  v-model:value="formData.maximum"
                  allow-clear
                  :options="formData.EEnum?.maximum?.map((option) => ({
                    value: option,
                    label: option
                  })) || []"
                  :disabled="isFieldDisabled('maximum')"
                />
              </a-form-item>
              <a-form-item label="Minimum">
                <a-select
                  v-model:value="formData.minimum"
                  allow-clear
                  :options="formData.EEnum?.minimum?.map((option) => ({
                    value: option,
                    label: option
                  })) || []"
                  :disabled="isFieldDisabled('minimum')"
                />
              </a-form-item>
            </a-col>

            <a-button
              v-if="currentConstraint === null"
              type="primary"
              block
              :disabled="invalidForm"
              @click="onAddConstraint"
            >
              <template #icon><plus-outlined /></template>
              Add Constraint
            </a-button>
            <a-button
              v-else
              type="primary"
              block
              :disabled="invalidForm"
              @click="onUpdateConstraint"
            >
              <template #icon><edit-outlined /></template>
              Update Constraint
            </a-button>
          </a-form>
        </a-card>
      </div>
    </a-col>
  </a-space>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from "vue";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from "@ant-design/icons-vue";
import { useObject } from "../composables/ObjectID";
import { displayNotification, NotificationType } from '@/utils/notification';
import ProfileEditForm from "@/components/forms/ProfileEditForm.vue";

const { currentObjectID } = useObject();

const props = defineProps({
  esId: {
    type: String,
    default: ""
  },
  objectId: {
    type: String,
    default: ""
  },
  embeddedView: {
    type: Boolean,
    default: false
  }
});

// ENUM
const SegmentOptions = Object.freeze({
  CONSTRAINTS: "Constraints",
  ADD_CONSTRAINT: "Add Constraint",
});

const ConstraintType = Object.freeze({
  PROFILE: "ProfileConstraint",
  RANGED: "RangedConstraint",
  PIPEDIAMETER: "PipeDiameterConstraint"
});

const ProfileTag = Object.freeze({
  MAX: "Maximum",
  MIN: "Minimum",
});


// State
const activeEsdlId = ref(null);
const assetId = ref(null);

const attributeReferenceOptions = ref([]);
const availableConstraintTypes = ref([]);

const activeSegment = ref(SegmentOptions.CONSTRAINTS);

const profileModalVisible = ref(false);
const activeProfileTag = ref(null);
const activeProfile = ref(null);

const currentConstraint = ref(null);

// This controls which fields are disabled in the form based on the backend response.
const disabledFields = ref([]);

const initProfileConstraintForm = {
  id: null,
  name: "New Profile Constraint",
  description: "",
  attributeReference: "",
  type: ConstraintType.PROFILE,
  maximum: null,
  minimum: null,
};

const initRangedConstraintForm = {
  id: null,
  name: "New Ranged Constraint",
  description: "",
  attributeReference: "",
  type: ConstraintType.RANGED,
  range: {
    id: null,
    name: "New Range",
    min_value: null,
    mid_value: null,
    max_value: null,
  },
};

const initPipeDiameterConstraintForm = {
  id: null,
  name: "New PipeDiameterConstraint",
  description: "",
  attributeReference: "",
  type: ConstraintType.PIPEDIAMETER,
  maximum: null,
  minimum: null,
};

const constraintTypeColor = {
  [ConstraintType.PROFILE]: "blue",
  [ConstraintType.RANGED]: "green",
  [ConstraintType.PIPEDIAMETER]: "orange",
};

// Form state (default to Profile Constraint)
const formData = reactive({ ...initProfileConstraintForm });

const constraints = ref([]);

// Table configuration
const columns = [
  {
    title: "Name",
    dataIndex: "name",
    key: "name",
    width: "30%",
  },
  {
    title: "Value",
    key: "value",
  },
  {
    title: "Actions",
    key: "action",
    width: 70,
    align: "right",
  },
];

onMounted(() => {
  console.debug("Asset Constraint component mounted");

  activeEsdlId.value = props.esId || currentObjectID.value?.["es_id"];
  assetId.value = props.objectId || currentObjectID.value?.["object_id"];

  if (!activeEsdlId.value || !assetId.value) {
    console.error("Asset Constraint: esId or objectId is undefined or null.");
    displayNotification(NotificationType.ERROR, "Unable to load asset constraints: asset or energy system ID is missing.");
    return;
  }

  getAssetConstraint(activeEsdlId.value, assetId.value);
});

onUnmounted(() => {
  activeEsdlId.value = null;
  assetId.value = null;

  console.debug("Asset Constraint component unmounted");
});

const segmentedOptions = computed(() => [
  { value: SegmentOptions.CONSTRAINTS, label: SegmentOptions.CONSTRAINTS },
  { value: SegmentOptions.ADD_CONSTRAINT, label: currentConstraint.value ? "Update Constraint" : SegmentOptions.ADD_CONSTRAINT },
]);

const invalidForm = computed(() => {
  return (
    formData.name === "" ||
    (formData.type === ConstraintType.RANGED && formData.range.name === "")
  );
});

const getNewEmptyConstraint = async (constraintType) => {
  try {
    const response = await fetch(`/asset_constraint/${constraintType}`);
    return await response.json();
  } catch (error) {
    console.error(error);
  }
}

const isFieldDisabled = (fieldName) => {
  return disabledFields.value.includes(fieldName);
};

const getAssetConstraint = async (esId, assetId) => {
  try {
    const response = await fetch(`/asset_constraint/${esId}/${assetId}`);
    if (response.status !== 200) {
      const result = await response.text();
      console.error(response.status, result);
      displayNotification(NotificationType.ERROR, "An error occurred when loading the asset constraints.");
      return;
    }
    const data = await response.json();
    constraints.value = [...data.constraints];

    // Update UI state based on the backend response

    availableConstraintTypes.value = data.available_constraint_types;
    // Default form to first available constraint type
    if (availableConstraintTypes.value.length > 0 && !currentConstraint.value) {
      formData.type = availableConstraintTypes.value[0];
      await resetForm();
    }
    attributeReferenceOptions.value = data.available_attribute_references.map(
      (attr) => ({ value: attr, label: attr })
    );
    if (attributeReferenceOptions.value.length === 1) {
      formData.attributeReference = attributeReferenceOptions.value[0].value;
    }
    disabledFields.value = data.disabled_fields || [];

    if (data.notification) {
      displayNotification(NotificationType.WARNING, data.notification);
    }
  } catch (error) {
    console.error(error);
    displayNotification(NotificationType.ERROR, "An error occurred when loading the asset constraints.");
  }
};

const setAssetConstraint = async (esId, assetId, constraints) => {
  try {
    const response = await fetch(`/asset_constraint/${esId}/${assetId}`, {
      method: "POST",
      body: JSON.stringify(constraints),
      headers: { "Content-type": "application/json; charset=UTF-8" },
    });

    if (response.status !== 200) {
      const result = await response.text();
      console.error(response.status, result);
      displayNotification(NotificationType.ERROR, "An error occurred when adding or updating the asset constraint. Your changes will not be saved.");
      return;
    }

    getAssetConstraint(esId, assetId);
  } catch (error) {
    console.error(error);
    displayNotification(NotificationType.ERROR, "An error occurred when adding or updating the asset constraint. Your changes will not be saved.");
  }
};

const resetForm = async () => {
  let newForm = {};
  if (formData.type === ConstraintType.RANGED) {
    // Deep clone since initRangedConstraintForm is a nested object.
    newForm = JSON.parse(JSON.stringify(initRangedConstraintForm));
  } else if (formData.type === ConstraintType.PROFILE) {
    newForm = initProfileConstraintForm;
  } else if (formData.type === ConstraintType.PIPEDIAMETER) {
    // TODO: make below applicable for other constraints
    // Retrieve esdl attributes and references from backend
    const emptyConstraint = await getNewEmptyConstraint(formData.type);
    // Extract attribute and its value from the defined set of attributes
    Object.keys(initPipeDiameterConstraintForm).forEach((field) => {
      const attribute = emptyConstraint["attrs"].find((attr) => attr["name"] === field);
      if (attribute) {
        // A new ESDL object has null for unset attributes; keep the initial default then.
        newForm[field] = attribute["value"] ?? initPipeDiameterConstraintForm[field];

        if (attribute["type"] === "EEnum") {
          if (!Object.hasOwn(newForm, "EEnum")) {
            newForm["EEnum"] = {};
          }
          newForm["EEnum"] = {
            ...newForm["EEnum"],
            [field]: attribute["options"]
          };
        }
      } else {
        newForm[field] = initPipeDiameterConstraintForm[field];
      }
    })
  } else {
    console.error("Unsupported constraint type.");
  }

  // Clear all existing keys
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });

  Object.assign(formData, {...newForm});

  if (attributeReferenceOptions.value.length === 1) {
    formData.attributeReference = attributeReferenceOptions.value[0].value;
  }
};

const onSelectConstraintType = () => {
  resetForm();
};

const onSelectSegment = () => {
  // On 'Add' constraint mode
  if (
    activeSegment.value === SegmentOptions.ADD_CONSTRAINT &&
    currentConstraint.value === null
  ) {
    resetForm();
  }
  if (
    activeSegment.value === SegmentOptions.CONSTRAINTS &&
    currentConstraint.value !== null
  ) {
    currentConstraint.value = null;
    resetForm();
  }
};

const openProfileModal = (profileTag) => {
  if (profileTag === ProfileTag.MAX) {
    activeProfile.value = formData.maximum ? {...formData.maximum} : null;
    activeProfileTag.value = ProfileTag.MAX;
  }
  if (profileTag === ProfileTag.MIN) {
    activeProfile.value = formData.minimum ? {...formData.minimum} : null;
    activeProfileTag.value = ProfileTag.MIN;
  }
  profileModalVisible.value = true;
};

const closeProfileModal = () => {
  activeProfileTag.value = null;
  activeProfile.value = null;
  profileModalVisible.value = false;
};

const onSaveProfileFormData = (profileFormData) => {
  // Retrieve profileInfo emitted from the stateful form inputs.
  const profileInfo = {...profileFormData.profileInfo};

  if (profileFormData.tag === ProfileTag.MAX) {
    formData.maximum = {
      profileClass: profileInfo.profileClass,
      profileObj: profileInfo.profileObj
    };
  }
  if (profileFormData.tag === ProfileTag.MIN) {
    formData.minimum = {
      profileClass: profileInfo.profileClass,
      profileObj: profileInfo.profileObj
    };
  }
  closeProfileModal();
};

const onCancelProfileFormData = () => {
  closeProfileModal();
};

const onEditConstraintMinMax = (profileTag) => {
  openProfileModal(profileTag);
};

const onDeleteConstraintMinMax = (profileTag) => {
  if (profileTag === ProfileTag.MAX) {
    formData.maximum = null;
  }
  if (profileTag === ProfileTag.MIN) {
    formData.minimum = null;
  }
};

const constructProfileDisplayedName = (profileObj) => {
  const qau = profileObj.profileQuantityAndUnit.description;
  let displayedName = ``;
  if (profileObj.name) {
    displayedName = `${profileObj.name} [${qau}]`;
  } else {
    displayedName = `${profileObj.columnName} [${qau}]`;
  }
  return displayedName;
}

// Returns the assigned values of a constraint as [{ label, text }] for the table's Value column.
const getConstraintValues = (record) => {
  const items = [];
  const hasValue = (v) => v !== null && v !== undefined && v !== "";

  if (record.type === ConstraintType.RANGED) {
    const range = record.range ?? {};
    const text = [
      ["minValue", range.min_value],
      ["midValue", range.mid_value],
      ["maxValue", range.max_value],
    ]
      .filter(([, v]) => hasValue(v))
      .map(([label, v]) => `${label}: ${v}`)
      .join(" · ");
    if (text) {
      items.push({ label: "range", text });
    }
  } else {
    for (const field of ["maximum", "minimum"]) {
      const v = record[field];
      if (!hasValue(v)) continue;
      const text = record.type === ConstraintType.PROFILE
        ? constructProfileDisplayedName(v.profileObj)
        : v;
      items.push({ label: field, text });
    }
  }
  return items;
};

const onAddConstraint = async () => {
  constraints.value.push({ ...formData });
  await setAssetConstraint(
    activeEsdlId.value,
    assetId.value,
    constraints.value,
  );

  currentConstraint.value = null;
  await resetForm();
  activeSegment.value = SegmentOptions.CONSTRAINTS;
};

const onEditConstraint = async (constraint) => {
  // Switch to add constraint segment
  activeSegment.value = SegmentOptions.ADD_CONSTRAINT;
  currentConstraint.value = constraint;

  // Reset to ensure formData structure matches the corresponding ConstraintType
  await resetForm();

  Object.assign(formData, { ...constraint });
};

const onUpdateConstraint = async () => {
  if (!currentConstraint.value) return;

  const index = constraints.value.findIndex(
    (c) => c.id === currentConstraint.value.id,
  );
  if (index !== -1) {
    constraints.value[index] = { ...formData };
  }

  await setAssetConstraint(
    activeEsdlId.value,
    assetId.value,
    constraints.value,
  );

  currentConstraint.value = null;
  await resetForm();
  activeSegment.value = SegmentOptions.CONSTRAINTS;
};

const onDeleteConstraint = async (id) => {
  constraints.value = constraints.value.filter((c) => c.id !== id);
  await setAssetConstraint(
    activeEsdlId.value,
    assetId.value,
    constraints.value,
  );

  currentConstraint.value = null;
};
</script>

<style scoped>
.asset-constraint-menu {
  width: 400px;
  height: 100vh;
  border-right: 1px solid #e8e8e8;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
}

.constraint-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.ant-tabs-content) {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

:deep(.ant-segmented-item),
:deep(.ant-segmented-item::selection) {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.constraints-table {
  height: 100%;
}

.cell-ellipsis {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.value-label {
  color: #8c8c8c;
}

.type-tag {
  display: block;
  width: fit-content;
  max-width: 100%;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.action-buttons-vertical {
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}
</style>
