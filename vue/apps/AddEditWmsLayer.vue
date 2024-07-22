<!--
  - This work is based on original code developed and copyrighted by TNO 2020.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <a-space
    id="add-edit-wms-layer"
    direction="vertical"
    style="width: 100%; padding: 8px;"
  >
    <h1>
      {{ isNewLayer ? "Add WMS Layer" : "Edit WMS Layer" }}
    </h1>
    <!-- Add WMS layer UI -->
    <div v-if="isNewLayer">
      <!-- Step 1: An input field to specify WMS service URL -->
      <a-col
        v-if="addWmsLayerStep === stepOptions[0]"
        :span="24"
      >
        <a-row>
          <a-input 
            id="input-WmsUrl"
            v-model:value="wmsFormState.url"
            type="text"
            placeholder="WMS service URL"
            :status="urlInputStatus"
            @change="resetUrlInputState"
          />
          <p v-if="urlInputMsg.length" class="input-error-message">{{ urlInputMsg }}</p>
        </a-row>
        <a-row type="flex" justify="end" style="padding-top: 8px;">
          <a-button 
            type="primary" 
            :disabled="isFetchingWmsGetCapabilities" 
            @click="onNextBtnClick"
          >
            <template v-if="isFetchingWmsGetCapabilities">
              <a-spin />
            </template>
            <template v-else>
              Next
            </template>
          </a-button>
        </a-row>
      </a-col>
      <!-- Step 2: Displaying available layer options -->
      <a-col
        v-if="addWmsLayerStep === stepOptions[1]"
        :span="24"
      >
        <a-row style="border: 1px solid #DBDBDB; border-radius: 8px;">
          <a-list style=" max-height: 250px; overflow-y: auto; margin: 8px;">
            <a-checkbox-group 
              v-model:value="selectedLayers" 
            >
              <a-col 
                v-for="(layer, index) in layerOptions" 
                :key="index" 
                :span="24"
              >
                <a-checkbox :value="layer['name']">{{ layer['name'] }}</a-checkbox>
              </a-col>
            </a-checkbox-group>
          </a-list>
        </a-row>
        <a-row type="flex" justify="end" style="padding-top: 8px;">
          <a-space>
            <a-button @click="onBackBtnClick">
              Back
            </a-button>
            <a-button type="primary" :disabled="selectedLayers.length === 0" @click="onAddToMapBtnClick">
              Add to map
            </a-button>
          </a-space>
        </a-row>
      </a-col>
    </div>
    <!-- Edit WMS layer UI -->
    <div v-if="!isNewLayer">
      <a-row v-for="(value, key) in wmsLayer" :key="key" style="padding-bottom: 8px;">
        <a-col :span="9">
          <span>{{ camelCase(key) }}</span>
        </a-col>
        <a-col :span="15">
          <a-input
            v-model:value="wmsLayer[key]"
            class="fe_box"
            size="small"
            type="text"
            :disabled="disabledWmsFields.includes(key)"
          />
        </a-col>
      </a-row>
      <a-row style="padding-top: 8px;">
        <a-col :span="24">
          <a-space>
            <a-button type="primary" @click="onUpdateBtnClick">Update WMS Layer</a-button>
            <a-button @click="cancel">Cancel</a-button>
          </a-space>
        </a-col>
      </a-row>
    </div>
  </a-space>
</template>

<script setup>
import {ref, onBeforeMount, reactive, toRaw} from "vue";
import {useObject} from "../composables/ObjectID";
import {useWmsLayers} from "../composables/wmsLayers";
import {camelCase} from "../utils/utils";
import {getWmsServiceBaseUrl, updateGlobalWmsLayerList} from "../composables/wmsLayers";
const {
  addWmsLayer, 
  updateLayer, 
  getWmsGetCapabilities, 
  showWmsLayer
} = useWmsLayers();

const wmsLayer = ref(null);
const parentId = ref(null);
const parentLayerGroup = ref(null);
const isNewLayer = ref(false);

const {currentObjectID} = useObject();
// Disable these form fields from editing when the user tries to "update" the layer.
const disabledWmsFields = ["url", "layerName"];

const stepOptions = ["specifyUrl", "selectLayers"];
const addWmsLayerStep = ref(stepOptions[0]);

const initInputStatus = "";
const initInputMsg = "";
const urlInputStatus = ref(initInputStatus);
const urlInputMsg = ref(initInputMsg);
const isFetchingWmsGetCapabilities = ref(false);

// When the getWmsGetCapabilities() call is successful, 
// layerOptions will be updated to an array of WmsServiceLayerInfo object, each with `name`, `title`, and `legend_url` properties.
const layerOptions = ref([]);
// To keep user selected layer names in an array
const selectedLayers = ref([]);

const wmsBaseUrl = ref("");
const wmsFormState = reactive({url: ""});

onBeforeMount(() => {
  if (currentObjectID.value.startsWith("__")) {
    parentId.value = currentObjectID.value.replace("__", "");
    window.socket.emit('get_wms_layer_group', {id: parentId.value}, function (group_info) {
      parentLayerGroup.value = group_info;
    });
    isNewLayer.value = true;
    wmsLayer.value = {
      description: '',
      url: '',
      layerName: '',
      legendUrl: '',
      attribution: '',
      minZoomLevel: '',
    };
  } else {
    window.socket.emit('get_wms_layer', {id: currentObjectID.value}, function (lyr_info) {
      wmsLayer.value = {
        description: lyr_info.description,
        url: lyr_info.url,
        layerName: lyr_info.layer_name,
        legendUrl: lyr_info.legend_url,
        minZoomLevel: lyr_info.min_zoom_level,
        attribution: lyr_info.attribution,
      };
    });
  }
});

/**
 * Reset WMS url input field to the initial state
 */
const resetUrlInputState = () => {
  urlInputStatus.value = initInputStatus;
  urlInputMsg.value = initInputMsg;
};

/**
 * Navigate to step one UI to let users specify the WMS URL.
 */
const onBackBtnClick = () => {
  addWmsLayerStep.value = stepOptions[0];
};

/**
 * Handles the "Next" button click event to process the WMS service URL input.
 * 
 * @returns {Promise<void>}
 */
const onNextBtnClick = async() => {
  const inputUrl = toRaw(wmsFormState).url;
  
  // Show an error message when the URL input field is empty
  if (!inputUrl.length) {
    urlInputStatus.value = "error";
    urlInputMsg.value = "Please provide a WMS service URL before continuing.";
  }
  else {
    // Get the WMS service base URL from the user input URL (which can contain additional query parameters)
    // and show an error message if an invalid URL is found.
    const parsedUrl = getWmsServiceBaseUrl(inputUrl);
    if (parsedUrl instanceof Error) {
      urlInputStatus.value = "error";
      urlInputMsg.value = `${parsedUrl.message}. Please check the URL before continuing.`;
    } 
    else {
      wmsBaseUrl.value = parsedUrl;
      isFetchingWmsGetCapabilities.value = true;
      try {
        const resp = await getWmsGetCapabilities(wmsBaseUrl.value);
        if (resp.success) {
          // Navigate the user to the layer selection UI
          addWmsLayerStep.value = stepOptions[1];
          layerOptions.value = resp.result;
        } else {
          console.error(resp.result);
          urlInputStatus.value = "error";
          urlInputMsg.value = `${resp.result} Please check the provided URL and try again.`;
        }
      } catch (error) {
        console.error(error);
        urlInputStatus.value = "error";
        urlInputMsg.value = `${error.message} Please check the provided URL and try again.`;
      } finally {
        isFetchingWmsGetCapabilities.value = false;
      }
    }
  }
};

/**
 * Handles the "Add to Map" button click event to add selected WMS layers 
 * to the backend (MongoDB) and then to the map.
 * 
 * @returns {Promise<void>}
 */
const onAddToMapBtnClick = async () => {
  for (const layerName of selectedLayers.value) {
    const layerId = window.uuidv4();
    const layerUrl = wmsBaseUrl.value;
    const layerLegendUrl = layerOptions.value.filter((l) => l.name === layerName)[0].legend_url || "";
    // Users can override the default values when "editing" the layer.
    const layerDescr = layerName; // Default layerDescr to be layerName
    const layerAttr = "";         // Default layerAttr to be an empty string
    const minZoomLevel = null;    // Default minZoomLevel to be null

    try {
      const allLayers = await addWmsLayer(
        layerId,
        layerDescr,
        layerUrl,
        layerName,
        layerLegendUrl,
        layerAttr,
        minZoomLevel,
        parentLayerGroup.value.project_name,
        parentLayerGroup.value.setting_type,
        parentId.value,
      );
      updateGlobalWmsLayerList(allLayers, layerId);
      showWmsLayer(layerId);
    } 
    catch (error) {
      console.error(error);
      window.alert(error);
    }
  }
  cancel();
};

const onUpdateBtnClick = () => {
  updateLayer(
    currentObjectID.value,
    wmsLayer.value.description,
    wmsLayer.value.url,
    wmsLayer.value.layerName,
    wmsLayer.value.legendUrl || "",
    wmsLayer.value.attribution || "",
    wmsLayer.value.minZoomLevel || null,
  );
  cancel();
};

const cancel = () => {
  window.sidebar.hide();
};

</script>


<style>
.fe_box {
  border-width: 1px;
}
</style>