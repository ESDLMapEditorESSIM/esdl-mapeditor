/**
 * A composable for managing ESDL layers currently active.
 * 
 * Currently, this operates directly on the shared global state, namely
 * window.esdl_list. That's not very nice, and it should be made local to this
 * composable, however then the state needs to be kept in sync with the regular JS
 * part of the application. That could be done through the PubSubManager, but that's
 * still experimental.
 */
import {ref} from "vue";
import {useVisibleLayers} from "@/composables/visibleLayers";
import {MessageNames, PubSubManager} from "@/bridge";
import {useToasts} from "@/composables/toasts";

const {showToast} = useToasts();

/** @type {import('vue').Ref<string[]>} */
const enabledEsdlIdList = ref([]);

const esdlLoadingStatus = ref({});

export function useEsdlLayers() {
    const {createVisibleLayerGroup, removeVisibleLayerGroup, hideVisibleLayer, showVisibleLayer} = useVisibleLayers();

    const getActiveEsdlLayerId = () => ref(window.active_layer_id);

    const clearEsdlLayers = (exceptId = null) => {
        for (const id in window.esdl_list) {
            const esdlLayer = window.esdl_list[id];
            if ((exceptId != null && exceptId !== id) || esdlLayer.title !== 'Untitled EnergySystem') {
                window.remove_esdl_layer(id);
            }
        }
    }

    /**
     * Enable an ESDL layer on the map. This makes it visible, however an enabled ESDL does not need to be visible;
     * visibility is managed hereafter in the visibleLayers composable.
     * @param es_id
     * @param force_redo
     */
    function enableEsdl(es_id, force_redo = false) {
        console.debug("Enabling ESDL layer with ID " + es_id);
        // Check if the ESDL layer is already enabled. If so, do nothing (unless forced).
        if (enabledEsdlIdList.value.includes(es_id)) {
            if (force_redo) {
                disableEsdl(es_id);
            } else {
                return;
            }
        }
        const es = window.esdl_list[es_id];
        if (es === undefined) {
            console.error("Could not find ESDL layer with ID " + es_id, window.esdl_list);
            return;
        }
        enabledEsdlIdList.value.push(es_id);
        const sublayers = [];
        Object.entries(es.layers).reverse().forEach(([key, esdl_layer]) => {
            esdl_layer.eachLayer(function (sublayer) {
                if (sublayer.options.group_name) {
                    const sublayerId = es_id + "_" + key + "_" + sublayer.options.group_name;
                    const sublayerDescription = sublayer.options.group_name;
                    const sublayerVisibleLayer = {
                        id: sublayerId,
                        visible: true,
                        description: sublayerDescription,
                        es_id: es_id,
                        parent_esdl_layer: key,
                        es: es,
                        layer_ref: sublayer
                    };
                    sublayers.push(sublayerVisibleLayer);
                }
            });
            const visibleEsdlLayer = {
                id: es_id + "_" + key,
                visible: true,
                description: key,
                es_id: es_id,
                es: es,
                layer_ref: esdl_layer
            };
            sublayers.push(visibleEsdlLayer);
        });
        createVisibleLayerGroup(es_id, es.title, sublayers);
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

    function disableAllEsdls() {
        enabledEsdlIdList.value.forEach((es_id) => {
            disableEsdl(es_id);
        });
    }

    function showEsdlLayerOnMap(es_id, layer_name, parent_esdl_layer) {
        window.show_esdl_layer_on_map(es_id, layer_name, parent_esdl_layer);
        window.set_leaflet_sizes();
    }

    function hideEsdlLayerFromMap(es_id, layer_name, parent_esdl_layer) {
        window.hide_esdl_layer_from_map(es_id, layer_name, parent_esdl_layer);
    }

    /**
     * Iterate over all enabled ESDL IDs, and call hideVisibleLayer for each of them.
     * @param layer_name
     */
    function hideEsdlLayerAllEsdls(layer_name) {
        enabledEsdlIdList.value.forEach((es_id) => {
            const layerId = es_id + "_" + layer_name;
            hideVisibleLayer(layerId);
        });
    }

    /**
     * Iterate over all enabled ESDL IDs, and call showVisibleLayer for each of them.
     * @param layer_name
     */
    function showEsdlLayerAllEsdls(layer_name) {
        enabledEsdlIdList.value.forEach((es_id) => {
            const layerId = es_id + "_" + layer_name;
            showVisibleLayer(layerId);
        });
    }

    return {
        clearEsdlLayers,
        getActiveEsdlLayerId,
        disableAllEsdls,
        enableEsdl,
        disableEsdl,
        enabledEsdlIdList,
        showEsdlLayerOnMap,
        hideEsdlLayerFromMap,
        hideEsdlLayerAllEsdls,
        showEsdlLayerAllEsdls,
        isEsdlLoaded,
    }
}

/**
 * A list of message names that are mandatory for loading an ESDL. This is used to check if all messages have been
 * received for a specific ESDL.
 * @type {(string)[]}
 */
const MANDATORY_ESDL_LOADING_MESSAGES = [
    MessageNames.CREATE_NEW_ESDL_LAYER,
    MessageNames.CARRIER_LIST,
    MessageNames.ADD_BUILDING_OBJECTS,
    MessageNames.ADD_ESDL_OBJECTS,
    MessageNames.AREA_BLD_LIST,
    MessageNames.ADD_CONNECTIONS,
    MessageNames.ADD_NOTES,
];

/**
 * Add a status to the ESDL loading status object.
 * @param es_id
 * @param status
 */
function addEsdlLoadingStatus(es_id, status) {
    if (!esdlLoadingStatus.value[es_id]) {
        esdlLoadingStatus.value[es_id] = new Set();
    }
    esdlLoadingStatus.value[es_id].add(status);
}

/**
 * Check if all messages have been received for the given ESDL ID.
 * @param es_id
 * @returns {this is (string)[]}
 */
function isEsdlLoaded(es_id) {
    return MANDATORY_ESDL_LOADING_MESSAGES.every((messageName) => esdlLoadingStatus.value[es_id]?.has(messageName));
}

/**
 * This function sets up a subscription to the create_new_esdl_layer event. When this event is received, the ESDL layer
 * with the given ID is enabled in the map.
 */
function setupSubscription() {
    const {enableEsdl, disableAllEsdls, disableEsdl} = useEsdlLayers();

    PubSubManager.subscribe(MessageNames.GEOJSON_PROCESSED, (name, message) => {
        // Only at this point is the complete area layer available in the frontend. So we now enable the ESDL layer,
        // so that it is checked in the UI and is visible on the map.
        if (message.layer === 'area_layer') {
            enableEsdl(message.es_id, true);
        }
    });
    PubSubManager.subscribe(MessageNames.REMOVE_ESDL_LAYER, (name, message) => {
        disableEsdl(message.es_id);
    });
    PubSubManager.subscribe(MessageNames.CLEAR_ESDL_LAYER_LIST, () => {
        disableAllEsdls();
    });

    const esdlLoadingStatusHandler = (name, message) => {
        const es_id = message.es_id;
        addEsdlLoadingStatus(es_id, name);
        console.debug("Received message " + name + " for ESDL with ID " + es_id);
        window.show_loader("es")
        // Check if all message names are in the esdlLoadingStatus. If so, hide the loader.
        if (isEsdlLoaded(es_id)) {
            console.debug("All messages received for ESDL with ID " + es_id);
            window.hide_loader("es");
        }
    }

    for (const messageName of MANDATORY_ESDL_LOADING_MESSAGES) {
        PubSubManager.subscribe(messageName, esdlLoadingStatusHandler);
    }
}

// Setup the subscription. Call this function outside the composable to start listening as soon as possible.
setupSubscription();
