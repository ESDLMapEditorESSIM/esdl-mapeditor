<template>
  <h1>Heat Transition</h1>
  <p v-if="isLoading">Loading data ...</p>
  <a-space direction="vertical" v-else>
    <a-card style="width: 100%">
      <p>
        This plugin allows you to modify the energy demand for heating by applying isolation measures and choosing the
        heating technology.
      </p>
    </a-card>
    <a-card>
      <h2>{{ area_name }} ({{ area_id }})</h2>
      <a-table
        v-if="area_info_present"
        :columns="columns"
        :data-source="area_info"
        :pagination="false"
        row-key="key"
      />
    </a-card>
    <a-card>
      <h2>Alternative technologies for gas boilers</h2>
      <a-row v-for="tech in technologies" :key="tech.key" :gutter="[0, 4]">
        <a-col :span="9">
          <span>{{ tech.name }}</span>
        </a-col>
        <a-col :span="15">
          <FancyNumberEdit
            v-model:value="tech.percentage"
            unit="&percnt;"
            size="small"
            @update:value="(val) => { updateTechnologyPercentage(tech.key, val);}"
          />
        </a-col>
      </a-row>
    </a-card>

    <a-space direction="horizontal">
      <a-button type="primary" @click="apply_measures">Apply</a-button>
      <a-button type="primary" @click="cancel">Cancel</a-button>
    </a-space>
  </a-space>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useObject } from "@/composables/ObjectID"
import FancyNumberEdit from "@/components/forms/FancyNumberEdit.vue";

const isLoading = ref(true);

const { currentObjectID } = useObject();
const area_name = ref("");
const area_id = ref("");
const area_info_present = ref(false);

const columns = ref([
  {
    title: 'Type',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: 'Number',
    dataIndex: 'number',
    key: 'number'
  }
]);

const area_info = ref([
  {
    key: '1',
    name: 'Residential',
    number: 0
  },
  {
    key: '2',
    name: 'Utility',
    number: 0
  },
  {
    key: '3',
    name: 'Industry',
    number: 0
  },
  {
    key: '4',
    name: 'Other',
    number: 0
  },
]);

const technologies = ref([
  {
    key: '1',
    name: 'Electric heat pump',
    percentage: 100,
  },
  {
    key: '2',
    name: 'District heat network',
    percentage: 0,
  },
  {
    key: '3',
    name: 'Hybrid heatpump (biogas)',
    percentage: 0,
  }
]);

const currentObjectIDs = computed(() => {
  return (Array.isArray(currentObjectID.value) ? currentObjectID.value : [currentObjectID.value]);
});
const multipleAssetsSelected = computed(() => {
  return (this.currentObjectIDs.length > 1);
});

function get_heat_transition_data() {
  if (!multipleAssetsSelected) {
    retrieve_area_info(currentObjectIDs.value[0]);
  } else {
    socket.emit('etm_heat_transition_get_areas_info', currentObjectIDs.value, function(res) {
      area_name.value = "Multiple areas selected";
      area_id.value = currentObjectIDs.value.join(", ");
      isLoading.value = false;
    });
  }
}
get_heat_transition_data();

function retrieve_area_info(id) {
  socket.emit('etm_heat_transition_get_area_info', id, function(res) {
    if (res) {
      area_name.value = res.name;
      area_id.value = id;
      if (res.info) {
        area_info.value[0].number = res.info.num_woon;
        area_info.value[1].number = res.info.num_utiliteit;
        area_info.value[2].number = res.info.num_industrie;
        area_info.value[3].number = res.info.num_overige;
        area_info_present.value = true;
      }
    } else {
      console.log("ERROR: No result returned for area with ID " + id);
    }
    isLoading.value = false;
  });
}

function updateTechnologyPercentage(tech_key, val) {
  for (let i=0; i<technologies.value.length; i++) {
    if (technologies.value[i].key == tech_key) {
      technologies.value[i].percentage = val;
    }
  }
}

function apply_measures() {
  // Clear both the area and the kpi layer, as both will be redrawn after calculations finish
  // window.clear_layers(active_layer_id, 'area_layer');
  // window.clear_layers(active_layer_id, 'kpi_layer');
  window.saveSelectedKPI();   // save the currently selected KPI

  socket.emit(
    'etm_heat_transition_apply',
    {
      area_ids: currentObjectIDs.value,
      technology_info: technologies.value
    }
  );
  window.sidebar.hide();
}

function cancel() {
  window.sidebar.hide()
}

</script>
