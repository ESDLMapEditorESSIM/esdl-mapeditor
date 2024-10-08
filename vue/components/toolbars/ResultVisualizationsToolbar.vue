<template>
  <div
    v-show="kpis_present || animation_possible || external_link_description!=null"
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
        </a-space>
        <a-space>
          <a-button
            v-if="external_link_description!=null" size="small" type="primary"
            @click="handleShowExternalLink"
          >
            {{ external_link_description }}
          </a-button>
        </a-space>
        <a-space-compact v-if="animation_possible" block size="small">
          <a-select
            ref="select"
            v-model:value="anim_selected_field"
            style="width: 150px"
            :options="anim_field_options"
            @change="handleChange"
          />
          <a-button
            :disabled="anim_selected_field === 'Choose field ...'"
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
const anim_field_options = ref([]);
const anim_selected_field = ref("Choose field ...");
const esdl_id = ref(null);
const anim_filter_tag_name = ref(null);
const anim_filter_tag_value = ref(null);
const anim_influxdb_host_override = ref(null);
const model_name = ref(null);
const calc_name = ref(null);
const external_link_description = ref(null);
const external_link_url = ref(null);

onMounted(() => {
  window.addEventListener('load', () => {
    // run after everything is in-place
    window.socket.on('kpis_present', function (data) {
      console.log('kpis_present:', data['es_id']);
      setEsdlId(data['es_id']);
      kpis_present.value = true;
    });
    window.socket.on('animation_esdl_data', function (data) {
      console.log('animation_esdl_data, esdl id: ', data['es_id']);
      setEsdlId(data['es_id']);
      animation_possible.value = true;
      anim_field_options.value = [];
      data['fields'].forEach((field) => {
        anim_field_options.value.push(
            {
              value: field,
              label: field,
            }
        );
      });
      model_name.value = data['model_name'];
      calc_name.value = data['calc_name'];
      anim_filter_tag_name.value = data["filter_tag_name"];
      anim_filter_tag_value.value = data["filter_tag_value"];
      anim_influxdb_host_override.value = data["influxdb_host_override"];
    });
    window.socket.on('results_external_link', function (data) {
      console.log('results_external_link:', data);
      setEsdlId(data['es_id']);
      external_link_description.value = data["description"]
      external_link_url.value = data["url"]
    });
  });
});

const handleShowDashboard = () => {
  window.kpi_dashboard.open();
};

const handleShowExternalLink = () => {
  window.open(external_link_url.value, '_blank');
};

const handleLoadAnimation = () => {
  console.log("Results animation", anim_filter_tag_value.value);
  time_dimension.initialize(
      esdl_id.value, anim_filter_tag_name.value, anim_filter_tag_value.value, [], anim_selected_field.value, anim_influxdb_host_override.value
  );
};

const handleDismiss = () => {
  clearData();
};

const handleChange = (value) => {
  console.log(`selected: ${value}`);
  anim_selected_field.value = value;
};

const setEsdlId = (new_esdl_id) => {
  if (new_esdl_id !== esdl_id.value) {  // remove data info if new ESDL
    clearData();
    esdl_id.value = new_esdl_id;
  }
}

const clearData = () => {
  time_dimension.removeGeoJSONLayers();
  time_dimension.show_hide_animation_toolbar(false);
  kpis_present.value = false;
  animation_possible.value = false;
  anim_selected_field.value = "Choose field ...";
  anim_filter_tag_name.value = null;
  anim_filter_tag_value.value = null;
  anim_influxdb_host_override.value = null;
  esdl_id.value = null;
  model_name.value = null;
  calc_name.value = null;
  external_link_description.value = null;
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
