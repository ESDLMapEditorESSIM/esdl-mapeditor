import { ref } from "vue";

/*
Currently loaded energy project.
Fields:
    - name: The project name.
    - base_variant:
        - name
        - children
 */
const energyProject = ref(null);

const showProjectView = ref(true);

export function useEnergyProjects() {
    function getActiveEnergyProject() {
        window.socket.emit('get_active_energy_project', {}, (responseProject) => {
            console.log(responseProject);
            if (responseProject) {
                energyProject.value = responseProject;
            }
        });
    }

    const toggleProjectView = () => showProjectView.value = !showProjectView.value;

    return {
        toggleProjectView,
        showProjectView,
        getActiveEnergyProject,
        energyProject,
    }
}
