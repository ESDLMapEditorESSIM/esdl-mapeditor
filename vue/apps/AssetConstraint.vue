<template>
  <a-space
    id="asset-constraint"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%"
  >
    <!-- Header -->
    <a-row>
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
        :options="Object.values(SegmentOptions)"
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
            :scroll="{ y: 'calc(100vh - 180px)' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'type'">
                <a-tag color="blue">
                  {{ record.type }}
                </a-tag>
              </template>

              <template v-if="column.key === 'action'">
                <div class="action-buttons">
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
                  Object.entries(ConstraintType).map(([_, label]) => ({
                    value: label,
                    label: label,
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
            <a-form-item label="Name" required>
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
                    <p
                      v-if="
                        formData.maximum.displayed_name &&
                          formData.maximum.qau_description
                      "
                    >
                      {{
                        `${formData.maximum.displayed_name} [${formData.maximum.qau_description}]`
                      }}
                    </p>
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
                  @click="openProfileModal(ProfileTag.MAX)"
                >
                  Add maximum
                </a-button>
              </a-form-item>
              <a-form-item label="Minimum">
                <a-row v-if="formData.minimum !== null">
                  <a-col :span="20">
                    <p
                      v-if="
                        formData.minimum.displayed_name &&
                          formData.minimum.qau_description
                      "
                    >
                      {{
                        `${formData.minimum.displayed_name} [${formData.minimum.qau_description}]`
                      }}
                    </p>
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
                  @click="openProfileModal(ProfileTag.MIN)"
                >
                  Add minimum
                </a-button>
              </a-form-item>
              <ProfileFormEdit
                :visible="profileModalVisible"
                :profile-tag="activeProfileTag"
                :profile-info="activeProfile"
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
              <a-form-item label="Name" required>
                <a-input v-model:value="formData.range.name" />
              </a-form-item>
              <a-row>
                <a-space direction="horizontal" style="width: 100%">
                  <a-form-item label="Minimum">
                    <a-input-number
                      v-model:value="formData.range.min_value"
                      style="width: 100%"
                      :step="0.1"
                    />
                  </a-form-item>
                  <a-form-item label="Mid-value">
                    <a-input-number
                      v-model:value="formData.range.mid_value"
                      style="width: 100%"
                      :step="0.1"
                    />
                  </a-form-item>
                  <a-form-item label="Maximum">
                    <a-input-number
                      v-model:value="formData.range.max_value"
                      style="width: 100%"
                      :step="0.1"
                    />
                  </a-form-item>
                </a-space>
              </a-row>
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
import { notification } from "ant-design-vue";
import { v4 as uuidv4 } from "uuid";
import ProfileFormEdit from "@/components/forms/ProfileFormEdit.vue";
import { useObject } from "../composables/ObjectID";
import { useEsdlLayers } from "../composables/esdlLayers";

const { currentObjectID } = useObject();
const { getActiveEsdlLayerId } = useEsdlLayers();

// ENUM
const SegmentOptions = Object.freeze({
  CONSTRAINTS: "Constraints",
  ADD_CONSTRAINT: "Add Constraint",
});

const ConstraintType = Object.freeze({
  PROFILE: "Profile constraint",
  RANGED: "Ranged constraint",
});

const ProfileTag = Object.freeze({
  MAX: "Maximum",
  MIN: "Minimum",
});

// Default to support power; can be extended or made dynamic in the future.
const attributeReferenceOptions = [
    { value: "power", label: "power" },
    { value: "capacity", label: "capacity" },
    { value: "volume", label: "volume" },
    { value: "aggregationCount", label: "aggregationCount" }
];

// State
const activeEsdlId = ref(getActiveEsdlLayerId().value);
const assetId = ref(currentObjectID.value);

const activeSegment = ref(SegmentOptions.CONSTRAINTS);

const profileModalVisible = ref(false);
const activeProfileTag = ref(null);
const activeProfile = ref(null);

const currentConstraint = ref(null);

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

// Form state (default to Profile Constraint)
const formData = reactive({ ...initProfileConstraintForm });

const constraints = ref([]);

// Table configuration
const columns = [
  {
    title: "Name",
    dataIndex: "name",
    key: "name",
  },
  {
    title: "Type",
    key: "type",
  },
  {
    title: "Actions",
    key: "action",
    width: 100,
    align: "right",
  },
];

onMounted(() => {
  console.debug("Asset Constraint component mounted");

  activeEsdlId.value = getActiveEsdlLayerId().value;
  assetId.value = currentObjectID.value;

  getAssetConstraint(activeEsdlId.value, assetId.value);
});

onUnmounted(() => {
  console.debug("Asset Constraint component unmounted");
});

const invalidForm = computed(() => {
  return (
    formData.name === "" ||
    (formData.type === ConstraintType.RANGED && formData.range.name === "")
  );
});

const getAssetConstraint = async (esId, assetId) => {
  try {
    const response = await fetch(`/asset_constraint/${esId}/${assetId}`);
    const assetConstraints = await response.json();
    constraints.value = [...assetConstraints];
  } catch (error) {
    console.error(error);
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
      notification["error"]({
        message: "Error",
        description:
          "An error occurred when adding or updating the asset constraint. Your changes will not be saved.",
        placement: "bottomRight",
        duration: 8,
      });
    }

    getAssetConstraint(esId, assetId);
  } catch (error) {
    console.error(error);
  }
};

const resetForm = () => {
  // Deep clone since initRangedConstraintForm is a nested object.
  const newForm = JSON.parse(
    JSON.stringify(
      formData.type === ConstraintType.RANGED
        ? initRangedConstraintForm
        : initProfileConstraintForm,
    ),
  );

  newForm.id = uuidv4();
  if (formData.type === ConstraintType.RANGED) {
    newForm.range.id = uuidv4();
  }

  // Clear all existing keys
  Object.keys(formData).forEach((key) => {
    delete formData[key];
  });

  Object.assign(formData, newForm);
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
    activeProfile.value = formData.maximum;
    activeProfileTag.value = ProfileTag.MAX;
  }
  if (profileTag === ProfileTag.MIN) {
    activeProfile.value = formData.minimum;
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
  if (profileFormData.tag === ProfileTag.MAX) {
    formData.maximum = profileFormData.data;
  }
  if (profileFormData.tag === ProfileTag.MIN) {
    formData.minimum = profileFormData.data;
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

const onAddConstraint = async () => {
  constraints.value.push({ ...formData });
  await setAssetConstraint(
    activeEsdlId.value,
    assetId.value,
    constraints.value,
  );

  currentConstraint.value = null;
  resetForm();
  activeSegment.value = SegmentOptions.CONSTRAINTS;
};

const onEditConstraint = (constraint) => {
  // Switch to add constraint segment
  activeSegment.value = SegmentOptions.ADD_CONSTRAINT;
  currentConstraint.value = constraint;

  // Reset to ensure formData structure matches the corresponding ConstraintType
  resetForm();

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
  resetForm();
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

::v-deep(.ant-segmented-item, .ant-segmented-item::selection) {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.constraints-table {
  height: 100%;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
