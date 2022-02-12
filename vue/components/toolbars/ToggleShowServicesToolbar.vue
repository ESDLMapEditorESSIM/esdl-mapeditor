<template>
  <a class="dropdown-item" href="#" @click="toggleShowServicesToolbar">
    <div
      class="menu-icon"
      :class="{ 'ui-icon-check ui-icon': showServicesToolbar }"
    >
      &nbsp;
    </div>
    Show/hide services toolbar
  </a>
</template>

<script>
import { PubSubManager, MessageNames } from "../../bridge.js";
import { useServicesToolbar } from "../../composables/servicesToolbar.js";

PubSubManager.subscribe(MessageNames.USER_SETTINGS, (name, message) => {
    let ui_settings = message.ui_settings;
    const { initShowServicesToolbar } = useServicesToolbar();
    initShowServicesToolbar(ui_settings.services_toolbar.visible_on_startup);
});

export default {
  name: "ToggleShowServicesToolbar",
  setup() {
    const { toggleShowServicesToolbar, showServicesToolbar, initShowServicesToolbar } = useServicesToolbar();

    return {
      toggleShowServicesToolbar,
      showServicesToolbar,
      initShowServicesToolbar,
    };
  },
};
</script>
