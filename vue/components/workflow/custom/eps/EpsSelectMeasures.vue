<template>
  <p>Please select EPS measures to apply to the ESDL.</p>
  <a-checkbox-group v-model:value="value" name="measures" :options="plainOptions" />
  <br>
  <a-button type="primary" @click="doPost"> Run ESDL service </a-button>
</template>

<script setup="props">
import {defineProps, ref, watch} from "vue";
import {genericErrorHandler} from "../../../../utils/errors.js";
import {useWorkflow} from "../../../../composables/workflow.js";
// eslint-disable-next-line no-unused-vars
// eslint-disable-next-line no-unused-vars
import "@jsonforms/vue-vanilla/vanilla.css";

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const { getParamsFromState } = useWorkflow();
const workflowStep = props.workflowStep;

const plainOptions = ['LED', 'Isolatie (dak, gevel, glas)', 'Warmteterugwinning uit ventilatie', 'Warmtepomp', 'PV'];
const value = ref([...plainOptions]);

// eslint-disable-next-line no-unused-vars
const doPost = async () => {
  window.show_loader();

  const params = {
    remote_url: workflowStep.url,
  };

  try {
  } catch (e) {
    genericErrorHandler(e);
  } finally {
    window.hide_loader();
  }
};

watch(value,
    (value, prevValue) => {
      console.log(value);
      console.log(prevValue);
      if (value.includes('Warmtepomp') && !prevValue.includes('Warmtepomp')) {
        const warmtepompPreqs = ['Isolatie (dak, gevel, glas)', 'Warmteterugwinning uit ventilatie'];
        for (const preq of warmtepompPreqs) {
          if (!value.includes(preq)) {
            value.push(preq);
          }
        }
      }
      console.log(value);
    }
)
</script>



<style scoped>
.ant-checkbox-wrapper {
  display: block;
}
</style>
