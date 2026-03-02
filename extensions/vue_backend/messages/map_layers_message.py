from dataclasses import dataclass
from typing import Dict, List, Optional, Union

@dataclass
class MouseEventLatLng:
    """Leaflet MouseClick event object"""
    lat: float
    lng: float

@dataclass
class WmsLayerRequestInfo:
    """
    WMS layer info. passed from frontend to backend to request the layer feature properties.
    """
    name: str
    """WMS layer name"""
    url: str
    """WMS layer GetFeatureInfo Url"""

@dataclass
class WmsLayerFeatureRequestBody:
    """
    The request body passed from frontend to backend for querying WMS layers features.
    """
    ev_lat_lng: MouseEventLatLng
    """Geographical LatLng property of the Leaflet MouseClick event"""
    layers: List[WmsLayerRequestInfo]
    """List of WmsLayerRequestInfo used for querying WMS layers features"""

@dataclass
class LayerFeaturePropsResp:
    """
    Layer feature properties response
    """
    name: str
    """Layer name"""
    feature_props: Optional[Dict]
    """Layer feature properties in dictionary. None is returned when the request is not successful."""

@dataclass
class WmsLayerFeatureResp:
    """
    The response passed from backend to frontend after receiving WMS layers features properties.
    """
    ev_lat_lng: MouseEventLatLng
    """Geographical LatLng property of the Leaflet MouseClick event"""
    layers_features_props: List[LayerFeaturePropsResp]
    """List of WMS layers features properties query response dictionary"""

@dataclass
class GetCapabilitiesRequestBody:
    """
    The request body passed from the frontend to the backend for fetching web service GetCapabilities.
    """
    url: str
    """WMS/WFS service URL"""
    service_type: str
    """"WMS" or "WFS"""

@dataclass
class ServiceLayerInfo:
    """
    The extracted layer information required by the frontend from the requested WMS/WFS service.
    """
    name: str
    """Layer name"""
    title: str
    """Layer title"""
    legend_url: Optional[str]
    """Layer legend URL. Only applicable for WMS layer"""

@dataclass
class ServiceGetCapabilitiesResp:
    """
    The response of the service GetCapabilities request passed from the backend to the frontend.
    """
    success: bool
    """GetCapabilities request is successful or not"""
    result: Union[List[ServiceLayerInfo], str]
    """If successful, a list of ServiceLayerInfo is returned; Otherwise, an error message is returned"""

@dataclass
class LayerOpacitySettingRequestBody:
    """
    The request body passed from the frontend to the backend for keeping the layer opacity setting in the settings_storage.
    """
    layer_id: str
    """Layer id"""
    opacity: float
    """Layer opacity"""