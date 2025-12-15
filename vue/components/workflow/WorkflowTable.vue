<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :label-col="{ span: 0 }">
    <a-form-item>
      <a-table
        :columns="columns"
        :row-selection="rowSelection"
        :row-key="rowIdKey"
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
                    v-else-if="itemEnabled(action, record)"
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
                    <a v-if="itemEnabled(action, record)" href="#" @click="doAction(record, action)">{{
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

import {computed, onMounted, ref, watch, h} from "vue";
import {useWorkflow} from "@/composables/workflow";
import {useOngoingBackendProcesses} from "@/composables/ongoingBackendProcesses";
import {WorkflowNextStepTriggerOptions} from "@/composables/workflow";
import {convertUnit} from "@/utils/unitConversion";

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
  getState,
  getInputData,
  sendOutputData,
  setWorkflowStepInputValid
} = useWorkflow();
const {
  setStartingBackendProcessId,
  addOngoingBackendProcessId,
  isBackendProcessIdOngoing,
} = useOngoingBackendProcesses();

/** @type {import('vue').Ref<StepParameters|null>} */
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
const rowIdKey = ref("");
const additional_fields = ref(null);
const actions = ref([]);
const tableRows = ref([]);

const pagination = ref({"position": 'bottom', "hideOnSinglePage": true, "defaultPageSize": 10});

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

  // put record key, optional additional variables, in state
  if (stepParams.value.data.output_wrapper_variable) {
    state[stepParams.value.data.output_wrapper_variable] = {};
    state[stepParams.value.data.output_wrapper_variable][rowIdKey.value] = record[rowIdKey.value];
    for (const field of additional_fields.value) {
      state[stepParams.value.data.output_wrapper_variable][field] = record[field];
    }
  } else {
    state[rowIdKey.value] = record[rowIdKey.value];
    for (const field of additional_fields.value) {
      state[field] = record[field];
    }
  }

  if ("wait_icon" in action) {
    const processId = action.title + record[rowIdKey.value];
    addOngoingBackendProcessId(processId);
    setStartingBackendProcessId(processId);
  }

  if ("next_step" in action) {
    goToStep(action.next_step);
  }
};

const actionWaiting = (action, record) => {
  return isBackendProcessIdOngoing(action.title + record[rowIdKey.value]);
};

const itemEnabled = (item, row) => {
  if (item.enabled) {
    if (item.enabled.dataIndex) {
      if ("values" in item.enabled) {
        const value = row[item.enabled.dataIndex];
        return !!item.enabled.values.includes(value);
      } else if ("exists" in item.enabled) {
        const dataExists = item.enabled.dataIndex in row;
        return item.enabled.exists ? dataExists : !dataExists;
      } else if ("condition" in item.enabled) {
        const value = row[item.enabled.dataIndex];
        const condition = item.enabled.condition;
        if (condition.type === "larger_than") {
          return value > condition.value;
        } else if (condition.type === "larger_equal_than") {
          return value >= condition.value;
        } else if (condition.type === "smaller_than") {
          return value < condition.value;
        } else if (condition.type === "smaller_equal_than") {
          return value <= condition.value;
        }
      }
    }
  }
  return true;  // default enabled
};

const updateDataToSubmit = async (data) => {
  if (!data || data.length === 0) {
    setWorkflowStepInputValid(stepParams.value.id, false);
  } else {
    if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
      sendOutputData(stepParams.value.data, data);
    }
    setWorkflowStepInputValid(stepParams.value.id, true);
  }
}

const handleData = (data) => {
  if (data === null) {
    return;
  }
  if (!Array.isArray(data)) {
    data = Object.entries(data).map(([key, value]) => ({
      dictKey: key,
      ...value
    }));
  }
  if (props.rows === null) {
    tableRows.value = data;
  } else {
    tableRows.value = props.rows;
  }

  const config = stepParams.value.config;
  columns.value = config.columns;
  actions.value = config.actions;
  rowIdKey.value = config.value_field;
  additional_fields.value = config.additional_fields;

  // process defined columns in workflow config
  // column syntax follows AntDV table column definition.
  columns.value.forEach((column) => {
  if (column.formatter) {
    if (column.formatter === 'formatDate') {
      column.customRender = formatDate;
      column.sorter = (a, b) => {
        if (a[column.dataIndex] != null && b[column.dataIndex] != null) {
          return new Date(a[column.dataIndex]) - new Date(b[column.dataIndex]);
        } else {
          return -10000000;
        }
      };
    }
  } else {
    column.customRender = (row) => {
      let value = row.text;

      if (value === undefined || value === null || value === "" || isNaN(Number(value))) {
        return value; // return text values directly
      }

      try {
        let numericValue = Number(value);

        // Unit conversion if both sourceUnit and targetUnit are defined
        if (column.sourceUnit && column.targetUnit) {
          numericValue = convertUnit(numericValue, column.sourceUnit, column.targetUnit);
        }

        const fullValue = numericValue; // full converted value for tooltip

        // Apply rounding if nrOfDecimals is defined
        let displayValue = numericValue;
        if ("nrOfDecimals" in column && column.nrOfDecimals !== undefined) {
          displayValue = numericValue.toFixed(column.nrOfDecimals);
        }

        return h(
          'a-tooltip',
          { title: fullValue.toString() },
          { default: () => displayValue }
        );

      } catch (e) {
        console.error("Column formatting error:", e.message);
        return value;
      }
    };
    // add default sorter otherwise
    column.sorter = (a, b) => ('' + a[column.dataIndex]).localeCompare(b[column.dataIndex]);
  }
});

  const hasActionColumn = columns.value.find(o => o.key === 'action');
  if (!hasActionColumn && actions.value) {
    columns.value.push(
        {
          key: 'action',
          title: 'Action',
          slots: {
            customRender: "action",
          }
        });
  }
  isLoading.value = false;
};

const rowSelection = computed(() => {
  const rowSelection = stepParams.value.config.row_selection ?? null;
  if (!rowSelection) return null;

  return {
    type: rowSelection.type,
    columnWidth: 20,
    onChange: (selectedRowKeys) => {
      if (rowSelection.type === "radio") {  // one selected row
        updateDataToSubmit(tableRows.value.find(row => row[rowIdKey.value] === selectedRowKeys[0]));
      } else { // multiple selected rows
        updateDataToSubmit(tableRows.value.filter(row => selectedRowKeys.includes(row[rowIdKey.value])));
      }
    },
    getCheckboxProps: (row) => ({
      disabled: !itemEnabled(rowSelection, row),
    }),
  };
});

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
  await updateDataToSubmit(null);
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
