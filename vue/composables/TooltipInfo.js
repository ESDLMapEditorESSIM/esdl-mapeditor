import { ref } from "vue";

export const tooltipObjectID = ref(null);
export const tooltipTitle = ref(null);

export function useTooltipInfo () {
    const newTooltipObjectID = (obj_id) => {
        tooltipObjectID.value = obj_id
    }

    const newTitle = (title) => {
        tooltipTitle.value = title
    }

    return {
        newTooltipObjectID,
        newTitle,
        tooltipObjectID,
        tooltipTitle
    }
}
