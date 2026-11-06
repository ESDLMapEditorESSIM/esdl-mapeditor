import {ref} from "vue";
import {MessageNames, PubSubManager} from "@/bridge";

const carriersByEsdlId = ref(new Map());

PubSubManager.subscribe(MessageNames.CARRIER_LIST, (name, message) => {
    carriersByEsdlId.value.set(message.es_id, message.carrier_list);
});

PubSubManager.subscribe(MessageNames.REMOVE_ESDL_LAYER, (name, message) => {
    carriersByEsdlId.value.delete(message.es_id);
});

PubSubManager.subscribe(MessageNames.CLEAR_ESDL_LAYER_LIST, () => {
    carriersByEsdlId.value.clear();
});

/** Access the carrier lists for loaded energy systems. */
export function useCarriers() {
    function getCarriers(esId) {
        return carriersByEsdlId.value.get(esId) || [];
    }

    return {getCarriers};
}
