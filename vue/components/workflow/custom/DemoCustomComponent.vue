<template>
  <p>This is a custom component with some custom styling. This component can be programmed to do whatever you want it do.</p>
  <a-space direction="vertical" :size="12">
    <a-date-picker v-model:value="value1" />
<!--    <a-date-picker v-model:value="value2" picker="week" />-->
<!--    <a-date-picker v-model:value="value3" picker="month" />-->
<!--    <a-date-picker v-model:value="value4" picker="quarter" />-->
<!--    <a-date-picker v-model:value="value5" picker="year" />-->
  </a-space>
</template>

<script setup="props">
import {ref} from 'vue';

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const value1 = ref();
// const value2 = ref();
// const value3 = ref();
// const value4 = ref();
// const value5 = ref();
</script>

<style scoped>
p {
  color: red;
  font-size: 18px;
}
</style>