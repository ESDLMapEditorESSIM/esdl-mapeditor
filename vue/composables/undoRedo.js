import { ref } from "vue";

const showUndoRedoControl = ref(false);

export function useUndoRedo() {
  const toggleShowUndoRedoControl = () => showUndoRedoControl.value = !showUndoRedoControl.value;

  return {
    showUndoRedoControl,
    toggleShowUndoRedoControl,
  }
}
