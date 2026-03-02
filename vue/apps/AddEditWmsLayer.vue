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

<!-- TODO: rename component. -->

<template>
  <a-space
    id="add-edit-web-service-layer"
    direction="vertical"
    style="width: 100%; padding: 8px;"
  >
    <h1>
      {{ isNewLayer ? `Add ${layerType} Layer` : `Edit ${layerType} Layer` }}
    </h1>
    <!-- Layer type selector -->
    <a-segmented
      v-if="isNewLayer"
      v-model:value="layerType"
      :options="[
        { label: 'WMS', value: 'WMS' },
        { label: 'WFS', value: 'WFS' }
      ]"
      style="width: 100%; margin-bottom: 8px;"
      block
      @change="onSelectLayerType"
    />
    <!-- Add layer UI -->
    <div v-if="isNewLayer">
      <!-- Step 1: An input field to specify layer URL -->
      <a-col
        v-if="addLayerStep === stepOptions[0]"
        :span="24"
      >
        <a-row>
          <a-input 
            id="input-layer-url"
            v-model:value="formState.url"
            type="text"
            placeholder="Layer URL"
            :status="urlInputStatus"
            @change="resetUrlInputState"
          />
          <p v-if="urlInputMsg.length" class="input-error-message">{{ urlInputMsg }}</p>
        </a-row>
        <a-row style="padding-top: 8px;">
          <a-button 
            style="color: #4096ff; border: 0px; box-shadow: none;"
            @click="onAddParamsBtnClick"
          >
            + Add query parameter
          </a-button>
          <a-popover>
            <template #content>
              <p style="width: 250px;">
                {{ "Optionally, add parameters that are specific to accessing this service. " + 
                  "Parameter names and values should be defined on the service and are particular to that service." }}
              </p>
            </template>
            <a-button type="text">
              <template #icon>
                <InfoCircleOutlined />
              </template>
            </a-button>
          </a-popover>
        </a-row>
        <a-row 
          v-if="formState.customParams"
          style="padding-top: 8px; padding-left: 16px;"
        >
          <a-row 
            v-for="paramId of Object.keys(formState.customParams)" 
            :key="paramId"
            style="padding-bottom: 8px;"
          >
            <a-space>
              <a-col>
                <a-input
                  v-model:value="formState.customParams[paramId].key"
                  type="text"
                  placeholder="Parameter"
                />
              </a-col>
              <a-col>
                <a-input
                  v-model:value="formState.customParams[paramId].value"
                  type="text"
                  placeholder="Value"
                />
              </a-col>
              <a-button 
                type="text"
                danger
                @click="() => onRemoveParamBtnClick(paramId)"
              >
                <template #icon>
                  <DeleteOutlined />
                </template>
              </a-button>
            </a-space>
          </a-row>
        </a-row>
        <a-row type="flex" justify="end" style="padding-top: 8px;">
          <a-button 
            type="primary"
            :loading="isLoading"
            :disabled="isLoading"
            @click="onNextBtnClick"
          >
            Next
          </a-button>
        </a-row>
      </a-col>
      <!-- Step 2: Displaying available layer options -->
      <a-col
        v-if="addLayerStep === stepOptions[1]"
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
            <a-button
              type="primary"
              :disabled="selectedLayers.length === 0 || isLoading"
              @click="layerType === 'WMS' ? onWmsAddToMapBtnClick() : onWfsAddToMapBtnClick()"
            >
              Add to map
            </a-button>
          </a-space>
        </a-row>
      </a-col>
    </div>
    <!-- TODO Edit WMS layer UI -->
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
import { DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
import {useObject} from "../composables/ObjectID";
import {camelCase} from "../utils/utils";
import {
  getServiceBaseUrl,
  getServiceGetCapabilities,
  addServiceLayer,
  updateGlobalServiceLayerList,
  showLayer,
  useWmsLayers
} from "@/composables/wmsLayers";
const {
  updateLayer, 
} = useWmsLayers();

const wmsLayer = ref(null);
const parentId = ref(null);
const parentLayerGroup = ref(null);
const isNewLayer = ref(false);
const layerType = ref('WMS');

const {currentObjectID} = useObject();
// Disable these form fields from editing when the user tries to "update" the layer.
const disabledWmsFields = ["url", "layerName"];

const stepOptions = ["specifyUrl", "selectLayers"];
const addLayerStep = ref(stepOptions[0]);

const initInputStatus = "";
const initInputMsg = "";
const urlInputStatus = ref(initInputStatus);
const urlInputMsg = ref(initInputMsg);
const isLoading = ref(false);

// When the getServiceGetCapabilities() call is successful, 
// layerOptions will be updated to an array of ServiceLayerInfo object, each with `name`, `title`, and `legend_url` properties.
const layerOptions = ref([]);
// To keep user selected layer names in an array
const selectedLayers = ref([]);

const layerBaseUrl = ref("");
const formState = reactive({url: "", customParams: {}});

// TODO
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
 * Reset layer url input field to the initial state
 */
const resetUrlInputState = () => {
  urlInputStatus.value = initInputStatus;
  urlInputMsg.value = initInputMsg;
};

// Reset content inputs to the initial state
const onSelectLayerType = () => {
  addLayerStep.value = stepOptions[0];
  Object.assign(formState, {url: "", customParams: {}});
  resetUrlInputState();
}

/**
 * Navigate to step one UI to let users specify the layer URL.
 */
const onBackBtnClick = () => {
  addLayerStep.value = stepOptions[0];
};

const onAddParamsBtnClick = () => {
  const paramId = window.uuidv4();
  const newParamObj = {
    key: "",
    value: ""
  };
  Object.assign(formState.customParams, { [paramId]: newParamObj });
};

const onRemoveParamBtnClick = (paramId) => {
  delete formState.customParams[paramId];
};

/**
 * Handles the "Next" button click event to process the layer URL input.
 * 
 * @returns {Promise<void>}
 */
const onNextBtnClick = async() => {
  const formInputs = toRaw(formState);
  
  // Show an error message when the URL input field is empty
  if (!formInputs.url.length) {
    urlInputStatus.value = "error";
    urlInputMsg.value = `Please provide a ${layerType.value} URL before continuing.`;
  }
  else {
    // Get the WMS/WFS service base URL from the user input URL (which can contain additional query parameters)
    // and show an error message if an invalid URL is found.
    const serviceUrl = getServiceBaseUrl(formInputs.url);
    if (serviceUrl instanceof Error) {
      urlInputStatus.value = "error";
      urlInputMsg.value = `${serviceUrl.message}. Please check the URL before continuing.`;
      return;
    }

    const queryParams = [];
    if (formInputs.customParams) {
      Object.values(formInputs.customParams).forEach((param) => {
        if (param.key && param.value) {
          queryParams.push(`${param.key}=${param.value}`);
        }
      });
    }
    layerBaseUrl.value = queryParams.length ? `${serviceUrl}?${queryParams.join("&")}` : serviceUrl;

    isLoading.value = true;
    try {
      const resp = await getServiceGetCapabilities(layerBaseUrl.value, layerType.value);
      if (resp.success) {
        // Navigate the user to the layer selection UI
        addLayerStep.value = stepOptions[1];
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
      isLoading.value = false;
    }
  }
};

/**
 * Add the selected WFS layers to MongoDB and then show on the map.
 */
const onWfsAddToMapBtnClick = async () => {
  for (const layerName of selectedLayers.value) {
    const layerId = window.uuidv4();
    const serviceUrl = layerBaseUrl.value;

    const featureStyle = {
      color: _getRandomColor(),
      weight: 4,
      opacity: 0.3
    };
    featureStyle['fillOpacity'] = featureStyle['opacity'] * 0.3;

    const wfsLayerInfo = {
      type: 'WFS',
      layerId: layerId,
      layerDescr: layerName,
      layerUrl: serviceUrl,
      layerName: layerName,
      style: featureStyle,
      settingtype: parentLayerGroup.value.setting_type,
      projectName: parentLayerGroup.value.project_name,
      legendUrl: null,
      min_zoom_level: null,
      groupId: parentId.value
    };

    try {
      const allLayers = await addServiceLayer(wfsLayerInfo);
      await updateGlobalServiceLayerList(allLayers, layerId);
      await showLayer(layerId);
    } catch (error) {
      console.error(error);
      window.alert(error);
    }
  }
  cancel();
}

/**
 * Handles the "Add to Map" button click event to add selected WMS layers 
 * to the backend (MongoDB) and then to the map.
 * 
 * @returns {Promise<void>}
 */
const onWmsAddToMapBtnClick = async () => {
  for (const layerName of selectedLayers.value) {
    const layerId = window.uuidv4();
    const serviceUrl = layerBaseUrl.value;
    const layerLegendUrl = layerOptions.value.filter((l) => l.name === layerName)[0].legend_url || "";
    // Users can override the default values when "editing" the layer.
    const layerDescr = layerName; // Default layerDescr to be layerName
    const minZoomLevel = null;    // Default minZoomLevel to be null

    const wmsLayerInfo = {
      type: 'WMS',
      layerId: layerId,
      layerDescr: layerDescr,
      layerUrl: serviceUrl,
      layerName: layerName,
      style: null,
      settingtype: parentLayerGroup.value.setting_type,
      projectName: parentLayerGroup.value.project_name,
      legendUrl: layerLegendUrl,
      min_zoom_level: minZoomLevel,
      groupId: parentId.value
    };

    try {
      const allLayers = await addServiceLayer(wmsLayerInfo);
      await updateGlobalServiceLayerList(allLayers, layerId);
      await showLayer(layerId);
    } 
    catch (error) {
      console.error(error);
      window.alert(error);
    }
  }
  cancel();
};

// TODO
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

// An util function to generate random color
const _getRandomColor = () => {
  const h = Math.floor(Math.random() * 360);
  return `hsl(${h}, 70%, 50%)`;
};

</script>


<style scoped>
.fe_box {
  border-width: 1px;
}

:deep(.ant-segmented-item),
:deep(.ant-segmented-item::selection) {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>