<template>
  <div>
    <component
      :is="current"
      :workflow-step="workflowStep"
    />
  </div>
</template>

<script setup="props">
import {default as WorkflowEpsInspectResult} from './custom/pdtoolsuite/eps/WorkflowEpsInspectResult.vue';
import {default as WorkflowEpsService} from './custom/pdtoolsuite/eps/WorkflowEpsService.vue';
import {default as EpsCreateProject} from './custom/pdtoolsuite/eps/EpsCreateProject.vue';
import {default as EpsSelectMeasures} from './custom/pdtoolsuite/eps/EpsSelectMeasures.vue';
import {default as EpsCustomMeasures} from './custom/pdtoolsuite/eps/EpsCustomMeasures.vue';
import {default as PDToolsuiteGenerateProfileTemplate} from './custom/pdtoolsuite/PDToolsuiteGenerateProfileTemplate.vue';
import {default as PDToolsuiteUploadProfiles} from './custom/pdtoolsuite/PDToolsuiteUploadProfiles.vue';
import {default as DemoCustomComponent} from './custom/DemoCustomComponent.vue';
import {default as WorkflowFlexScanInspectPhase1} from './custom/pdtoolsuite/flexscan/WorkflowFlexScanInspectPhase1.vue';
import {default as WorkflowFlexScanImportEPS} from './custom/pdtoolsuite/flexscan/WorkflowFlexScanImportEPS.vue';
import {default as PDToolsuiteInitEnergyHub} from "@/components/workflow/custom/pdtoolsuite/PDToolsuiteInitEnergyHub.vue";
import {default as PDToolsuiteHeatNetworkPlan} from "@/components/workflow/custom/pdtoolsuite/PDToolsuiteHeatNetworkPlan.vue";
import {default as CostInformationGenerateTemplate} from './custom/pdtoolsuite/cost-information/CostInformationGenerateTemplate.vue';
import {default as CostInformationUploadTemplate} from './custom/pdtoolsuite/cost-information/CostInformationUploadTemplate.vue';

const components = {
  "eps-inspect-result": WorkflowEpsInspectResult,
  "eps-service": WorkflowEpsService,
  "eps-create-project": EpsCreateProject,
  "eps-select-measures": EpsSelectMeasures,
  "eps-custom-measures": EpsCustomMeasures,
  "pdtoolsuite-init-energy-hub": PDToolsuiteInitEnergyHub,
  "pdtoolsuite-heat-network-plan": PDToolsuiteHeatNetworkPlan,
  "pdtoolsuite-generate-profile-template": PDToolsuiteGenerateProfileTemplate,
  "pdtoolsuite-upload-profiles": PDToolsuiteUploadProfiles,
  "flexscan-inspect-phase1": WorkflowFlexScanInspectPhase1,
  "flexscan-import-eps": WorkflowFlexScanImportEPS,
  "demo-custom": DemoCustomComponent,
  "cost-information-generate-template": CostInformationGenerateTemplate,
  "cost-information-upload-template": CostInformationUploadTemplate,
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
