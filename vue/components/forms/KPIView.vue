<template>
  <a-table
    class="kpi-table"
    :class="{ 'kpi-table-compact': compact }"
    :columns="tableColumns"
    :data-source="kpiInfo"
    :size="tableSize"
    table-layout="fixed"
    :pagination="pagination"
    :locale="{ emptyText: 'No KPIs available' }"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.key === 'name'">
        <span :class="{ 'compact-distribution-name': compact && record.type === 'DistributionKPI' }">
          <span :title="record.name">{{ formatKPIName(record.name) }}</span>
          <a-tooltip v-if="record.description" :title="record.description" :trigger="['hover', 'focus']">
            <a-button class="kpi-description" size="small" type="text" :aria-label="'Description for ' + formatKPIName(record.name)">
              <InfoCircleOutlined style="vertical-align: 0.1rem" />
            </a-button>
          </a-tooltip>
        </span>
        <template v-if="compact && record.type === 'DistributionKPI'">
          <div v-for="(item, index) in record.items" :key="index" class="compact-distribution-item">
            <span>{{ item.label }}</span>
            <KPIValue :value="item.value" />
            <span>{{ record.unit }}</span>
          </div>
          <span v-if="!record.items.length">No values</span>
        </template>
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

<script setup>
import { computed } from 'vue';
import { InfoCircleOutlined } from '@ant-design/icons-vue';
import KPIValue from './KPIValue.vue';
import { formatKPIName } from '@/utils/kpi';

const columns = [
  { title: 'KPI', dataIndex: 'name', key: 'name', width: '40%' },
  { title: 'Value', dataIndex: 'value', key: 'value', width: '45%', align: 'right', ellipsis: true },
  { title: 'Unit', dataIndex: 'unit', key: 'unit', width: '15%' },
];

const paginationConfig = { hideOnSinglePage: true };

const props = defineProps({
  kpiInfo: {
    type: Array,
    default: () => [],
  },
  compact: {
    type: Boolean,
    default: false,
  },
});

const tableColumns = computed(() => {
  if (!props.compact) {
    return columns;
  }
  const distributionValueCell = (record) => {
    if (record.type === 'DistributionKPI') {
      return { colSpan: 0 };
    }
    return {};
  };
  return [
    {
      ...columns[0], width: '60%',
      customCell: (record) => {
        if (record.type === 'DistributionKPI') {
          return { colSpan: 3 };
        }
        return {};
      },
    },
    { ...columns[1], width: '25%', customCell: distributionValueCell },
    { ...columns[2], customCell: distributionValueCell },
  ];
});

const tableSize = computed(() => {
  if (props.compact) {
    return 'small';
  }
  return 'middle';
});

const pagination = computed(() => {
  if (props.compact) {
    return false;
  }
  return paginationConfig;
});
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

.kpi-table :deep(.ant-table-cell) {
  vertical-align: top;
}

.kpi-table :deep(.ant-table-cell:not(.ant-table-cell-ellipsis)),
.distribution-label {
  overflow-wrap: anywhere;
  white-space: normal;
}

.distribution-label {
  text-align: right;
}

.kpi-table-compact :deep(.ant-table.ant-table-small .ant-table-cell) {
  padding-block: 3px;
}

.compact-distribution-name {
  display: block;
  margin-bottom: 4px;
}

.compact-distribution-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 100px) auto;
  gap: 8px;
  align-items: baseline;
}
</style>
