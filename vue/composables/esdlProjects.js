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

function setEsdlProject(responseProject) {
    console.log("Setting ESDL Project:", responseProject);
    esdlProject.value = responseProject;
}

watchEffect(() => {
    if (socket.value) {
        socket.value.on('update_active_esdl_project', (responseProject) => {
            if (responseProject) {
                setEsdlProject(responseProject);
            }
            window.hide_loader();
        });
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

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    return {
        toggleProjectView,
        showProjectView,
        getESDLProject,
        esdlProject,
    }
}
