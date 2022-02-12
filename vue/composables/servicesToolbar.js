import { ref } from "vue";

const showServicesToolbar = ref(false);

export function useServicesToolbar() {
  const toggleShowServicesToolbar = () => showServicesToolbar.value = !showServicesToolbar.value;

  const initShowServicesToolbar = (value) => {
    showServicesToolbar.value = value;
  }

  return {
    showServicesToolbar,
    toggleShowServicesToolbar,
    initShowServicesToolbar,
  }
}
