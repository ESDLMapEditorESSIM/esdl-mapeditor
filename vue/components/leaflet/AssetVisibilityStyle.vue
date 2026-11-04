<template>
  <Teleport to="head">
    <component :is="'style'">{{ filterCss }}</component>
  </Teleport>
</template>

<script setup>
import {useAssetVisibility} from '@/composables/assetVisibility';

const {filterCss} = useAssetVisibility();
</script>
