<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :label-col="{ span: 0 }">
    <a-form-item>
      <a-row type="flex" justify="space-between">
        <a-col>
          <label>user group filter:</label>
        </a-col>
        <a-col>
          <a-tree-select
            v-model:value="selectedUserGroups"
            mode="multiple"
            style="width: 300px;"
            size="small"
            placeholder="Please select"
            tree-checkable
            allow-clear
            tree-default-expand-all
            :tree-data="userGroupsForUser"
            :status="selectedUserGroups.length === 0 ? 'error' : ''"
            @change="updateFilteredRows"
            @mouseleave="hide_jquery_ui_popup"
          />
        </a-col>
      </a-row>
      <a-table
        :columns="columns"
        :row-selection="rowSelection"
        :row-key="rowIdKey"
        :data-source="filteredRows"
        :pagination="pagination"
        :loading="isLoading"
        size="small"
        style="font-size: 12px;"
      >
        <template #action="{ record }">
          <span>
            <a-row :gutter="4">
              <a-col v-for="action in actions" :key="action.title">
                <div v-if="'icon' in action">
                  <i
                    v-if="actionWaiting(action, record)"
                    :class="action.wait_icon"
                    :title="action.wait_title"
                    @mouseleave="hide_jquery_ui_popup"
                  />
                  <i
                    v-else-if="actionEnabled(action, record)"
                    :class="action.icon"
                    class="action-pointer"
                    :title="action.title"
                    @mouseleave="hide_jquery_ui_popup"
                    @click="doAction(record, action)"
                  />
                  <i v-else :class="action.icon" class="action-disabled" />
                </div>
                <div v-else>
                  <li>
                    <a v-if="actionEnabled(action, record)" href="#" @click="doAction(record, action)">{{
                      action.title
                    }}</a>
                    <div v-else class="action-disabled">{{ action.title }}</div>
                  </li>
                </div>
              </a-col>
            </a-row>
          </span>
        </template>
        <template #tags="{ record, column }">
          <a-progress
            v-if="hasProgressIndication(record,column)"
            :percent="getProgressPercent(record, column)"
            status="normal"
            :size="'small'"
          />
          <a-tag v-else :color="getTagColor(record[column.dataIndex])">{{ record[column.dataIndex] }}</a-tag>
        </template>
      </a-table>
    </a-form-item>
  </a-form>
  <a-modal
    v-model:open="actionModalActive"
    :title="modalTitle"
    :ok-text="activeAction.title === EDIT? 'Save' : [DELETE, DELETE_MULTIPLE].includes(activeAction.title) ? 'Delete' : 'Ok'"
    :ok-button-props="{danger: [DELETE, DELETE_MULTIPLE].includes(activeAction.title)}"
    width="80%"
    style="top: 50px"
    :body-style="{'max-height': 'calc(100vh - 200px)', 'overflow': 'auto'}"
    @ok="handleModalOk"
  >
    <json-forms
      v-if="activeAction.title === EDIT"
      :data="jfFormData"
      :schema="jfSchema"
      :uischema="jfUiSchema"
      :renderers="renderers"
      :ajv="ajv"
      @change="onChange"
    />
    <!-- eslint-disable vue/no-v-html (sanitized with DOMPurify) -->
    <p v-if="runDetailsText !== ''" v-html="DOMPurify.sanitize(runDetailsText, {ADD_ATTR: ['target', 'rel']})" />
  </a-modal>
</template>

<script setup="props">

import {onMounted, ref, h} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {useOngoingBackendProcesses} from "@/composables/ongoingBackendProcesses";
import {useWorkflowTableState} from "@/composables/workflowTableState";

import {JsonForms} from "@jsonforms/vue";
import Ajv from "ajv";
import {Tooltip} from 'ant-design-vue';
import addFormats from "ajv-formats";
import {vanillaRenderers,} from "@jsonforms/vue-vanilla";
import "@jsonforms/vue-vanilla/vanilla.css";
import DOMPurify from 'dompurify';

const renderers = Object.freeze([...vanillaRenderers]);
const ajv = new Ajv({allErrors: true, useDefaults: true, $data: true});
addFormats(ajv);

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  }
});

const {getSelectedUserGroupsRef} = useWorkflowTableState();
const selectedUserGroups = getSelectedUserGroupsRef();

const {
  getWorkflowStepParameters,
  getInputData,
} = useWorkflow();
const {
  addOngoingBackendProcessId,
  isBackendProcessIdOngoing,
} = useOngoingBackendProcesses();

/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});

onMounted(() => {
  init();
});

const LOAD_RESULT = "Load result";
const VIEW_FEEDBACK = "View feedback";
const EDIT = "Edit";
const VIEW_DETAILS = "View details";
const DOWNLOAD_XLSX = "Download xlsx";
const LOAD_INPUT_ESDL = "Load input ESDL";
const DELETE = "Delete";
const DELETE_MULTIPLE = "Delete multiple";

const isLoading = ref(true);
const activeAction = ref({});
const activeRowId = ref(null);
const actionModalActive = ref(false);
const modalTitle = ref("");

const columns = ref([]);
const rowIdKey = ref("run_id");
const runNameKey = ref("run_name");
const actions = ref([]);
const tableRows = ref([]);
const filteredRows = ref([]);
const userGroupsForUser = ref([{value: "my_runs", label: "my runs"}]);

const checkedRows = ref([]);
const deleteRunsEnabled = ref(false);

const pagination = ref({"position": 'bottom', "hideOnSinglePage": true, "defaultPageSize": 10});

const jfFormData = ref({});
const jfSchema = ref({});
const jfUiSchema = ref({});
const editedRunData = ref(null);

const runDetailsText = ref("");

const onChange = (event) => {
  editedRunData.value = event.data;
};

const formatDate = (row) => {
  if (row.text !== undefined && row.text != null) {
    let d = new Date(row.text);
    return d.toLocaleString('nl-NL'); // return VNode
  }
  return row.text;
};

const getTagColor = (text) => {
  let up = text.toUpperCase();
  if (up === "FINISHED" || up === "SUCCESS" || up === "SUCCEEDED" || up === "OK" || up === "READY") {
    return "green";
  } else if (up === "REGISTERED" || up === "INITIALIZED" || up === "SUBMITTED") {
    return "blue";
  } else if (up === "RUNNING" || up === "IN_PROGRESS" || up === "CALCULATING") {
    return "orange";
  } else if (up === "ERROR" || up === "FAILED") {
    return "red";
  } else {
    return "black";
  }
};

const doAction = (record, action) => {
  hide_jquery_ui_popup();

  const processId = action.title + record[rowIdKey.value];
  if ("wait_icon" in action) {
    addOngoingBackendProcessId(processId);
  }
  if ([LOAD_RESULT, VIEW_FEEDBACK, LOAD_INPUT_ESDL].includes(action.title)) {
    window.show_loader();
    const params = {
      "service_config": {
        "name": action.title,
        "type": "",
        "result": [
          {
            "action": "esdl"
          }
        ],
        "state_params": true
      }
    };
    if (action.title === LOAD_RESULT) {
      params.service_config.external_model = "output_or_input_esdl";
      params.service_config.result[0].model_short_name = stepParams.value.config.model_short_name;
      if (stepParams.value.config.result_external_link) {
        params.service_config.result[0].external_link = stepParams.value.config.result_external_link;
      }
    } else if (action.title === VIEW_FEEDBACK) {
      params.service_config.external_model = "output_or_input_esdl";
      params.service_config.result[0].show_asset_feedback = true;
    } else if (action.title === LOAD_INPUT_ESDL) {
      params.service_config.external_model = "input_esdl";
    }
    params.state_params = {
      [rowIdKey.value]: record[rowIdKey.value],
      [runNameKey.value]: record[runNameKey.value]
    }
    window.socket.emit("command", {cmd: "query_esdl_service", params: params}, () => {
      window.hide_loader();
    });
  } else if (action.title === VIEW_DETAILS) {
    activeAction.value = action;
    modalTitle.value = `Run details`;
    window.socket.emit("external_models_get_run_text", {"run_id": record[rowIdKey.value]}, (text) => {
      runDetailsText.value = text;
      actionModalActive.value = true;
    });
  } else if (action.title === EDIT) {
    activeAction.value = action;
    modalTitle.value = `Edit ${stepParams.value.config.model_short_name} run: '${record[runNameKey.value]}'`;
    window.socket.emit("external_models_get_run_jsonforms", {"run_id": record[rowIdKey.value]}, (extModJsonForms) => {
      jfSchema.value = extModJsonForms.schema;
      jfFormData.value = extModJsonForms.formData;
      jfUiSchema.value = extModJsonForms.uischema;
      actionModalActive.value = true;
    });
  } else if (action.title === DELETE) {
    activeAction.value = action;
    activeRowId.value = record[rowIdKey.value];
    modalTitle.value = `Delete ${stepParams.value.config.model_short_name} run: '${record[runNameKey.value]}'?`;
    window.socket.emit("external_models_get_run_text", {"run_id": record[rowIdKey.value]}, (text) => {
      runDetailsText.value = text;
      actionModalActive.value = true;
    });
  } else if (action.title === DOWNLOAD_XLSX) {
    const params = stepParams.value.config.time_series_xlsx_download;
    params["run_id"] = record[rowIdKey.value];
    params["backend_process_id"] = processId;
    window.socket.emit("external_models_download_run", params);
  }
};

const handleModalOk = () => {
  if (activeAction.value.title === EDIT) {
    window.socket.emit("external_models_update_run", editedRunData.value, async () => {
      actionModalActive.value = false;
      await getInputData(stepParams.value.data, handleData);
    });
  } else if (activeAction.value.title === DELETE) {
    const params = {"run_id": activeRowId.value};
    if (stepParams.value.config.delete_result_url) {
      params["delete_result_url"] = stepParams.value.config.delete_result_url;
    }
    window.socket.emit("external_models_delete_run", params, async () => {
      actionModalActive.value = false;
      await getInputData(stepParams.value.data, handleData);
    });
  } else if (activeAction.value.title === DELETE_MULTIPLE) {
    for (let iRow = 0; iRow < checkedRows.value.length; iRow++) {
      const params = {"run_id": checkedRows.value[iRow][rowIdKey.value]};
      if (stepParams.value.config.delete_result_url) {
        params["delete_result_url"] = stepParams.value.config.delete_result_url;
      }
      window.socket.emit("external_models_delete_run", params, async () => {
        if (iRow === checkedRows.value.length - 1) {
          deleteRunsEnabled.value = false;
          actionModalActive.value = false;
          await getInputData(stepParams.value.data, handleData);
        }
      });
    }
  } else {
    actionModalActive.value = false;
  }
  runDetailsText.value = "";
};

const actionWaiting = (action, record) => {
  return isBackendProcessIdOngoing(action.title + record[rowIdKey.value]);
};

const actionEnabled = (action, row) => {
  if (action.enabled) {
    if (action.enabled.dataIndex) {
      if ("values" in action.enabled) {
        let value = row[action.enabled.dataIndex];
        return !!action.enabled.values.includes(value);
      } else if ("exists" in action.enabled) {
        const dataExists = action.enabled.dataIndex in row;
        return action.enabled.exists ? dataExists : !dataExists;
      }
    }
  }
  return true;  // default enabled
};

const handleData = (data) => {
  if (data === null) {
    return;
  }
  if (!Array.isArray(data)) {
    data = Object.values(data);
  }
  tableRows.value = data;
  updateFilteredRows();

  setColumns();
  setActions();

  isLoading.value = false;
};

const hasProgressIndication = (record, column) => {
  return record.status === "RUNNING" && "progressAttribute" in column;
};

const getProgressPercent = (record, column) => {
  let progress = record[column["progressAttribute"]];
  return isNaN(progress) ? 0 : Math.round(100 * progress);
};

const buildTreeFromPaths = (paths) => {
  const root = [];
  for (const path of paths) {
    const parts = path.replace(/^\/+/, '').split('/');  // remove initial slash and split
    let currentLevel = root;
    let currentPath = '';
    for (const part of parts) {
      currentPath += '/' + part;
      let existing = currentLevel.find(node => node.label === part);
      if (!existing) {
        existing = {
          value: currentPath,
          label: part,
          children: []
        };
        currentLevel.push(existing);
      }
      currentLevel = existing.children;
    }
  }
  return root;
}

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  await getInputData(stepParams.value.data, handleData);

  window.socket.emit("get_user_group_paths", (userGroupPaths) => {
        userGroupsForUser.value = [{value: "my_runs", label: "my runs"}];
        if (userGroupPaths.length > 0) {
          userGroupsForUser.value = userGroupsForUser.value.concat(buildTreeFromPaths(userGroupPaths));
        }
      }
  );

  window.socket.off('wfe_update_model_run');
  window.socket.on('wfe_update_model_run', (run_data) => {
    const tableRow = tableRows.value.find(i => i["run_id"] === run_data["run_id"]);
    if (tableRow === undefined) {
      tableRows.value.push(run_data);
    } else {
      for (const [key, value] of Object.entries(run_data)) {
        tableRow[key] = value;
      }
    }
    updateFilteredRows();
  });
};

const updateFilteredRows = () => {
  filteredRows.value = [];
  for (const row of tableRows.value) {
    if (row.is_owner && selectedUserGroups.value.some(r => r === "my_runs")
        || selectedUserGroups.value.some(r => row.user_group_paths.includes(r))) {
      filteredRows.value.push(row);
    }
  }
};

// to prevent stuck popup
const hide_jquery_ui_popup = () => {
  window.jquery(".ui-tooltip-content").parents('div').remove();
};

const deleteSelectedRuns = () => {
  activeAction.value = {title: DELETE_MULTIPLE};
  modalTitle.value = `Delete runs?`;
  const keysToShow = ['run_name', 'model_name', 'status', 'last_updated_from_external_model_at', 'user_group_paths']
  runDetailsText.value = checkedRows.value.map(obj => {
    const entries = keysToShow.map(k => {
      if (k in obj) {
        return `&nbsp;&nbsp;${k}: <b>${obj[k]}</b>`;
      }
      return null;
    }).filter(Boolean).join('<br>')
    return `-${entries}`;
  }).join('<br><br>');

  actionModalActive.value = true;
};

const rowSelection = {
  onChange: (selectedRowKeys) => {
    checkedRows.value = tableRows.value.filter(row =>
        selectedRowKeys.includes(row[rowIdKey.value])
    );
    deleteRunsEnabled.value = selectedRowKeys.length > 0;
  },
  columnWidth: 18,
  columnTitle: () =>
      h(
          Tooltip,
          {title: deleteRunsEnabled.value ? 'Delete selected run(s)' : 'No runs selected'},
          {
            default: () =>
                h(
                    'div',
                    {
                      style: {
                        cursor: deleteRunsEnabled.value ? 'pointer' : 'not-allowed',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        opacity: deleteRunsEnabled.value ? 1 : 0.4,
                      },
                      onClick: () => {
                        if (deleteRunsEnabled.value) deleteSelectedRuns()
                      },
                    },
                    [
                      h('i', {
                        class: 'far fa-trash-alt',
                        style: {color: deleteRunsEnabled.value ? 'red' : 'gray', fontSize: '16px'},
                      }),
                    ]
                ),
          }
      ),
  getCheckboxProps: (row) => ({
    disabled: !row.is_owner,
  }),
};

const setColumns = () => {
  columns.value = [
    {
      dataIndex: "run_name",
      title: "Name",
      ellipsis: true
    },
    {
      dataIndex: "status",
      title: "Status",
      align: "center",
      progressAttribute: "progress_fraction",
      slots: {
        customRender: "tags"
      }
    },
    {
      dataIndex: "submitted_to_external_model_at",
      title: "Submitted",
      formatter: "formatDate",
      defaultSortOrder: "descend"
    }
  ];

  // process defined columns in workflow config
  // column syntax follows AntDV table column definition.
  columns.value.forEach((column) => {
    if (column.formatter) {  // special property for this component
      if (column.formatter === 'formatDate') {
        column.customRender = formatDate;
        column.sorter = (a, b) => {
          if (a[column.dataIndex] != null && a[column.dataIndex] !== "" && b[column.dataIndex] != null && b[column.dataIndex] !== "") {
            return (new Date(a[column.dataIndex])) - (new Date(b[column.dataIndex]));
          } else {
            return -10000000;
          }
        }
        //column.sortOrder = 'descend'; -> moved to config
      }
    } else {
      // add default sorter otherwise
      column.sorter = (a, b) => ('' + a[column.dataIndex]).localeCompare(b[column.dataIndex]);  // '' forces a string comparison
    }
  });

  columns.value.push(
      {
        key: 'action',
        title: 'Action',
        slots: {
          customRender: "action",
        }
      }
  );
};

const setActions = () => {
  actions.value = [
    {
      title: LOAD_RESULT,
      icon: "far fa-eye",
      enabled: {
        dataIndex: "status",
        values: [
          "SUCCEEDED"
        ]
      }
    }];
  if (stepParams.value.config.has_feedback_messages) {
    actions.value.push(
        {
          title: VIEW_FEEDBACK,
          icon: "far fa-comment",
          enabled: {
            dataIndex: "esdl_feedback",
            exists: true
          }
        }
    );
  }
  actions.value.push(
      {
        "title": VIEW_DETAILS,
        "icon": "fas fa-info-circle",
      }
  );
  actions.value.push(
      {
        title: EDIT,
        icon: "far fa-edit",
        enabled: {
          dataIndex: "is_owner",
          values: [
            true
          ]
        }
      }
  );
  if (stepParams.value.config.time_series_xlsx_download) {
    actions.value.push(
        {
          title: DOWNLOAD_XLSX,
          icon: "fas fa-download",
          wait_title: "Extracting data..",
          wait_icon: "fas fa-spinner fa-spin",
          enabled: {
            dataIndex: "status",
            values: [
              "SUCCEEDED"
            ]
          }
        }
    );
  }
  if (stepParams.value.config.load_input_esdl) {
    actions.value.push(
        {
          title: LOAD_INPUT_ESDL,
          icon: "fas fa-sign-in-alt"
        }
    );
  }
  actions.value.push(
      {
        title: DELETE,
        icon: "far fa-trash-alt",
        enabled: {
          dataIndex: "is_owner",
          values: [
            true
          ]
        },
      }
  );
};

</script>

<style scoped>
.ant-table table {
  font-size: 10px !important;
  line-height: 1.2 !important;
}

div.ant-modal-content {
  height: calc(100vh - 200px);
}

.action-pointer {
  cursor: pointer;
}

.action-disabled {
  color: lightgray;
}

::v-deep .ant-table th.ant-table-selection-column,
::v-deep .ant-table td.ant-table-selection-column {
  padding-left: 1px !important;
  padding-right: 1px !important;
}

::v-deep .ant-table th.ant-table-selection-column .ant-checkbox-wrapper,
::v-deep .ant-table td.ant-table-selection-column .ant-checkbox-wrapper {
  margin-left: 0 !important;
  margin-right: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

</style>
