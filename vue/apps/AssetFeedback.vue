<template>
  <a-row style="padding: 8px;">
    <a-typography-title :level="3">
      ESDL feedback
    </a-typography-title>
  </a-row>
  <template
    v-if="Object.keys(currentAssetFeedbackList).length"
  >
    <a-col style="padding: 8px;">
      <p>
        The following feedback was given for the objects in the energy system.
        For asset feedback messages, you can select an item from the list to focus the asset on the map.
      </p>
      <a-row>
        <a-typography-title :level="5" style="padding-right: 8px;">
          Displayed severity
        </a-typography-title>
        <a-checkbox-group 
          v-model:value="selectedSeverityState"
          :options="severityOptions"
          @change="onCheckSeverity"
        >
          <template #label="{ label }">
            <span>{{ label }}</span>
          </template>
        </a-checkbox-group>
      </a-row>
      <br>
      <div>
        <a-table
          v-if="filtered_general_feedback_list.length"
          :columns="generalColumns"
          :data-source="filtered_general_feedback_list"
          row-key="id"
          :pagination="{ pageSize: 5 }"
          :scroll="{ y: 'max-content' }"
        >
          <template #bodyCell="{ column, record }">
            <b v-if="column.dataIndex === 'name'">
              {{ record.name }}
            </b>
            <br>
            <span
              v-for="item in record.messages"
              :key="item.key"
              style="font-size: x-small"
            >
              <p style="margin: 0;">
                <span :style="severity_color_mapping[item.severity]">{{ item.severity }}</span>
                {{ ` - ${item.validationMessage }` }}
              </p>
              <ul 
                v-if="Array.isArray(item.checkResultMessages)"
                style="margin-left: -1rem; margin-bottom: 0.1rem;"
              >
                <li v-for="(msg, index) in item.checkResultMessages" :key="index">
                  {{ msg }}
                </li>
              </ul>
            </span>
          </template>
        </a-table>
      </div>
      <div>
        <a-col style="padding-bottom: 8px;">
          <a-typography-title :level="5">
            Asset filter
          </a-typography-title>
          <a-select
            v-model:value="selectedAssetKeys"
            :options="assetSelectorOptions"
            style="width: 100%"
            mode="multiple"
            :show-search="true"
            allow-clear
            max-tag-count="responsive"
            @mouseleave="removeTooltipPopup"
          />
        </a-col>
        <a-table
          v-if="filtered_asset_feedback_list.length"
          :columns="columns"
          :data-source="filtered_asset_feedback_list"
          row-key="id"
          :custom-row="customRow"
          :pagination="{ pageSize: 50 }"
          :scroll="{ y: 'max-content' }"
          class="table-with-hover"
        >
          <template #bodyCell="{ column, record }">
            <b v-if="column.dataIndex === 'name'">
              {{ record.name }}
            </b>
            <br>
            <span
              v-for="item in record.messages"
              :key="item.key"
              style="font-size: x-small"
            >
              <p style="margin: 0;">
                <span :style="severity_color_mapping[item.severity]">{{ item.severity }}</span>
                {{ ` - ${item.validationMessage }` }}
              </p>
              <ul 
                v-if="Array.isArray(item.checkResultMessages)"
                style="margin-left: -1rem; margin-bottom: 0.1rem;"
              >
                <li v-for="(msg, index) in item.checkResultMessages" :key="index">
                  {{ msg }}
                </li>
              </ul>
            </span>
          </template>
        </a-table>
      </div>
    </a-col>
  </template>
  <template v-else>
    <a-row style="padding: 8px;">
      <p>
        The validation service could not detect any errors.
      </p>
    </a-row>
  </template>
  <a-space style="padding: 8px;">
    <a-button type="primary" @click="onClose">Ok</a-button>
    <a-button
      v-if="asset_feedback_list.length"
      type="primary"
      @click="clearAssetFeedbackFromMap"
    >
      Clear feedback from map
    </a-button>
  </a-space>
</template>

<script setup>
import {ref, computed, onMounted, onUnmounted} from 'vue'
import {useAssetFeedbackList} from '../composables/assetFeedback';
import {v4 as uuidv4} from 'uuid';

// to prevent stuck popup on UI
const removeTooltipPopup = () => {
  window.jquery(".ui-tooltip-content").parents("div").remove();
};

const {currentAssetFeedbackList} = useAssetFeedbackList();

const generalColumns = [
  {
    title: 'Feedback message(s)',
    dataIndex: 'name',
    width: 150,
  },
];

const columns = [
  {
    title: 'Asset feedback message(s): click to zoom',
    dataIndex: 'name',
    width: 150,
  },
];

const selectedSeverityState = ref(['ERROR', 'WARNING']);
const severityOptions = [
  { label: 'ERROR', value: 'ERROR' },
  { label: 'WARNING', value: 'WARNING' },
];

const asset_feedback_list = ref([]);
// To be used as asset selector options
const assetSelectorOptions = ref([]);
const selectedAssetKeys = ref([]);

// A list of feedback that can't be linked to the specific asset.
const general_feedback_list = ref([]);

const severity_color_mapping = {
  // "INFO": "color:#00FF00",
  "WARNING": "color:#FFA500",
  "ERROR": "color:#FF0000",
}

onMounted(() => {
  console.debug("AssetFeedback mounted");
  create_asset_feedback_list();
});

onUnmounted(() => {
  // Reset to default
  asset_feedback_list.value = ['ERROR', 'WARNING'];
  clearAssetFeedbackFromMap();
  console.debug("AssetFeedback unmounted");
});

const onCheckSeverity = () => {
  create_asset_feedback_list();
}

const filtered_general_feedback_list = computed(() => {
  return general_feedback_list.value;
});

const filtered_asset_feedback_list = computed(() => {
  if (selectedAssetKeys.value.length) {
    return asset_feedback_list.value.filter((f) => selectedAssetKeys.value.includes(f.key));
  } else {
    return asset_feedback_list.value;
  }
});

function customRow(record) {
  return {
    onClick: () => {
      console.log(record);
      if (record.layer instanceof window.L.Marker) {
        window.map.setView(record.layer.getLatLng(), 20);
      } else {
        window.map.fitBounds(record.layer.getBounds());
      }
    },
  };
}

function clearAssetFeedbackFromMap() {
  window.clear_layers(window.active_layer_id, 'sim_layer');
}

function onClose() {
  clearAssetFeedbackFromMap();
  window.sidebar.hide();
}

function create_asset_feedback_list() {
  // Retrieve list of ESDL layers from the map, such that feedback can refer to this data
  let active_es_id = window.active_layer_id;
  let active_es_asset_info = window.get_layers(active_es_id, 'esdl_layer');
  let active_es_asset_layers = active_es_asset_info.getLayers();

  let tmp_asset_feedback_list = [];
  let found_feedback_ids = [];

  for (let i = 0; i < active_es_asset_layers.length; i++) {
    const asset = active_es_asset_layers[i];
    const assetId = asset.id;
    const assetName = asset.name;
    if (assetId in currentAssetFeedbackList.value) {
      found_feedback_ids.push(assetId)
      let messages = [];

      currentAssetFeedbackList.value[assetId].forEach((validationResult) => {
        if (selectedSeverityState.value.includes(validationResult['severity'])) {
          messages.push({
            key: uuidv4(),
            severity: validationResult['severity'],
            validationMessage: validationResult['validation_message'], 
            checkResultMessages: validationResult['check_result_messages'],
          });
        }
      })

      const feedback_item = {
        key: assetId,
        name: assetName,
        messages: messages,
        layer: asset,
      }

      if (messages.length) {
        tmp_asset_feedback_list.push(feedback_item);
      }
    }
  }
  asset_feedback_list.value = tmp_asset_feedback_list;

  updateAssetSelectorOptions(asset_feedback_list.value);

  let tmp_general_feedback_list = [];
  for (const messagesId in currentAssetFeedbackList.value) {
    if (!found_feedback_ids.includes(messagesId)) {
      let messages = [];

      currentAssetFeedbackList.value[messagesId].forEach((validationResult) => {
        if (selectedSeverityState.value.includes(validationResult['severity'])) {
           messages.push({
            key: uuidv4(),
            severity: validationResult['severity'],
            validationMessage: validationResult['validation_message'], 
            checkResultMessages: validationResult['check_result_messages']
          });
        }
      })

      const feedback_item = {
        key: messagesId,
        name: messagesId,
        messages: messages
      }
      if (messages.length) {
        tmp_general_feedback_list.push(feedback_item);
      }
    }
  }
  general_feedback_list.value = tmp_general_feedback_list;
}

const updateAssetSelectorOptions = (feedbackList) => {
  assetSelectorOptions.value = feedbackList.map((f) => ({
    label: f.name,
    value: f.key,
  }))
}

</script>

<style scoped>
.table-with-hover {
  cursor: pointer;
}
</style>