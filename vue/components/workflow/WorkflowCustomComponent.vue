<template>
  <div>
    <component
      :is="current"
      :workflow-step="workflowStep"
    />
  </div>
</template>

<script setup="props">
import {default as WorkflowEpsInspectResult} from './custom/eps/WorkflowEpsInspectResult';
import {default as WorkflowEpsService} from './custom/eps/WorkflowEpsService';
import {default as EpsCreateProject} from './custom/eps/EpsCreateProject';
import {default as EpsSelectMeasures} from './custom/eps/EpsSelectMeasures';
import {default as EpsCustomMeasures} from './custom/eps/EpsCustomMeasures';
import {default as DiceExportEssim} from './custom/dice/DiceExportESSIM';
import {default as DiceGenerateProfileTemplate} from './custom/dice/DiceGenerateProfileTemplate';
import {default as DiceUploadProfiles} from './custom/dice/DiceUploadProfiles';
import {defineProps} from 'vue'

const components = {
  "eps-inspect-result": WorkflowEpsInspectResult,
  "eps-service": WorkflowEpsService,
  "eps-create-project": EpsCreateProject,
  "eps-select-measures": EpsSelectMeasures,
  "eps-custom-measures": EpsCustomMeasures,
  "dice-export-essim": DiceExportEssim,
  "dice-generate-profile-template": DiceGenerateProfileTemplate,
  "dice-upload-profiles": DiceUploadProfiles,
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
