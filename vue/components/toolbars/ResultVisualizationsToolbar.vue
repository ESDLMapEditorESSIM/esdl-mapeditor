<template>
  <div
    v-show="kpis_present || animation_possible"
    class="my-control leaflet-result-visualizations-toolbar"
  >
    <a-row type="flex" justify="space-between">
      <a-col>
        <span><b>Visualization Options</b></span>
      </a-col>
      <a-col :span="3">
        <a-button size="small" type="ghost" @click="handleDismiss">
          <close-outlined />
        </a-button>
      </a-col>
    </a-row>

    <a-row v-if="model_name!=null && calc_name!=null">
      <a-space direction="vertical" align="center">
        <span>For {{ model_name }} result: '{{ calc_name }}'</span>
      </a-space>
    </a-row>
    <br>
    <a-row>
      <a-space direction="vertical" align="center">
        <a-space>
          <a-button v-if="kpis_present" size="small" type="primary" @click="handleShowDashboard">
            Show KPI dashboard
          </a-button>
          <span v-else>No KPI's available</span>
        </a-space>

        <a-space-compact v-if="animation_possible" block size="small">
          <a-select
            ref="select"
            v-model:value="selected_field"
            style="width: 150px"
            :options="field_options"
            @focus="focus"
            @change="handleChange"
          />
          <a-button
            :disabled="selected_field === 'Choose field ...'"
            size="small"
            type="primary"
            @click="handleLoadAnimation"
          >
            Load animation
          </a-button>
        </a-space-compact>
        <a-space v-else-if="model_name!=null && calc_name!=null">
          <span>No animation available</span>
        </a-space>
      </a-space>
    </a-row>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {CloseOutlined} from '@ant-design/icons-vue';

const kpis_present = ref(false);
const animation_possible = ref(false);
const field_options = ref([]);
const selected_field = ref("Choose field ...");
const anim_esdl_id = ref(null);
const model_name = ref(null);
const calc_name = ref(null);

onMounted(() => {
  window.addEventListener('load', () => {
    // run after everything is in-place
    window.socket.on('kpis_present', function (data) {
      console.log('kpis_present:', data['es_id']);
      if (data['es_id'] !== anim_esdl_id.value) {  // remove animation info if new ESDL
        time_dimension.removeGeoJSONLayers();
        time_dimension.show_hide_animation_toolbar(false);
        animation_possible.value = false;
        anim_esdl_id.value = null;
        model_name.value = null;
        calc_name.value = null;
      }
      kpis_present.value = true;
    });
    window.socket.on('animation_esdl_data', function (data) {
      console.log('animation_possible, esdl id: ', data['es_id']);
      animation_possible.value = true;
      field_options.value = [];
      data['fields'].forEach((field) => {
        field_options.value.push(
            {
              value: field,
              label: field,
            }
        )
      });
      anim_esdl_id.value = data['es_id'];
      model_name.value = data['model_name'];
      calc_name.value = data['calc_name'];
    });
  });
});

const handleShowDashboard = () => {
  window.kpi_dashboard.open();
};
const handleLoadAnimation = () => {
  console.log("Results animation");
  // TODO simulation_id set to 'null' since we don't know the output mesido simulationRun, use for essim

  time_dimension.initialize(anim_esdl_id.value, null, [], selected_field.value);
};
const handleDismiss = () => {
  time_dimension.removeGeoJSONLayers();
  time_dimension.show_hide_animation_toolbar(false);
  kpis_present.value = false;
  animation_possible.value = false;
  anim_esdl_id.value = null;
  model_name.value = null;
  calc_name.value = null;
};
const handleChange = (value) => {
  console.log(`selected: ${value}`);
  selected_field.value = value;
};

</script>

<style>
.leaflet-result-visualizations-toolbar {
  padding: 5px;
  z-index: 2000;
  background: white;

  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
  border-radius: 5px;
}

.leaflet-result-visualizations-toolbar p {
  margin-bottom: 0;
}

</style>
