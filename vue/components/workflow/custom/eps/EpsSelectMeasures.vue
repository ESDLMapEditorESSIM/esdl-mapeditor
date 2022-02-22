<template>
  <p>Please select EPS measures to apply to the ESDL.</p>
  <p>
    Please note that the "Warmtepomp" measure also implies all isolation measures, as well as "Warmteterugwinning uit
    ventilatie" and PV. Those cannot be deselected if "Warmtepomp" is selected.
  </p>
  <div>
    <a-checkbox
      v-model:checked="checkAll"
      :indeterminate="indeterminate"
      @change="onCheckAllChange"
    >
      Check all
    </a-checkbox>
  </div>
  <hr>
  <div id="eps-measures-checkbox-group">
    <a-checkbox-group v-model:value="selectedMeasures" name="measures" :options="plainOptions" />
  </div>
  <a-button type="primary" @click="loadEsdl"> Run ESDL service </a-button>
</template>

<script setup="props">
import {defineProps, ref, watch} from "vue";
import {useWorkflow} from "../../../../composables/workflow.js";
// eslint-disable-next-line no-unused-vars
import "@jsonforms/vue-vanilla/vanilla.css";
import {symDiff} from "../../../../utils/utils";

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

const indeterminate = ref(false);
const checkAll = ref(true);

const plainOptions = [EpsMeasures.LED, EpsMeasures.DAKISOLATIE, EpsMeasures.GEVELISOLATIE, EpsMeasures.GLASISOLATIE, EpsMeasures.WTW, EpsMeasures.WARMTEPOMP, EpsMeasures.PV];
const selectedMeasures = ref([...plainOptions]);

// eslint-disable-next-line no-unused-vars
const onCheckAllChange = (e) => {
  indeterminate.value = false;
  if (e.target.checked) {
    selectedMeasures.value = [...plainOptions];
  } else {
    selectedMeasures.value = []
  }
};

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

  window.show_loader();
  window.socket.emit("command", { cmd: "query_esdl_service", params: params });
};

const warmtepompPreqs = [EpsMeasures.DAKISOLATIE, EpsMeasures.GEVELISOLATIE, EpsMeasures.GLASISOLATIE, EpsMeasures.WTW];

watch(selectedMeasures,
    (newMeasures, oldMeasures) => {
      const isChecking = newMeasures.length > oldMeasures.length;
      const changedValue = symDiff(newMeasures, oldMeasures)[0];
      if (changedValue === EpsMeasures.WARMTEPOMP) {
          for (const preq of warmtepompPreqs) {
            if (isChecking) {
              if (!newMeasures.includes(preq)) {
                newMeasures.push(preq);
              }
            }
          }
      } else if (warmtepompPreqs.includes(changedValue)) {
        const idx = newMeasures.indexOf(EpsMeasures.WARMTEPOMP);
        if (idx > 0) {
          newMeasures.splice(idx, 1);
        }
      }
      indeterminate.value = !!newMeasures.length && newMeasures.length < plainOptions.length;
      checkAll.value = newMeasures.length === plainOptions.length;
    }
)
</script>

<style scoped>
hr {
  margin-top: 7px;
  margin-bottom: 7px;
}
button {
  margin-top: 7px;
}
</style>

<style>
#eps-measures-checkbox-group .ant-checkbox-group-item {
  display: block;
}
</style>

