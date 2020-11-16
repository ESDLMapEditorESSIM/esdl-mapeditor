<template>
  <a-table :columns="costInformationColumns" :data-source="costInformation" size="middle">
    <template
      v-for="civ in ['civalue']"
      #[civ]="{ text, record }"
      :key="civ"
    >
      <div :key="civ">
        <a-input
          style="margin: -5px 0"
          :value="text"
          @change="e => handleChange(e.target.value, record.key, civ)"
        />
      </div>
    </template>

    <template #operation="{ record }">
      <div class="editable-row-operations">
        <span>
          <a @click="deleteCostInformationType(record.key)">
            <i class="fa fa-trash"/>
          </a>
        </span>
      </div>      
    </template>
  </a-table>
</template>

<script>
import FancyNumberEdit from './FancyNumberEdit';

const costInformationColumns = [
  { title: 'Type', dataIndex: 'name', key: 'citype' },
  { title: 'Value', dataIndex: 'value', key: 'civalue', slots: { customRender: 'civ' }},
  { title: '', slots: { customRender: 'operation' }},
];

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
    }
  },
  data() {
    return {
       costInformation: this.costInfo,
       costInformationColumns
    }
  },
  mounted() {
    console.log(this.costInformation);
  },
  computed: {

  },
  methods: {
    deleteCostInformationType(key) {
      console.log(key);
    }
  }
}
</script>
