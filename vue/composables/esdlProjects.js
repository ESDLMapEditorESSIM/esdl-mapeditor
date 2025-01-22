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
    esdlProject.value = responseProject;

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

    function activeVariant() {
        return esdlProject.value.variants.find(variant => variant.id === esdlProject.value.active_variant_id);
    }

    const active_es_id = computed(() => esdlProject.value.active_es_id);

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    function setActiveVariant(variantId, esId) {
        const loaderScope = "set_active_variant"
        window.show_loader(loaderScope);
        socket.value.emit('set_active_variant', {id: variantId}, () => {
            window.hide_loader(loaderScope);
        });
        if (esId) {
            // TODO: This doesn't work until the active variant is done generating.
            // window.select_active_layer(esId);
        }
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
