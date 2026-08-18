<template>
  <a-space
    id="port-profile-editor"
    direction="vertical"
    style="width: 100%; padding: 8px; height: 100%"
  >
    <!-- Header -->
    <a-row>
      <a-typography-title :level="3">
        <img src="/static/icons/Graph.png" style="width: 24px; height: 24px">
        Port Profile Editor
      </a-typography-title>
    </a-row>

    <!----------------------------------->
    <!------------- Content ------------->
    <!----------------------------------->
    <a-col style="height: 100%">
      <a-segmented
        v-if="portOptions.length"
        v-model:value="activePortId"
        :options="portOptions"
        style="width: 100%"
        block
        @change="onSelectPortSegment"
      />
      <br>
      <div style="width: 100%">
        <a-col v-if="listedPortProfiles.length">
          <a-table
            :data-source="listedPortProfiles"
            :columns="columns"
            :pagination="false"
            size="middle"
            :scroll="{ y: 'calc(100vh - 180px)' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'action'">
                <div class="action-buttons">
                  <a-button
                    type="text"
                    size="small"
                    @click="onEditRecord(record)"
                  >
                    <edit-outlined />
                  </a-button>
                  <!-- TODO: check sometimes need double click -->
                  <a-button
                    type="text"
                    size="small"
                    danger
                    @click="onDeleteRecord(record)"
                  >
                    <delete-outlined />
                  </a-button>
                </div>
              </template>
            </template>
          </a-table>
        </a-col>
        <!-- No profiles defined -->
        <a-col v-else>
          <a-empty
            :description="'No profiles defined'"
            :image-style="{ height: '150px' }"
          />
        </a-col>
        <ProfileEditForm
          :visible="profileModalVisible"
          :active-esdl-id="activeEsdlId"
          :active-profile-container-id="activePortId"
          :profile-tag="activeProfileTag"
          :profile-info="activeProfile"
          @on-save="onSaveProfileFormData"
          @on-cancel="onCancelProfileFormData"
        />
        <a-col
          v-if="activePortId !== null"
          style="display: flex; justify-content: flex-end; margin-top: 16px"
        >
          <a-button type="primary" style="width: 50%" @click="onAddRecord">
            Add profile
          </a-button>
        </a-col>
      </div>
    </a-col>
  </a-space>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { EditOutlined, DeleteOutlined } from "@ant-design/icons-vue";
import { useEsdlLayers } from "@/composables/esdlLayers";
import { useObject } from "../composables/ObjectID";

import { fetchData } from "@/utils/api";
import { displayNotification, NotificationType } from "@/utils/notification";

import ProfileEditForm from "@/components/forms/ProfileEditForm.vue";

const { currentObjectID } = useObject();
const { getActiveEsdlLayerId } = useEsdlLayers();

// ----------------------------------------- //
// ------------ Component states ----------- //
// ----------------------------------------- //

const activeEsdlId = ref(null);
const assetId = ref(null);

const isLoadingData = ref(false);

const portsProfiles = ref([]);
const portOptions = ref([]);
const activePortId = ref(null);

const listedPortProfiles = ref([]);

const profileModalVisible = ref(false);
const activeProfileTag = ref(null);
const activeProfile = ref({});

// ----------------------------------------- //
// ---------- Component constant ----------- //
// ----------------------------------------- //

// Table configuration
const columns = [
  {
    title: "Profile Name",
    key: "profileName",
    customRender: ({ record }) => { return getProfileDisplayedName(record) },
  },
  {
    title: "Unit",
    key: "profileUnit",
    customRender: ({ record }) => { return getProfileUnit(record) },
    width: 100,
  },
  {
    title: "Actions",
    key: "action",
    width: 100,
    align: "right",
  },
];

onMounted(async () => {
  console.debug("Port profile editor component mounted");
  resetState();

  activeEsdlId.value = currentObjectID.value["es_id"] ? currentObjectID.value["es_id"] : getActiveEsdlLayerId().value;
  assetId.value = currentObjectID.value["object_id"] ? currentObjectID.value["object_id"] : null;

  initPortsProfiles();
});

onUnmounted(() => {
  resetState();
  console.debug("Port profile editor component unmounted");
});

// Reset to default state.
const resetState = () => {
  activeEsdlId.value = null;
  assetId.value = null;
};

/**
 * Reset all port-related reactive state.
 */
const resetPortsState = () => {
  portsProfiles.value = [];
  portOptions.value = [];
  activePortId.value = null;
  listedPortProfiles.value = [];
};

/**
 * Initialize asset ports profiles and related UI state.
 */
const initPortsProfiles = async () => {
  const assetPortsProfiles = await fetchAssetPortsProfiles(
    activeEsdlId.value,
    assetId.value
  );

  // No response or failed fetch
  if (!assetPortsProfiles) {
    resetPortsState();
    return;
  }

  const ports = assetPortsProfiles.ports_profiles ?? [];

  // No ports defined
  if (ports.length === 0) {
    displayNotification(
      NotificationType.WARNING,
      `Asset (id=${assetId.value}) has no ports defined.`
    );
    resetPortsState();
    return;
  }

  portsProfiles.value = ports;
  portOptions.value = ports.map((port) => ({
    label: `${port["port_type"]} - ${port["port_name"]}`,
    value: port["port_id"],
  }));

  // Auto-select first port if none selected
  if (activePortId.value === null) {
    activePortId.value = portOptions.value[0].value;
  }

  listedPortProfiles.value = listPortProfiles(activePortId.value);
};

const fetchAssetPortsProfiles = async (esId, assetId) => {
  isLoadingData.value = true;

  try {
    const assetPortsProfilesRequest = {
      es_id: esId,
      asset_id: assetId,
    };
    const assetPortsProfiles = await fetchData("get_asset_ports_profiles", assetPortsProfilesRequest);
    return assetPortsProfiles;
  } catch (e) {
    console.error(e);
    displayNotification(
      NotificationType.ERROR,
      `Failed to retrieve ports and profiles for asset (id=${assetId}). Please verify that the corresponding ESDL is active.`
    );
  } finally {
    isLoadingData.value = false;
  }
};

const listPortProfiles = (activePortId) => {
  let profiles = [];
  if (portsProfiles.value.length) {
    profiles = portsProfiles.value.find(
      (portProfiles) => portProfiles.port_id === activePortId
    )["port_profiles"];
  }
  return profiles;
};

const getProfileDisplayedName = (profileInfo) => {
  if (profileInfo.profileClass === "SingleValue" || profileInfo.profileClass === "TimeSeriesProfile") {
    return profileInfo.profileObj.name || profileInfo.profileObj.id;
  } else {
    return profileInfo.profileObj.columnName || profileInfo.profileObj.name || "Undefined";
  }
}

const getProfileUnit = (profileInfo) => {
  return profileInfo.profileObj.profileQuantityAndUnit?.description || "Undefined";
}


const onSelectPortSegment = (portId) => {
  listedPortProfiles.value = listPortProfiles(portId);
};

// Open modal with default form value
const onAddRecord = () => {
  activeProfile.value = null;
  profileModalVisible.value = true;
};

const onEditRecord = (record) => {
  activeProfile.value = {...record};
  profileModalVisible.value = true;
};

const onDeleteRecord = async (record) => {
  const portId = activePortId.value;
  const profileId = record.profileObj.id;

  // Remove profile from port
  window.remove_profile_from_port(portId, profileId);

  // Reinitialize asset ports profiles
  initPortsProfiles();
};

const onSaveProfileFormData = () => {
  closeProfileModal();

  // Reinitialize asset ports profiles
  initPortsProfiles();
};

const onCancelProfileFormData = () => {
  closeProfileModal();
};

const closeProfileModal = () => {
  activeProfileTag.value = null;
  activeProfile.value = {};
  profileModalVisible.value = false;
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

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
