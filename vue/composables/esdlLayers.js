/**
 * A composable for managing ESDL layers currently active.
 * 
 * Currently, this operates directly on the shared global state, namely
 * window.esdl_list. That's not very nice, and it should be made local to this
 * composable, however then the state needs to be kept in sync with the regular JS
 * part of the application. That could be done through the PubSubManager, but that's
 * still experimental.
 */
import {computed, ref} from "vue";
import {useVisibleLayers} from "@/composables/visibleLayers";
import {useSocketIO} from "@/composables/socketio";

const enabledEsdlIdList = ref([]);

export function useEsdlLayers() {
    const {addToVisibleLayerList, removeFromVisibleLayerList} = useVisibleLayers();

    /**
     * The list of ESDL layers currently present in the frontend. Not necessarily visible.
     */
    const esdlList = computed(() => window.esdl_list);

    const removeEsdlLayer = (id) => window.remove_esdl_layer(id);

    const getActiveEsdlLayerId = () => ref(window.active_layer_id);

    const clearEsdlLayers = (exceptId = null) => {
        for (const id in esdlList.value) {
            const esdlLayer = esdlList.value[id];
            if ((exceptId != null && exceptId !== id) || esdlLayer.title !== 'Untitled EnergySystem') {
                window.remove_esdl_layer(id);
            }
        }
    }

    /**
     * Enable an ESDL layer on the map. This makes it visible, however an enabled ESDL does not need to be visible;
     * visibility is managed hereafter in the visibleLayers composable.
     * @param es_id
     */
    function enableEsdl(es_id) {
        // Check if the ESDL layer is already enabled. If so, do nothing.
        if (enabledEsdlIdList.value.includes(es_id)) {
            return;
        }
        const es = esdlList.value[es_id];
        enabledEsdlIdList.value.push(es_id);
        Object.entries(es.layers).reverse().forEach(([key, esdl_layer]) => {
            const esdlLayer = {
                id: es_id + "_" + key,
                es_id: es_id,
                es: es,
                layer_type: key,
                layer_ref: esdl_layer
            };
            addToVisibleLayerList(esdlLayer);
        });
        showEsdlLayerOnMap(es_id);
    }

    /**
     * Disable an ESDL layer on the map.
     * @param es_id
     */
    function disableEsdl(es_id) {
        // Check if the ESDL layer is already disabled. If so, do nothing.
        if (!enabledEsdlIdList.value.includes(es_id)) {
            return;
        }
        const es = esdlList.value[es_id];
        enabledEsdlIdList.value = enabledEsdlIdList.value.filter(id => id !== es_id);
        Object.entries(es.layers).forEach(([key, esdl_layer]) => {
            const esdlLayerId = es_id + "_" + key;
            removeFromVisibleLayerList(esdlLayerId);
        });
        hideEsdlLayerFromMap(es_id);
    }

    function showEsdlLayerOnMap(es_id, layer_name) {
        window.show_esdl_layer_on_map(es_id, layer_name);
        window.set_leaflet_sizes();
    }

    function hideEsdlLayerFromMap(es_id, layer_name) {
        window.hide_esdl_layer_from_map(es_id, layer_name);
    }

    return {
        esdlList,
        removeEsdlLayer,
        clearEsdlLayers,
        getActiveEsdlLayerId,
        enableEsdl,
        disableEsdl,
        enabledEsdlIdList,
        showEsdlLayerOnMap,
        hideEsdlLayerFromMap,
    }
}


/**
 * This function sets up a subscription to the create_new_esdl_layer event. When this event is received, the ESDL layer
 * with the given ID is enabled in the map.
 */
function setupSubscription() {
    const {subscribe} = useSocketIO();
    const {enableEsdl} = useEsdlLayers();

    subscribe('create_new_esdl_layer', function(message) {
        enableEsdl(message.es_id);
    });
}

// Setup the subscription. Call this function outside the composable to start listening as soon as possible.
setupSubscription();
