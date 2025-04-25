<template>
  <div v-if="currentWorkflow" id="app">
    <div style="display: inline-block">
      <template v-if="currentWorkflow.hasPreviousStep()">
        <a-button
          type="link"
          @click="goToPreviousStep()"
        >
          <i class="fas fa-long-arrow-alt-left icon" />
        </a-button>
      </template>

      <a-dropdown>
        <a-button type="text" @click.prevent>
          <template #icon>
            <i class="fas fa-bars icon" />
          </template>
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item v-if="currentWorkflow.name" disabled>
              <strong>Name: {{ currentWorkflow.name }}</strong>
            </a-menu-item>
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
            <a-menu-item key="logState" @click="logState">Log workflow state</a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
      <span style="color: var(--gray); margin-left: 20px;">{{ activeEnergySystemTitle }}</span>
    </div>

    <template v-if="showPreviousSteps()">
      <a-breadcrumb
        separator=">"
      >
        <a-breadcrumb-item v-for="prevStep in currentWorkflow.prevWorkflowSteps" :key="prevStep.id">
          {{ prevStep.name }}
        </a-breadcrumb-item>
      </a-breadcrumb>
    </template>

    <hr>

    <h1>{{ currentWorkflow.service.name }}</h1>
    <br v-if="currentWorkflow.workflowStep.name">
    <h3>{{ currentWorkflow.workflowStep.name }}</h3>
    <p>{{ currentWorkflow.workflowStep.description }}</p>

    <WorkflowChoice
      v-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CHOICE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowSelect
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.SELECT"
      :key="currentWorkflow.workflowStep.name"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowTable
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.TABLE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowTableExternalModel
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.TABLE_EXTERNAL_MODEL"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowEsdlService
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.ESDL_SERVICE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowDownloadFile
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.DOWNLOAD_FILE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowUploadFile
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.UPLOAD_FILE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowHttpPost
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.HTTP_POST"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowProgress
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.PROGRESS"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowText
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.TEXT"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowEngineMonitor
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.ENGINE_MONITOR"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowCustomComponent
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CUSTOM"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowCallJsFunction
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.CALL_JS_FUNCTION"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowJsonForm
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.JSON_FORM"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowJsonForm2
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.JSON_FORM2"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowDataIO
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.GET_SEND_DATA"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <WorkflowCompositeStep
      v-else-if="currentWorkflow.workflowStep.type === WorkflowStepTypes.COMPOSITE"
      :workflow-step="currentWorkflow.workflowStep"
    />
    <p v-else>
      Unknown workflow step: {{ currentWorkflow.workflowStep.type }}.
      <br>
      <a-button type="dashed" @click="goToFirstStep()"> Start over.</a-button>
    </p>
  </div>
</template>

<script setup>
import {useWorkflow, WorkflowStepTypes} from "@/composables/workflow";
import {default as WorkflowChoice} from "@/components/workflow/WorkflowChoice";
import {default as WorkflowSelect} from "@/components/workflow/WorkflowSelect";
import {default as WorkflowTable} from "@/components/workflow/WorkflowTable";
import {default as WorkflowTableExternalModel} from "@/components/workflow/WorkflowTableExternalModel";
import {default as WorkflowEsdlService} from "@/components/workflow/WorkflowEsdlService";
import {default as WorkflowDownloadFile} from "@/components/workflow/WorkflowDownloadFile";
import {default as WorkflowUploadFile} from "@/components/workflow/WorkflowUploadFile";
import {default as WorkflowHttpPost} from "@/components/workflow/WorkflowHttpPost";
import {default as WorkflowProgress} from "@/components/workflow/WorkflowProgress";
import {default as WorkflowText} from "@/components/workflow/WorkflowText";
import {default as WorkflowEngineMonitor} from "@/components/workflow/WorkflowEngineMonitor.vue";
import {default as WorkflowCustomComponent} from "@/components/workflow/WorkflowCustomComponent";
import {default as WorkflowJsonForm} from "@/components/workflow/WorkflowJsonForm";
import {default as WorkflowJsonForm2} from "@/components/workflow/WorkflowJsonForm2";
import {default as WorkflowCallJsFunction} from "@/components/workflow/WorkflowCallJsFunction";
import {default as WorkflowCompositeStep} from "@/components/workflow/WorkflowCompositeStep.vue";
import WorkflowDataIO from "@/components/workflow/WorkflowDataIO.vue";
import {MenuOutlined} from "@ant-design/icons-vue";
import {MessageNames, PubSubManager} from "@/bridge";
import {useEsdlLayers} from "@/composables/esdlLayers";
import {ref} from "vue";
import EpsInitEnergyHub from "@/components/workflow/custom/eps/EpsInitEnergyHub.vue";

const {getActiveEsdlLayerId} = useEsdlLayers();

const {
  currentWorkflow,
  goToFirstStep,
  goToPreviousStep,
  persistWorkflow,
  savedWorkflows,
  loadSavedWorkflows,
  activatePersistedWorkflow,
  deletePersistedWorkflow,
  getState
} = useWorkflow();

const activeEnergySystemTitle = ref("Please select an energy system");
const activeEnergySystemId = ref("");
try {
  activeEnergySystemTitle.value = window.esdl_list[getActiveEsdlLayerId().value].title;
} catch (e) {
  // Skip.
}

PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, () => {
  activeEnergySystemTitle.value = window.esdl_list[getActiveEsdlLayerId().value].title;
  activeEnergySystemId.value = window.esdl_list[getActiveEsdlLayerId().value].id;
});

const confirmPersistWorkflow = () => {
  let workflowName = currentWorkflow.value.name;
  if (!workflowName) {
    workflowName = prompt("Please enter a workflow name")
  }
  if (workflowName) {
    currentWorkflow.value.setName(workflowName);
    currentWorkflow.value.setPersistence(true);
    persistWorkflow(true);
  }
};

const logState = () => {
  console.log("State:", getState());
  alert("See console for state.");
};

const showPreviousSteps = () => {
  const currentService = currentWorkflow.value.service;
  if ('hide_step_history' in currentService && currentService.hide_step_history === true) {
    return false;
  }
  return currentWorkflow.value.hasPreviousStep();
};

loadSavedWorkflows();

</script>
