<template>
  <div style="width: 100%; height: 100%;">
    <a-row class="analytics-panel-header vue-draggable-handle">
      <h5 class="analytics-panel-title">{{ props.options?.title || '' }}</h5>
      <a-button 
        type="text"
        class="analytics-panel-header-icon-btn"
        @click="emit('onEdit')"
      >
        <template #icon>
          <FormOutlined />
        </template>
      </a-button>
      <a-button 
        type="text" 
        class="analytics-panel-header-icon-btn"
        @click="emit('onRemove')"
      >
        <template #icon>
          <CloseOutlined />
        </template>
      </a-button>
    </a-row>
    <a-row class="analytics-panel-plot-container no-drag">
      <AnalyticsPlot
        :trace="props.options?.currentTrace || []"
        :layout="props.options?.currentLayout || {}"
      />
    </a-row>
  </div>
</template>
    
<script setup>
import { defineProps } from "vue";
import AnalyticsPlot from "../esdlanalytics/AnalyticsPlot.vue";
import { CloseOutlined, FormOutlined } from "@ant-design/icons-vue";
  
const props = defineProps({
	options: {
		type: Object,
		default: null
	}
});

const emit = defineEmits(['onRemove', 'onEdit']);

</script>

<style>
.analytics-panel-header {
	margin: 0;
	height: 35px;
	width: 100%;
	flex-direction: row;
	background-color: #f1f1f196;
}

.analytics-panel-header:hover {
	background-color: #f5f5f5e8;
}

.analytics-panel-header-icon-btn {
	right: 5px;
	color: #363636;
}

.analytics-panel-plot-container {
	/* height of the plot container = 100% - panel-header height (35px) */
	height: calc(100% - 35px);
}

.analytics-panel-title {
	font-size: 1.1em;
	width: 70%;
  overflow: hidden;
	margin: 0;
	padding: 0.5rem;
	color: #363636;
	font-weight: bolder;
	flex-grow: 1;
}
</style>