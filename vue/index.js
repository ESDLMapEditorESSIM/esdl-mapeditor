/**
 * The entrypoint for the Vue components. This file should contain all externally
 * available functions that trigger mounting a Vue Component to some part of the
 * DOM.
 */
import {createApp} from "vue";
import ControlStrategy from './apps/ControlStrategy';
import MarginalCostsEdit from "./apps/MarginalCostsEdit";
import ObjectProperties from './apps/ObjectProperties';
import EDRAssets from './apps/EDRAssets';
import EnvironmentalProfiles from './apps/EnvironmentalProfiles';
import Carriers from './apps/Carriers.vue';
import Sectors from './apps/Sectors.vue';
import AboutBox from './apps/AboutBox';
import ReleaseNotes from './apps/ReleaseNotes';
import {useReleaseNotes} from "./composables/releaseNotes";
import SearchAssets from './apps/SearchAssets';
import AssetFeedback from './apps/AssetFeedback';
import KPIDashboard from './apps/KPIDashboard';
import AssetTableEditor from './apps/AssetTableEditor';
import CustomIconsSettings from "./apps/CustomIconsSettings";
import {
    createVueLControl,
    mountApp,
    mountSettingsComponent,
    mountSidebarComponent,
    mountTooltipComponent,
} from "./mounts";
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
import {useTooltipInfo} from './composables/TooltipInfo';
import AssetTooltip from './apps/AssetTooltip';
import ActiveLongProcess from './components/progress/ActiveProcess'
// import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import './bridge.js';
import Swal from "sweetalert2";
import AnnouceKPIsToolbar from "./components/toolbars/AnnouceKPIsToolbar";


// Vue.config.productionTip = false

window.activate_service_workflow = async (serviceIndex, service, state) => {
    const { startNewWorkflow, currentWorkflow } = useWorkflow();
    if (currentWorkflow.value && currentWorkflow.value.resumable) {
        const result = await Swal.fire({
          title: "Would you like to resume the currently active workflow?",
          icon: 'question',
          showDenyButton: true,
          confirmButtonText: "Yes",
          denyButtonText: "No, start from the beginning",
        })
        if (result.isDenied) {
            startNewWorkflow(serviceIndex, service, state);
        }
    } else {
        startNewWorkflow(serviceIndex, service, state);
    }
    mountSidebarComponent(Workflow);
}

window.control_strategy_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ControlStrategy);
}

window.marginal_costs_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(MarginalCostsEdit);
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

window.show_tooltip = (object_title, object_id) => {
    const { newTooltipObjectID, newTitle } = useTooltipInfo();
    newTooltipObjectID(object_id);
    newTitle(object_title);
    mountTooltipComponent(AssetTooltip);
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

window.activate_custom_icons_settings = () => {
    mountSettingsComponent(CustomIconsSettings);
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

window.activate_kpi_dashboard_window = () => {
    mountApp(KPIDashboard, '#kpi_dashboard_window');
}

createVueLControl(AnnouceKPIsToolbar, {
        position: 'bottomright',
    });

window.sectors_window = () => {
    mountSidebarComponent(Sectors);
}
