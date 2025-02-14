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
      <WorkflowTable
        :workflow-step="childTable"
        :rows="filteredRows"
      />
    </a-form-item>
  </a-form>
</template>

<script setup="props">
import {v4 as uuidv4} from 'uuid';
import {onMounted, ref, watch} from "vue";
import {default as WorkflowTable} from "@/components/workflow/WorkflowTable";
import tableConfig from "@/components/workflow/configuration/workflow_table_external_model_config.json"
import {useWorkflow} from "@/composables/workflow";

import {useWorkflowTableState} from "@/composables/workflowTableState";

const {getSelectedUserGroupsRef} = useWorkflowTableState();
const selectedUserGroups = getSelectedUserGroupsRef();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const stepParams = ref({});
const childTable = ref({});

onMounted(() => {
  init();
  doGetData();
  refresh();
  watch(props.workflowStep.workflowTrigger, () => {
    refresh();
  });
});

const isLoading = ref(true);

const {getWorkflowStepParameters, getInputData} = useWorkflow();
const actions = ref([]);
const tableRows = ref([]);
const filteredRows = ref([]);
const userGroupsForUser = ref([{value: "my_runs", label: "my runs"}]);

const doGetData = async () => {
  await getInputData(stepParams.value.data, handleData);

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
        userGroupsForUser.value = [
          {value: "my_runs", label: "my runs"},
          {value: "Organizations", label: "Organizations", children: organizations},
          {value: "Projects", label: "Projects", children: projects}
        ];
      }
  );
};

const handleData = (data) => {
  if (data != null) {
    if (!Array.isArray(data)) {
      data = Object.values(data);
    }
    actions.value = null;
    tableRows.value = data;
    updateFilteredRows();
  }
  isLoading.value = false;
};

const init = async () => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  childTable.value = structuredClone(props.workflowStep);
  setOverwrittenTable();
};

const refresh = async () => {
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

const setOverwrittenTable = () => {
  const overriddenTableConfig = structuredClone(tableConfig);
  const actionsToRemove = [];
  
  // overwrite loading ESDL results params for loading results action
  const showResultsEsdlService = overriddenTableConfig.actions[0].next_step_config.service;
  showResultsEsdlService.id = uuidv4();  // set load esdl service id
  showResultsEsdlService.external_model = stepParams.value.config.external_model;
  showResultsEsdlService.result[0].model_short_name = stepParams.value.config.model_short_name;
  if (stepParams.value.config.result_animation) {
    showResultsEsdlService.result[0].animation = stepParams.value.config.result_animation;
  } else {
    delete showResultsEsdlService.result[0].animation;
  }
  if (stepParams.value.config.result_external_link) {
    showResultsEsdlService.result[0].external_link = stepParams.value.config.result_external_link;
  } else {
    delete showResultsEsdlService.result[0].external_link;
  }

  // check if feedback messages present for show feedback message action
  if (!stepParams.value.config.has_feedback_messages) {
    actionsToRemove.push(overriddenTableConfig.actions[1]);
  } else {
    overriddenTableConfig.actions[1].next_step_config.service.id = uuidv4();  // set load esdl service id
    overriddenTableConfig.actions[1].next_step_config.service.external_model = stepParams.value.config.external_model;
  }

  // check if time series download available and overwrite for download xlsx action
  if (stepParams.value.config.time_series_xlsx_download) {
    overriddenTableConfig.actions[4].next_step_config.data.from_config = stepParams.value.config.time_series_xlsx_download;
  } else {
    actionsToRemove.push(overriddenTableConfig.actions[4]);
  }

  // check if model delete url available and overwrite for delete model action
  if (stepParams.value.config.delete_result_url) {
    overriddenTableConfig.actions[5].next_step_config.data.from_config.delete_result_url = stepParams.value.config.delete_result_url;
  } else {
    delete overriddenTableConfig.actions[5].next_step_config.data.from_config.delete_result_url;
  }
  // Remove inactive actions
  overriddenTableConfig.actions = overriddenTableConfig.actions.filter(action => !actionsToRemove.includes(action));

  childTable.value.config = overriddenTableConfig;
  childTable.value.data.output_wrapper_variable = "model_run";
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
.ant-table table {
  font-size: 10px !important;
  line-height: 1.2 !important;
}
</style>
