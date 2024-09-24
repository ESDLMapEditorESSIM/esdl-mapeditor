<template>
  <div :id="props.id">
    <a-row>
      <a-col :span="24">
        <a-slider 
          v-model:value="sliderValue"
          :min="props.min" 
          :max="props.max" 
          :step="props.step"
          @change="onSliderChange"
        />
      </a-col>
    </a-row>
  </div>
</template>
  
  <script setup>
  import { defineProps, ref } from "vue";
  
  const props = defineProps({
    id: {
      type: String,
      default: "SimpleSlider"
    },
    inputValue: {
      type: Number,
      default: 1.0
    },
    min: {
      type: Number,
      default: 0.0
    },
    max: {
      type: Number,
      default: 1.0
    },
    step: {
      type: Number,
      default: 0.1
    },
  });
  
  const sliderValue = ref(props.inputValue);
  
  const emit = defineEmits(["on-slider-value-change"]);
  
  /**
   * Pass the slider value to the parent component via emitting on-slider-value-change event.
   * 
   * @param {number} sliderValue slider value
   */
  const onSliderChange = (sliderValue) => {
    emit("on-slider-value-change", sliderValue);
  };
  
  </script>