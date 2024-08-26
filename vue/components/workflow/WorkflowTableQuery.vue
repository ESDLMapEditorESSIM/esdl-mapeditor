<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
      <a-button type="primary" :disabled="isLoading" :loading="isLoading" @click="doGetData">
        Reload
      </a-button>
      <a-table
        :columns="columns"
        :row-key="rowkey"
        :data-source="dataSource"
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
          <a-tag :color="getTagColor(record[column.dataIndex])">{{ record[column.dataIndex] }}</a-tag>
        </template>
      </a-table>
    </a-form-item>
  </a-form>
</template>

<script setup="props">

import {ref, watch} from "vue";
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
// eslint-disable-next-line no-unused-vars
watch(workflowTrigger, (currentValue, oldValue) => {
  init();
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
const dataSource = ref([]);

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
  if ("from_socket_emit" in action) {
    let params = {};
    if ("params" in action.from_socket_emit) {
      params = action.from_socket_emit.params;
    }
    if ("record_params" in action.from_socket_emit) {
      for (const [key, record_key] of Object.entries(action.from_socket_emit.record_params)) {
        params[key] = record[record_key];
      }
    }
    window.socket.emit(action.from_socket_emit.event, params, (res) => {
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
  } else if ("from_socket_emit" in workflowStep.source) {
    const from_socket_emit = workflowStep.source.from_socket_emit;
    window.socket.emit(from_socket_emit.event, from_socket_emit.params, (res) => {
          handleData(res);
        }
    )
  }
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
    rowkey.value = source.value_field; // "job_id"; // "record => record." + source.value_field
    additional_fields.value = source.additional_fields;
    dataSource.value = data;
  }
  isLoading.value = false;
};

const init = () => {
  workflowStep = props.workflowStep;
  workflowTrigger = props.workflowStep.workflowTrigger;
  doGetData();
};
init();

const hide_jquery_ui_popup = () => {
  window.jquery(".ui-tooltip-content").parents('div').remove();
}

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
