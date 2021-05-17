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
            @update:value="(val) => handleChange(val, record.key)"
          />
        </template>
        <template #ciunit="{ record }">
          <a-select
            v-model:value="record.unit"
            style="width: 140px"
            placeholder="Please select a unit..."
          >
            <a-select-option
              v-for="ptype in costInformationProfileTypes"
              :key="ptype.key" :value="ptype.key"
            >
              {{ ptype.type }}
            </a-select-option>
          </a-select>
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
  { key: '', type: "Please select a unit..."},
  { key: 'EUR', type: "EUR"},
  { key: 'EUR/yr', type: "EUR/yr"},
  { key: 'EUR/kW', type: "EUR/kW"},
  { key: 'EUR/MW', type: "EUR/MW"},
  { key: 'EUR/kWh', type: "EUR/kWh"},
  { key: 'EUR/MWh', type: "EUR/MWh"},
  { key: 'EUR/kWh/yr', type: "EUR/kWh/yr"},
  { key: 'EUR/MWh/yr', type: "EUR/MWh/yr"},
  { key: 'EUR/m', type: "EUR/m"},
  { key: 'EUR/km', type: "EUR/km"},
  { key: '%', type: "% of CAPEX"},
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
    objectID: String
  },
  data() {
    return {
        visible: false,
        costInformation: this.costInfo,
        objectIdentifier: this.objectID,
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
      window.socket.emit('DLA_set_cost_information', {'id': this.objectIdentifier}, this.costInformation);
      this.visible = false;
    },
    handleChange(val, key) {
      // console.log(val);
      // console.log(key);
      for (let i=0; i<this.costInformation.length; i++) {
        if (this.costInformation[i]["key"] == key) this.costInformation[i]["value"] = val;
      }
    },
    deleteCostInformation(key) {
      for (let i=0; i<this.costInformation.length; i++) {
        if (this.costInformation[i]["key"] == key) {
          this.costInformation[i]["value"] = null;
          this.costInformation[i]["unit"] = null;
        }
      }
    }
  },
};
</script>
