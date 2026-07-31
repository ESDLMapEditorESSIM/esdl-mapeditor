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
import AddEditServiceLayer from '@/apps/AddEditServiceLayer.vue';
import Carriers from '@/apps/Carriers.vue';
import Sectors from '@/apps/Sectors.vue';
import AboutBox from '@/apps/AboutBox.vue';
import ReleaseNotes from '@/apps/ReleaseNotes.vue';
import {useReleaseNotes} from "./composables/releaseNotes";
import SearchAssets from '@/apps/SearchAssets.vue';
import AssetFeedback from '@/apps/AssetFeedback.vue';
import AssetTableEditor from '@/apps/AssetTableEditor.vue';
import CustomIconsSettings from "@/apps/CustomIconsSettings.vue";
import ExternalServiceSettings from "@/apps/ExternalServiceSettings.vue";
import KPIDashboard from '@/apps/KPIDashboard.vue';
import ESDLAnalytics from '@/apps/ESDLAnalytics.vue';
import OwnershipDialog from '@/apps/OwnershipDialog.vue';
import PortProfileEditor from "@/apps/PortProfileEditor.vue";
import PortProfileViewer from '@/apps/PortProfileViewer.vue';
import {
    createVueLControl,
    createVueMapEditorDialog,
    mountApp,
    mountSettingsComponent,
    mountSidebarComponent,
    mountSidebarBottomComponent,
    mountTooltipComponent,
} from "./mounts";
import UndoRedoControl from "./apps/UndoRedoControl";
import UndoRedoMenu from "./components/toolbars/UndoRedoMenu";
import ToggleShowUndoRedoControl from './components/toolbars/ToggleShowUndoRedoControl'
import LoadProjectFileButton from './components/projects/LoadSaveProjectButtons';
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
import ActiveLongProcess from '@/components/progress/ActiveProcess.vue'
import SidePane from "@/apps/SidePane.vue"
// import ToggleActiveLongProcess from './components/progress/ToggleActiveLongProcess'
import {useTooltipInfo} from './composables/TooltipInfo';
import "./composables/toasts.js";
import AssetTooltip from './apps/AssetTooltip';
import './bridge.js';
import Swal from "sweetalert2";
import {useUndoRedo} from "./composables/undoRedo";
import ActivityContextSelector from "@/apps/ActivityContextSelector.vue";
import ActivityContextManagement from "@/apps/admin/AdminDialog.vue";
import ApplicationContextSelector from "@/apps/application-context/ApplicationContextSelector.vue";
import ResidentialArea from "@/apps/ResidentialArea.vue";
import HeatTransition from "@/apps/HeatTransition.vue";
import './utils/startDrawAsset';
import ResultVisualizationsToolbar from "@/components/toolbars/ResultVisualizationsToolbar.vue";
import ETMInterface from "@/apps/ETMInterface.vue";
import {useReplaceEDRAsset} from "@/composables/replaceEDRAsset";
import ToastNotifications from "@/apps/ToastNotifications.vue";
import PromptDialog from "@/apps/PromptDialog.vue";

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

window.activate_port_profile_editor = (es_id, object_id) => {
    const { newObject } = useObject();
    newObject({
        es_id: es_id,
        object_id: object_id
    });
    mountSidebarComponent(PortProfileEditor);
}


window.activate_port_profile_viewer = (es_id, object_id) => {
    const { newObject } = useObject();
    newObject({
        es_id: es_id,
        object_id: object_id
    });
    mountSidebarBottomComponent(PortProfileViewer);
}

window.marginal_costs_window = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(MarginalCostsEdit);
}

window.carriers_window = () => {
    mountSidebarComponent(Carriers);
}

window.object_properties_active_panels = null;
window.object_properties_window = (object_id) => {
    console.log('object_properties_list', object_id)
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(ObjectProperties);
}

window.edr_asset_window = () => {
    mountSidebarComponent(EDRAssets);
}

window.etm_interface_window = () => {
    mountSidebarComponent(ETMInterface);
}

window.show_tooltip = (object_title, object_id, el_id, es_id) => {
    const { newTooltipObjectID, newTitle, newESid } = useTooltipInfo();
    newTooltipObjectID(object_id);
    newTitle(object_title);
    newESid(es_id);
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

window.activate_external_service_management_settings = () => {
    mountSettingsComponent(ExternalServiceSettings);
}

window.environmental_profiles = () => {
    mountSidebarComponent(EnvironmentalProfiles);
}

window.activate_admin_settings = () => {
    mountApp(ActivityContextManagement, '#admin_dialog_window');
}

window.add_edit_web_service_layer = (object_id) => {
    const { newObject } = useObject();
    newObject(object_id);
    mountSidebarComponent(AddEditServiceLayer)
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
mountApp(ToggleShowServicesToolbar, '#vue_toggle_show_services_toolbar')

const {undoRedoMapEditorDialog, showUndoRedoControl} = useUndoRedo();
const mapEditorDialog = createVueMapEditorDialog(UndoRedoControl, {
    initOpen: false,
    size: [300, 500],
    maxSize: [2000, 1200],
    onClose: () => showUndoRedoControl.value = false,
});
mapEditorDialog._handleMinimize();
undoRedoMapEditorDialog.value = mapEditorDialog;
mountApp(ToggleShowUndoRedoControl, '#vue_toggle_show_undo_redo_control');
var mountEl = document.querySelector("#vue_undo_menu");
createApp(UndoRedoMenu, {...mountEl.dataset}).mount('#vue_undo_menu');
mountEl = document.querySelector("#vue_redo_menu");
createApp(UndoRedoMenu, {...mountEl.dataset}).mount('#vue_redo_menu');

createVueLControl(AssetDrawToolbar, {});
mountApp(ToggleShowAssetDrawToolbar, '#vue_toggle_show_asset_draw_toolbar')
mountApp(SidePane, '#vue_side_pane_root')
createApp(ActivityContextSelector).mount('#vue_activity_context_selector')
createApp(ApplicationContextSelector).mount('#vue_application_context_selector')

mountApp(LoadProjectFileButton, '#vue_load_project_file')

const [,toastNotificationInstance] = mountApp(ToastNotifications, '#toast_notifications');
import {useToastNotifications} from "@/composables/toastNotifications";
const {setToastNotificationsInstance } = useToastNotifications();
setToastNotificationsInstance(toastNotificationInstance);

mountApp(PromptDialog, '#prompt_dialog');

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

window.activate_ownership_window = () => {
    mountApp(OwnershipDialog, '#ownership_window');
}

createVueLControl(ResultVisualizationsToolbar, {
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

window.replace_with_edr_asset = (object_id_list, object_class) => {
    const { newAssetInfo } = useReplaceEDRAsset();
    newAssetInfo(object_id_list, object_class);
    mountSidebarComponent(EDRAssets)
}
