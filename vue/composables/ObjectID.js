import { ref } from "vue";

export const currentObjectID = ref(null);

export function useObject() {
    const newObject = (obj_id) => {
        currentObjectID.value = obj_id
    }

    return {
        newObject,
        currentObjectID
    }
}
