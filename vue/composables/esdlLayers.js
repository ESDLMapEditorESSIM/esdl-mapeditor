/**
 * A composable for managing ESDL layers currently active.
 * 
 * Currently, this operates directly on the shared global state, namely
 * window.esdl_list. That's not very nice, and it should be made local to this
 * composable, however then the state needs to be kept in sync with the regular JS
 * part of the application. That could be done through the PubSubManager, but that's
 * still experimental.
 */
import { ref } from "vue";


export function useEsdlLayers() {
    /**
     * Get all currently active ESDL layers. This is a object with as keys the ID of the layer.
     */
    const getEsdlLayers = () => ref(window.esdl_list);

    /**
     * Remove ESDL layer by ID.
     */
    const removeEsdlLayer = (id) => window.remove_esdl_layer(id);

    /**
     * Remove all ESDL layers, except for the provided ID. If not provided, it will keep the Untitled EnergySystem.
     */
    const clearEsdlLayers = (exceptId = null) => {
        const esdlLayers = getEsdlLayers().value;

        for (const id in esdlLayers) {
            const esdlLayer = esdlLayers[id];
            if ((exceptId != null && exceptId != id) || esdlLayer.title != 'Untitled EnergySystem') {
                window.remove_esdl_layer(id);
            }
        }
    }

    return {
        getEsdlLayers,
        removeEsdlLayer,
        clearEsdlLayers,
    }
}
