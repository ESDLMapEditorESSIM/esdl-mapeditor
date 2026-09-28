<template>
  <div v-if="showControl" class="my-control leaflet-plan-control">
    <strong>Plan</strong>
    <span
      class="plan-color-swatch"
      :style="{backgroundColor: PLAN_COLOR}"
      aria-hidden="true"
    />
    <a-select
      v-model:value="selectedPlanId"
      class="plan-control-select"
      size="small"
      :options="planOptions"
      aria-label="Select Plan"
    />
  </div>
</template>

<script setup>
import {computed} from "vue";
import {NO_PLAN_ID, PLAN_LAYER_NAME, usePlans} from "@/composables/plans";
import {PLAN_COLOR} from "@/utils/planVisualization";
import {useVisibleLayers} from "@/composables/visibleLayers";

const {
    activeEsdlId,
    activePlans,
    selectedPlanId,
} = usePlans();
const {layerIsVisible} = useVisibleLayers();

const planOptions = computed(() => {
    const options = [{label: "No plan", value: NO_PLAN_ID}];
    for (const plan of activePlans.value) {
        options.push({
            label: plan.name || "Unnamed Plan",
            value: plan.id,
        });
    }
    return options;
});

const showControl = computed(() => {
    return Boolean(
        activeEsdlId.value &&
        activePlans.value.length > 0 &&
        layerIsVisible(`${activeEsdlId.value}_${PLAN_LAYER_NAME}`)
    );
});
</script>

<style scoped>
.leaflet-plan-control {
  display: flex;
  width: 250px;
  padding: 5px;
  align-items: center;
  gap: 5px;
  background: white;
  border-radius: 5px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.65);
}

.plan-color-swatch {
  width: 16px;
  height: 5px;
  flex: none;
  border-radius: 2px;
}

.plan-control-select {
  min-width: 0;
  flex: 1;
}
</style>
