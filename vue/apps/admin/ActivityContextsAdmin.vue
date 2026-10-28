<template>
  <h1>Activity Contexts</h1>
  <p>Reload the page after changes to refresh the selectors.</p>
  <a-alert v-if="errorText" :message="errorText" type="error" show-icon />
  <a-form v-if="activityContext" :model="activityContext" layout="vertical" :disabled="saving" style="max-width: 720px; margin: 16px 0" @finish="saveActivityContext">
    <h2>Add activity context</h2>
    <a-row :gutter="16">
      <a-col :xs="24" :sm="12">
        <a-form-item label="Activity ID" name="activity_id" :rules="[{ required: true, whitespace: true }]">
          <a-input v-model:value="activityContext.activity_id" />
        </a-form-item>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-form-item label="Name" name="name" :rules="[{ required: true, whitespace: true }]">
          <a-input v-model:value="activityContext.name" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-form-item>
      <a-checkbox v-model:checked="activityContext.is_global">Available to all users</a-checkbox>
    </a-form-item>
    <a-form-item label="Toast text">
      <a-textarea v-model:value="activityContext.toast_text" :rows="2" />
    </a-form-item>
    <a-form-item label="Application IDs">
      <a-input v-model:value="activityContext.application_ids" />
    </a-form-item>
    <a-form-item label="WMS layers">
      <a-input v-model:value="activityContext.wms_layers" />
    </a-form-item>
    <a-form-item label="Disable ESDL layers">
      <a-input v-model:value="activityContext.disable_esdl_layers" />
    </a-form-item>
    <a-row :gutter="16">
      <a-col :xs="24" :sm="12">
        <a-form-item label="Workflow">
          <a-input v-model:value="activityContext.workflow" />
        </a-form-item>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-form-item label="JS function">
          <a-input v-model:value="activityContext.js_function" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-space>
      <a-button type="primary" html-type="submit" :loading="saving">Save</a-button>
      <a-button :disabled="saving" @click="activityContext = null">Cancel</a-button>
    </a-space>
  </a-form>
  <a-button v-else type="primary" :disabled="loading || saving" @click="addActivityContext">Add</a-button>
  <a-table :columns="columns" :data-source="activityContexts" row-key="activity_id" :loading="loading" size="middle" style="width: 100%" :scroll="{ x: 1000 }">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'wms_layers'">
        <a-space direction="vertical">
          <span v-for="layer in record.wms_layers" :key="layer">{{ layer }}</span>
        </a-space>
      </template>
      <template v-else-if="column.key === 'application_ids'">
        <a-space direction="vertical">
          <span v-for="applicationId in record.application_ids" :key="applicationId">{{ applicationId }}</span>
        </a-space>
      </template>
      <template v-else-if="column.key === 'is_global'">
        <a-checkbox :checked="record.is_global" disabled />
      </template>
      <template v-else-if="column.key === 'actions'">
        <a-popconfirm title="Delete this activity context?" :disabled="saving || activityContext !== null" @confirm="deleteActivityContext(record.activity_id)">
          <a-button :disabled="saving || activityContext !== null">Delete</a-button>
        </a-popconfirm>
      </template>
    </template>
  </a-table>
</template>

<script setup>
import {ref} from "vue";
import {Popconfirm as APopconfirm} from 'ant-design-vue';

const activityContexts = ref([]);
const activityContext = ref(null);
const errorText = ref('');
const loading = ref(false);
const saving = ref(false);

const getActivityContexts = async () => {
  loading.value = true;
  try {
    const response = await fetch('/admin/context/activities');
    if (!response.ok) {
      throw new Error('Error loading activity contexts');
    }
    activityContexts.value = await response.json();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    loading.value = false;
  }
};
getActivityContexts();

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
];

const deleteActivityContext = async (id) => {
  errorText.value = '';
  saving.value = true;
  try {
    const response = await fetch('/admin/context/activities/' + encodeURIComponent(id), {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Error deleting activity context');
    }
    await getActivityContexts();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    saving.value = false;
  }
};

const saveActivityContext = async () => {
  errorText.value = '';
  saving.value = true;
  const context = activityContext.value;
  let applicationIds = context.application_ids.split(',').map(id => id.trim()).filter(Boolean);
  if (!applicationIds.length) {
    applicationIds = null;
  }
  try {
    const response = await fetch('/admin/context/activities', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        activity_id: context.activity_id.trim(),
        name: context.name.trim(),
        is_global: context.is_global,
        toast_text: context.toast_text.trim() || null,
        application_ids: applicationIds,
        wms_layers: context.wms_layers.split(',').map(id => id.trim()).filter(Boolean),
        disable_esdl_layers: context.disable_esdl_layers.split(',').map(name => name.trim()).filter(Boolean),
        workflow: context.workflow.trim() || null,
        js_function: context.js_function.trim() || null,
        context_menu_services: [],
        context_menu_js_functions: [],
      }),
    });
    if (!response.ok) {
      const contextError = await response.json().catch(() => ({}));
      throw new Error(contextError.error || 'Error saving activity context');
    }
    activityContext.value = null;
    await getActivityContexts();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    saving.value = false;
  }
};

const addActivityContext = () => {
  errorText.value = '';
  activityContext.value = {
    activity_id: '',
    name: '',
    is_global: false,
    toast_text: '',
    application_ids: '',
    wms_layers: '',
    disable_esdl_layers: '',
    workflow: '',
    js_function: '',
  };
};
</script>