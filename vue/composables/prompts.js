import {ref} from "vue";

const promptQueue = ref([]);

export function usePrompts() {
    function enqueue(prompt) {
        promptQueue.value.push(prompt);
    }

    function shift() {
        promptQueue.value.shift();
    }

    return {
        promptQueue,
        enqueue,
        shift,
    };
}
