import { ref } from "vue";

const showUndoRedoControl = ref(false);

export function useUndoRedo() {
  const toggleShowUndoRedoControl = () => showUndoRedoControl.value = !showUndoRedoControl.value;

  const undo = () => window.socket.emit('command', {cmd: 'undo', es_id: window.active_layer_id});
  const redo = () => window.socket.emit('command', {cmd: 'redo', es_id: window.active_layer_id});

  return {
    showUndoRedoControl,
    toggleShowUndoRedoControl,
    undo,
    redo,
  }
}
