import { ref, watchEffect } from "vue";
import {useSocketIO} from "./socketio"

const showSidePane = ref(false);
const activeTabs = ref({});

export function useSidePane() {

    const toggleSidePaneView = () => showSidePane.value = !showSidePane.value;
    const hideSidePaneView = () => showSidePane.value = false;
    const showSidePaneView = () => showSidePane.value = true;

    const initTabs = (tabs) => {
        tabs.value.forEach((tab) => {
            activeTabs.value[tab.key] = tab.active;
            if (tab.active) {
                showSidePaneView();
            }
        });
    }

    const clickTab = (tabKey) => {
        if (!showSidePane.value) {
            showSidePaneView();
        } else {
            if (activeTabs.value[tabKey]) {
                hideSidePaneView();
                return;
            }
        }
        for (let tk in activeTabs.value) {
            activeTabs.value[tk] = false;
        }
        activeTabs.value[tabKey] = true;
    }

    const isActiveTab = (tabKey) => {
        return activeTabs.value[tabKey];
    }

    return {
        toggleSidePaneView,
        showSidePane,
        initTabs,
        clickTab,
        isActiveTab,
        activeTabs
    }
}
