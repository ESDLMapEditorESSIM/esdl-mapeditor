<template>
  <div class="map-object-popup">
    <div class="map-object-header">
      <a-typography-text strong :ellipsis="true" :title="objectInfo.name || objectInfo.type" :content="objectInfo.name || objectInfo.type" class="map-object-title" />
    </div>
    <div class="map-object-body">
      <a-descriptions v-if="attributes.length" class="map-object-attributes" size="small" :column="1">
        <a-descriptions-item v-for="attribute in attributes" :key="attribute.name">
          <template #label>
            <a-typography-text type="secondary">{{ attribute.label }}</a-typography-text>
          </template>
          {{ attribute.value }}<template v-if="attribute.unit"> {{ attribute.unit }}</template>
        </a-descriptions-item>
      </a-descriptions>
      <KPIView :kpi-info="objectInfo.kpi_info" compact />
    </div>
  </div>
</template>

<script setup>
import {computed, nextTick, onMounted} from 'vue';
import KPIView from '@/components/forms/KPIView.vue';

const POPUP_ATTRIBUTES = {
  Building: [
    {name: 'buildingYear', label: 'Building year', unit: ''},
    {name: 'floorArea', label: 'Floor area', unit: 'm²'},
  ],
  AggregatedBuilding: [
    {name: 'floorArea', label: 'Floor area', unit: 'm²'},
  ],
};

const props = defineProps({
  objectInfo: {type: Object, required: true},
});
const emit = defineEmits(['resize']);

const attributes = computed(() => {
  const selected = POPUP_ATTRIBUTES[props.objectInfo.type] || [];
  // Building attributes are already included in the map's KPI dictionary.
  const values = props.objectInfo.KPIs || {};
  return selected.filter(attribute => Object.hasOwn(values, attribute.name))
    .map(attribute => ({...attribute, value: values[attribute.name]}));
});

onMounted(async () => {
  await nextTick();
  emit('resize');
});
</script>

<style>
.map-object-hover-popup .leaflet-popup-content-wrapper {
  padding: 0;
  overflow: hidden;
}

.map-object-hover-popup .leaflet-popup-content {
  margin: 0;
}
</style>

<style scoped>
.map-object-header {
  padding: 8px;
  background: #f5f5f5;
  border-bottom: 1px solid #f0f0f0;
}

.map-object-title {
  display: block;
  max-width: 100%;
}

.map-object-body {
  max-height: min(360px, 45vh);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.map-object-attributes {
  padding: 4px 8px;
  border-bottom: 1px solid #f0f0f0;
}

.map-object-attributes :deep(.ant-descriptions-row > td.ant-descriptions-item) {
  padding: 2px 0;
}

.map-object-attributes :deep(.ant-descriptions-item-content) {
  justify-content: flex-end;
  text-align: right;
  overflow-wrap: anywhere;
}
</style>
