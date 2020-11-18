<template>
  <a-table :columns="costInformationColumns" :data-source="ci_filtered" size="middle" />
  <CostInformationEdit v-model:costInfo="costInformation" v-model:objectID="objectIdentifier"/>
</template>

<script>
import FancyNumberEdit from './FancyNumberEdit';
import CostInformationEdit from './CostInformationEdit'

const costInformationColumns = [
  { title: 'Type', dataIndex: 'uiname', key: 'citype' },
  { title: 'Value', dataIndex: 'value', key: 'civalue'},
  { title: 'Unit', dataIndex: 'unit', key: 'ciunit'},
];

export default {
  name: "CostInformationView",
  components: {
    FancyNumberEdit,
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
       costInformationColumns
    }
  },
  mounted() {
    console.log(this.costInformation);
  },
  computed: {
    ci_filtered: function() {
      return this.costInformation.filter(ci => ci.value != "");
    }
  },
  methods: {
    deleteCostInformationType(key) {
      console.log(key);
    }
  }
}
</script>
