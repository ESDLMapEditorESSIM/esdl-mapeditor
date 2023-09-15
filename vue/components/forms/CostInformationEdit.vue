<template>
  <div>
    <a-button type="primary" @click="showModal">
      Change or add costs
    </a-button>
    <a-modal v-model:visible="visible" title="Cost Information" width="750px" @ok="handleOk">
      <a-table :columns="costInformationColumns" :data-source="costInformation" size="middle" :pagination="paginationConfig">
        <template #civalue="{ text, record }">
          <!--
          <a-input
            style="margin: -5px 0"
            :value="text"
            @change="e => handleChange(e.target.value, record.key)"
          />
          -->
          <FancyNumberEdit
            style="margin: -5px 0"
            :value="text"
            @update:value="(val) => handleFNEChange(val, record.key)"
          />
        </template>
        <template #ciunit="{ record }">
          <a-select
            v-model:value="record.unit"
            style="width: 140px"
            :options="costInformationProfileTypes"
            placeholder="Please select a unit..."
            @change="val => handleUnitChange(val, record.key)"
          />
        </template>
        <template #operation="{ record }">
          <div v-if="record.value != null">
            <a @click="deleteCostInformation(record.key)">
              <i class="fa fa-trash" />
            </a>
          </div>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script>
import FancyNumberEdit from "./FancyNumberEdit"

const costInformationColumns = [
  { title: 'Type', dataIndex: 'uiname', key: 'citype' },
  { title: 'Value', dataIndex: 'value', key: 'civalue', slots: { customRender: 'civalue' }},
  { title: 'Unit', dataIndex: 'unit', key: 'ciunit', slots: { customRender: 'ciunit' }},
  { title: '', slots: { customRender: 'operation' }},
];

// For the time being a fixed list of possible options
const costInformationProfileTypes = [
  { value: '', label: "Please select a unit..."},
  { value: 'EUR', label: "EUR"},
  { value: 'EUR/yr', label: "EUR/yr"},
  { value: 'EUR/kW', label: "EUR/kW"},
  { value: 'EUR/MW', label: "EUR/MW"},
  { value: 'EUR/kWh', label: "EUR/kWh"},
  { value: 'EUR/MWh', label: "EUR/MWh"},
  { value: 'EUR/kWh/yr', label: "EUR/kWh/yr"},
  { value: 'EUR/MWh/yr', label: "EUR/MWh/yr"},
  { value: 'EUR/m', label: "EUR/m"},
  { value: 'EUR/km', label: "EUR/km"},
  { value: 'EUR/m2', label: "EUR/m2"},
  { value: 'EUR/m3', label: "EUR/m3"},
  { value: '%', label: "% of CAPEX"},
]

const paginationConfig = { hideOnSinglePage: true};

export default {
  name: "CostInformationEdit",
  components: {
    FancyNumberEdit
  },
  props: {
    costInfo: {
      type: Array,
      default: function() {
        return [
        ];
      }
    },
    objectIDs: {
      type: Array,
      default: function() {
        return [
        ];
      }
    },
  },
  data() {
    return {
        visible: false,
        costInformation: this.costInfo,
        objectIdentifiers: this.objectIDs,
        costInformationColumns,
        costInformationProfileTypes,
        paginationConfig
    }
  },
  computed: {
  },
  mounted() {
    console.log(this.costInformation);
  },
  methods: {
    showModal() {
      this.visible = true;
    },
    handleOk() {
      window.socket.emit('DLA_set_cost_information', {'id': this.objectIdentifiers}, this.costInformation);
      this.visible = false;
    },
    handleFNEChange(val, key) {
      // console.log(val);
      // console.log(key);
      for (let i=0; i<this.costInformation.length; i++) {
        if (this.costInformation[i]["key"] == key) {
          this.costInformation[i]["value"] = val;
          this.costInformation[i]["changed"] = true;
        }
      }
    },
    handleUnitChange(val, key) {
      for (let i=0; i<this.costInformation.length; i++) {
        if (this.costInformation[i]["key"] == key) {
          this.costInformation[i]["changed"] = true;
        }
      }
    },
    deleteCostInformation(key) {
      for (let i=0; i<this.costInformation.length; i++) {
        if (this.costInformation[i]["key"] == key) {
          this.costInformation[i]["value"] = null;
          this.costInformation[i]["unit"] = null;
          this.costInformation[i]["changed"] = true;
        }
      }
    }
  },
};
</script>
