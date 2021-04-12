import { ref } from "vue";

const showAssetDrawToolbar = ref(false);

export function useAssetDrawToolbar() {
  const toggleShowAssetDrawToolbar = () => showAssetDrawToolbar.value = !showAssetDrawToolbar.value;

  const initShowAssetDrawToolbar = (value) => {
    showAssetDrawToolbar.value = value;
  }

  return {
    showAssetDrawToolbar,
    toggleShowAssetDrawToolbar,
    initShowAssetDrawToolbar,
  }
}
