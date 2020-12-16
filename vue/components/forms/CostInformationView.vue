<template>
  <a-table :columns="costInformationColumns" :data-source="ci_filtered" size="middle" :pagination="paginationConfig" />
  <CostInformationEdit v-model:costInfo="costInformation" v-model:objectID="objectIdentifier" />
</template>

<script>
import CostInformationEdit from './CostInformationEdit'

const costInformationColumns = [
  { title: 'Type', dataIndex: 'uiname', key: 'citype' },
  { title: 'Value', dataIndex: 'value', key: 'civalue'},
  { title: 'Unit', dataIndex: 'unit', key: 'ciunit'},
];

const paginationConfig = { hideOnSinglePage: true};

export default {
  name: "CostInformationView",
  components: {
    CostInformationEdit
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
       costInformation: this.costInfo,
       objectIdentifier: this.objectID,
       costInformationColumns,
       paginationConfig
    }
  },
  computed: {
    ci_filtered: function() {
      return this.costInformation.filter(ci => ci.value != "");
    }
  },
  mounted() {
    console.log(this.costInformation);
  },
  methods: {
    deleteCostInformationType(key) {
      console.log(key);
    }
  }
}
</script>
