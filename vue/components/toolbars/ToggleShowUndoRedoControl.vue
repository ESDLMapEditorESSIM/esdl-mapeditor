<template>
  <a class="dropdown-item" href="#" @click="toggleShowUndoRedoControl">
    <div
      class="menu-icon"
      :class="{ 'ui-icon-check ui-icon': showUndoRedoControl }"
    >
      &nbsp;
    </div>
    Show history sidebar
  </a>
</template>

<script>
import { useUndoRedo } from "../../composables/undoRedo.js";

export default {
  name: "ToggleShowUndoRedoControl",
  setup() {
    const { toggleShowUndoRedoControl, showUndoRedoControl } = useUndoRedo();

    return {
      toggleShowUndoRedoControl,
      showUndoRedoControl,
    };
  },
};
</script>
