<template>
  <div
    v-if="activeEsdlVisualizationAvailable()"
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
    <a-row v-if="activeEsdlParams.message!=null">
      <a-space direction="vertical" align="center">
        <span style="width: 250px; display: inline-block; word-break: break-all;">{{ activeEsdlParams.message }}</span>
      </a-space>
    </a-row>
    <br>
    <a-row>
      <a-space direction="vertical" align="center">
        <a-space>
          <a-button v-if="activeEsdlParams.kpis_present" size="small" type="primary" @click="handleShowDashboard">
            Show KPI dashboard
          </a-button>
        </a-space>
        <a-space>
          <a-button
            v-if="activeEsdlParams.external_link_description!=null" size="small" type="primary"
            @click="handleShowExternalLink"
          >
            {{ activeEsdlParams.external_link_description }}
          </a-button>
        </a-space>
        <a-space-compact v-if="activeEsdlParams.animation_possible" block size="small">
          <a-select
            ref="select"
            v-model:value="activeEsdlParams.anim_selected_field"
            style="width: 150px"
            :options="activeEsdlParams.anim_field_options"
            @change="handleChange"
          />
          <a-button
            :disabled="activeEsdlParams.anim_selected_field === 'Choose field ...'"
            size="small"
            type="primary"
            @click="handleLoadAnimation"
          >
            Load animation
          </a-button>
        </a-space-compact>
      </a-space>
    </a-row>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {CloseOutlined} from '@ant-design/icons-vue';
import {MessageNames, PubSubManager} from "@/bridge";
import {useEsdlLayers} from "@/composables/esdlLayers";

const {getActiveEsdlLayerId} = useEsdlLayers();

class VisualParams {
  constructor(esdl_id) {
    this.esdl_id = esdl_id;
    this.kpis_present = false;
    this.animation_possible = false;
    this.anim_selected_field = "Choose field ...";
    this.anim_filter_tag_name = null;
    this.anim_filter_tag_value = null;
    this.message = null;
    this.external_link_url = null;
    this.external_link_description = null;
  }
}

/**  @type {import('vue').Ref<Record<string, VisualParams>>} */
const paramsPerEsdl = ref({});
/**  @type {import('vue').Ref<VisualParams>} */
const activeEsdlParams = ref(null);

onMounted(() => {
  window.addEventListener('load', () => {
    // run after everything is in-place
    window.socket.on('clear_visualization_options', function () {
      console.log('clear_visualization_options');
      clearData();
    });

    window.socket.on('kpis', function (data) {
      console.log('kpis_present:', data['es_id']);
      setActiveEsdlParams(data['es_id']);

      activeEsdlParams.value.kpis_present = true;
      // kpis are always loaded with general ESDL id, message, don't overwrite
      if (activeEsdlParams.value.message === null) {
        activeEsdlParams.value.message = data['message'];
      }
    });
    window.socket.on('animation_esdl_data', function (data) {
      console.log('animation_esdl_data, esdl id: ', data['es_id']);
      setActiveEsdlParams(data['es_id']);
      activeEsdlParams.value.animation_possible = true;
      activeEsdlParams.value.anim_field_options = [];
      data['fields'].forEach((field) => {
        activeEsdlParams.value.anim_field_options.push(
            {
              value: field,
              label: field,
            }
        );
      });
      activeEsdlParams.value.message = data['message'];
      activeEsdlParams.value.anim_filter_tag_name = data["filter_tag_name"];
      activeEsdlParams.value.anim_filter_tag_value = data["filter_tag_value"];
    });
    window.socket.on('results_external_link', function (data) {
      console.log('results_external_link:', data['es_id']);
      setActiveEsdlParams(data['es_id']);
      activeEsdlParams.value.message = data['message'];
      activeEsdlParams.value.external_link_description = data["description"];
      activeEsdlParams.value.external_link_url = data["url"];
    });
  });
});

const setActiveEsdlParams = (esdl_id) => {
  if (activeEsdlParams.value !== null && esdl_id === activeEsdlParams.value.esdl_id) {
    return;
  }
  if (!(esdl_id in paramsPerEsdl.value)) {
    paramsPerEsdl.value[esdl_id] = new VisualParams(esdl_id);
  }
  activeEsdlParams.value = paramsPerEsdl.value[esdl_id];
};

const activeEsdlVisualizationAvailable = () => {
  if (activeEsdlParams.value !== null) {
    if (activeEsdlParams.value.kpis_present || activeEsdlParams.value.animation_possible || activeEsdlParams.value.external_link_description != null) {
      return true;
    }
  }
  return false;
};

PubSubManager.subscribe(MessageNames.SELECT_ACTIVE_LAYER, (name, message) => {
  const esdl_id = message.active_layer_id;
  if (activeEsdlParams.value !== null && esdl_id === activeEsdlParams.value.esdl_id) {
    return;
  }
  clearData();
  setActiveEsdlParams(window.esdl_list[getActiveEsdlLayerId().value].id);
});

PubSubManager.subscribe(MessageNames.REMOVE_LAYER, (name, message) => {
  const esdl_id = message.removed_layer_id;
  delete paramsPerEsdl.value[esdl_id];
  clearData();
});

const handleShowDashboard = () => {
  window.kpi_dashboard.open();
};

const handleShowExternalLink = () => {
  window.open(activeEsdlParams.value.external_link_url, '_blank');
};

const handleLoadAnimation = () => {
  time_dimension.initialize(
      activeEsdlParams.value.esdl_id,
      activeEsdlParams.value.anim_filter_tag_name,
      activeEsdlParams.value.anim_filter_tag_value,
      [],
      activeEsdlParams.value.anim_selected_field
  );
};

const handleDismiss = () => {
  clearData();
};

const handleChange = (value) => {
  activeEsdlParams.value.anim_selected_field = value;
};

const clearData = () => {
  time_dimension.removeGeoJSONLayers();
  time_dimension.show_hide_animation_toolbar(false);
  activeEsdlParams.value = null;
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
