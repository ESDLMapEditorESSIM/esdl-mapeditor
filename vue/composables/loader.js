import {computed, reactive} from "vue";

export const LoaderScopes = Object.freeze({
    DEFAULT: "default",
    ESDL: "esdl",
});

const activeLoaders = reactive(new Map());
const scopedLoaderIds = [];
const loaderIdsByScope = new Map();
let nextLoaderId = 0;

export const loaderCount = computed(() => activeLoaders.size);
export const isLoading = computed(() => loaderCount.value > 0);

/**
 * Start a loader operation and return its unique ID.
 * @param scope
 * @returns {number}
 */
export function startLoader(scope) {
    nextLoaderId += 1;
    activeLoaders.set(nextLoaderId, scope);
    if (scope !== undefined) {
        scopedLoaderIds.push(nextLoaderId);
        if (!loaderIdsByScope.has(scope)) {
            loaderIdsByScope.set(scope, []);
        }
        loaderIdsByScope.get(scope).push(nextLoaderId);
    }
    return nextLoaderId;
}

function removeFromArray(values, value) {
    const index = values.lastIndexOf(value);
    if (index !== -1) {
        values.splice(index, 1);
    }
}

function removeLoader(loaderId) {
    if (!activeLoaders.has(loaderId)) {
        return false;
    }

    const scope = activeLoaders.get(loaderId);
    activeLoaders.delete(loaderId);
    if (scope !== undefined) {
        removeFromArray(scopedLoaderIds, loaderId);
        const scopeLoaderIds = loaderIdsByScope.get(scope);
        removeFromArray(scopeLoaderIds, loaderId);
        if (scopeLoaderIds.length === 0) {
            loaderIdsByScope.delete(scope);
        }
    }
    return true;
}

/**
 * Stop a loader operation by ID or scope, or the latest scoped loader when neither is provided.
 * @param loaderIdOrScope
 * @returns {boolean}
 */
export function stopLoader(loaderIdOrScope) {
    if (typeof loaderIdOrScope === "number") {
        return removeLoader(loaderIdOrScope);
    }

    let loaderId;
    if (loaderIdOrScope === undefined) {
        loaderId = scopedLoaderIds[scopedLoaderIds.length - 1];
    } else {
        const scopeLoaderIds = loaderIdsByScope.get(loaderIdOrScope);
        loaderId = scopeLoaderIds?.[scopeLoaderIds.length - 1];
    }
    if (loaderId === undefined) {
        return false;
    }
    return removeLoader(loaderId);
}

/**
 * Stop all loader operations.
 */
export function clearLoaders() {
    activeLoaders.clear();
    scopedLoaderIds.length = 0;
    loaderIdsByScope.clear();
}

/**
 * Access the shared loader state.
 */
export function useLoader() {
    return {
        activeLoaders,
        loaderCount,
        isLoading,
        startLoader,
        stopLoader,
        clearLoaders,
    };
}
