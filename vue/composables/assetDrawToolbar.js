import { ref } from "vue";

const showAssetDrawToolbar = ref(false);

export function useAssetDrawToolbar() {
  const toggleShowAssetDrawToolbar = () => showAssetDrawToolbar.value = !showAssetDrawToolbar.value;

  return {
    showAssetDrawToolbar,
    toggleShowAssetDrawToolbar,
  }
}
