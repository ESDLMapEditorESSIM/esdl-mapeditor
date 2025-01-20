<template>
  <a-row class="dialog-header">
    <h2 style="font-weight: bold; font-size: 2rem">Ownership</h2>
    <a-button
      type="primary"
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
      @ok="addNewParty"
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
  <a-row style="padding-left: 24px;">
    <a-typography-text>
      {{ displayedText }}
    </a-typography-text>
  </a-row>
  <a-row class="dialog-content">
    <a-collapse
      v-if="parties.length"
      v-model:activeKey="activeKey"
      style="width: 95%"
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
            style="margin-top: 16px;"
            @click="deleteParty"
          >
            {{ `Remove ${party.name}` }}
          </a-button>
        </a-row>
      </a-collapse-panel>
    </a-collapse>
  </a-row>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { notification } from 'ant-design-vue';

const displayedText = ref('');

// Control which collapse panel is opened.
// The value contains a list of one collapse panel key (which is defined as party.id)
const activeKey = ref(null);

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

onMounted(async () => {
  console.debug("Initializing Ownership Dialog");
  initOwnershipState();
});

/**
 * Displays a notification with the specified level and description.
 * 
 * @param {string} level The level of the notification ("info", "warning", "error").
 * @param {string} description The description text of the notification.
 */
 const displayNotification = (level, description) => {
  notification[level.toLowerCase()]({
    message: level.toUpperCase(),
    description: description,
    placement: "bottomRight",
    duration: 8
  });
};

const resetForm = () => {
  newParty.value = {...initNewParty};
};

const onModalClose = () => {
  resetForm();
  openNewPartyModal.value = false;
};

const addNewParty = async () => {
  try {
    const url = "/ownership/parties";
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
    initOwnershipState();
  } catch (error) {
    console.error(error);
    displayNotification("Error", "Something went wrong when creating a new party.");
  } finally {
    onModalClose();
  }
};

const deleteParty = async () => {
  const activePartyId = activeKey.value;
  try {
    const url = `/ownership/parties/${activePartyId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.status === 204) {
      displayNotification("Success", "Successfully removed the party.");
      initOwnershipState();
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

const getPartiesList = async () => {
  try {
    const response = await fetch("/ownership/parties");
    const data = await response.json();
    return data.parties;
  } catch (error) {
    console.error(error);
    displayNotification(
      "error", 
      "Something went wrong when retrieving the party list from the ESDL."
    );
  }
};

const getAssetsList = async () => {
  try {
    const response = await fetch("/ownership/assets");
    const data = await response.json();
    return data.assets;
  } catch (error) {
    console.error(error);
    displayNotification(
      "error", 
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

const initOwnershipState = async () => {
  parties.value = await getPartiesList();
  assets.value = await getAssetsList();
  ownershipState.value = updateOwnershipState(parties.value, assets.value);
  
  if (parties.value.length) {
    displayedText.value = 'Open the accordion below to assign or revoke asset ownership.';
  } else {
    displayedText.value = 'The ESDL has no ownership party defined yet.';
  }
};

const renderTransferListItem = (item) => {
  let text = `${item.title}`;
  if (item.disabled && item.description) {
    text += ` (Owned by ${item.description})`;
  }
  return text;
};

const onChange = async (targetKeys, direction, moveKeys) => {
  const activePartyId = activeKey.value;
  let assignment = {
    'assigned_asset_ids': [],
    'revoked_asset_ids': [],
  };
  if (direction === 'right') {
    assignment.assigned_asset_ids = targetKeys;
  } else if (direction === 'left') {
    assignment.revoked_asset_ids = moveKeys;
  }
  postOwnershipAssignment(activePartyId, assignment);
};

const postOwnershipAssignment = async (partyId, assignment) => {
  try {
    const url = `/ownership/assignment/${partyId}`;
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
    initOwnershipState();
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

.dialog-content {
  height: calc(100% - 60px);
  justify-content: space-around;
  align-items: flex-start;
  padding-top: 24px;
  padding: 16px;
}

.collapse-panel-content {
  overflow: auto;
}

</style>