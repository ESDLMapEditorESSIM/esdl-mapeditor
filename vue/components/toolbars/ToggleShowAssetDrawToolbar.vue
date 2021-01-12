<template>
  <a class="dropdown-item" href="#" @click="toggleShowAssetDrawToolbar">
    <div
      class="menu-icon"
      :class="{ 'ui-icon-check ui-icon': showAssetDrawToolbar }"
    >
      &nbsp;
    </div>
    Show/hide asset draw toolbar
  </a>
</template>

<script>
import { useAssetDrawToolbar } from "../../composables/assetDrawToolbar.js";

export default {
  name: "ToggleShowAssetDrawToolbar",
  setup() {
    const { toggleShowAssetDrawToolbar, showAssetDrawToolbar } = useAssetDrawToolbar();

    return {
      toggleShowAssetDrawToolbar,
      showAssetDrawToolbar,
    };
  },
};
</script>
