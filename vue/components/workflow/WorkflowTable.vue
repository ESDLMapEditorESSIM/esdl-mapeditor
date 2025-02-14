<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :label-col="{ span: 0 }">
    <a-form-item>
      <a-table
        :columns="columns"
        :row-key="rowKey"
        :data-source="tableRows"
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
                    class="pointer"
                    :title="action.title"
                    @mouseleave="hide_jquery_ui_popup"
                    @click="doAction(record, action)"
                  />
                  <i v-else :class="action.icon" class="disabled" />
                </div>
                <div v-else>
                  <li>
                    <a v-if="actionEnabled(action, record)" href="#" @click="doAction(record, action)">{{
                      action.title
                    }}</a>
                    <div v-else class="disabled">{{ action.title }}</div>
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
import {useOngoingBackendProcesses} from "@/composables/ongoingBackendProcesses";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
  rows: {
    type: Object,
    default: null,
    required: false,
  },
});
const {
  getWorkflowStepParameters,
  goToStep,
  goToNextStepConfig,
  getState,
  getInputData,
} = useWorkflow();
const {
  setStartingBackendProcessId,
  addOngoingBackendProcessId,
  isBackendProcessIdOngoing,
} = useOngoingBackendProcesses();

const stepParams = ref({});

onMounted(() => {
  init();
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
  watch(() => props.rows, () => {
    tableRows.value = props.rows;
  });
});

const isLoading = ref(true);


const state = getState();
const columns = ref([]);
const rowKey = ref("");
const additional_fields = ref(null);
const actions = ref([]);
const tableRows = ref([]);

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
  // console.log('Action selected: ', record[rowKey.value], action);
  if (stepParams.value.data.output_wrapper_variable) {
    state[stepParams.value.data.output_wrapper_variable] = {};
    state[stepParams.value.data.output_wrapper_variable][rowKey.value] = record[rowKey.value];
    for (const field of additional_fields.value) {
      state[stepParams.value.data.output_wrapper_variable][field] = record[field];
    }
  } else {
    state[rowKey.value] = record[rowKey.value];
    for (const field of additional_fields.value) {
      state[field] = record[field];
    }
  }

  if ("wait_icon" in action) {
    const processId = action.title + record[rowKey.value];
    addOngoingBackendProcessId(processId);
    setStartingBackendProcessId(processId);
  }

  if ("next_step_config" in action) {
    goToNextStepConfig(action.next_step_config);
  } else if ("next_step" in action) {
    goToStep(action.next_step);
  }
};

const actionWaiting = (action, record) => {
  return isBackendProcessIdOngoing(action.title + record[rowKey.value]);
};

const actionEnabled = (action, row) => {
  if (action.enabled) {
    // console.log("Action enabled: ", action, row);
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
  if (props.rows === null) {
    tableRows.value = data;
  } else {
    tableRows.value = props.rows;
  }

  const config = stepParams.value.config;
  columns.value = config.columns;
  actions.value = config.actions;
  rowKey.value = config.value_field; // "job_id"
  additional_fields.value = config.additional_fields;

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

  let hasActionColumn = columns.value.find(o => o.key === 'action');
  if (!hasActionColumn && actions.value) {
    columns.value.push(
        {
          'key': 'action',
          'title': 'Action',
          "slots": {
            "customRender": "action",
          }
        });
  }
  isLoading.value = false;
};

const hasProgressIndication = (record, column) => {
  return record.status === "RUNNING" && "progressAttribute" in column;
};

const getProgressPercent = (record, column) => {
  let progress = record[column["progressAttribute"]];
  return isNaN(progress) ? 0 : Math.round(100 * progress);
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  await getInputData(stepParams.value.data, handleData);
};

// to prevent stuck popup
const hide_jquery_ui_popup = () => {
  window.jquery(".ui-tooltip-content").parents('div').remove();
};

</script>

<style scoped>
.ant-table table {
  font-size: 10px !important;
  line-height: 1.2 !important;
}

.pointer {
  cursor: pointer;
}

.disabled {
  color: lightgray;
}
</style>
