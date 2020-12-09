<template>
  <div id="app">
    <h1>{{ currentWorkflow.service.name }}</h1>
    <h3>{{ currentWorkflow.workflowStep.name }}</h3>
    <p>{{ currentWorkflow.workflowStep.description }}</p>
    <WorkflowChoice
      v-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CHOICE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowSelectQuery
      v-else-if="
        currentWorkflow.workflowStep.type === WorkflowStepTypes.SELECT_QUERY
      "
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
    <WorkflowCustomComponent
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CUSTOM"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <p v-else>
      Unknown workflow step: {{ currentWorkflow.workflowStep.type }}.
      <br>
      <a-button type="dashed" @click="goToStep(0)"> Start over. </a-button>
    </p>

    <a-button
      v-if="currentWorkflow.workflowStep.previous_step"
      type="dashed"
      @click="goToPreviousStep()"
    >
      Previous
    </a-button>
  </div>
</template>

<script>
import { useWorkflow, WorkflowStepTypes } from "../composables/workflow";
import { default as WorkflowChoice } from "../components/workflow/WorkflowChoice";
import { default as WorkflowSelectQuery } from "../components/workflow/WorkflowSelectQuery";
import { default as WorkflowEsdlService } from "../components/workflow/WorkflowEsdlService";
import { default as WorkflowDownloadFile } from "../components/workflow/WorkflowDownloadFile";
import { default as WorkflowUploadFile } from "../components/workflow/WorkflowUploadFile";
import { default as WorkflowHttpPost } from "../components/workflow/WorkflowHttpPost";
import { default as WorkflowProgress } from "../components/workflow/WorkflowProgress";
import { default as WorkflowCustomComponent } from "../components/workflow/WorkflowCustomComponent";

export default {
  setup() {
    const { currentWorkflow, goToStep, goToPreviousStep } = useWorkflow();
    return {
      currentWorkflow,
      goToStep,
      goToPreviousStep,
      WorkflowStepTypes,
      WorkflowUploadFile,
      WorkflowHttpPost,
      WorkflowCustomComponent,
      WorkflowChoice,
      WorkflowSelectQuery,
      WorkflowEsdlService,
      WorkflowProgress,
      WorkflowDownloadFile,
    };
  },
};
</script>
