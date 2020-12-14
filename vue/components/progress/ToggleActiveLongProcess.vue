<template>
  <a class="dropdown-item" href="#" @click="toggleShowActiveLongProcess">
    <div
      class="menu-icon"
      :class="{ 'ui-icon-check ui-icon': showActiveLongProcess }"
    >
      &nbsp;
    </div>
    Show/hide active processes
  </a>
</template>

<script>
import { useLongProcessState } from "../../composables/longProcess.js";

export default {
  name: "ToggleActiveLongProcesss",
  setup() {
    const { toggleShowActiveLongProcess, showActiveLongProcess } = useLongProcessState();

    return {
      toggleShowActiveLongProcess,
      showActiveLongProcess,
    };
  },
};
</script>
