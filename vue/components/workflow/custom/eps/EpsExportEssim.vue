<!--
  - This work is based on original code developed and copyrighted by TNO 2020.
  - Subsequent contributions are licensed to you by the developers of such code and are
  - made available to the Project under one or several contributor license agreements.
  -
  - This work is licensed to you under the Apache License, Version 2.0.
  - You may obtain a copy of the license at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Contributors:
  -     TNO         - Initial implementation
  - Manager:
  -     TNO
  -->

<template>
  <p>Description</p>
  <a-input
    v-model:value="es_id"
    placeholder="ES ID"
  />
  <a-input
    v-model:value="simulation_run"
    placeholder="Simulation run"
  />
  <a-button type="primary" @click="onSubmit"> Generate ESSIM export</a-button>
</template>

<script setup="props">
import {defineProps, ref} from "vue";
import {useWorkflow} from "../../../../composables/workflow";
import {doPost} from "../../../../utils/api";
const { goToPreviousStep } = useWorkflow();

const props = defineProps({
  workflowStep: {
    type: Object,
    default: null,
    required: true,
  },
});

const simulation_run = ref("");
const es_id = ref("");

const onSubmit = async () => {
  console.log(simulation_run)
  const response = await doPost("dice_workflow/export_essim", {simulation_run: simulation_run.value, es_id: es_id.value});
  console.log(response);
}
</script>

<style scoped>

</style>