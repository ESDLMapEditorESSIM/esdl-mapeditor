<template>
  <div v-if="currentWorkflow" id="app">
    <div style="display: inline-block">
      <template v-if="currentWorkflow.hasPreviousStep()">
        <a-button
          type="link"
          @click="goToPreviousStep()"
        >
          <i class="fas fa-long-arrow-alt-left small-icon" />
        </a-button>
      </template>

      <a-dropdown>
        <a class="ant-dropdown-link" @click.prevent>
          <a-button type="text" @click.prevent>
            <template #icon>
              <MenuOutlined />
            </template>
          </a-button>
        </a>
        <template #overlay>
          <a-menu>
            <a-menu-item v-if="currentWorkflow.name" disabled><strong>Name: {{ currentWorkflow.name }}</strong></a-menu-item>
            <a-menu-item key="setname" disabled>Set workflow name</a-menu-item>
            <a-menu-item key="save" @click="confirmPersistWorkflow">Save</a-menu-item>
            <a-sub-menu key="load" title="Load workflow">
              <a-menu-item
                v-for="workflow in savedWorkflows"
                :key="workflow.uuid"
                @click="activatePersistedWorkflow(workflow.uuid)"
              >
                {{ workflow.name }}
              </a-menu-item>
            </a-sub-menu>
            <a-sub-menu key="delete" title="Delete workflow">
              <a-menu-item
                v-for="workflow in savedWorkflows"
                :key="workflow.uuid"
                @click="deletePersistedWorkflow(workflow.uuid)"
              >
                {{ workflow.name }}
              </a-menu-item>
            </a-sub-menu>
          </a-menu>
        </template>
      </a-dropdown>
    </div>

    <template v-if="currentWorkflow.hasPreviousStep()">
      <a-breadcrumb
        separator=">"
      >
        <a-breadcrumb-item v-for="prevStep in currentWorkflow.prevWorkflowSteps" :key="prevStep.id">{{ prevStep.name }}</a-breadcrumb-item>
      </a-breadcrumb>
    </template>

    <hr>

    <h1>{{ currentWorkflow.service.name }}</h1>
    <h3>{{ currentWorkflow.workflowStep.name }}</h3>
    <p>{{ currentWorkflow.workflowStep.description }}</p>

    <WorkflowChoice
      v-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CHOICE"
      :key="currentWorkflow.workflowStep.name"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowSelectQuery
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.SELECT_QUERY
      "
      :key="currentWorkflow.workflowStep.name"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowEsdlService
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.ESDL_SERVICE
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowDownloadFile
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.DOWNLOAD_FILE
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowUploadFile
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.UPLOAD_FILE
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowHttpPost
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.HTTP_POST
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowProgress
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.PROGRESS
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowText
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.TEXT
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowCustomComponent
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CUSTOM"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowJsonForm
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.JSON_FORM
      "
      :workflow-step="currentWorkflow.workflowStep"
    />
    <p v-else>
      Unknown workflow step: {{ currentWorkflow.workflowStep.type }}.
      <br>
      <a-button type="dashed" @click="goToFirstStep()"> Start over. </a-button>
    </p>
  </div>
</template>

<script>
import {currentWorkflow, useWorkflow, WorkflowStepTypes} from "../composables/workflow";
import {default as WorkflowChoice} from "../components/workflow/WorkflowChoice";
import {default as WorkflowSelectQuery} from "../components/workflow/WorkflowSelectQuery";
import {default as WorkflowEsdlService} from "../components/workflow/WorkflowEsdlService";
import {default as WorkflowDownloadFile} from "../components/workflow/WorkflowDownloadFile";
import {default as WorkflowUploadFile} from "../components/workflow/WorkflowUploadFile";
import {default as WorkflowHttpPost} from "../components/workflow/WorkflowHttpPost";
import {default as WorkflowProgress} from "../components/workflow/WorkflowProgress";
import {default as WorkflowText} from "../components/workflow/WorkflowText";
import {default as WorkflowCustomComponent} from "../components/workflow/WorkflowCustomComponent";
import {default as WorkflowJsonForm} from "../components/workflow/WorkflowJsonForm";
import {MenuOutlined} from "@ant-design/icons-vue";

export default {
  setup() {
    const { currentWorkflow, goToFirstStep, goToPreviousStep, persistWorkflow, savedWorkflows, loadSavedWorkflows, activatePersistedWorkflow, deletePersistedWorkflow } = useWorkflow();

    function confirmPersistWorkflow() {
      let workflowName = currentWorkflow.value.name;
      if (!workflowName) {
        workflowName = prompt("Please enter a workflow name")
      }
      if (workflowName) {
        currentWorkflow.value.setName(workflowName);
        currentWorkflow.value.setPersistence(true);
        persistWorkflow(true);
      }
    }

    loadSavedWorkflows();

    return {
      MenuOutlined,
      confirmPersistWorkflow,
      currentWorkflow,
      goToFirstStep,
      goToPreviousStep,
      WorkflowStepTypes,
      WorkflowUploadFile,
      WorkflowHttpPost,
      WorkflowCustomComponent,
      WorkflowChoice,
      WorkflowSelectQuery,
      WorkflowEsdlService,
      WorkflowProgress,
      WorkflowText,
      WorkflowDownloadFile,
      WorkflowJsonForm,
      savedWorkflows,
      activatePersistedWorkflow,
      deletePersistedWorkflow,
    };
  },
};
</script>
