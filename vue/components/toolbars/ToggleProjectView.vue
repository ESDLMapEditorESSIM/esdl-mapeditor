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
import { useESDLProjects } from "../../composables/esdlProjects.js";

export default {
  name: "ToggleProjectView",
  setup() {
    const { toggleProjectView, showProjectView } = useESDLProjects();

    return {
      toggleProjectView,
      showProjectView,
    };
  },
};
</script>
