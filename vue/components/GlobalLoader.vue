<template>
  <div v-if="isLoading" id="loader">
    <div id="loader-hider" @click="hideLoaderAfterThreeClicks" />
    <div class="spinner" />
  </div>
</template>

<script setup>
import {onUnmounted} from "vue";
import {useLoader} from "@/composables/loader";

const {isLoading, clearLoaders} = useLoader();
let clickCount = 0;
let clickTimer = null;

function hideLoaderAfterThreeClicks() {
  clickCount += 1;

  if (clickTimer) {
    clearTimeout(clickTimer);
  }

  clickTimer = setTimeout(() => {
    clickCount = 0;
  }, 1000);

  if (clickCount === 3) {
    clickCount = 0;
    clearTimeout(clickTimer);
    clickTimer = null;
    clearLoaders();
  }
}

onUnmounted(() => {
  if (clickTimer) {
    clearTimeout(clickTimer);
  }
});
</script>
