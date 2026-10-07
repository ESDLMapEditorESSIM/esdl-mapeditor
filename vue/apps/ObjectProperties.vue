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
  <template v-if="!isLoading && !noResult">
    <h1>
      <span
        v-if="!obj_properties.multi_select_info"
        :title="obj_properties.object.doc"
      >
        {{ obj_properties.object.name }}
      </span>
      <span
        v-if="obj_properties.multi_select_info"
      >
        {{ obj_properties.multi_select_info.num_assets_selected }} assets selected of type:
        {{ obj_properties.multi_select_info.selected_asset_type }}
      </span>
    </h1>
  </template>
  <template v-if="isLoading && !noResult">
    <h1>
      <span>
        Collecting information...
      </span>
    </h1>
    <spinner />
  </template>
  <div v-if="!isLoading && !noResult" id="object-properties">
    <a-row :gutter="[0, 24]">
      <a-col :span="24">
        <a-collapse v-model:activeKey="activePanels" default-active-key="Basic">
          <a-collapse-panel
            v-for="(cat, key) in obj_properties.attributes"
            :key="key"
            :header="key + ' attributes'"
            :collapsible="panelCollapsible(key)"
          >
            <div style="margin-bottom: 10px;">
              <a-row v-for="attr in cat" :key="attr.name" :gutter="[0, 4]" type="flex" align="middle">
                <!-- attributes -->
                <a-col v-if="isAttribute(attr)" :span="9">
                  <span :title="attr.doc">{{ camelCase(attr.name) }}</span>
                </a-col>
                <a-col v-if="isAttribute(attr)" :span="15">
                  <FancyNumberEdit
                    v-if="attr.type == 'EInt'"
                    v-model:value="attr.value"
                    v-model:unit="attr.unit"
                    size="small"
                    @update:value="(val) => { updateAttribute(attr.name, val);}"
                  />
                  <FancyNumberEdit
                    v-if="attr.type == 'EDouble'"
                    v-model:value="attr.value"
                    v-model:unit="attr.unit"
                    size="small"
                    @update:value="(val) => { updateAttribute(attr.name, val); }"
                  />
                  <a-input
                    v-if="attr.type == 'EString' && attr.name !== 'description'"
                    v-model:value="attr.value"
                    class="fe_box"
                    size="small"
                    type="text"
                    @blur="updateAttribute(attr.name, attr.value)"
                  />
                  <a-textarea
                    v-if="attr.type == 'EString' && attr.name === 'description'"
                    v-model:value="attr.value"
                    size="small"
                    auto-size
                    @blur="updateAttribute(attr.name, attr.value)"
                  />
                  <a-select
                    v-if="attr.type == 'EEnum' || attr.type == 'EBoolean'"
                    v-model:value="attr.value" size="small" style="width: 100%"
                    :options="dropdownOptions(attr.options)"
                    @change="updateAttribute(attr.name, attr.value)"
                  />
                  <a-date-picker
                    v-if="attr.type == 'EDate'"
                    format="YYYY-MM-DD HH:mm:ss"
                    size="small"
                    style="width: 100%"
                    :default-value="get_default_date(attr.value)"
                    :show-time="{ defaultValue: dayjs('00:00:00', 'HH:mm:ss') }"
                    @change="(date) => { updateDateAttribute(date, attr.name); }"
                  />
                </a-col>
                <a-col v-if="!multipleAssetsSelected && !isAttribute(attr) && !ignoredRefs.includes(attr.name)" :span="24">
                  <a-row :gutter="[0, 0]" type="flex" align="middle">
                    <ReferenceViewer
                      :parent-object-i-d="currentObjectIDs[0]"
                      :reference="attr"
                      @update="updateRef($event, attr)"
                    />
                  </a-row>
                </a-col>
              </a-row>
            </div>
          </a-collapse-panel>
          <a-collapse-panel key="Ports" header="Ports" :collapsible="panelCollapsible('Ports')">
            <PortsEdit
              v-model:portList="obj_properties.port_connected_to_info"
              v-model:objectID="obj_properties.object.id"
            />
          </a-collapse-panel>
          <a-collapse-panel key="CostInformation" header="Cost information" :collapsible="panelCollapsible('CostInformation')">
            <CostInformationView
              v-model:costInfo="obj_properties.cost_information"
              v-model:objectIDs="currentObjectIDs"
            />
          </a-collapse-panel>
          <a-collapse-panel key="KPI" header="KPI" :collapsible="panelCollapsible('KPI')">
            <span v-if="multipleAssetsSelected">Select a single asset to view its KPIs.</span>
            <KPIView v-else :kpi-info="obj_properties.kpi_information" />
          </a-collapse-panel>
          <a-collapse-panel key="Constraints" header="Constraints" :collapsible="panelCollapsible('Constraints')">
            <AssetConstraint 
              :es-id="activeEsdlId"
              :object-id="obj_properties.object.id"
              :embedded-view="true"
            />
          </a-collapse-panel>
        </a-collapse>
      </a-col>
    </a-row>
    <a-row>
      <!-- these buttons are not necessary I think... -->
      <a-col :span="24" style="padding-top: 16px;">
        <a-space>
          <a-button type="primary" @click="save">Save</a-button>
          <a-button type="primary" @click="cancel">Cancel</a-button>
        </a-space>
      </a-col>
    </a-row>
  </div>
  <template v-if="noResult">
    <h1>
      <span>
        Error retrieving information...
      </span>
    </h1>
    <a-card style="width: 100%">
      <p>
        No information could be found for the selected object in the currently active energy system. This is
        most probably caused by the fact that you have multiple energy systems loaded and you're selecting an
        object on the map that belongs to (one of) the inactive energy system(s).
      </p>
      <p>
        Please change the active energy system in the ESDL layers control box at the top right side of the map
        and click on the object on the map again.
      </p>
    </a-card>
  </template>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import dayjs from "dayjs";
import FancyNumberEdit from "@/components/forms/FancyNumberEdit.vue";
import AssetConstraint from "@/apps/AssetConstraint.vue";
import PortsEdit from "@/components/forms/PortsEdit.vue";
import CostInformationView from "@/components/forms/CostInformationView.vue";
import KPIView from "@/components/forms/KPIView.vue";
import ReferenceViewer from "@/components/forms/ReferenceViewer.vue";
import { useObject } from "@/composables/ObjectID";
import { useEsdlLayers } from "@/composables/esdlLayers";
import spinner from "@/components/Spinner.vue";
import { displayNotification, NotificationType } from "@/utils/notification";

const { getActiveEsdlLayerId } = useEsdlLayers();
const { currentObjectID } = useObject();

const ignoredRefs = ['port', 'costInformation', 'KPIs', 'constraint', 'geometry'];
const obj_properties = ref({});
const activePanels = ref(window.object_properties_active_panels || ["Basic"]);
const isLoading = ref(true);
const noResult = ref(false);
const savedAttributeValues = new Map();

const activeEsdlId = computed(() => {
  return getActiveEsdlLayerId().value;
});

const currentObjectIDs = computed(() => {
  if (Array.isArray(currentObjectID.value)) {
    return currentObjectID.value;
  }
  return [currentObjectID.value];
});

const multipleAssetsSelected = computed(() => {
  return currentObjectIDs.value.length > 1;
});

const availablePanels = computed(() => {
  const panels = new Set();
  Object.entries(obj_properties.value.attributes || {}).forEach(([key, attributes]) => {
    const hasVisibleFields = attributes.some((feature) => {
      if (isAttribute(feature)) {
        return true;
      }
      return !multipleAssetsSelected.value && !ignoredRefs.includes(feature.name);
    });
    if (hasVisibleFields) {
      panels.add(key);
    }
  });

  const capabilities = obj_properties.value.capabilities || {};
  if (capabilities.ports && !multipleAssetsSelected.value) {
    panels.add("Ports");
  }
  if (capabilities.cost_information) {
    panels.add("CostInformation");
  }
  if (capabilities.kpis && !multipleAssetsSelected.value) {
    panels.add("KPI");
  }
  if (capabilities.constraints && !multipleAssetsSelected.value) {
    panels.add("Constraints");
  }

  return panels;
});

watch(activePanels, () => {
  window.object_properties_active_panels = activePanels.value;
});

onMounted(() => {
  getDataSocketIO();
});

function camelCase(str) {
  return window.camelCaseToWords(str);
}

function panelCollapsible(panel) {
  if (!availablePanels.value.has(panel)) {
    return "disabled";
  }
  return undefined;
}

function dropdownOptions(attrOpts) {
  return attrOpts.map((opt) => {
    return {
      label: opt,
      value: opt,
    };
  });
}

function getDataSocketIO() {
  const tmp_coid = JSON.parse(JSON.stringify(currentObjectID.value));
  window.socket.emit(
    "DLA_get_object_properties",
    { id: currentObjectID.value },
    (res) => {
      console.log("Object properties:", res);
      isLoading.value = false;
      if (res) {
        obj_properties.value = res;
        savedAttributeValues.clear();
        Object.values(res.attributes).forEach((category) => {
          category.forEach((feature) => {
            if (isAttribute(feature)) {
              savedAttributeValues.set(feature.name, feature.value);
            }
          });
        });
        activePanels.value = activePanels.value.filter((panel) => availablePanels.value.has(panel));
        if (!activePanels.value.length && availablePanels.value.has("Basic")) {
          activePanels.value = ["Basic"];
        }
        currentObjectID.value = tmp_coid;
      } else {
        noResult.value = true;
      }
    }
  );
}

function save() {
  window.socket.emit(
    "DLA_set_object_properties",
    { id: currentObjectID.value },
    obj_properties.value
  );
  window.sidebar.hide();
}

function cancel() {
  window.sidebar.hide();
}

function updateAttribute(name, new_value) {
  if (
    !multipleAssetsSelected.value &&
    savedAttributeValues.has(name) &&
    Object.is(savedAttributeValues.get(name), new_value)
  ) {
    return;
  }

  window.socket.emit("command", {
    cmd: "set_asset_param",
    id: currentObjectID.value,
    param_name: name,
    param_value: new_value,
  }, (response) => {
    if (!response || !response.success) {
      return;
    }

    savedAttributeValues.set(name, new_value);
    displayNotification(NotificationType.SUCCESS, `${camelCase(name)} updated.`, {
      title: "Saved",
      duration: 2,
    });
    window.PubSubManager.broadcast('ASSET_PROPERTIES', {
      id: currentObjectID.value,
      name: name,
      value: new_value,
    });
  });
}

function updateDateAttribute(date, name) {
  let new_value;
  if (date) {
    new_value = date.format('YYYY-MM-DDTHH:mm:ss.SSSSSSZZ');
  } else {
    new_value = '';
  }
  updateAttribute(name, new_value);
}

function get_default_date(value) {
  console.log("Getting default date", value);
  if (value) {
    return dayjs(value, 'YYYY-MM-DDTHH:mm:ss.SSSSSSZZ');
  }
  return null;
}

function isAttribute(feature) {
  return !('containment' in feature);
}

function updateRef(event, reference) {
  console.log('OP ref updated: ', event, reference);
  reference.value.type = event.value.type;
  reference.value.repr = event.value.repr;
}
</script>

<style>
.fe_box {
  border-width: 1px;
}
</style>

