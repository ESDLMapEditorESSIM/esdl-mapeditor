/**
 * The entrypoint for the Vue components. This file should contain all externally
 * available functions that trigger mounting a Vue Component to some part of the
 * DOM.
 */
import { createApp } from "vue";
import ControlStrategy from './apps/ControlStrategy';
import ObjectProperties from './apps/ObjectProperties';
import EDRAssets from './apps/EDRAssets';
import { createVueLControl, mountApp, mountSidebarComponent } from "./mounts";
import AssetDrawToolbar from './components/toolbars/AssetDrawToolbar'
import ToggleShowAssetDrawToolbar from './components/toolbars/ToggleShowAssetDrawToolbar'
import { useWorkflow } from "./composables/workflow";
import Workflow from "./apps/Workflow";
import { useObject } from './composables/ObjectID';
import ActiveLongProcess from './components/progress/ActiveProcess'
import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import './bridge.js';


// Vue.config.productionTip = false

window.activate_service_workflow = (serviceIndex, service) => {
    const { startNewWorkflow } = useWorkflow();
    startNewWorkflow(serviceIndex, service);
    mountSidebarComponent(Workflow);
}

window.continue_service_workflow = () => {
    mountSidebarComponent(Workflow);
}

window.control_strategy_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ControlStrategy);
}

window.object_properties_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ObjectProperties);
}

window.edr_asset_window = () => {
    mountSidebarComponent(EDRAssets);
}

createVueLControl(ActiveLongProcess);
mountApp(ToggleActiveLongProcess, '#vue_toggle_long_process_view');

createVueLControl(AssetDrawToolbar);
createApp(ToggleShowAssetDrawToolbar).mount('#vue_toggle_show_asset_draw_toolbar')
