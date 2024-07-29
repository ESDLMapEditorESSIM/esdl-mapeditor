<template>
  <!-- NICE TO HAVE: position the popover next to the target layer node -->
  <a-popover 
    v-if="layerOpacityPopover.isOpened"
    v-model:open="layerOpacityPopover.isOpened"
    :title="layerOpacityPopover.popoverTitle"
    trigger="click"
    placement="right"
    @open-change="closeLayerOpacityPopover"
  >
    <template #content>
      <SimpleSlider :input-value="layerOpacityPopover.layerOpacity" @on-slider-value-change="onLayerOpacityChange" />
      <a @click="closeLayerOpacityPopover">Close</a>
    </template>
  </a-popover>
</template>
  
<script setup>
  import { computed, defineProps } from "vue";
  import SimpleSlider from "../slider/SimpleSlider.vue";
  import { useVisibleLayers } from "@/composables/visibleLayers";
  const { 
    getVisibleLayerById, 
    adjustVisibleLayerOpacity,
    saveVisibleLayerOpacitySetting,
  } = useVisibleLayers(); 
  
  const props = defineProps({
    layerId: {
      type: String,
      required: true
    },
  });
  
  const emit = defineEmits(["close-popover"]);
  
  /**
   * Compute layer opacity popover properties based on props.layerId
   */
  const layerOpacityPopover = computed(() => {
    let isOpened = false;
    let popoverTitle = "";
    let layerOpacity = 1.0;
        
    if (props.layerId !== "") {
      const layer = getVisibleLayerById(props.layerId);
      if (layer) {
        isOpened = true;
        const layerDescription = layer.description;
        const currentLayerOpacity = layer.layer_ref.options.opacity;
        popoverTitle = `Adjust '${layerDescription}' WMS layer opacity`;
        layerOpacity = currentLayerOpacity;
      } else {
        console.error("Layer not found");
      }
    }
  
    return {
      isOpened: isOpened,
      popoverTitle: popoverTitle,
      layerOpacity: layerOpacity,
    };
  });
  
  /**
   * Adjust the layer opacity based on the slider value
   * 
   * @param {number} newSliderValue slider value emitted from the child component
   */
  const onLayerOpacityChange = (newSliderValue) => {
    if (props.layerId !== "") {
      adjustVisibleLayerOpacity(props.layerId, newSliderValue);
    }
  };
  
  /**
   * When triggered, it first saves the current layer opacity setting in the backend
   * and closes the popover by emitting an event, which resets the layerId to an empty string at the parent component.
   */
  const closeLayerOpacityPopover = () => {
    saveVisibleLayerOpacitySetting(props.layerId);
    emit("close-popover");
  };
  
</script>
  