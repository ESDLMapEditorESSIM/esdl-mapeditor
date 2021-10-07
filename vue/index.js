/**
 * The entrypoint for the Vue components. This file should contain all externally
 * available functions that trigger mounting a Vue Component to some part of the
 * DOM.
 */
import { createApp } from "vue";
import ControlStrategy from './apps/ControlStrategy';
import ObjectProperties from './apps/ObjectProperties';
import EDRAssets from './apps/EDRAssets';
//import EsdlProfiles from './apps/EsdlProfiles';
import EnvironmentalProfiles from './apps/EnvironmentalProfiles';
import Carriers from './apps/Carriers.vue';
import AboutBox from './apps/AboutBox';
import SearchAssets from './apps/SearchAssets';
import AssetFeedback from './apps/AssetFeedback';
import { createVueLControl, mountApp, mountSidebarComponent, mountSettingsComponent } from "./mounts";
import AssetsToBeAddedToolbar from './components/toolbars/AssetsToBeAddedToolbar'
import AssetDrawToolbar from './components/toolbars/AssetDrawToolbar'
import AssetDrawToolbarEDRAssetsSettings from './components/toolbars/AssetDrawToolbarEDRAssetsSettings'
import AssetDrawToolbarStandardAssetsSettings from './components/toolbars/AssetDrawToolbarStandardAssetsSettings'
import ToggleShowAssetDrawToolbar from './components/toolbars/ToggleShowAssetDrawToolbar'
import { useWorkflow } from "./composables/workflow";
import Workflow from "./apps/Workflow";
import { useObject } from './composables/ObjectID';
import { useAssetFeedbackList } from './composables/assetFeedback';
// import ActiveLongProcess from './components/progress/ActiveProcess'
// import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import './bridge.js';


// Vue.config.productionTip = false

window.activate_service_workflow = (serviceIndex, service) => {
    const { startNewWorkflow } = useWorkflow();
    startNewWorkflow(serviceIndex, service);
    mountSidebarComponent(Workflow);
}

window.continue_service_workflow = () => {
    const { currentWorkflow } = useWorkflow();
    if (currentWorkflow.value) {
        mountSidebarComponent(Workflow);
    } else {
        alert("No workflow active.");
    }
}

window.control_strategy_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ControlStrategy);
}

window.carriers_window = () => {
    mountSidebarComponent(Carriers);
}

window.object_properties_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ObjectProperties);
}

window.edr_asset_window = () => {
    mountSidebarComponent(EDRAssets);
}

window.search_assets_window = () => {
    mountSidebarComponent(SearchAssets);
}

window.asset_feedback_window = (asset_feedback_info) => {
    const { newAssetFeedbackList } = useAssetFeedbackList();
    newAssetFeedbackList(asset_feedback_info);
    mountSidebarComponent(AssetFeedback);
}

//window.activate_esdl_profiles = () => {
//    mountApp(EsdlProfiles, '#settings_module_contents');
//}

window.activate_asset_draw_toolbar_edr_assets_settings = () => {
    mountSettingsComponent(AssetDrawToolbarEDRAssetsSettings);
    // mountApp(AssetDrawToolbarEDRAssetsSettings, '#settings_module_contents')
}

window.activate_asset_draw_toolbar_standard_assets_settings = () => {
    mountSettingsComponent(AssetDrawToolbarStandardAssetsSettings);
    // mountApp(AssetDrawToolbarStandardAssetsSettings, '#settings_module_contents')
}

window.environmental_profiles = () => {
    mountSidebarComponent(EnvironmentalProfiles);
}

// createVueLControl(ActiveLongProcess);
// mountApp(ToggleActiveLongProcess, '#vue_toggle_long_process_view');

createVueLControl(AssetDrawToolbar, {});
createApp(ToggleShowAssetDrawToolbar).mount('#vue_toggle_show_asset_draw_toolbar')
mountApp(AboutBox, '#vue_show_about_box')

createVueLControl(AssetsToBeAddedToolbar, {
        position: 'bottomright',
    });
