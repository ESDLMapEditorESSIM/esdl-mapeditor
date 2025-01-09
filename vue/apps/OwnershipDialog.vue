<template>
  <a-row>
    <a-col span="20">
      <h1>
        Ownership
      </h1>
    </a-col>
    <a-col span="4">
      <div>Tst</div>
    </a-col>
  </a-row>

  <template v-if="parties_list">
    <a-row
      v-for="party in parties_list"
      :key="party.id">
      {{ party.name }}
    </a-row>
  </template>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const parties_list = ref([]);

const getPartiesList = async () => {
  const response = await fetch("/ownership/parties");
  if (response.ok) {
    const data = await response.json();
    console.log(data);
    parties_list.value = data.parties;
  } else {
    // TODO: Handle error
  }
};
getPartiesList();

</script>

<style scoped>

</style>