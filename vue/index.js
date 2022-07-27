/**
 * The entrypoint for the Vue components. This file should contain all externally
 * available functions that trigger mounting a Vue Component to some part of the
 * DOM.
 */
import {createApp} from "vue";
import ControlStrategy from './apps/ControlStrategy';
import ObjectProperties from './apps/ObjectProperties';
import EDRAssets from './apps/EDRAssets';
import EnvironmentalProfiles from './apps/EnvironmentalProfiles';
import Carriers from './apps/Carriers.vue';
import AboutBox from './apps/AboutBox';
import ReleaseNotes from './apps/ReleaseNotes';
import {useReleaseNotes} from "./composables/releaseNotes";
import SearchAssets from './apps/SearchAssets';
import AssetFeedback from './apps/AssetFeedback';
import AssetTableEditor from './apps/AssetTableEditor';
import {createVueLControl, mountApp, mountSettingsComponent, mountSidebarComponent} from "./mounts";
import AssetsToBeAddedToolbar from './components/toolbars/AssetsToBeAddedToolbar'
import AssetDrawToolbar from './components/toolbars/AssetDrawToolbar'
import AssetDrawToolbarEDRAssetsSettings from './components/toolbars/AssetDrawToolbarEDRAssetsSettings'
import AssetDrawToolbarStandardAssetsSettings from './components/toolbars/AssetDrawToolbarStandardAssetsSettings'
import ToggleShowAssetDrawToolbar from './components/toolbars/ToggleShowAssetDrawToolbar'
import {useWorkflow} from "./composables/workflow";
import Workflow from "./apps/Workflow";
import ServicesToolbar from './components/toolbars/ServicesToolbar'
import ToggleShowServicesToolbar from './components/toolbars/ToggleShowServicesToolbar'
import {useObject} from './composables/ObjectID';
import {useAssetFeedbackList} from './composables/assetFeedback';
import ActiveLongProcess from './components/progress/ActiveProcess'
// import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import './bridge.js';
import Swal from "sweetalert2";


// Vue.config.productionTip = false

window.activate_service_workflow = async (serviceIndex, service) => {
    const { startNewWorkflow, currentWorkflow } = useWorkflow();
    if (currentWorkflow.value && currentWorkflow.value.restartable) {
        const result = await Swal.fire({
          title: "Would you like to continue the currently active workflow?",
          icon: 'question',
          showDenyButton: true,
          confirmButtonText: "Yes",
          denyButtonText: "No, start from the beginning",
        })
        if (result.isDenied) {
            startNewWorkflow(serviceIndex, service);
        }
    } else {
        startNewWorkflow(serviceIndex, service);
    }
    mountSidebarComponent(Workflow);
    // window.sidebar.on("hide", closeWorkflow);
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
    console.log('object_properties_list', object_id)
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

createVueLControl(ActiveLongProcess, {position: 'bottomright'});
// mountApp(ToggleActiveLongProcess, '#vue_toggle_long_process_view');
mountApp(AboutBox, '#vue_show_about_box')
mountApp(ReleaseNotes, '#vue_show_release_notes')
window.show_new_release_notes = () => {
   const { showNewReleaseNotes } = useReleaseNotes();
   // show new release notes if any...
   showNewReleaseNotes();
}

createVueLControl(ServicesToolbar, {position: 'topleft'});
createApp(ToggleShowServicesToolbar).mount('#vue_toggle_show_services_toolbar')

createVueLControl(AssetDrawToolbar, {});
createApp(ToggleShowAssetDrawToolbar).mount('#vue_toggle_show_asset_draw_toolbar')

createVueLControl(AssetsToBeAddedToolbar, {
        position: 'bottomright',
    });

window.activate_table_editor_window = () => {
    mountApp(AssetTableEditor, '#table_editor_window');
}
