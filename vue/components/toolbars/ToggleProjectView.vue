<template>
  <a class="dropdown-item" href="#" @click="toggleProjectView">
    <div
      class="menu-icon"
      :class="{ 'ui-icon-check ui-icon': showProjectView }"
    >
      &nbsp;
    </div>
    Toggle project view
  </a>
</template>

<script>
import { useEnergyProjects } from "../../composables/energyProjects.js";

export default {
  name: "ToggleProjectView",
  setup() {
    const { toggleProjectView, showProjectView } = useEnergyProjects();

    return {
      toggleProjectView,
      showProjectView,
    };
  },
};
</script>
