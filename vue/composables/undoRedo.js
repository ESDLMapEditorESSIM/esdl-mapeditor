import { ref } from "vue";

const showUndoRedoControl = ref(false);
const undoRedoMapEditorDialog = ref(null);

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
    }
  }

  const undo = () => window.socket.emit('command', {cmd: 'undo', es_id: window.active_layer_id});
  const redo = () => window.socket.emit('command', {cmd: 'redo', es_id: window.active_layer_id});
  const undoRedoUntil = (idx) => window.socket.emit('command', {cmd: 'undo_redo_until', target_idx: idx, es_id: window.active_layer_id});

  return {
    showUndoRedoControl,
    toggleShowUndoRedoControl,
    undo,
    redo,
    undoRedoUntil,
    undoRedoMapEditorDialog,
  }
}
