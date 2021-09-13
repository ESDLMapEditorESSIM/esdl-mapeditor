<template>
  <a-table :columns="costInformationColumns" :data-source="ci_filtered" size="middle" :pagination="paginationConfig" />
  <CostInformationEdit v-model:costInfo="costInformation" v-model:objectIDs="objectIdentifiers" />
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
    objectIDs: {
      type: Array,
      default: function() {
        return [
        ];
      },
    },
  },
  data() {
    return {
       costInformation: this.costInfo,
       objectIdentifiers: this.objectIDs,
       costInformationColumns,
       paginationConfig
    }
  },
  computed: {
    ci_filtered: function() {
      return this.costInformation.filter(ci => (ci.value != null && !isNaN(ci.value)));
    }
  },
  mounted() {
    // console.log(this.costInformation);
  },
  methods: {
    deleteCostInformationType(key) {
      console.log(key);
    }
  }
}
</script>
