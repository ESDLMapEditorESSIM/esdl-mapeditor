<template>
  <CodeEditor
    ref="editor"
    v-model="code"
    :language="language"
    :rows="25"
    :update-on-input="true"
    :format-on-blur="true"
    @validate="onValidate"
  />
  <a-button
    v-if="stepParams.nextStepTrigger === WorkflowNextStepTriggerOptions.BUTTON_CLICK && stepParams.buttonText"
    type="primary"
    @click="onSubmit"
  >
    {{ stepParams.buttonText }}
  </a-button>
</template>

<script setup>
import {ref, onMounted, onUnmounted, watch} from 'vue';
import {useWorkflow, WorkflowNextStepTriggerOptions} from '@/composables/workflow';
import YAML from 'js-yaml';
import {XMLParser} from 'fast-xml-parser';
import {default as CodeEditor} from '@/components/forms/CodeEditor.vue';

const props = defineProps({
  workflowStep: {type: Object, default: null, required: true},
});

/** @type {import('vue').Ref<StepParameters|null>} */
const stepParams = ref({});
const nrOfRows = ref(20);
let subscriptionId = null;
const code = ref("");
const language = ref("");

const {getWorkflowStepParameters, getInputData, setWorkflowStepInputValid, sendOutputData, goToStep} = useWorkflow();

const updateData = (data, reset = false) => {
  if (!reset) return;

  code.value = data ? JSON.stringify(convertArrayLikeObject(data), null, 2) : '';
  language.value = stepParams.value.config.language;
  if (stepParams.value.config.number_of_rows) {
    nrOfRows.value = stepParams.value.config.number_of_rows;
  }
};

const onValidate = (validation) => {
  setWorkflowStepInputValid(stepParams.value.id, validation.valid);
};

const convertArrayLikeObject = (obj) => {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return obj;
  const keys = Object.keys(obj).map(Number).sort((a, b) => a - b);
  if (!keys.every((k, i) => k === i)) return obj;
  return keys.map(k => obj[k]);
};

const onSubmit = async () => {
  let dataToSend = code.value;

  try {
    switch (language.value) {
      case 'json':
        dataToSend = JSON.parse(code.value);
        break;

      case 'yaml':
        dataToSend = YAML.load(code.value);
        break;

      case 'xml':
        dataToSend = new XMLParser({ ignoreAttributes: false }).parse(code.value);
        break;

      // other languages remain as string
      default:
        dataToSend = code.value;
        break;
    }
  } catch (e) {
    console.error(`Invalid ${language.value} content, cannot submit:`, e);
    return;
  }
  await sendOutputData(stepParams.value.data, dataToSend, afterSendOutput);
};

const afterSendOutput = () => {
  goToStep(stepParams.value.nextStep);
};

watch(code, () => {
  if (stepParams.value.nextStepTrigger === WorkflowNextStepTriggerOptions.INPUT_CHANGE) {
    onSubmit();
  }
});

onMounted(async () => {
  await init(true);
  watch(props.workflowStep.workflowTrigger, () => {
    init();
  });
});

const init = async (reset = false) => {
  stepParams.value = getWorkflowStepParameters(props.workflowStep);
  await getInputData(stepParams.value.data, (data) => updateData(data, reset));
};

onUnmounted(() => {
  if (subscriptionId !== null) {
    PubSubManager.unsubscribe(subscriptionId);
  }
});
</script>

<style scoped>
</style>
