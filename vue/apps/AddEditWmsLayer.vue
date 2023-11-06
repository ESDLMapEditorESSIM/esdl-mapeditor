<template>
  <h1>
    {{ isNewLayer ? "Add WMS Layer" : "Update WMS Layer" }}
  </h1>
  <a-space
    v-if="!isLoading"
    id="add-edit-wms-layer"
    direction="vertical"
    style="width: 100%"
  >
    <div style="margin-bottom: 10px;">
      <a-row v-for="(value, key) in wmsLayer" :key="key" :gutter="[4, 4]" type="flex" align="middle">
        <a-col :span="9">
          <span>{{ camelCase(key) }}</span>
        </a-col>
        <a-col :span="15">
          <a-input
            v-model:value="wmsLayer[key]"
            class="fe_box"
            size="small"
            type="text"
          />
          <!--          <a-select-->
          <!--            v-if="isNewLayer && key === 'projectName'"-->
          <!--            v-model:value="wmsLayer[key]" size="small" style="width: 100%"-->
          <!--            :options="projectOptions()"-->
          <!--          />-->
          <!--        </a-col>-->
        </a-col>
      </a-row>
    </div>
    <a-row>
      <a-col :span="24">
        <a-space>
          <a-button type="primary" @click="addUpdate">
            {{ isNewLayer ? "Add WMS Layer" : "Update WMS Layer" }}
          </a-button>
          <a-button type="primary" @click="cancel">Cancel</a-button>
        </a-space>
      </a-col>
    </a-row>
  </a-space>
</template>

<script setup>
import {ref, onBeforeMount, defineExpose, defineEmits} from "vue";
import {useObject} from "../composables/ObjectID";
import {useWmsLayers} from "../composables/wmsLayers";

const {getWmsLayerList, addWmsLayer, updateLayer} = useWmsLayers();

const wmsLayer = ref(null);
const parentId = ref(null);
const parentLayerGroup = ref(null);
const isNewLayer = ref(false);
const isLoading = ref(false);

const {currentObjectID} = useObject();

onBeforeMount(() => {
  if (currentObjectID.value.startsWith("__")) {
    parentId.value = currentObjectID.value.replace("__", "");
    window.socket.emit('get_wms_layer_group', {id: parentId.value}, function (group_info) {
      parentLayerGroup.value = group_info;
    });
    isNewLayer.value = true;
    wmsLayer.value = {
      description: 'AardwarmteKrijtJura',
      url: 'https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?',
      layerName: 'AardwarmteKrijtJura',
      legendUrl: '',
      attribution: '',
    }
  } else {
    window.socket.emit('get_wms_layer', {id: currentObjectID.value}, function (lyr_info) {
      wmsLayer.value = {
        description: lyr_info.description,
        url: lyr_info.url,
        layerName: lyr_info.layer_name,
        legendUrl: lyr_info.legend_url,
        attribution: lyr_info.attribution,
      }
    });
  }
});

// eslint-disable-next-line no-unused-vars
const camelCase = (str) => {
  // TODO: import this function from utils.js and let utils.js export functions
  return window.camelCaseToWords(str);
};


// eslint-disable-next-line no-unused-vars
const projectOptions = () => {
  const projectNames = [];
  for (const [key, layer] of Object.entries(getWmsLayerList()['layers'])) {
    if (layer.project_name !== undefined) {
      projectNames.push(layer.project_name);
    }
  }

  const options = [];
  for (const uniqueName of [...new Set(projectNames)]) {
    options.push({
      label: uniqueName,
      value: uniqueName,
    })
  }
  return options;
}

// eslint-disable-next-line no-unused-vars
const addUpdate = () => {
  if (isNewLayer.value) {
    addWmsLayer(
        wmsLayer.value.description,
        wmsLayer.value.url,
        wmsLayer.value.layerName,
        wmsLayer.value.legendUrl,
        wmsLayer.value.attribution,
        parentLayerGroup.value.project_name,
        parentLayerGroup.value.setting_type,
        parentId.value,
    );
  } else {
    updateLayer(
        currentObjectID.value,
        wmsLayer.value.description,
        wmsLayer.value.url,
        wmsLayer.value.layerName,
        wmsLayer.value.legendUrl,
        ''
    );
  }
  cancel();
};

const cancel = () => {
  window.sidebar.hide();
}
</script>


<style>
.fe_box {
  border-width: 1px;
}
</style>