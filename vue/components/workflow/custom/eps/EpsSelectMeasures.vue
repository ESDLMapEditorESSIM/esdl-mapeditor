<template>
  <p>Please select EPS measures to apply to the ESDL.</p>
  <a-checkbox-group v-model:value="selectedMeasures" name="measures" :options="plainOptions" />
  <br>
  <a-button type="primary" @click="loadEsdl"> Run ESDL service </a-button>
</template>

<script setup="props">
import {defineProps, ref, watch} from "vue";
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

const EpsMeasures = Object.freeze({
    DAKISOLATIE: "Dakisolatie",
    GEVELISOLATIE: "Gevelisolatie",
    GLASISOLATIE: "Glasisolatie",
    WTW: "Warmteterugwinning uit ventilatie",
    LED: "LED",
    WARMTEPOMP: "Warmtepomp",
    PV: "PV",
});

const plainOptions = [EpsMeasures.LED, EpsMeasures.DAKISOLATIE, EpsMeasures.GEVELISOLATIE, EpsMeasures.GLASISOLATIE, EpsMeasures.WTW, EpsMeasures.WARMTEPOMP, EpsMeasures.PV];
const selectedMeasures = ref([...plainOptions]);

// eslint-disable-next-line no-unused-vars
const loadEsdl = () => {
  const params = {};
  params["service_id"] = workflowStep.service.id;

  if (workflowStep["state_params"]) {
    params["query_parameters"] = getParamsFromState(workflowStep["state_params"]);
  } else {
    params["query_parameters"] = {};
  }

  params["query_parameters"]['isolation_roof'] = selectedMeasures.value.includes(EpsMeasures.DAKISOLATIE);
  params["query_parameters"]['isolation_facade'] = selectedMeasures.value.includes(EpsMeasures.GEVELISOLATIE);
  params["query_parameters"]['isolation_glass'] = selectedMeasures.value.includes(EpsMeasures.GLASISOLATIE);
  params["query_parameters"]['wtw'] = selectedMeasures.value.includes(EpsMeasures.WTW);
  params["query_parameters"]['led'] = selectedMeasures.value.includes(EpsMeasures.LED);
  params["query_parameters"]['heat_pump'] = selectedMeasures.value.includes(EpsMeasures.WARMTEPOMP);
  params["query_parameters"]['pv'] = selectedMeasures.value.includes(EpsMeasures.PV);
  console.log(params);

  window.show_loader();
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
};

watch(selectedMeasures,
    (value) => {
      if (value.includes('Warmtepomp')) {
        const warmtepompPreqs = [EpsMeasures.DAKISOLATIE, EpsMeasures.GEVELISOLATIE, EpsMeasures.GLASISOLATIE, EpsMeasures.WTW];
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
