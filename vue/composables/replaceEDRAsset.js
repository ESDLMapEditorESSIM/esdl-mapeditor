import { ref, reactive } from "vue";

const assetIdList= ref();
const assetClass = ref();

export function useReplaceEDRAsset() {

    const newAssetInfo = (asset_id_list, asset_class) => {
        assetIdList.value = asset_id_list;
        assetClass.value = asset_class
    }

    return {
        assetClass,
        assetIdList,
        newAssetInfo
    }
}
