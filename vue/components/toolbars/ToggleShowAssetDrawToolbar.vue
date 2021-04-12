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
import { PubSubManager, MessageNames } from "../../bridge.js";
import { useAssetDrawToolbar } from "../../composables/assetDrawToolbar.js";

PubSubManager.subscribe(MessageNames.USER_SETTINGS, (name, message) => {
    let ui_settings = message.ui_settings;
    const { initShowAssetDrawToolbar } = useAssetDrawToolbar();
    initShowAssetDrawToolbar(ui_settings.asset_bar.visible_on_startup);
});

export default {
  name: "ToggleShowAssetDrawToolbar",
  setup() {
    const { toggleShowAssetDrawToolbar, showAssetDrawToolbar, initShowAssetDrawToolbar } = useAssetDrawToolbar();

    return {
      toggleShowAssetDrawToolbar,
      showAssetDrawToolbar,
      initShowAssetDrawToolbar,
    };
  },
};
</script>
