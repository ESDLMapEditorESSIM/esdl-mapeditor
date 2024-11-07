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
            console.log(responseProject)
        });
    }

    function activeVariant() {
        return esdlProject.value.variants.find(variant => variant.id === esdlProject.value.active_variant_id);
    }

    const active_es_id = computed(() => esdlProject.value.active_es_id);

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    return {
        activeVariant,
        active_es_id,
        toggleProjectView,
        showProjectView,
        getESDLProject,
        esdlProject,
    }
}

PubSubManager.subscribe(MessageNames.GEOJSON_PROCESSED, (name, message) => {
    // Trigger the selection of the active layer if the active layer is the same as the layer that was processed.
    const {active_es_id} = useESDLProjects();
    if (active_es_id.value === message.es_id) {
        window.select_active_layer(active_es_id);
    }
});
