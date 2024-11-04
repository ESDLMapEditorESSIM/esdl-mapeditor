/**
 * The entrypoint for the Vue components. This file should contain all externally
 * available functions that trigger mounting a Vue Component to some part of the
 * DOM.
 */
import {createApp} from "vue";
import ControlStrategy from '@/apps/ControlStrategy.vue';
import MarginalCostsEdit from "@/apps/MarginalCostsEdit.vue";
import ObjectProperties from '@/apps/ObjectProperties.vue';
import EDRAssets from '@/apps/EDRAssets.vue';
import EnvironmentalProfiles from '@/apps/EnvironmentalProfiles.vue';
import AddEditWmsLayer from '@/apps/AddEditWmsLayer.vue';
import Carriers from '@/apps/Carriers.vue';
import Sectors from '@/apps/Sectors.vue';
import AboutBox from '@/apps/AboutBox.vue';
import ReleaseNotes from '@/apps/ReleaseNotes.vue';
import {useReleaseNotes} from "./composables/releaseNotes";
import ModelContext from "@/apps/ModelContext.vue";
import SearchAssets from '@/apps/SearchAssets.vue';
import AssetFeedback from '@/apps/AssetFeedback.vue';
import AssetTableEditor from '@/apps/AssetTableEditor.vue';
import CustomIconsSettings from "@/apps/CustomIconsSettings.vue";
import KPIDashboard from './apps/KPIDashboard.vue';
import ESDLAnalytics from './apps/ESDLAnalytics.vue';
import {
    createVueLControl,
    mountApp,
    mountSettingsComponent,
    mountSidebarComponent,
    mountTooltipComponent,
} from "./mounts";
import AssetsToBeAddedToolbar from '@/components/toolbars/AssetsToBeAddedToolbar.vue'
import AssetDrawToolbar from '@/components/toolbars/AssetDrawToolbar.vue'
import AssetDrawToolbarEDRAssetsSettings from '@/components/toolbars/AssetDrawToolbarEDRAssetsSettings.vue'
import AssetDrawToolbarStandardAssetsSettings from '@/components/toolbars/AssetDrawToolbarStandardAssetsSettings.vue'
import ToggleShowAssetDrawToolbar from '@/components/toolbars/ToggleShowAssetDrawToolbar.vue'
import {useWorkflow} from "@/composables/workflow";
import Workflow from "@/apps/Workflow.vue";
import ServicesToolbar from '@/components/toolbars/ServicesToolbar.vue'
import ToggleShowServicesToolbar from '@/components/toolbars/ToggleShowServicesToolbar.vue'
import {useObject} from '@/composables/ObjectID';
import {useAssetFeedbackList} from '@/composables/assetFeedback';
import {useTooltipInfo} from '@/composables/TooltipInfo';
import AssetTooltip from '@/apps/AssetTooltip.vue';
import ActiveLongProcess from '@/components/progress/ActiveProcess.vue'
import SidePane from "@/apps/SidePane.vue"
// import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import './bridge.js';
import Swal from "sweetalert2";
import AnnouceKPIsToolbar from "@/components/toolbars/AnnouceKPIsToolbar.vue";
import ActivityContextSelector from "@/apps/ActivityContextSelector.vue";
import ActivityContextManagement from "@/apps/admin/AdminDialog.vue";
import ResidentialArea from "@/apps/ResidentialArea.vue";
import HeatTransition from "@/apps/HeatTransition.vue";
import './utils/startDrawAsset';

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

window.show_tooltip = (object_title, object_id, el_id) => {
    const { newTooltipObjectID, newTitle } = useTooltipInfo();
    newTooltipObjectID(object_id);
    newTitle(object_title);
    mountTooltipComponent(AssetTooltip, el_id);
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

window.activate_admin_settings = () => {
    mountApp(ActivityContextManagement, '#admin_dialog_window');
}

window.add_edit_wms_layer = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(AddEditWmsLayer)
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

// mountApp(ModelContext, '#vue_model_context')

createVueLControl(ServicesToolbar, {position: 'topleft'});
createApp(ToggleShowServicesToolbar).mount('#vue_toggle_show_services_toolbar')

createVueLControl(AssetDrawToolbar, {});
createApp(ToggleShowAssetDrawToolbar).mount('#vue_toggle_show_asset_draw_toolbar')
mountApp(SidePane, '#vue_side_pane_root')
createApp(ActivityContextSelector).mount('#vue_activity_context_selector')

createVueLControl(AssetsToBeAddedToolbar, {
        position: 'bottomright',
    });

window.activate_table_editor_window = () => {
    mountApp(AssetTableEditor, '#table_editor_window');
}

window.activate_kpi_dashboard_window = () => {
    mountApp(KPIDashboard, '#kpi_dashboard_window');
}

window.activate_esdl_analytics_window = () => {
    mountApp(ESDLAnalytics, '#esdl_analytics_window');
}

createVueLControl(AnnouceKPIsToolbar, {
        position: 'bottomright',
    });

window.sectors_window = () => {
    mountSidebarComponent(Sectors);
}

mountApp(ResidentialArea, '#vue_test_edr_residential_area')

window.heat_transition_window = (area_id) => {
    const { newObject } = useObject();
    newObject(area_id);
    mountSidebarComponent(HeatTransition);
}
