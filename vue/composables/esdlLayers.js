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
import {LoaderScopes, useLoader} from "@/composables/loader";
import {displayNotification} from "@/utils/notification";
import {useEsdlLayerMapActions} from "./esdlLayerMapActions";
import {PLAN_LAYER_NAME, usePlans} from "@/composables/plans";

/** @type {import('vue').Ref<string[]>} */
const enabledEsdlIdList = ref([]);

const esdlLoadingStatus = ref({});
const esdlLoaderIds = new Map();
// finishEsdlLoad deletes esdlLoadingStatus entries, so track completion separately for isEsdlLoaded.
const completedEsdlIds = new Set();

const {hideEsdlLayerFromMap, showEsdlLayerOnMap} = useEsdlLayerMapActions();
const {startLoader, stopLoader} = useLoader();

export function useEsdlLayers() {
    const {createVisibleLayerGroup, removeVisibleLayerGroup, hideVisibleLayer, showVisibleLayer} = useVisibleLayers();
    const {getPlans} = usePlans();

    /**
     * Get all currently active ESDL layers. This is a object with as keys the ID of the layer.
     */
    const getEsdlLayers = () => ref(window.esdl_list);

    /**
     * Get the ID of the active ESDL layer.
     */
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
        /** @type {import('@/composables/visibleLayers').VisibleLayer[]} */
        const sublayers = [];

        Object.entries(es.layers).reverse().forEach(([esLayerName, esdl_layer]) => {
            if (esLayerName === PLAN_LAYER_NAME && getPlans(es_id).length === 0) {
                return;
            }
            esdl_layer.eachLayer(function (sublayer) {
                // Handle logical groups. Add each logical group as their own sublayer, and descend recursively
                if (sublayer.options.group_name) {
                    // A logical group.
                    const logicalGroupId = es_id + "_" + esLayerName + "_" + sublayer.options.group_name;
                    const logicalGroupName = sublayer.options.group_name;

                    const logicalGroupVisibleLayer = {
                        id: logicalGroupId,
                        visible: true,
                        description: logicalGroupName,
                        es_id: es_id,
                        es_layer_name: esLayerName,
                        es: es,
                        layer_refs: [sublayer],
                        child_layers: [],
                    };
                    sublayers.push(logicalGroupVisibleLayer);

                    // Recursively collect deeper levels.
                    const descendants = collectAllLayers(sublayer);
                    // Group into L1, L2, L3...
                    const levels = groupByLevels(descendants);

                    // For each level, create a visible layer entry
                    levels.forEach((levelNodes, index) => {
                        const levelNumber = index + 1;
                        const levelId = `${logicalGroupId}_L${levelNumber}`;
                        const levelName = `${logicalGroupName} L${levelNumber}`;

                        const sublevelVisibleLayer = {
                            id: levelId,
                            visible: true,
                            description: levelName,
                            es_id: es_id,
                            es_layer_name: esLayerName,
                            es: es,
                            layer_refs: levelNodes.map(n => n.layer_ref ?? n)
                        };
                        logicalGroupVisibleLayer.child_layers.push(sublevelVisibleLayer);
                        sublayers.push(sublevelVisibleLayer);
                        levelNodes.forEach(n => {
                            // Set this for use in hiding and showing them on the map. See multi_esdl.js.
                            n.options.level_name = levelName;
                            n.options.group_name = logicalGroupName;
                        });
                    });
                }
            });

            // Add the root esdl_layer. This is "area" or "kpi".
            /** @type {import('@/composables/visibleLayers').VisibleLayer} */
            const visibleEsdlLayer = {
                id: `${es_id}_${esLayerName}`,
                visible: true,
                description: esLayerName,
                es_id: es_id,
                es: es,
                layer_refs: [esdl_layer]
            };
            sublayers.push(visibleEsdlLayer);

        });
        console.log(sublayers)
        createVisibleLayerGroup(es_id, es.title, sublayers);
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
        getEsdlLayers,
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
    MessageNames.PLANS,
    MessageNames.ADD_BUILDING_OBJECTS,
    MessageNames.ADD_ESDL_OBJECTS,
    MessageNames.AREA_BLD_LIST,
    MessageNames.ADD_CONNECTIONS,
    MessageNames.ADD_NOTES,
];

/**
 * Add a status to the ESDL loading status object.
 * @param esId
 * @param status
 */
function addEsdlLoadingStatus(esId, status) {
    if (!esdlLoadingStatus.value[esId]) {
        return;
    }
    esdlLoadingStatus.value[esId].add(status);
}

/**
 * Check if all messages have been received for the given ESDL.
 * @param esId
 * @returns {boolean}
 */
function isEsdlLoaded(esId) {
    return completedEsdlIds.has(esId) ||
           MANDATORY_ESDL_LOADING_MESSAGES.every((messageName) => esdlLoadingStatus.value[esId]?.has(messageName));
}

/**
 * Finish an ESDL load and remove its progress state.
 * @param esId
 */
function finishEsdlLoad(esId) {
    completedEsdlIds.add(esId);
    const loaderId = esdlLoaderIds.get(esId);
    if (loaderId !== undefined) {
        stopLoader(loaderId);
    }
    esdlLoaderIds.delete(esId);
    delete esdlLoadingStatus.value[esId];
}

/**
 * Clear all active ESDL loads.
 */
function clearEsdlLoadingStatus() {
    completedEsdlIds.clear();
    for (const loaderId of esdlLoaderIds.values()) {
        stopLoader(loaderId);
    }
    esdlLoaderIds.clear();
    esdlLoadingStatus.value = {};
}


/**
 * Recursively collect sublayers of a given layer.
 * @param layer - The layer to collect sublayers from.
 */
export function collectAllLayers(layer) {
    if (typeof layer.eachLayer !== 'function') {
        return [layer];
    }
    const result = [];
    layer.eachLayer(function (child) {
        const descendants = collectAllLayers(
            child,
        );
        result.push(...descendants);
    });
    return result;
}

export function groupByLevels(descendants) {
    const byId = new Map(descendants.map(d => [d.id, d]));
    const allIds = new Set(byId.keys());

    // Level 1 = nodes whose parent is not one of the other IDs.
    const level1 = descendants.filter(
        d => !allIds.has(d.parent_area_id)
    );

    const build = (currentLevel, assigned) => {
        if (currentLevel.length === 0) {
            return [];
        }

        const nextAssigned = new Set([
            ...assigned,
            ...currentLevel.map(d => d.id),
        ]);

        const currentLevelIds = new Set(currentLevel.map(d => d.id));

        const nextLevel = descendants.filter(
            d => !nextAssigned.has(d.id) && currentLevelIds.has(d.parent_area_id)
        );

        return [
            currentLevel,
            ...build(nextLevel, nextAssigned),
        ];
    };

    return build(level1, new Set());
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
        clearEsdlLoadingStatus();
        stopLoader(LoaderScopes.ESDL);
    });

    PubSubManager.subscribe(MessageNames.ESDL_LOAD_STARTED, (name, message) => {
        const esId = message.es_id;
        if (!esId) {
            console.error("Cannot start ESDL load without an ESDL ID");
            return;
        }
        if (esdlLoaderIds.has(esId)) {
            finishEsdlLoad(esId);
        }
        stopLoader(LoaderScopes.ESDL);
        esdlLoadingStatus.value[esId] = new Set();
        completedEsdlIds.delete(esId); // reset on reload so isEsdlLoaded is false until the new load completes
        esdlLoaderIds.set(esId, startLoader());
        console.debug("Started loading ESDL with ID " + esId);
    });

    PubSubManager.subscribe(MessageNames.ESDL_LOAD_FAILED, (name, message) => {
        stopLoader(LoaderScopes.ESDL);
        if (message.es_id) {
            finishEsdlLoad(message.es_id);
        }
        console.error("Failed loading ESDL with ID " + message.es_id, message.error);
        displayNotification("error", message.error);
    });

    const esdlLoadingStatusHandler = (name, message) => {
        const esId = message.es_id;
        if (!esId || !esdlLoadingStatus.value[esId]) {
            return;
        }

        addEsdlLoadingStatus(esId, name);
        console.debug("Received message " + name + " for ESDL with ID " + esId);
        if (isEsdlLoaded(esId)) {
            console.debug("All messages received for ESDL with ID " + esId);
            finishEsdlLoad(esId);
        }
    };

    for (const messageName of MANDATORY_ESDL_LOADING_MESSAGES) {
        PubSubManager.subscribe(messageName, esdlLoadingStatusHandler);
    }
}

// Setup the subscription. Call this function outside the composable to start listening as soon as possible.
setupSubscription();
