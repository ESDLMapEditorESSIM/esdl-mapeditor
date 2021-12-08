import { ref, watchEffect } from "vue";
import {useSocketIO} from "./socketio"

/*
Currently loaded energy project.
Fields:
    - name: The project name.
    - base_variant:
        - name
        - children
 */
const esdlProject = ref(null);
const showProjectView = ref(true);

const {socket} = useSocketIO();

watchEffect(() => {
    if (socket.value) {
        socket.value.on('update_active_esdl_project', (responseProject) => {
            console.log("updating active esdl project")
            if (responseProject) {
                esdlProject.value = responseProject;
            }
        });
    }
});

export function useESDLProjects() {
    function getESDLProject() {
        socket.value.emit('get_active_energy_project', {}, (responseProject) => {
            if (responseProject) {
                esdlProject.value = responseProject;
            }
        });
    }

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    return {
        toggleProjectView,
        showProjectView,
        getESDLProject,
        esdlProject,
    }
}
