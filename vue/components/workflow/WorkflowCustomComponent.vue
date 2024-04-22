<template>
  <div>
    <component
      :is="current"
      :workflow-step="workflowStep"
    />
  </div>
</template>

<script setup="props">
import {default as WorkflowEpsInspectResult} from './custom/eps/WorkflowEpsInspectResult.vue';
import {default as WorkflowEpsService} from './custom/eps/WorkflowEpsService.vue';
import {default as EpsCreateProject} from './custom/eps/EpsCreateProject.vue';
import {default as EpsSelectMeasures} from './custom/eps/EpsSelectMeasures.vue';
import {default as EpsCustomMeasures} from './custom/eps/EpsCustomMeasures.vue';
import {default as DiceExportEssim} from './custom/dice/DiceExportESSIM.vue';
import {default as DiceGenerateProfileTemplate} from './custom/dice/DiceGenerateProfileTemplate.vue';
import {default as DiceUploadProfiles} from './custom/dice/DiceUploadProfiles.vue';
import {default as DemoCustomComponent} from './custom/DemoCustomComponent.vue';
import {default as WorkflowFlexScanInspectPhase1} from './custom/flexscan/WorkflowFlexScanInspectPhase1.vue';
import {default as WorkflowFlexScanImportEPS} from './custom/flexscan/WorkflowFlexScanImportEPS.vue';

const components = {
  "eps-inspect-result": WorkflowEpsInspectResult,
  "eps-service": WorkflowEpsService,
  "eps-create-project": EpsCreateProject,
  "eps-select-measures": EpsSelectMeasures,
  "eps-custom-measures": EpsCustomMeasures,
  "dice-export-essim": DiceExportEssim,
  "dice-generate-profile-template": DiceGenerateProfileTemplate,
  "dice-upload-profiles": DiceUploadProfiles,
  "flexscan-inspect-phase1": WorkflowFlexScanInspectPhase1,
  "flexscan-import-eps": WorkflowFlexScanImportEPS,
  "demo-custom": DemoCustomComponent,
};
const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const workflowStep = props.workflowStep;
// The current custom component.
// eslint-disable-next-line no-unused-vars
const current = components[workflowStep.component];

</script>
