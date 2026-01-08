<template>
  <div v-for="(step, key) in workflowSteps" :key="key">
    <br v-if="step.name">
    <h3>{{ step.name }}</h3>
    <!-- eslint-disable vue/no-v-html (sanitized with DOMPurify) -->
    <p v-html="DOMPurify.sanitize(step.description, {ADD_ATTR: ['target', 'rel']})" />

    <WorkflowChoice
      v-if="step.type === WorkflowStepTypes.CHOICE"
      :key="step.name"
      :workflow-step="step"
    />
    <WorkflowSelect
      v-else-if="step.type === WorkflowStepTypes.SELECT"
      :workflow-step="step"
    />
    <WorkflowTable
      v-else-if="step.type === WorkflowStepTypes.TABLE"
      :workflow-step="step"
    />
    <WorkflowTableExternalModel
      v-else-if="step.type === WorkflowStepTypes.TABLE_EXTERNAL_MODEL"
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
    <WorkflowDataIO
      v-else-if="step.type === WorkflowStepTypes.GET_SEND_DATA"
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
import {default as WorkflowDataIO} from "@/components/workflow/WorkflowDataIO";
import DOMPurify from "dompurify";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const {getWorkflowStepParameters, getWorkflowStep} = useWorkflow();
const workflowSteps = ref([]);

onMounted(() => {
  init();
});

const init = () => {
  for (const stepIdOrRef of getWorkflowStepParameters(props.workflowStep).config.step_ids) {
    workflowSteps.value.push(getWorkflowStep(stepIdOrRef));
  }
};
</script>

<style scoped>
</style>