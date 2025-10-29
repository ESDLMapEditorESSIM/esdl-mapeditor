<template>
  <a-row class="dialog-header">
    <h2 style="font-weight: bold; font-size: 2rem">Ownership</h2>
  </a-row>
  <a-tabs
    v-model:activeKey="activeEsdlId"
    type="card"
    style="padding: 24px;"
    @change="onActiveTabChange"
  >
    <a-tab-pane
      v-for="esdl in esdls"
      :key="esdl.id"
      :tab="esdl.title"
      :disabled="isLoading"
    >
      <!-- Tab pane header row -->
      <a-row style="padding: 12px; display: flex; justify-content: space-between;">
        <a-typography-text>
          {{ displayedText }}
        </a-typography-text>  
        <a-button
          type="primary"
          :disabled="isLoading"
          @click="() => (openNewPartyModal = true)"
        >
          Add new party
        </a-button>
        <a-modal
          title="Add a new ownership party"
          :destroy-on-close="true"
          :open="openNewPartyModal"
          width="750px"
          ok-text="Submit"
          @ok="() => addNewParty(activeEsdlId)"
          @cancel="onModalClose"
        >
          <a-form
            :model="newParty"
            :wrapper-col="{ span: 6 }"
          >
            <a-form-item label="Party name" name="name" :rules="[{ required: true, max: 20 }]">
              <a-input v-model:value="newParty.name" />
            </a-form-item>
            <a-form-item label="Short name" name="short_name" :rules="[{ required: false, max: 20 }]">
              <a-input v-model:value="newParty.short_name" />
            </a-form-item>
          </a-form>
        </a-modal>
      </a-row>
      <!-- Tab pane collapsable transfer component part -->
      <a-row class="tab-content">
        <a-collapse
          v-if="parties.length"
          v-model:activeKey="activeKey"
          style="width: 100%"
          accordion
        >
          <a-collapse-panel
            v-for="party in parties"
            :key="party.id"
            :header="party.name"
            class="collapse-panel-content"
          >
            <a-transfer
              v-model:target-keys="assignedAssetKeys[party.id]"
              :data-source="ownershipState[party.id]"
              show-search
              :list-style="{
                width: '80%',
                height: '300px',
              }"
              :operations="[`Owned by ${party.name}`, 'Unassign']"
              :render="renderTransferListItem"
              @change="onChange"
            >
              <template #notFoundContent>
                <span>No data</span>
              </template>
            </a-transfer>
            <a-row style="justify-content: flex-end;">
              <a-button
                type="primary"
                :disabled="isLoading"
                style="margin-top: 16px;"
                @click="() => deleteParty(activeEsdlId)"
              >
                {{ `Remove ${party.name}` }}
              </a-button>
            </a-row>
          </a-collapse-panel>
        </a-collapse>
      </a-row>
    </a-tab-pane>
  </a-tabs>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { displayNotification } from '@/utils/notification';

const displayedText = ref('');

const esdls = ref([]);

// When a user switches tabs, the state value is updated to the selected ESDL ID.
const activeEsdlId = ref(undefined);

// Control which collapse panel is opened.
// The value contains a list of one collapse panel key (which is defined as party.id)
const activeKey = ref(undefined);

const initNewParty = {
  id: '', // Default to an empty string
  name: '',
  short_name: ''
};
const newParty = ref({...initNewParty});
const openNewPartyModal = ref(false);

const parties = ref([]);
const assets = ref([]);

const ownershipState = ref({});
const assignedAssetKeys = ref({});

const isLoading = ref(false);

onMounted(async () => {
  console.debug("Initializing Ownership Dialog");
  getEsdls();

  const esId = activeEsdlId.value;
  getOwnershipState(esId);
});

/**
 * Get opened ESDLs and update activeEsdlId state with the first ESDL.
 */
 const getEsdls = () => {
  const esIDs = Object.keys(esdl_list);
  if (esIDs.length) {
    activeEsdlId.value = esIDs[0];
  }

  esIDs.forEach((esId) => {
    const title = esdl_list[esId].title;
    esdls.value.push({
      id: esId,
      title: title
    });
  });
};

const onActiveTabChange = (activeEsdlId) => {
  activeKey.value = undefined;
  getOwnershipState(activeEsdlId);
};

const resetForm = () => {
  newParty.value = {...initNewParty};
};

const onModalClose = () => {
  resetForm();
  openNewPartyModal.value = false;
};

const addNewParty = async (esId) => {
  try {
    const url = `/ownership/${esId}/parties`;
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(newParty.value),
      headers: { "Content-type": "application/json; charset=UTF-8" }
    });
    const result = await response.json();

    if (!response.ok) {
      console.error(response.status, result.error);
      displayNotification("Error", `Something went wrong when creating a new party. ${result.error}`);
      return;
    }

    displayNotification("Success", `${result.message}`);
    getOwnershipState(esId);
  } catch (error) {
    console.error(error);
    displayNotification("Error", "Something went wrong when creating a new party.");
  } finally {
    onModalClose();
  }
};

const deleteParty = async (esId) => {
  const activePartyId = activeKey.value;
  try {
    const url = `/ownership/${esId}/parties/${activePartyId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.status === 204) {
      displayNotification("Success", "Successfully removed the party.");
      getOwnershipState(esId);
    } else {
      const result = await response.json();
      console.error(response.status, result.error);
      displayNotification("Error", `Something went wrong when removing the party. ${result.error}`);
    }
  } catch (error) {
    console.error(error);
    displayNotification("Error", "Something went wrong when removing the party.");
  }
};

const getPartiesList = async (esId) => {
  try {
    const response = await fetch(`/ownership/${esId}/parties`);
    const data = await response.json();
    return data.parties;
  } catch (error) {
    console.error(error);
    displayNotification(
      "Error", 
      "Something went wrong when retrieving the party list from the ESDL."
    );
  }
};

const getAssetsList = async (esId) => {
  try {
    const response = await fetch(`/ownership/${esId}/assets`);
    const data = await response.json();
    return data.assets;
  } catch (error) {
    console.error(error);
    displayNotification(
      "Error", 
      "Something went wrong when retrieving the asset list from the ESDL."
    );
  }
};

const updateOwnershipState = (parties, assets) => {
  const ownership = {};
  parties.forEach((p) => {
    const enrichedAssets = assets.map((a) => {
      return {
        ...a,
        // Attributes required by the Transfer component
        key: a.id,
        title: a.name,
        description: a.is_owned_by ? a.is_owned_by.name : null,
        chosen: a.is_owned_by !== null && a.is_owned_by.id === p.id,
        disabled: a.is_owned_by !== null && a.is_owned_by.id !== p.id
      };
    });
    ownership[p.id] = enrichedAssets;

    assignedAssetKeys.value[p.id] = listAssignedAssets(enrichedAssets);
  });
  return ownership;
};

const listAssignedAssets = (assets) => {
  return assets.filter(a => a.chosen === true).map(a => a.key);
};

/**
 * Get ESDL ownership state with the given esId.
 * 
 * @param {string} esId The active energy system ID 
 */
const getOwnershipState = async (esId) => {
  isLoading.value = true;
  parties.value = await getPartiesList(esId);
  assets.value = await getAssetsList(esId);
  ownershipState.value = updateOwnershipState(parties.value, assets.value);
  
  if (parties.value.length) {
    displayedText.value = 'Open the accordion below to assign or revoke asset ownership.';
  } else {
    displayedText.value = 'The ESDL has no ownership party defined yet.';
  }
  isLoading.value = false;
};

const renderTransferListItem = (item) => {
  let text = `${item.title}`;
  if (item.disabled && item.description) {
    text += ` (Owned by ${item.description})`;
  }
  return text;
};

const onChange = async (targetKeys, direction, moveKeys) => {
  let assignment = {
    'assigned_asset_ids': [],
    'revoked_asset_ids': [],
  };
  if (direction === 'right') {
    assignment.assigned_asset_ids = targetKeys;
  } else if (direction === 'left') {
    assignment.revoked_asset_ids = moveKeys;
  }

  const esId = activeEsdlId.value;
  const activePartyId = activeKey.value;
  postOwnershipAssignment(esId, activePartyId, assignment);
};

const postOwnershipAssignment = async (esId, partyId, assignment) => {
  try {
    isLoading.value = true;
    const url = `/ownership/${esId}/assignment/${partyId}`;
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(assignment),
      headers: { "Content-type": "application/json; charset=UTF-8" }
    });
    const result = await response.json();

    if (response.status === 200) {
      displayNotification("Success", `${result.message}`);
    } else {
      console.error(response.status, result.error);
      displayNotification("Error", "Something went wrong when assigning ownership.");
    }    
  } catch (error) {
    console.error(error);
    displayNotification("Error", "Something went wrong when assigning ownership.");
  } finally {
    getOwnershipState(esId);
    isLoading.value = false;
  }
};

</script>

<style scoped>

.dialog-header {
  height: 60px;
  padding-left: 24px;
  padding-right: 24px;
  justify-content: space-between;
  align-items: center;
}

.tab-content {
  justify-content: space-around;
  align-items: flex-start;
  padding-top: 16px;
}

.collapse-panel-content {
  overflow: auto;
}

</style>