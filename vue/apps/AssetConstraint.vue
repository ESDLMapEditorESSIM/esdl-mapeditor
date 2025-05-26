<template>
  <a-space
    id="asset-constraint"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%;"
  >
    <!-- Header -->
    <a-row>
      <a-typography-title :level="3">
        <!-- TODO: replace with chain logo -->
        <i class="fa fa-compress" />
        Asset Constraint
      </a-typography-title>
    </a-row>

    <!----------------------------------->
    <!------------- Content ------------->
    <!----------------------------------->
    <a-col style="height: 100%;">
      <a-segmented
        v-model:value="activeSegment"
        :options="Object.values(SegmentOptions)"
        style="width: 100%;"
        block
        @change="onSelectSegment"
      />
      <br>
      <!------------- CONSTRAINTS ------------->
      <div v-if="activeSegment === SegmentOptions.CONSTRAINTS" style="width: 100%;">
        <!-- TODO: fix UI -->
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
                  <a-button type="text" size="small" @click="onEditConstraint(record)">
                    <edit-outlined />
                  </a-button>
                  <a-button type="text" size="small" danger @click="onDeleteConstraint(record.id)">
                    <delete-outlined />
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>
        </a-col>

        <!-- Empty state: no constraints -->
        <a-col v-else>
          <a-empty :description="'No constraints defined'" :image-style="{ height: '150px'}" />
        </a-col>
      </div>

      <!------------- ADD_CONSTRAINT ------------->
      <div v-if="activeSegment === SegmentOptions.ADD_CONSTRAINT" style="width: 100%;">
        <!-- TODO: make it a child component -->
        <a-card>
          <a-form layout="vertical">
            <a-form-item label="ID">
              <a-input v-model:value="formData.id" disabled />
            </a-form-item>

            <a-form-item label="Name" required>
              <a-input v-model:value="formData.name" placeholder="Constraint name" />
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
                :options="[ { 
                  value: 'power', 
                  label: 'power' 
                } ]"
                allow-clear
              />
            </a-form-item>

            <a-form-item label="Maximum">
              <a-row v-if="formData.maximum !== null">
                <a-col :span="20">
                  <p v-if="formData.maximum.uiname && formData.maximum.type">
                    {{ `${formData.maximum.uiname || formData.maximum.uiname.label} [${formData.maximum.type || formData.maximum.type.label}]` }}
                  </p>
                </a-col>
                <a-col :span="4">
                  <div class="action-buttons">
                    <a-button type="text" size="small">
                      <edit-outlined @click="onEditConstraintMinMax" />
                    </a-button>
                    <a-button type="text" size="small" danger @click="onDeleteConstraintMinMax">
                      <delete-outlined />
                    </a-button>
                  </div>
                </a-col>
              </a-row>
              <a-button v-else block @click="openProfileModal">Add maximum</a-button>
              <!-- TODO: now fix it to InfluxDB profile-->
              <ProfileFormEdit
                :visible="profileModalVisible"
                :profile-info="formData.maximum"
                @on-save="onSaveProfileFormData"
                @on-cancel="onCancelProfileFormData"
              />
            </a-form-item>
              
            <a-button
              v-if="currentConstraint === null"
              type="primary"
              block
              @click="onAddConstraint"
            >
              <template #icon><plus-outlined /></template>
              Add Constraint
            </a-button>
            <a-button
              v-else
              type="primary"
              block
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
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';
import { v4 as uuidv4 } from 'uuid';
import ProfileFormEdit from '@/components/forms/ProfileFormEdit.vue';
import { useObject } from '../composables/ObjectID'

const { currentObjectID } = useObject();

// ENUM
const SegmentOptions = Object.freeze({
	CONSTRAINTS: "Constraints",
	ADD_CONSTRAINT: "Add Constraint"
});

const ConstraintType = Object.freeze({
  PROFILE: "Profile constraint",
});

// State
const assetId = ref(currentObjectID.value);

const activeSegment = ref(SegmentOptions.CONSTRAINTS);
const profileModalVisible = ref(false);

const currentConstraint = ref(null);

const initConstraintForm = {
  id: '',
  name: '',
  description: '',
  attributeReference: '',
  maximum: null
};

onMounted(() => {
  console.debug('Asset Constraint component mounted');

  assetId.value = currentObjectID.value;
  getAssetConstraint(assetId.value);
});

onUnmounted(() => {
  console.debug('Asset Constraint component unmounted');
});

// Form state
const formData = reactive({ ...initConstraintForm });

const constraints = ref([]);

// Table configuration
const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'Type',
    key: 'type',
  },
  {
    title: 'Actions',
    key: 'action',
    width: 100,
    align: 'right'
  }
];

// Methods
const getAssetConstraint = (assetId) => {
  console.debug("Fetching asset constraint");
  window.socket.emit('command', {'cmd': 'get_asset_constraint', 'asset_id': assetId}, (res) => {
    // Append or update asset.constraints to constraints state in UI
    if (res && res.constraint.length) {
      constraints.value = [...res.constraint];
      // res.constraint.forEach((aConstraint) => {
      //   const index = constraints.value.findIndex(c => c.id === aConstraint.id);
      //   // Update
      //   if (index !== -1) {
      //     constraints.value[index] = { ...aConstraint };
      //   }
      //   // Append 
      //   else {
      //     constraints.value.push({...aConstraint});
      //   }
      // })
      console.debug(constraints.value);
    }
  });
}

const setAssetConstraint = (assetId, constraints) => {
  window.socket.emit('command', {'cmd': 'set_asset_constraint', 'asset_id': assetId, 'constraint': constraints}, (res) => {
    console.debug(res);
    if (res['res'] === 'success') {
      getAssetConstraint(assetId);
    }
  });
}

const onSelectSegment = () => {
	if (activeSegment.value === SegmentOptions.ADD_CONSTRAINT) {
    // On Add constraint mode
    if (currentConstraint.value === null) {
      resetForm();
      formData.id = uuidv4();
    } else {
      // TODO: On edit mode
    }
  }
  if (activeSegment.value === SegmentOptions.CONSTRAINTS) {
    if (currentConstraint.value !== null) {
      currentConstraint.value = null;
      resetForm();
    }
  }
};

const openProfileModal = () => {
	profileModalVisible.value = true;
}

const closeProfileModal = () => {
  profileModalVisible.value = false;
}

const onSaveProfileFormData = (profileFormObj) => {
  formData.maximum = { 
    ...profileFormObj,
    type: profileFormObj.type.label,
    uiname: profileFormObj.uiname.label
   };
  closeProfileModal();
}

const onCancelProfileFormData = () => {
  closeProfileModal();
}

const onEditConstraintMinMax = () => {
  openProfileModal();
}

const onDeleteConstraintMinMax = () => {
  formData.maximum = null;
}

const resetForm = () => {
  Object.assign(formData, { ...initConstraintForm });
}

const onAddConstraint = () => {
  const newConstraint = {
    id: formData.id,
    name: formData.name,
    type: ConstraintType.PROFILE,
    description: formData.description,
    attributeReference: formData.attributeReference,
    maximum: formData.maximum
  };
  
  constraints.value.push(newConstraint);

  setAssetConstraint(assetId.value, constraints.value)

  currentConstraint.value = null;
  resetForm();
  
  // Switch to constraints segment
  activeSegment.value = SegmentOptions.CONSTRAINTS;
};

const onEditConstraint = (constraint) => {
  // Switch to add constraint segment
  activeSegment.value = SegmentOptions.ADD_CONSTRAINT;

  currentConstraint.value = constraint;
  
  // Populate form data
  formData.id = constraint.id;
  formData.name = constraint.name;
  formData.description = constraint.description;
  formData.attributeReference = constraint.attributeReference;
  formData.maximum = constraint.maximum;
};

const onUpdateConstraint = () => {
  if (!currentConstraint.value) return;
  
  const index = constraints.value.findIndex(c => c.id === currentConstraint.value.id);
  if (index !== -1) {
    constraints.value[index] = {
      ...constraints.value[index],
      name: formData.name,
      description: formData.description,
      attributeReference: formData.attributeReference,
      maximum: formData.maximum
    };
  }

  setAssetConstraint(assetId.value, constraints.value)

  currentConstraint.value = null;
  resetForm();
  
  // Switch to constraints segment
  activeSegment.value = SegmentOptions.CONSTRAINTS;
};

const onDeleteConstraint = (id) => {
  constraints.value = constraints.value.filter(c => c.id !== id);

  setAssetConstraint(assetId.value, constraints.value)

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

.constraints-table {
  height: 100%;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>