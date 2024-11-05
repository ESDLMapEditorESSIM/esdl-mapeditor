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
import {useVisibleLayers, VisibleLayerType} from "@/composables/visibleLayers";
import {useSocketIO} from "@/composables/socketio";

const enabledEsdlIdList = ref([]);

export function useEsdlLayers() {
    const {createVisibleLayerGroup, addToVisibleLayerList, removeVisibleLayerGroup} = useVisibleLayers();

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
        if (es === undefined) {
            console.error("Could not find ESDL layer with ID " + es_id);
            return;
        }
        enabledEsdlIdList.value.push(es_id);
        createVisibleLayerGroup(es_id, es.title);
        Object.entries(es.layers).reverse().forEach(([key, esdl_layer]) => {
            console.log("esdl_layer", key, esdl_layer)
            /** @type {VisibleLayer} */
            const visibleEsdlLayer = {
                id: es_id + "_" + key,
                visible: true,
                description: key,
                es_id: es_id,
                es: es,
                layer_ref: esdl_layer
            };
            addToVisibleLayerList(visibleEsdlLayer, es_id);

            // Iterate over the _layers to find any sublayers we need to show.
            esdl_layer.eachLayer(function (sublayer) {
                if (sublayer.options.group_name) {
                    const sublayerId = es_id + "_" + key + "_" + sublayer.options.group_name;
                    const sublayerDescription = sublayer.options.group_name;
                    /** @type {VisibleLayer} */
                    const sublayerVisibleLayer = {
                        id: sublayerId,
                        visible: true,
                        description: sublayerDescription,
                        es_id: es_id,
                        parent_esdl_layer: key,
                        es: es,
                        layer_ref: sublayer
                    };
                    addToVisibleLayerList(sublayerVisibleLayer, es_id);
                }
            });
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
        enabledEsdlIdList.value = enabledEsdlIdList.value.filter(id => id !== es_id);
        removeVisibleLayerGroup(es_id);
        hideEsdlLayerFromMap(es_id);
    }

    function showEsdlLayerOnMap(es_id, layer_name, parent_esdl_layer) {
        window.show_esdl_layer_on_map(es_id, layer_name, parent_esdl_layer);
        window.set_leaflet_sizes();
    }

    function hideEsdlLayerFromMap(es_id, layer_name, parent_esdl_layer) {
        window.hide_esdl_layer_from_map(es_id, layer_name, parent_esdl_layer);
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
