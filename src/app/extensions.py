"""
Application extension registration.
"""

from dataclasses import dataclass

from flask import Flask
from flask_executor import Executor
from flask_socketio import SocketIO

from esdl.ecore_documentation import EcoreDocumentation
from extensions.activity_context import ActivityContextExtension
from extensions.application_context import ApplicationContextExtension
from extensions.asset_constraint.asset_constraint import AssetConstraint
from extensions.bag import BAG
from extensions.boundary_service import BoundaryService
from extensions.data_manager.data_manager import DataManager
from extensions.es_statistics import ESStatisticsService
from extensions.esdl_api import ESDL_API
from extensions.esdl_browser import ESDLBrowser
from extensions.esdl_compare import ESDLCompare
from extensions.esdl_drive.esdl_drive import ESDLDrive
from extensions.esdl_merge import ESDLMerge
from extensions.essim import ESSIM
from extensions.essim_sensitivity import ESSIMSensitivity
from extensions.etm_interface import ETMInterface
from extensions.external_models.external_models import ExternalModels
from extensions.external_models.external_models_storage import ExternalModelsStorage
from extensions.heatnetwork import HeatNetwork
from extensions.ibis import IBISBedrijventerreinen
from extensions.layer_style.layer_style import LayerStyleEditor
from extensions.mapeditor_settings import MapEditorSettings
from extensions.ownership.ownership import Ownership
from extensions.pdtoolsuite_workflow.cost_information import CostInformation
from extensions.pdtoolsuite_workflow.pdtoolsuite_workflow import PDToolsuiteWorkflow
from extensions.pico_rooftoppv_potential import PICORooftopPVPotential
from extensions.port_profile_viewer import PortProfileViewer
from extensions.profiles import Profiles
from extensions.prompt_manager import PromptManager
from extensions.residential_area.residential_area import ResidentialArea
from extensions.settings_storage import SettingsStorage
from extensions.shapefile_converter import ShapefileConverter
from extensions.spatial_operations import SpatialOperations
from extensions.time_dimension import TimeDimension
from extensions.toast_notifications import ToastNotifications
from extensions.tooltip_info import TooltipInfo
from extensions.workflow import Workflow
from extensions.workflow_engine import WorkflowEngine
from src.asset_draw_toolbar import AssetDrawToolbar
from src.assets_to_be_added import AssetsToBeAdded
from src.custom_icons import CustomIcons
from src.datalayer_api import DataLayerAPI
from src.edr_client import EDRClient
from src.esdl2inlineprofile import ESDL2InlineProfile
from src.esdl2shapefile import ESDL2Shapefile
from src.esdl_file_import import ESDLFileImport
from src.esdl_file_io import ESDLFileIO
from src.esdl_services import ESDLServices
from src.essim_kpis import ESSIM_KPIs
from src.kpi_dashboard import KPIDashboard
from src.model_contexts import ModelContexts
from src.release_notes import ReleaseNotes
from src.table_editor import TableEditor
from src.tno.events_api import EventsAPI
from src.wms_layers import WMSLayers


@dataclass
class RegisteredExtensions:
    """
    Shared extension instances used by app.py after registration.
    """

    wms_layers: WMSLayers
    esdl_api: ESDL_API
    essim: ESSIM
    edr_client: EDRClient
    esdl_services: ESDLServices
    data_manager: DataManager


def register_extensions(
    app: Flask,
    socketio: SocketIO,
    executor: Executor,
    settings_storage: SettingsStorage,
    models_storage: ExternalModelsStorage,
    esdl_doc: EcoreDocumentation,
) -> RegisteredExtensions:
    """
    Register the MapEditor extension classes and return shared instances.
    """
    toast_notifications = ToastNotifications(app, socketio)
    PromptManager(app, socketio)
    wms_layers = WMSLayers(app, socketio, settings_storage)
    HeatNetwork(app, socketio)
    IBISBedrijventerreinen(app, socketio)
    ESDLBrowser(app, socketio, esdl_doc)
    BAG(app, socketio)
    BoundaryService(app, socketio, settings_storage)
    esdl_api = ESDL_API(app, socketio)
    ESDLCompare(app, socketio)
    ESDLMerge(app, socketio, executor)
    essim_kpis = ESSIM_KPIs(app, socketio)
    essim = ESSIM(app, socketio, executor, essim_kpis, settings_storage)
    ESSIMSensitivity(app, socketio, settings_storage, essim)
    Workflow(app, socketio, settings_storage, executor)
    PDToolsuiteWorkflow(app, socketio, executor, settings_storage)
    CostInformation(app)
    ESStatisticsService(app, socketio)
    MapEditorSettings(app, socketio, settings_storage)
    edr_client = EDRClient(app, socketio, settings_storage)
    Profiles(app, socketio, executor, settings_storage)
    ESDLDrive(app, socketio, executor)
    ShapefileConverter(app, socketio, executor)
    TimeDimension(app, socketio, executor, settings_storage)
    ETMInterface(app, socketio, settings_storage)
    PortProfileViewer(app, socketio, settings_storage)
    esdl_services = ESDLServices(app, socketio, settings_storage, models_storage)
    PICORooftopPVPotential(app, socketio)
    SpatialOperations(app, socketio)
    DataLayerAPI(app, socketio, esdl_doc)
    EventsAPI(app, socketio, settings_storage)
    ModelContexts(app, socketio, settings_storage)
    AssetsToBeAdded(app, socketio)
    AssetDrawToolbar(app, socketio, settings_storage)
    TableEditor(app, socketio, esdl_doc, settings_storage)
    ESDLFileIO(app, socketio, executor)
    ESDLFileImport(app, socketio, executor)
    ReleaseNotes(app, socketio, settings_storage)
    ESDL2Shapefile(app)
    ESDL2InlineProfile(app)
    CustomIcons(app, socketio, settings_storage)
    KPIDashboard(app, socketio, settings_storage)
    TooltipInfo(app, socketio)
    ActivityContextExtension(app, socketio, settings_storage)
    ApplicationContextExtension(app, socketio, settings_storage)
    ResidentialArea(app, socketio, settings_storage)
    Ownership(app)
    LayerStyleEditor(app, socketio, settings_storage)
    AssetConstraint(app)
    data_manager = DataManager(app, socketio, settings_storage)
    ExternalModels(app, socketio, models_storage, toast_notifications)
    WorkflowEngine(app, socketio, models_storage, esdl_services, toast_notifications)

    return RegisteredExtensions(
        wms_layers=wms_layers,
        esdl_api=esdl_api,
        essim=essim,
        edr_client=edr_client,
        esdl_services=esdl_services,
        data_manager=data_manager,
    )
