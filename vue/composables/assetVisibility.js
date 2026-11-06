import {computed, ref} from "vue";
import {MessageNames, PubSubManager} from "@/bridge";
import {carrierToken} from "@/utils/assetCarrierClasses";

const selectedCarrierByEsdlId = ref(new Map());
const hideOthersByEsdlId = ref(new Map());

const filterCss = computed(() => {
    return Array.from(selectedCarrierByEsdlId.value, ([esId, carrierId]) => {
        const systemClass = window.CSS.escape(`esdl-carrier-system-${carrierToken(esId)}`);
        const carrierClass = window.CSS.escape(`esdl-carrier-${carrierToken(carrierId)}`);
        const selector = `.leaflet-container .${systemClass}:not(.${carrierClass})`;
        if (hideOthersByEsdlId.value.get(esId)) {
            return `${selector} { display: none !important; }`;
        }
        return `${selector} { opacity: 0.35 !important; pointer-events: none !important; }
${selector}.esdl-connection { opacity: 0.06 !important; }`;
    }).join("\n");
});

PubSubManager.subscribe(MessageNames.CARRIER_LIST, (name, message) => {
    const selected = selectedCarrierByEsdlId.value.get(message.es_id);
    if (!message.carrier_list.some(carrier => carrier.id === selected)) {
        selectedCarrierByEsdlId.value.delete(message.es_id);
    }
});

PubSubManager.subscribe(MessageNames.REMOVE_ESDL_LAYER, (name, message) => {
    selectedCarrierByEsdlId.value.delete(message.es_id);
    hideOthersByEsdlId.value.delete(message.es_id);
});

PubSubManager.subscribe(MessageNames.CLEAR_ESDL_LAYER_LIST, () => {
    selectedCarrierByEsdlId.value.clear();
    hideOthersByEsdlId.value.clear();
});

/** Manage the carrier filter without changing Leaflet layer membership. */
export function useAssetVisibility() {
    function toggleCarrier(esId, carrierId) {
        if (!carrierId || selectedCarrierByEsdlId.value.get(esId) === carrierId) {
            selectedCarrierByEsdlId.value.delete(esId);
        } else {
            selectedCarrierByEsdlId.value.set(esId, carrierId);
        }
    }

    return {filterCss, selectedCarrierByEsdlId, hideOthersByEsdlId, toggleCarrier};
}
