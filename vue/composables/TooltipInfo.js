import { ref } from "vue";

export const tooltipObjectID = ref(null);
export const tooltipTitle = ref(null);
export const tooltipESid = ref(null);

export function useTooltipInfo () {
    const newTooltipObjectID = (obj_id) => {
        tooltipObjectID.value = obj_id
    }

    const newTitle = (title) => {
        tooltipTitle.value = title
    }

    const newESid = (es_id) => {
        tooltipESid.value = es_id
    }

    return {
        newTooltipObjectID,
        newTitle,
        newESid,
        tooltipObjectID,
        tooltipTitle,
        tooltipESid
    }
}
