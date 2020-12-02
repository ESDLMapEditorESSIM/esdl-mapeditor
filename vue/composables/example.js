/**
 * An example composable, broadcasting a shared state of a simple reactive counter,
 * and a function to increment this counter.
 * 
 * This can be used to test reactivity between components, but can be removed after
 * we have it up and running.
 */
import { readonly, ref } from "vue";

const count = ref(0);

export function useExampleState() {
  const increment = () => count.value++;

  return {
    count: readonly(count),
    increment,
  }
}
