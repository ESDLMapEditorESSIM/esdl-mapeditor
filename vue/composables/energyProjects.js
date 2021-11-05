import { ref } from "vue";

const energyProject = ref({});

export function useEnergyProjects() {

    return {
        energyProject,
    }
}
