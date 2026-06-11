import { ref, computed } from "vue";

const showUndoRedoControl = ref(false);
const undoRedoMapEditorDialog = ref(null);
const stack = ref([]);
const stack_index = ref(null);

export function useUndoRedo() {
  const toggleShowUndoRedoControl = () => {
    if (undoRedoMapEditorDialog.value !== null) {
      if (showUndoRedoControl.value) {
        undoRedoMapEditorDialog.value.close();
      } else {
        undoRedoMapEditorDialog.value.open();
        undoRedoMapEditorDialog.value._handleMinimize();
      }
      showUndoRedoControl.value = !showUndoRedoControl.value;
      console.log("Undo redo control checked", showUndoRedoControl.value);
    }
  }

  const undo = () => window.socket.emit('command', {cmd: 'undo', es_id: window.active_layer_id});
  const redo = () => window.socket.emit('command', {cmd: 'redo', es_id: window.active_layer_id});
  const undoRedoUntil = (idx) => window.socket.emit('command', {cmd: 'undo_redo_until', target_idx: idx, es_id: window.active_layer_id});
  const canUndo = computed( () => stack_index.value !== null && stack.value.length > 0 && stack_index.value >= 0);
  const canRedo = computed( () => stack_index.value !== null && stack.value.length > 0 && stack_index.value + 1 < stack.value.length);
  
  return {
    showUndoRedoControl,
    toggleShowUndoRedoControl,
    undo,
    redo,
    undoRedoUntil,
    undoRedoMapEditorDialog,
    stack,
    stack_index,
    canUndo,
    canRedo
  }
}
