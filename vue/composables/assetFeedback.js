import { ref } from "vue";

export const currentAssetFeedbackList = ref(null);

export function useAssetFeedbackList() {
    const newAssetFeedbackList = (asset_feedback_info) => {
        currentAssetFeedbackList.value = asset_feedback_info
    }

    return {
        newAssetFeedbackList,
        currentAssetFeedbackList
    }
}
