import {computed, ref} from "vue";

const WMS_LAYERS_GROUP_NAME = 'wms_layers';
const VISIBLE_LAYER_ORDER_STORAGE_KEY = 'visibleLayerOrder';

/** @type {import('vue').Ref<import('@/composables/visibleLayers').VisibleLayerGroup[]>} */
const visibleLayerGroups = ref([]);

/**
 * Checks if a stored layer order can be restored or saved.
 */
const shouldStoreLayerOrder = (groupId, order) => {
    return typeof groupId === 'string' &&
        groupId !== WMS_LAYERS_GROUP_NAME &&
        Array.isArray(order) &&
        order.every(id => typeof id === 'string');
};

/**
 * Restores per-ESDL layer order from localStorage.
 */
const loadLayerOrderCache = () => {
    const layerOrder = new Map();

    try {
        const storedLayerOrder = window.localStorage.getItem(VISIBLE_LAYER_ORDER_STORAGE_KEY);
        if (!storedLayerOrder) {
            return layerOrder;
        }

        const parsedLayerOrder = JSON.parse(storedLayerOrder);
        // Ignore unexpected data shapes so localStorage cannot break layer loading.
        if (!parsedLayerOrder || typeof parsedLayerOrder !== 'object' || Array.isArray(parsedLayerOrder)) {
            return layerOrder;
        }

        Object.entries(parsedLayerOrder).forEach(([groupId, order]) => {
            if (shouldStoreLayerOrder(groupId, order)) {
                layerOrder.set(groupId, order);
            }
        });
    } catch (e) {
        console.warn('Could not restore visible layer order.', e);
    }

    return layerOrder;
};

const layerOrderCache = ref(loadLayerOrderCache());
const layerVisibilityCache = ref({});

/**
 * Saves per-ESDL layer order to localStorage.
 */
const saveLayerOrderCache = () => {
    try {
        const storedLayerOrder = {};
        layerOrderCache.value.forEach((order, groupId) => {
            if (shouldStoreLayerOrder(groupId, order)) {
                storedLayerOrder[groupId] = order;
            }
        });
        window.localStorage.setItem(VISIBLE_LAYER_ORDER_STORAGE_KEY, JSON.stringify(storedLayerOrder));
    } catch (e) {
        console.warn('Could not save visible layer order.', e);
    }
};

/**
 * Updates the layer order cache and persists ESDL layer groups.
 */
const setLayerOrderCache = (groupId, order) => {
    if (typeof groupId !== 'string') {
        return;
    }

    layerOrderCache.value.set(groupId, order);
    if (groupId !== WMS_LAYERS_GROUP_NAME) {
        saveLayerOrderCache();
    }
};

const getDefaultGroupDescription = (groupId) => {
    return groupId === WMS_LAYERS_GROUP_NAME ? "Service layers" : "Untitled Group";
};

const getVisibleLayerList = () => {
    return visibleLayerGroups.value.reduce((acc, group) => {
        return acc.concat(group.layers);
    }, []);
};

const getVisibleLayerGroups = () => {
    return visibleLayerGroups.value;
};

const createVisibleLayerGroupState = (groupId, description = "Untitled Group") => {
    if (visibleLayerGroups.value.find(group => group.id === groupId)) {
        return false;
    }

    /** @type {import('@/composables/visibleLayers').VisibleLayerGroup} */
    const group = {
        id: groupId,
        visible: computed(() => {
            const thisGroup = visibleLayerGroups.value.find(group => group.id === groupId);
            return thisGroup.layers.some(layer => layer.visible);
        }),
        description,
        layers: [],
    };

    visibleLayerGroups.value.push(group);
    return true;
};

const addLayerToVisibleLayerGroup = (layer, groupId = WMS_LAYERS_GROUP_NAME) => {
    if (groupId === 0) {
        groupId = WMS_LAYERS_GROUP_NAME;
    }
    if (layer.id in layerVisibilityCache.value) {
        layer.visible = layerVisibilityCache.value[layer.id];
    } else if (layer.visible === undefined) {
        layer.visible = true;
    }

    let group = visibleLayerGroups.value.find(group => group.id === groupId);
    if (!group) {
        createVisibleLayerGroupState(groupId, getDefaultGroupDescription(groupId));
        group = visibleLayerGroups.value.find(group => group.id === groupId);
    }
    if (group) {
        const existingLayerIndex = group.layers.findIndex(l => l.id === layer.id);
        if (existingLayerIndex !== -1) {
            group.layers.splice(existingLayerIndex, 1, layer);
        } else {
            group.layers.push(layer);
        }
    }
    return group;
};

const removeLayerFromVisibleLayerGroups = (id) => {
    let layerToRemove;

    for (const group of visibleLayerGroups.value) {
        const layer = group.layers.find(layer => layer.id === id);
        if (layer !== undefined) {
            layerToRemove = layer;
            group.layers = group.layers.filter(layer => layer.id !== id);
        }
    }

    visibleLayerGroups.value = visibleLayerGroups.value.filter(group => group.layers.length > 0);
    return layerToRemove;
};

const layerIsVisible = (layerId) => {
    for (const visibleLayer of getVisibleLayerList()) {
        if (visibleLayer.id === layerId && visibleLayer.visible) {
            return true;
        }
    }
    return false;
};

const layerExists = (layerId) => {
    return getVisibleLayerList().find(layer => layer.id === layerId) !== undefined;
};

const getVisibleLayerById = (id) => {
    return getVisibleLayerList().find(layer => layer.id === id);
};

export function useVisibleLayerState() {
    return {
        addLayerToVisibleLayerGroup,
        createVisibleLayerGroupState,
        getVisibleLayerById,
        getVisibleLayerGroups,
        getVisibleLayerList,
        layerExists,
        layerIsVisible,
        layerOrderCache,
        layerVisibilityCache,
        removeLayerFromVisibleLayerGroups,
        setLayerOrderCache,
        visibleLayerGroups,
        WMS_LAYERS_GROUP_NAME
    };
}
