<template>
  <p v-if="isLoading">Loading data ...</p>
  <a-form v-else layout="vertical" :model="form" :label-col="{ span: 0 }">
    <a-form-item :label="workflowStep.label">
      <a-button type="primary" :disabled="isLoading" :loading="isLoading" @click="doGetData">
        Reload
      </a-button>
      <a-table :columns="columns" 
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
            <li v-for="a in actions" :key="a.title">
              <a href="#" @click="doAction(record[rowkey], a.next_step)">{{ a.title }}</a>
            </li>
          </span>
        </template>
        <template #tags="{ record, column }">
          <a-tag :color="getTagColor(record[column.dataIndex])">{{ record[column.dataIndex] }}</a-tag>
        </template>
      </a-table>
    </a-form-item>
    <!-- <a-form-item>
      <a-button type="primary" @click="onSubmit"> Select </a-button>
    </a-form-item> -->
  </a-form>
</template>

<script setup="props">


/*
This Workflow step shows a table from a REST query and allows you to specify actions (next workflow steps) based on what the user selects in the action column

Syntax for WorkflowTableQuery.

"workflow": [
			{
				"name": "Results overview",
				"description": "",
				"type": "table-query",
				"source": {
					"url": "http://localhost:9200/job/",
					"http_method": "get",
          "request_params": {"username": "session.email"},  // add extra request params. session.* are handled in the backend
					"columns": [                           //  columns is based on antdv 2.0 column syntax.
						{
							"dataIndex": "job_name",           // dataIndex is required, links to the attribute in the REST result json
							"title": "Name",                   // also required, used as column title
							"key": "job_name",                 // give this column a specific key. Not required currently
							"ellipsis": true                   // see AntDV: longer text gets abbreviated with ...
						},
						{
							"dataIndex": "status",
							"title": "Status",
							"key": "status",
							"slots": {                        // use a specific template to render this column. Two are currently supported: tags and actions (for action column)
								"customRender": "tags"
							}
						},
						{
							"dataIndex": "stopped_at",
							"title": "Finished at",
							"key": "stopped_at",
							"formatter": "formatDate",          // special attribute for this component: formatter links to a javascript function in this class
              "sortOrder": "descend"             // formatDate also contains sorting of column
						}
					],
					"actions": [                           // Defines the actions that can be done on the column
						{
							"title": "Load result",            // title of the action
							"next_step": 2                     // when button is clicked, the workflow moves to this step (e.g. call ESDL Service).
						},
						{
							"title": "Show log",
							"next_step": 3
						}
					],
					"value_field": "job_id"               // the uniqe key to identify each row, and is stored in the state (using target_variable)
				},
				"target_variable": "job",
				"next_step": 1                         // default next step (not used)
			},

*/

import { defineProps, ref } from "vue";
import { useWorkflow } from "../../composables/workflow.js";
import { workflowGetData } from "./utils/api.js";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;

const isLoading = ref(true);
const form = {};
form[workflowStep.target_variable] = "";

const { getParamsFromState, goToStep, getState } = useWorkflow();
const state = getState();
const columns = ref([]);
const rowkey = ref("");
const actions = ref([]);
const dataSource = ref([]);


// eslint-disable-next-line no-unused-vars
const pagination = ref({ "position": 'bottom', "hideOnSinglePage": true, "defaultPageSize": 9 })

const formatDate = (row) => {
  if (row.text !== undefined && row.text != null) {
    let d = new Date(row.text);
    return d.toLocaleString('nl-NL'); // return VNode
  }
  return row.text;
}

// eslint-disable-next-line no-unused-vars
const getTagColor = (text) => {
  let up = text.toUpperCase();
  if (up === "FINISHED" || up === "SUCCESS" || up === "OK" || up === "READY") {
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
}

// eslint-disable-next-line no-unused-vars
const doAction = (job_id, next_step) => {
  console.log('Action selected: ', job_id, next_step);  
  state[workflowStep.target_variable] = {};
  state[workflowStep.target_variable][rowkey.value] = job_id;
  goToStep(next_step);
}

const doGetData = async () => {
  const request_params = getParamsFromState(workflowStep.source.request_params);
  const data = await workflowGetData(workflowStep.source.url, request_params)
  // if (data == null) {
  //   alert("No data received.");
  //   return;
  // }
  if (data != null) {
    const source = workflowStep.source;
    // process defined columns in workflow config
    // column syntax follows AntDV table column definition.
    source.columns.forEach((column) => {
      if (column.formatter) {  // special property for this component
        if (column.formatter == 'formatDate') {
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
    dataSource.value = data;

  }
  isLoading.value = false;
}
doGetData();
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
</style>
