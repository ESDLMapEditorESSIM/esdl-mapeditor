<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
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
        :row-key="rowkey"
        :data-source="filteredRows"
        :pagination="pagination"
        :loading="isLoading"
        size="small"
        class="resulttable"
        style="font-size: 12px;"
      >
        <template #action="{ record }">
          <span>
            <a-row :gutter="4">
              <a-col v-for="a in actions" :key="a.title">
                <div v-if="'icon' in a">
                  <i
                    v-if="actionEnabled(a, record)"
                    :class="a.icon"
                    class="pointer"
                    :title="a.title"
                    @mouseleave="hide_jquery_ui_popup"
                    @click="doAction(record, a)"
                  />
                  <i v-else :class="a.icon" class="disabled" />
                </div>
                <div v-else>
                  <li>
                    <a v-if="actionEnabled(a, record)" href="#" @click="doAction(record, a)">{{ a.title }}</a>
                    <div v-else class="disabled">{{ a.title }}</div>
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
</template>

<script setup="props">

import {onMounted, ref, watch} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {workflowGetData} from "./utils/api.js";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

let workflowStep = props.workflowStep;
let workflowTrigger = props.workflowStep.workflowTrigger;

onMounted(() => {
  doGetData();
  refresh();
});

watch(workflowTrigger, () => {
  refresh();
});

const isLoading = ref(true);
const form = {};
form[workflowStep.target_variable] = "";

const {getParamsFromState, goToStep, getState} = useWorkflow();
const state = getState();
const columns = ref([]);
const rowkey = ref("");
const additional_fields = ref(null);
const actions = ref([]);
const tableRows = ref([]);
const filteredRows = ref([]);
const selectedUserGroups = ref(["my_runs"]);
const userGroupsForUser = ref([{value: "my_runs", label: "my runs"}]);

const pagination = ref({"position": 'bottom', "hideOnSinglePage": true, "defaultPageSize": 9});

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
  console.log('Action selected: ', record[rowkey.value], action);
  state[workflowStep.target_variable] = {};
  state[workflowStep.target_variable][rowkey.value] = record[rowkey.value];
  for (const field of additional_fields.value) {
    state[workflowStep.target_variable][field] = record[field];
  }

  isLoading.value = true;
  if ("to_socket" in action) {
    let params = "params" in action.to_socket ? action.to_socket.params : {};
    if ("record_params" in action.to_socket) {
      for (const [key, record_key] of Object.entries(action.to_socket.record_params)) {
        params[key] = record[record_key];
      }
    }
    window.socket.emit(action.to_socket.event, params, () => {
      doGetData();
    });
  }
  isLoading.value = false;

  if ("next_step" in action) {
    goToStep(action.next_step);
  }
};

const actionEnabled = (action, row) => {
  if (action.enabled) {
    //console.log("Action enabled: ", action, row);
    if (action.enabled.dataIndex) {
      let value = row[action.enabled.dataIndex];
      return !!action.enabled.values.includes(value);
    }
  }
  return true;  // default enabled
};

const doGetData = async () => {
  if ("url" in workflowStep.source) {
    const data = await workflowGetData(workflowStep.source.url, getParamsFromState(workflowStep.source.request_params))
    handleData(data);
  } else if ("from_socket" in workflowStep.source) {
    const from_socket = workflowStep.source.from_socket;
    window.socket.emit(from_socket.event, from_socket.params, (res) => {
          handleData(res);
        }
    );
  }
  window.socket.emit("get_user_group_paths", (user_group_paths) => {
        const organizations = [];
        const projects = [];
        for (const user_group_path of user_group_paths) {
          if (user_group_path.startsWith("/Organizations")) {
            organizations.push({
              value: user_group_path,
              label: user_group_path.replace("/Organizations/", "")
            });
          } else if (user_group_path.startsWith("/Projects")) {
            projects.push({
              value: user_group_path,
              label: user_group_path.replace("/Projects/", "")
            });
          }
        }
        userGroupsForUser.value.push({value: "Organizations", label: "Organizations", children: organizations});
        userGroupsForUser.value.push({value: "Projects", label: "Projects", children: projects});
      }
  );
};

const handleData = (data) => {
  if (data != null) {
    const source = workflowStep.source;
    // process defined columns in workflow config
    // column syntax follows AntDV table column definition.
    source.columns.forEach((column) => {
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
    let hasActionColumn = source.columns.find(o => o.key === 'action');
    if (!hasActionColumn && source.actions) {
      source.columns.push(
          {
            'key': 'action',
            'title': 'Action',
            "slots": {
              "customRender": "action",
            }
          });
    }
    actions.value = source.actions;
    columns.value = source.columns;
    rowkey.value = source.value_field; // "job_id"
    additional_fields.value = source.additional_fields;
    tableRows.value = data;
    updateFilteredRows();
  }
  isLoading.value = false;
};

const hasProgressIndication = (record, column) => {
  return record.status === "RUNNING" && "progressAttribute" in column;
};

const getProgressPercent = (record, column) => {
  let progress = record[column["progressAttribute"]];
  return isNaN(progress) ? 0 : 100 * progress;
};

const refresh = async () => {
  workflowStep = props.workflowStep;
  workflowTrigger = props.workflowStep.workflowTrigger;
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

</script>

<style scoped>
.resulttable { /* does not work...*/
  font-size: 10px;
  table-layout: auto;
  line-height: 1.2;
}

.ant-table table {
  font-size: 10px !important;
  line-height: 1.2 !important;
}

.ant-tag {
  font-size: 9px !important;
}

.pointer {
  cursor: pointer;
}

.disabled {
  color: lightgray;
}
</style>
