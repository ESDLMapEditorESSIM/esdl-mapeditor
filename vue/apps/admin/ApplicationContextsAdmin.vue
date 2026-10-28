<template>
  <h1>Application Contexts</h1>
  <p>Reload the page after changes to refresh the selectors.</p>
  <a-alert v-if="errorText" :message="errorText" type="error" show-icon />
  <a-form v-if="applicationContext" :model="applicationContext" layout="vertical" :disabled="saving" style="max-width: 720px; margin: 16px 0" @finish="saveApplicationContext">
    <h2 v-if="editingId !== null">Edit application context</h2>
    <h2 v-else>Add application context</h2>
    <a-row :gutter="16">
      <a-col :xs="24" :sm="12">
        <a-form-item label="Application ID" name="application_id" :rules="[{ required: true, whitespace: true }]">
          <a-input v-model:value="applicationContext.application_id" :disabled="editingId !== null" />
        </a-form-item>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-form-item label="Name" name="name" :rules="[{ required: true, whitespace: true }]">
          <a-input v-model:value="applicationContext.name" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-form-item>
      <a-checkbox v-model:checked="applicationContext.is_global">Available to all users</a-checkbox>
    </a-form-item>
    <a-form-item label="Toast text">
      <a-textarea v-model:value="applicationContext.toast_text" :rows="2" />
    </a-form-item>
    <a-space>
      <a-button type="primary" html-type="submit" :loading="saving">Save</a-button>
      <a-button :disabled="saving" @click="applicationContext = null">Cancel</a-button>
    </a-space>
  </a-form>
  <a-button v-else type="primary" :disabled="loading || saving" @click="addApplicationContext">Add</a-button>
  <a-table :columns="columns" :data-source="applicationContexts" row-key="application_id" :loading="loading" size="middle" style="width: 100%" :scroll="{ x: 700 }">
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'is_global'">
        <a-checkbox :checked="record.is_global" disabled />
      </template>
      <template v-else-if="column.key === 'actions'">
        <a-space>
          <a-button :disabled="saving || applicationContext !== null" @click="editApplicationContext(record)">Edit</a-button>
          <a-popconfirm title="Delete this application context?" :disabled="saving || applicationContext !== null" @confirm="deleteApplicationContext(record.application_id)">
            <a-button :disabled="saving || applicationContext !== null">Delete</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </template>
  </a-table>
</template>

<script setup>
import {ref} from "vue";
import {Popconfirm as APopconfirm} from 'ant-design-vue';

const applicationContexts = ref([]);
const applicationContext = ref(null);
const editingId = ref(null);
const errorText = ref('');
const loading = ref(false);
const saving = ref(false);

const columns = [
  {
    title: 'Application ID',
    dataIndex: 'application_id',
    key: 'application_id',
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'Global',
    key: 'is_global',
  },
  {
    title: 'Actions',
    key: 'actions',
  }
];

const getApplicationContexts = async () => {
  loading.value = true;
  try {
    const response = await fetch('/admin/context/applications');
    if (!response.ok) {
      throw new Error('Error loading application contexts');
    }
    applicationContexts.value = await response.json();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    loading.value = false;
  }
};
getApplicationContexts();

const addApplicationContext = () => {
  errorText.value = '';
  editingId.value = null;
  applicationContext.value = {
    application_id: '',
    name: '',
    toast_text: '',
    is_global: false,
  };
};

const editApplicationContext = (context) => {
  errorText.value = '';
  editingId.value = context.application_id;
  applicationContext.value = {
    application_id: context.application_id,
    name: context.name,
    toast_text: context.toast_text || '',
    is_global: context.is_global === true,
  };
};

const saveApplicationContext = async () => {
  errorText.value = '';
  saving.value = true;
  let url = '/admin/context/applications';
  let method = 'POST';
  if (editingId.value !== null) {
    url += '/' + encodeURIComponent(editingId.value);
    method = 'PUT';
  }
  try {
    const response = await fetch(url, {
      method: method,
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(applicationContext.value),
    });
    if (!response.ok) {
      const contextError = await response.json().catch(() => ({}));
      throw new Error(contextError.error || 'Error saving application context');
    }
    applicationContext.value = null;
    await getApplicationContexts();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    saving.value = false;
  }
};

const deleteApplicationContext = async (id) => {
  errorText.value = '';
  saving.value = true;
  try {
    const response = await fetch('/admin/context/applications/' + encodeURIComponent(id), {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Error deleting application context');
    }
    await getApplicationContexts();
  } catch (error) {
    errorText.value = error.message;
  } finally {
    saving.value = false;
  }
};
</script>
