<template>
  <h1>Activity Contexts</h1>
  <div v-if="addMode">
    <a-space direction="vertical">
      <a-input v-model:value="newActivityContextID" type="text" placeholder="ID" />
      <a-input v-model:value="newActivityContextName" type="text" placeholder="Name" />
      <a-textarea v-model:value="newWmsLayers" :rows="4" placeholder="WMS layers (comma-separated)" />
      <a-space direction="horizontal">
        <a-button type="primary" @click="saveActivityContext">
          Save
        </a-button>
        <a-button type="dashed" @click="cancelAddActivityContext">
          Cancel
        </a-button>
      </a-space>
    </a-space>
  </div>
  <a-button v-else type="primary" @click="addActivityContext">Add</a-button>
  <a-table :columns="columns" :data-source="activityContexts" size="middle" style="width: 100%">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'wms_layers'">
        <a-space direction="vertical">
          <a v-for="layer in record.wms_layers" :key="layer">{{ layer }}</a>
        </a-space>
      </template>
      <template v-else-if="column.key === 'actions'">
        <a-button @click="deleteActivityContext(record.activity_id)">Delete</a-button>
      </template>
    </template>
  </a-table>
</template>

<script setup>
import {ref} from "vue";

const addMode = ref(false);
const activityContexts = ref([]);
const newActivityContextID = ref('');
const newActivityContextName = ref('');
const newWmsLayers = ref('');

const get_activity_contexts = async (asset_type) => {
  const response = await fetch('/context/activities')
  activityContexts.value = await response.json()
  console.log('Activity contexts', activityContexts.value)
}
get_activity_contexts();

const columns = [
  {
    title: 'Activity ID',
    dataIndex: 'activity_id',
    key: 'activity_id',
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'WMS Layers',
    dataIndex: 'wms_layers',
    key: 'wms_layers',
  },
  {
    title: 'Actions',
    key: 'actions',
  }
]

const deleteActivityContext = async (id) => {
  console.log('Delete activity context', id)
  const response = await fetch('/context/activities/' + id, {
    method: 'DELETE'
  })
  if (!response.ok) {
    console.error('Error deleting activity context', response)
    alert('Error deleting activity context')
    return
  }
  await get_activity_contexts();
}

const saveActivityContext = async () => {
  console.log('Save activity context', newActivityContextName.value)
  const wmsLayers = newWmsLayers.value.split(",")
  const response = await fetch('/context/activities', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({activity_id: newActivityContextID.value, name: newActivityContextName.value, wms_layers: wmsLayers, context_services: []})
  })
  if (!response.ok) {
    console.error('Error saving activity context', response)
    alert('Error saving activity context')
    return
  }
  addMode.value = false;
  newActivityContextID.value = '';
  newActivityContextName.value = '';
  newWmsLayers.value = '';
  await get_activity_contexts();
}

const addActivityContext = () => {
  console.log('Add activity context')
  addMode.value = true;
}

const cancelAddActivityContext = () => {
  addMode.value = false;
}
</script>