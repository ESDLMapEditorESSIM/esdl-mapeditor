<template>
  <a-table
    class="kpi-table"
    :columns="columns"
    :data-source="kpiInfo"
    size="middle"
    table-layout="fixed"
    :pagination="paginationConfig"
    :locale="{ emptyText: 'No KPIs available' }"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'name'">
        <span :title="record.name">{{ formatKPIName(record.name) }}</span>
        <a-tooltip v-if="record.description" :title="record.description" :trigger="['hover', 'focus']">
          <a-button class="kpi-description" size="small" type="text" :aria-label="'Description for ' + formatKPIName(record.name)">
            <InfoCircleOutlined style="vertical-align: 0.1rem" />
          </a-button>
        </a-tooltip>
      </template>
      <template v-if="column.key === 'value'">
        <template v-if="record.type === 'DistributionKPI'">
          <a-row v-for="(item, index) in record.items" :key="index" :gutter="[8, 4]">
            <a-col :span="24" class="distribution-label">{{ item.label }}</a-col>
            <a-col :span="24">
              <KPIValue :value="item.value" />
            </a-col>
          </a-row>
          <span v-if="!record.items.length">No values</span>
        </template>
        <KPIValue v-else :value="record.value" />
      </template>
    </template>
  </a-table>
</template>

<script>
import { InfoCircleOutlined } from '@ant-design/icons-vue';
import KPIValue from './KPIValue.vue';
import { formatKPIName } from '@/utils/kpi';

const columns = [
  { title: 'KPI', dataIndex: 'name', key: 'name', width: '40%' },
  { title: 'Value', dataIndex: 'value', key: 'value', width: '45%', align: 'right', ellipsis: true },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: '15%' },
];

const paginationConfig = { hideOnSinglePage: true };

export default {
  name: 'KPIView',
  components: {
    KPIValue,
    InfoCircleOutlined,
  },
  props: {
    kpiInfo: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return { columns, paginationConfig };
  },
  methods: {
    formatKPIName,
  },
};
</script>

<style scoped>
.kpi-description {
  width: 16px;
  height: 16px;
  margin-left: 4px;
  padding: 0;
  font-size: 12px;
  line-height: 14px;
}

.kpi-table:has(.exponent:not(:empty)) {
  --kpi-exponent-width: 5ch;
}

.kpi-table :deep(.ant-table-cell) {
  vertical-align: top;
}

.kpi-table :deep(.ant-table-cell:not(.ant-table-cell-ellipsis)),
.distribution-label {
  overflow-wrap: anywhere;
  white-space: normal;
}

.distribution-label {
  text-align: left;
}
</style>
