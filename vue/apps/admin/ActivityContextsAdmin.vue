<template>
  <h1>Activity Contexts</h1>
  <div v-if="addMode">
    <a-space direction="vertical">
      <a-input v-model:value="newActivityContextID" type="text" placeholder="ID" />
      <a-input v-model:value="newActivityContextName" type="text" placeholder="Name" />
      <a-textarea v-model:value="newApplicationIds" :rows="2" placeholder="Application IDs (comma-separated)" />
      <a-textarea v-model:value="newWmsLayers" :rows="4" placeholder="WMS layers (comma-separated)" />
      <a-textarea v-model:value="newDisableEsdlLayers" :rows="4" placeholder="Disable ESDL layers (comma-separated)" />
      <a-input v-model:value="newWorkflow" type="text" placeholder="Workflow" />
      <a-input v-model:value="newJsFunction" type="text" placeholder="JS function" />
      <a-checkbox v-model:checked="newIsGlobal">Global</a-checkbox>
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
      <template v-else-if="column.key === 'application_ids'">
        <a-space direction="vertical">
          <a v-for="applicationId in record.application_ids" :key="applicationId">{{ applicationId }}</a>
        </a-space>
      </template>
      <template v-else-if="column.key === 'is_global'">
        <a-checkbox :checked="record.is_global" disabled />
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
const newApplicationIds = ref('');
const newWmsLayers = ref('');
const newDisableEsdlLayers = ref('');
const newWorkflow = ref('');
const newJsFunction = ref('');
const newIsGlobal = ref(false);

const get_activity_contexts = async () => {
  const response = await fetch('/admin/context/activities')
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
    title: 'Application IDs',
    dataIndex: 'application_ids',
    key: 'application_ids',
  },
  {
    title: 'WMS Layers',
    dataIndex: 'wms_layers',
    key: 'wms_layers',
  },
  {
    title: 'Disable ESDL layers',
    dataIndex: 'disable_esdl_layers',
    key: 'disable_esdl_layers',
  },
  {
    title: 'Workflow',
    dataIndex: 'workflow',
    key: 'workflow',
  },
  {
    title: 'JS function',
    dataIndex: 'js_function',
    key: 'js_function',
  },
  {
    title: 'Global',
    dataIndex: 'is_global',
    key: 'is_global',
  },
  {
    title: 'Actions',
    key: 'actions',
  }
]

const deleteActivityContext = async (id) => {
  const response = await fetch('/admin/context/activities/' + id, {
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
  // If newWmsLayers is not an empty string, convert it to list of strings.
  const wmsLayers = newWmsLayers.value ? newWmsLayers.value.split(',') : [];
  const disableEsdlLayers = newDisableEsdlLayers.value ? newDisableEsdlLayers.value.split(',') : [];
  let applicationIds = null;
  if (newApplicationIds.value) {
    applicationIds = newApplicationIds.value.split(',').map(applicationId => applicationId.trim());
  }
  const workflow = newWorkflow.value || null;
  const jsFunction = newJsFunction.value || null;
  const isGlobal = newIsGlobal.value;
  const response = await fetch('/admin/context/activities', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      activity_id: newActivityContextID.value,
      name: newActivityContextName.value,
      wms_layers: wmsLayers,
      disable_esdl_layers: disableEsdlLayers,
      toast_text: null,
      context_menu_services: [],
      context_menu_js_functions: [],
      workflow: workflow,
      js_function: jsFunction,
      application_ids: applicationIds,
      is_global: isGlobal,
    })
  })
  if (!response.ok) {
    console.error('Error saving activity context', response)
    alert('Error saving activity context')
    return
  }
  addMode.value = false;
  newActivityContextID.value = '';
  newActivityContextName.value = '';
  newApplicationIds.value = '';
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