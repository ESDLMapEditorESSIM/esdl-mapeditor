import {computed, ref, watchEffect} from "vue";
import {useSocketIO} from "./socketio"
import {MessageNames, PubSubManager} from "@/bridge";


/**
 * @typedef {Object} Variant
 * @property {string} id
 * @property {string} name
 * @property {string} description
 * @property {number} nr_of_changes
 * @property {string} es_id
 * @property {boolean} active
 * @property {Variant[]} children
 * @property {Object[]} changes
 */

/**
 * @typedef {Object} ESDLProject
 * @property {string} name
 * @property {string} description
 * @property {Variant[]} variants
 * @property {string} active_variant_id
 * @property {string} active_es_id
 */

/** @type {import('vue').Ref<ESDLProject|null>} */
const esdlProject = ref(null);
const showProjectView = ref(true);

const {socket, subscribe} = useSocketIO();

/**
 * @param {ESDLProject} responseProject
 */
function setEsdlProject(responseProject) {
    console.debug("Setting ESDL Project:", responseProject);
    // In rare cases, the active_variant_id is not set. We ignore the response in that case.
    if (responseProject.active_variant_id) {
        esdlProject.value = responseProject;
    }

    // TODO: Fix syncing left and right layer actions
    //window.select_active_layer(responseProject.active_variant_id);
}

subscribe('update_active_esdl_project', (responseProject) => {
    if (responseProject) {
        setEsdlProject(responseProject);
    }
});

export function useESDLProjects() {
    function getESDLProject() {
        socket.value.emit('get_active_esdl_project', {}, (responseProject) => {
            if (responseProject) {
                setEsdlProject(responseProject);
            }
        });
    }

    /**
     * Get the active variant of the current ESDL project. Recursively check all variants and their children.
     * @returns {Variant}
     */
    function activeVariant() {
        function findActiveVariant(variants) {
            for (const variant of variants) {
                if (variant.active) {
                    return variant;
                }
                if (variant.children && variant.children.length > 0) {
                    const activeChild = findActiveVariant(variant.children);
                    if (activeChild) {
                        return activeChild;
                    }
                }
            }
            return null;
        }

        if (esdlProject.value && esdlProject.value.variants) {
            return findActiveVariant(esdlProject.value.variants);
        }
        
    }

    const active_es_id = computed(() => esdlProject.value.active_es_id);

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    function setActiveVariant(variantId) {
        console.debug("Setting active variant to ID " + variantId);
        const loaderScope = "set_active_variant"
        window.show_loader(loaderScope);
        socket.value.emit('set_active_variant', {id: variantId}, () => {
            window.hide_loader(loaderScope);
        });
    }

    return {
        activeVariant,
        setActiveVariant,
        active_es_id,
        toggleProjectView,
        showProjectView,
        getESDLProject,
        esdlProject,
        setEsdlProject,
    }
}
