<template>
  <div v-for="(step, key) in workflowSteps" :key="key">
    <br v-if="step.name">
    <h3>{{ step.name }}</h3>
    <p>{{ step.description }}</p>

    <WorkflowChoice
      v-if="step.type === WorkflowStepTypes.CHOICE"
      :key="step.name"
      :workflow-step="step"
    />
    <WorkflowSelectQuery
      v-else-if="step.type === WorkflowStepTypes.SELECT_QUERY"
      :workflow-step="step"
    />
    <WorkflowTableQuery
      v-else-if="step.type === WorkflowStepTypes.TABLE_QUERY"
      :workflow-step="step"
    />
    <WorkflowEsdlService
      v-else-if="step.type === WorkflowStepTypes.ESDL_SERVICE"
      :workflow-step="step"
    />
    <WorkflowDownloadFile
      v-else-if="step.type === WorkflowStepTypes.DOWNLOAD_FILE"
      :workflow-step="step"
    />
    <WorkflowUploadFile
      v-else-if="step.type === WorkflowStepTypes.UPLOAD_FILE"
      :workflow-step="step"
    />
    <WorkflowHttpPost
      v-else-if="step.type === WorkflowStepTypes.HTTP_POST"
      :workflow-step="step"
    />
    <WorkflowProgress
      v-else-if="step.type === WorkflowStepTypes.PROGRESS"
      :workflow-step="step"
    />
    <WorkflowText
      v-else-if="step.type === WorkflowStepTypes.TEXT"
      :workflow-step="step"
    />
    <WorkflowEngineMonitor
      v-else-if="step.type === WorkflowStepTypes.ENGINE_MONITOR"
      :workflow-step="step"
    />
    <WorkflowCustomComponent
      v-else-if="step.type === WorkflowStepTypes.CUSTOM"
      :workflow-step="step"
    />
    <WorkflowCallJsFunction
      v-else-if="step.type === WorkflowStepTypes.CALL_JS_FUNCTION"
      :workflow-step="step"
    />
    <WorkflowJsonForm
      v-else-if="step.type === WorkflowStepTypes.JSON_FORM"
      :workflow-step="step"
    />
    <WorkflowJsonForm2
      v-else-if="step.type === WorkflowStepTypes.JSON_FORM2"
      :workflow-step="step"
    />
    <p v-else>
      Unknown workflow step: {{ step.type }}.
      <br>
    </p>
  </div>
</template>

<script setup="props">
import {ref, onMounted} from "vue";
import {useWorkflow, WorkflowStepTypes} from "@/composables/workflow";
import {default as WorkflowChoice} from "@/components/workflow/WorkflowChoice";
import {default as WorkflowSelectQuery} from "@/components/workflow/WorkflowSelectQuery";
import {default as WorkflowTableQuery} from "@/components/workflow/WorkflowTableQuery";
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

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const {getWorkflowStep} = useWorkflow();
const workflowSteps = ref([]);

onMounted(() => {
  init(true);
});

const init = () => {
  for (const stepIdOrRef of props.workflowStep.ids_or_refs) {
    workflowSteps.value.push(getWorkflowStep(stepIdOrRef));
  }
};
</script>
