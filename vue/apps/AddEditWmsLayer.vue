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
            v-if="key !== 'addToGroup'"
            v-model:value="wmsLayer[key]"
            class="fe_box"
            size="small"
            type="text"
          />
          <a-select
            v-if="isNewLayer && key === 'addToGroup'"
            v-model:value="wmsLayer[key]" size="small" style="width: 100%"
            :options="groupOptions()"
          />
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

const {getWmsLayerList, addWmsLayer, updateLayer} = useWmsLayers()
const wmsLayerList = ref(null);

onBeforeMount(() => {
  wmsLayerList.value = getWmsLayerList();
});

const wmsLayer = ref(null);
const isNewLayer = ref(false);
const isLoading = ref(false);

const {currentObjectID} = useObject();

onBeforeMount(() => {
  if (currentObjectID.value == null) {
    wmsLayer.value = {
      description: 'AardwarmteKrijtJura',
      url: 'https://rvo.b3p.nl/geoserver/WarmteAtlas/wms?',
      layerName: 'AardwarmteKrijtJura',
      legendUrl: '',
      attribution: '',
      addToGroup: '',
    }
    isNewLayer.value = true;
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
const groupOptions = () => {
  let options = [];
  for (const idx in wmsLayerList.value['groups']) {
    let group = wmsLayerList.value['groups'][idx];
    if (!group.readonly) {
      options.push({
            label: group.name,
            value: idx,
          }
      )
    }
  }
  return options;
}

// eslint-disable-next-line no-unused-vars
const addUpdate = () => {
  if (isNewLayer.value) {
    const group = wmsLayerList.value['groups'][wmsLayer.value.addToGroup];
    addWmsLayer(
        wmsLayer.value.description,
        wmsLayer.value.url,
        wmsLayer.value.layerName,
        wmsLayer.value.legendUrl,
        wmsLayer.value.attribution,
        group.project_name,
        group.setting_type,
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