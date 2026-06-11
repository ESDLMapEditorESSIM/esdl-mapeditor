import {computed, ref} from "vue";

const WMS_LAYERS_GROUP_NAME = 'wms_layers';

/** @type {import('vue').Ref<import('@/composables/visibleLayers').VisibleLayerGroup[]>} */
const visibleLayerGroups = ref([]);

const layerOrderCache = ref({});
const layerVisibilityCache = ref({});

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
    } else {
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
        visibleLayerGroups,
        WMS_LAYERS_GROUP_NAME
    };
}
